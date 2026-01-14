"""
phemex_ohlcv_source.py: Modular class for fetching, updating, and caching OHLCV data from Phemex (API + WebSocket).
- Uses ccxt for historical data (with proxy support)
- Uses websocket for live updates
- Normalizes and saves data to CSV for backtesting
- Thread-safe access to in-memory data
"""
import sys
import os
import time
import threading
import pandas as pd
import ccxt
from websocket import WebSocketApp
from dotenv import load_dotenv
import json
from src.exchange.config import load_config
from typing import Callable, Optional, Dict, Any

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception

# Enhanced TokenBucket Rate Limiting (updated with official Hyperliquid specs)
from src.utils.token_bucket import TokenBucket
from src.data.api_rate_monitor import record_api_call, get_api_monitor, async_record_api_call, async_get_exchange_status, async_export_dashboard_data, async_monitor_concurrent_calls

load_dotenv()

PHEMEX_API_KEY_TRADE = os.environ.get("PHEMEX_API_KEY_TRADE")
PHEMEX_API_SECRET_TRADE = os.environ.get("PHEMEX_API_SECRET_TRADE")

logger = setup_logger('phemex_ohlcv_source', json_logs=True)

class PhemexOHLCVDataSource:
    """
    Data source for fetching, updating, and caching OHLCV data from Phemex.
    Supports both historical (REST) and live (WebSocket) data, with thread-safe access.
    """
    def __init__(self, output_dir: str = os.path.join(project_root, 'data')) -> None:
        # Build config dict with proper typing to satisfy type checker
        config: Dict[str, Any] = {
            'rateLimit': True,  # Changed from enableRateLimit to rateLimit for newer CCXT versions
        }
        try:
            cfg = load_config()
            api_key = cfg.get('phemex_api_key') or os.environ.get("PHEMEX_API_KEY_TRADE")
            api_secret = cfg.get('phemex_api_secret') or os.environ.get("PHEMEX_API_SECRET_TRADE")
            if api_key:
                config['apiKey'] = api_key
            if api_secret:
                config['secret'] = api_secret
        except Exception as e:
            logger.warning(f'Could not load Phemex API credentials from central config loader: {e}')
        self.phemex = ccxt.phemex(config)  # type: ignore[arg-type]
        # Phemex: CCXT rateLimit 100ms = 10 req/sec (OFFICIAL)  
        self.phemex_bucket = TokenBucket(100, 10.0, "Phemex_OHLCV", enable_caching=False, cache_ttl=60)  # OFFICIAL specs
        # Removed ProxyManager - using direct connections only
        self.ohlcv_data: Dict[str, pd.DataFrame] = {}
        self.ohlcv_data_lock = threading.Lock()
        self.last_updates: Dict[str, Any] = {}
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.ws_endpoint = "wss://ws.phemex.com"
        self.max_candles = 1000
        self.timeframes = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "12h": 43200, "1d": 86400}

    def convert_seconds_to_timeframe(self, seconds: int) -> str:
        """
        Convert seconds to a Phemex timeframe string.
        """
        return next((tf for tf, sec in self.timeframes.items() if sec == seconds), "5m")

    @retry_on_exception()
    def fetch_historical_data(self, symbol: str, timeframe: str, limit: int = 1000, retries: int = 3) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a symbol and timeframe, with direct connection (NO PROXIES).
        Returns a DataFrame with columns: timestamp, open, high, low, close, volume.
        """
        wait = self.phemex_bucket.wait_time()
        if wait > 0:
            time.sleep(wait)
        if not self.phemex_bucket.consume():
            # Handle rate limit (retry/backoff/skip)
            logger.warning("Rate limit prevented API call, returning empty DataFrame", extra={"symbol": symbol, "timeframe": timeframe})
            return pd.DataFrame()
        start = time.time()

        api_symbol = symbol[1:] if symbol.startswith('s') else symbol
        logger.debug(f"[PHEMEX] Fetching OHLCV: input_symbol='{symbol}' -> api_symbol='{api_symbol}' timeframe={timeframe}")
        success = False
        for attempt in range(retries + 1):
            try:
                # DIRECT CONNECTION - NO PROXIES
                temp_config: Dict[str, Any] = {
                    'rateLimit': True,  # Changed from enableRateLimit to rateLimit for newer CCXT versions
                    'timeout': 15000,
                }
                if PHEMEX_API_KEY_TRADE is not None:
                    temp_config['apiKey'] = PHEMEX_API_KEY_TRADE
                if PHEMEX_API_SECRET_TRADE is not None:
                    temp_config['secret'] = PHEMEX_API_SECRET_TRADE
                    
                temp_phemex = ccxt.phemex(temp_config)  # type: ignore[arg-type]
                # API call symbol_discovery_Hyperliquid_meta consume 1 if it worked!!!
                # also if fail consume 1!!!
                ohlcv = temp_phemex.fetch_ohlcv(api_symbol, timeframe=timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
                df['timestamp'] = df['timestamp'].values  # Remove timezone info to match local format
                success = True
                record_api_call('phemex', '/ohlcv', method='GET', success=success, response_time = time.time() - start, tokens_consumed=1)
                logger.info(f'Successfully fetched the OHLCV data for: {symbol}')
                return df
            except Exception as e:
                success = False
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error("Failed to fetch data", extra={"symbol": symbol, "timeframe": timeframe, "error": str(e)})
                    record_api_call('phemex', '/ohlcv', method='GET', success=success, response_time = time.time() - start, tokens_consumed=0)
                    logger.error(f'Failed to fetch the OHLCV data for: {symbol}')
        # If all retries failed, return an empty DataFrame
        return pd.DataFrame()



    def normalize_ohlcv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure DataFrame has correct columns and types for OHLCV data.
        """
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = df[cols].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        for col in cols[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.sort_values('timestamp').reset_index(drop=True)

    def save_to_csv(self, symbol: str, timeframe: str) -> None:
        """
        Save cached OHLCV data to CSV for a given symbol and timeframe.
        """
        with self.ohlcv_data_lock:
            if symbol in self.ohlcv_data:
                fname = os.path.join(self.output_dir, f"{symbol}_{timeframe}.csv")
                self.ohlcv_data[symbol].to_csv(fname, index=False)

    def load_from_csv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        Load OHLCV data from CSV if available, and cache it in memory.
        """
        fname = os.path.join(self.output_dir, f"{symbol}_{timeframe}.csv")
        if os.path.exists(fname):
            df = pd.read_csv(fname, parse_dates=['timestamp'])
            with self.ohlcv_data_lock:
                self.ohlcv_data[symbol] = self.normalize_ohlcv(df)
            return self.ohlcv_data[symbol]
        return pd.DataFrame()

    def get_ohlcv(self, symbol: str) -> pd.DataFrame:
        """
        Thread-safe getter for in-memory OHLCV data for a symbol.
        """
        with self.ohlcv_data_lock:
            return self.ohlcv_data.get(symbol, pd.DataFrame()).copy()

    def update_ohlcv(self, symbol: str, df: pd.DataFrame) -> None:
        """
        Thread-safe setter for in-memory OHLCV data for a symbol.
        """
        with self.ohlcv_data_lock:
            self.ohlcv_data[symbol] = self.normalize_ohlcv(df)

# Example usage:
# Allow running this file directly without setting PYTHONPATH
#if __name__ == '__main__':
#    try:
#        # simple demo: fetch 5 recent 1h candles for sAAVEUSDT and print
#        ds = PhemexOHLCVDataSource()
#        df = ds.fetch_historical_data('sAAVEUSDT', '2h', limit=5, retries=2)
#        ds2 = PhemexOHLCVDataSource()
#        df2 = ds2.fetch_historical_data('sPAXGUSDT', '1h', limit=5, retries=2)
#
#        if df is None or df.empty:
#            print('No data returned (network or symbol issue)')
#        else:
#            print(df.tail().to_string())
#
#        if df2 is None or df2.empty:
#            print('No data returned (network or symbol issue)')
#        else:
#            print(df2.tail().to_string())
#    except Exception as e:
#        print('Error running demo:', e)
