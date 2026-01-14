import os
import sys
import ccxt
import pandas as pd
import time

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception

# Enhanced TokenBucket Rate Limiting (updated with official Hyperliquid specs)
from src.utils.token_bucket import TokenBucket
from src.data.api_rate_monitor import record_api_call

logger = setup_logger('coinbase_ohlcv_source', json_logs=True)

class CoinbaseOHLCVDataSource:
    def __init__(self):
        self.exchange = ccxt.coinbaseadvanced()
        # Coinbase: CCXT rateLimit 334ms = ~3 req/sec (OFFICIAL)
        self.coinbase_bucket = TokenBucket(30, 3.0, "Coinbase_OHLCV", enable_caching=False, cache_ttl=60)  # OFFICIAL specs

    def get_spot_symbols(self, retries: int = 3) -> pd.DataFrame:
        wait = self.coinbase_bucket.wait_time()
        if wait > 0:
            time.sleep(wait)
        if not self.coinbase_bucket.consume():
            # Handle rate limit (retry/backoff/skip)
            logger.warning("Rate limit prevented API call, returning empty DataFrame")
            return pd.DataFrame()
        start = time.time()

        success = False
        for attempt in range(retries + 1):
            try:
                markets = self.exchange.load_markets()
                logger.info(f"[CoinbaseOHLCV] Success fetching load_markets in the ohlcv module")
                success = True
                record_api_call('coinbase', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                # Only spot markets, filter out derivatives if present
                symbols = [symbol for symbol, info in markets.items() if info.get('spot')]
                df_symbols = pd.DataFrame(symbols, columns=['symbol'])
                return df_symbols
            except Exception as e:
                success = False
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    record_api_call('coinbase', '/load_markets', method='GET', success=False, response_time=time.time()-start, tokens_consumed=1)
                    logger.error(f"[CoinbaseOHLCV] Error fetching load_markets in the ohlcv module: {e}")
                    return pd.DataFrame()
        # If all retries failed, return an empty DataFrame
        return pd.DataFrame()

    @retry_on_exception()
    def fetch_historical_data(self, symbol: str, timeframe: str, limit: int = 1000, retries: int = 3) -> pd.DataFrame:
        # timeframe: '1m', '5m', '15m', '30m', '1h', '2h', '6h', '1d'
        # limit: max number of candles (CoinbasePro default is 300, but CCXT may allow more)
        wait = self.coinbase_bucket.wait_time()
        if wait > 0:
            time.sleep(wait)
        if not self.coinbase_bucket.consume():
            # Handle rate limit (retry/backoff/skip)
            logger.warning("Rate limit prevented API call, returning empty DataFrame", extra={"symbol": symbol, "timeframe": timeframe})
            return pd.DataFrame()
        start = time.time()

        success = False
        for attempt in range(retries + 1):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
                df['timestamp'] = df['timestamp'].values  # Remove timezone info to match local format
                record_api_call('coinbase', '/fetch_ohlcv', method='GET', success=True, response_time=time.time()-start, tokens_consumed=1)
                success = True
                return df
            except Exception as e:
                success = False
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    record_api_call('coinbase', '/fetch_ohlcv', method='GET', success=False, response_time=time.time()-start, tokens_consumed=1)
                    print(f"[CoinbaseOHLCV] Error fetching {symbol} {timeframe}: {e}")
                    return pd.DataFrame()
        # If all retries failed, return an empty DataFrame
        return pd.DataFrame()

# Example usage:
# Allow running this file directly without setting PYTHONPATH
#if __name__ == '__main__':
#    try:
#        # simple demo fetch_symbols
#        ds1 = CoinbaseOHLCVDataSource()
#        df1 = ds1.get_spot_symbols()
#        # simple demo: fetch 5 recent 1h, 2h candles and print
#        ds2 = CoinbaseOHLCVDataSource()
#        df2 = ds2.fetch_historical_data('BTC-USDC', '2h', limit=5)
#        ds3 = CoinbaseOHLCVDataSource()
#        df3 = ds3.fetch_historical_data('ETH-USDC', '1h', limit=5)
#
#        if df1 is None or df1.empty:
#            print('No data returned (network or symbol issue)')
#        else:
#            print(df1.tail().to_string())
#
#        if df2 is None or df2.empty:
#            print('No data returned (network or symbol issue)')
#        else:
#            print(df2.tail().to_string())
#
#        if df3 is None or df3.empty:
#            print('No data returned (network or symbol issue)')
#        else:
#            print(df3.tail().to_string())
#    except Exception as e:
#        print('Error running demo:', e)                        
