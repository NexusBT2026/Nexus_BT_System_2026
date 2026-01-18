"""
KuCoin OHLCV Data Source
Provides clean interface for fetching KuCoin Spot OHLCV data using REST API
"""

import os
import sys
import requests
import pandas as pd
import datetime
import time
from typing import Optional

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception

# Enhanced TokenBucket Rate Limiting
from src.utils.token_bucket import TokenBucket
from src.data.api_rate_monitor import record_api_call

logger = setup_logger('kucoin_ohlcv_source', json_logs=True)

class KucoinOHLCVDataSource:
    def __init__(self):
        self.base_url = "https://api.kucoin.com"
        # KuCoin: Conservative rate limiting (adjust based on VIP level)
        self.kucoin_bucket = TokenBucket(100, 5.0, "KuCoin_OHLCV", enable_caching=False, cache_ttl=60)

    @retry_on_exception()
    def fetch_historical_data(self, symbol: str, timeframe: str, limit: int = 500, retries: int = 3) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from KuCoin REST API

        Args:
            symbol: Trading pair in KuCoin format (e.g., 'BTC-USDT')
            timeframe: Timeframe string (e.g., '1m', '5m', '1h', '1d')
            limit: Number of candles to fetch (max ~1500)
            retries: Number of retry attempts

        Returns:
            DataFrame with OHLCV data
        """
        # Rate limiting
        wait = self.kucoin_bucket.wait_time()
        if wait > 0:
            time.sleep(wait)
        if not self.kucoin_bucket.consume():
            logger.warning("Rate limit prevented KuCoin API call", extra={"symbol": symbol, "timeframe": timeframe})
            return pd.DataFrame()

        # Map timeframe to KuCoin format
        timeframe_mapping = {
            '1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '1hour', '2h': '2hour', '4h': '4hour', '6h': '6hour', '8h': '8hour',
            '12h': '12hour', '1d': '1day', '3d': '3day', '1w': '1week'
        }
        kucoin_timeframe = timeframe_mapping.get(timeframe, timeframe)

        # Calculate time range (KuCoin returns data in reverse chronological order)
        end_time = datetime.datetime.now()
        # Estimate start time based on limit and timeframe
        if 'min' in kucoin_timeframe:
            minutes = int(kucoin_timeframe.replace('min', ''))
            start_time = end_time - datetime.timedelta(minutes=minutes * limit)
        elif 'hour' in kucoin_timeframe:
            hours = int(kucoin_timeframe.replace('hour', ''))
            start_time = end_time - datetime.timedelta(hours=hours * limit)
        elif 'day' in kucoin_timeframe:
            days = int(kucoin_timeframe.replace('day', ''))
            start_time = end_time - datetime.timedelta(days=days * limit)
        elif 'week' in kucoin_timeframe:
            weeks = int(kucoin_timeframe.replace('week', ''))
            start_time = end_time - datetime.timedelta(weeks=weeks * limit)
        else:
            start_time = end_time - datetime.timedelta(days=30)  # fallback

        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())

        url = f"{self.base_url}/api/v1/market/candles"
        params = {
            'symbol': symbol,
            'type': kucoin_timeframe,
            'startAt': start_timestamp,
            'endAt': end_timestamp
        }

        logger.info(f"Fetching KuCoin historical data: {symbol} {timeframe} ({limit} candles)",
                   extra={"symbol": symbol, "timeframe": timeframe, "url": url, "params": params})

        success = False
        for attempt in range(retries + 1):
            try:
                start = time.time()
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                if data.get('code') != '200000':
                    logger.error(f"KuCoin API error: {data}", extra={"symbol": symbol, "timeframe": timeframe})
                    return pd.DataFrame()

                candles = data.get('data', [])
                if not candles:
                    logger.warning(f"No candle data returned from KuCoin", extra={"symbol": symbol, "timeframe": timeframe})
                    return pd.DataFrame()

                # Convert to DataFrame
                # KuCoin returns: [timestamp, open, close, high, low, volume, turnover]
                df_data = []
                for candle in candles:
                    try:
                        timestamp = pd.to_datetime(int(candle[0]), unit='s', utc=True)
                        open_price = float(candle[1])
                        close_price = float(candle[2])
                        high_price = float(candle[3])
                        low_price = float(candle[4])
                        volume = float(candle[5])

                        df_data.append({
                            'timestamp': timestamp,
                            'open': open_price,
                            'high': high_price,
                            'low': low_price,
                            'close': close_price,
                            'volume': volume
                        })
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Skipping malformed candle data: {candle}", extra={"error": str(e)})
                        continue

                if not df_data:
                    logger.warning(f"No valid candle data after parsing", extra={"symbol": symbol, "timeframe": timeframe})
                    return pd.DataFrame()

                df = pd.DataFrame(df_data)
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()  # Ensure chronological order

                # Record API call
                record_api_call('kucoin', 'candles')

                logger.info(f"Successfully fetched {len(df)} candles from KuCoin",
                           extra={"symbol": symbol, "timeframe": timeframe, "count": len(df)})

                success = True
                return df

            except requests.exceptions.RequestException as e:
                logger.warning(f"KuCoin API request failed (attempt {attempt + 1}/{retries + 1}): {e}",
                              extra={"symbol": symbol, "timeframe": timeframe, "attempt": attempt + 1})
                if attempt < retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
            except Exception as e:
                logger.error(f"Unexpected error fetching KuCoin data: {e}",
                            extra={"symbol": symbol, "timeframe": timeframe, "error": str(e)})
                if attempt < retries:
                    time.sleep(1)
                continue

        # Record failed API call
        record_api_call('kucoin', 'candles')
        logger.error(f"Failed to fetch KuCoin data after {retries + 1} attempts",
                    extra={"symbol": symbol, "timeframe": timeframe})
        return pd.DataFrame()

    def get_available_timeframes(self) -> list:
        """Get list of supported timeframes for KuCoin"""
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']

    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is available on KuCoin spot"""
        try:
            # For now, just check if it's a valid format
            # Could extend to check against KuCoin's symbol list
            return '-' in symbol and len(symbol.split('-')) == 2
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
