import os
import sys
import requests
import pandas as pd
import datetime
import time

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception

# Enhanced TokenBucket Rate Limiting (updated with official Hyperliquid specs)
from src.utils.token_bucket import TokenBucket
from src.data.api_rate_monitor import record_api_call

logger = setup_logger('hyperliquid_ohlcv_source', json_logs=True)

class HyperliquidOHLCVDataSource:
    def __init__(self):
        self.base_url = "https://api.hyperliquid.xyz/info"
        # Hyperliquid: Official SDK specs = 100 capacity, 10 tokens/sec (FULL OFFICIAL CAPACITY - NOT CONSERVATIVE!)
        self.hyperliquid_bucket = TokenBucket(100, 10.0, "Hyperliquid_OHLCV", enable_caching=False, cache_ttl=60)  # FULL official specs

    @retry_on_exception()
    def fetch_historical_data(self, symbol: str, timeframe: str, lookback_days: int = 30, retries: int = 3) -> pd.DataFrame:
        # timeframe: '1m', '5m', '15m', '30m', '1h', '2h', '4h', '12h", '1d'
        wait = self.hyperliquid_bucket.wait_time()
        if wait > 0:
            time.sleep(wait)
        if not self.hyperliquid_bucket.consume():
            # Handle rate limit (retry/backoff/skip)
            logger.warning("Rate limit prevented API call, returning empty DataFrame", extra={"symbol": symbol, "timeframe": timeframe})
            return pd.DataFrame()
        start = time.time()
        
        success = False
        for attempt in range(retries + 1):
            try:
                end_time = datetime.datetime.now()
                start_time = end_time - datetime.timedelta(days=lookback_days)
                payload = {
                    'type': 'candleSnapshot',
                    'req': {
                        'coin': symbol,
                        'interval': timeframe,
                        'startTime': int(start_time.timestamp() * 1000),
                        'endTime': int(end_time.timestamp() * 1000)
                    }
                }
                logger.info(f"[HyperliquidOHLCV] POST {self.base_url} with: {payload}")
                resp = requests.post(self.base_url, headers={'Content-Type': 'application/json'}, json=payload)
                if resp.status_code != 200:
                    success = False
                    record_api_call('hyperliquid', '/ohlcv', method='POST', success=success, response_time=time.time()-start, tokens_consumed=1)
                    logger.error(f"[HyperliquidOHLCV] Error {resp.status_code} for symbol '{symbol}'. Response: {resp.content}")
                    return pd.DataFrame()
                data = resp.json()
                if not data:
                    success = False
                    record_api_call('hyperliquid', '/ohlcv', method='POST', success=success, response_time=time.time()-start, tokens_consumed=1)
                    logger.warning(f"[HyperliquidOHLCV] No data returned for symbol '{symbol}' and timeframe '{timeframe}'")
                    return pd.DataFrame()
                # Convert snapshot data to DataFrame
                columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                rows = []
                for candle in data:
                    rows.append([
                        datetime.datetime.fromtimestamp(candle['t'] / 1000),
                        candle['o'], candle['h'], candle['l'], candle['c'], candle['v']
                    ])
                df = pd.DataFrame(rows, columns=columns)
                logger.info(f"[HyperliquidOHLCV] Success for symbol: {symbol}, shape: {df.shape}")
                success = True
                record_api_call('hyperliquid', '/ohlcv', method='POST', success=success, response_time=time.time()-start, tokens_consumed=1)
                return df
            except Exception as e:
                success = False
                if attempt < retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error("Failed to fetch data", extra={"symbol": symbol, "timeframe": timeframe, "error": str(e)})
                    response_time = time.time() - start
                    record_api_call('hyperliquid', '/ohlcv', method='GET', success=success, response_time=response_time, tokens_consumed=0)
                    logger.error(f'Failed to fetch the OHLCV data for: {symbol}')
        # If all retries failed, return an empty DataFrame
        return pd.DataFrame()

# Example usage:
# Allow running this file directly without setting PYTHONPATH
if __name__ == '__main__':
    try:
        # simple demo: fetch 5 recent 1h, 2h candles and print
        ds = HyperliquidOHLCVDataSource()
        df = ds.fetch_historical_data('BTC', '1m', lookback_days=5)
        #ds2 = HyperliquidOHLCVDataSource()
        #df2 = ds2.fetch_historical_data('ETH', '1h', lookback_days=5)

        if df is None or df.empty:
            print('No data returned (network or symbol issue)')
        else:
            print(df.tail().to_string())

        #if df2 is None or df2.empty:
        #    print('No data returned (network or symbol issue)')
        #else:
        #    print(df2.tail().to_string())
    except Exception as e:
        print('Error running demo:', e)                        
