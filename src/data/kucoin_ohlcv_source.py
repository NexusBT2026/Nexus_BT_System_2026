"""
Kucoin OHLCV Data Source
Provides clean interface for fetching Kucoin Futures OHLCV data using CCXT
"""

import logging
import pandas as pd
import ccxt
import time
from datetime import datetime, timedelta
from typing import Optional
import json
from src.exchange.config import load_config
import os

logger = logging.getLogger(__name__)


class KucoinOHLCVDataSource:
    """Fetches OHLCV data from Kucoin USDT-M Futures using CCXT"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, password: Optional[str] = None):
        """Initialize Kucoin CCXT client for futures"""
        # Load credentials from parameters, env, or central config loader
        self.api_key = api_key or os.environ.get('KUCOIN_API_KEY')
        self.api_secret = api_secret or os.environ.get('KUCOIN_API_SECRET')
        self.password = password or os.environ.get('KUCOIN_API_PASSWORD')
        if not self.api_key or not self.api_secret:
            try:
                config = load_config()
                self.api_key = self.api_key or config.get('kucoin_api_key')
                self.api_secret = self.api_secret or config.get('kucoin_api_secret')
                self.password = self.password or config.get('kucoin_api_password')
            except Exception as e:
                logger.warning(f'Could not load Kucoin API credentials from central config loader: {e}')
        config = {
            'apiKey': self.api_key or '',
            'secret': self.api_secret or '',
            'password': self.password or '',
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # USDT-M perpetual swaps
            },
        }
        self.exchange = ccxt.kucoinfutures(config)  # type: ignore
        logger.info("Initialized KucoinOHLCVDataSource for USDT-M futures")
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Kucoin futures
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT' or 'BTC-USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', etc.)
            limit: Number of candles to fetch (max 1500 for Kucoin)
            since: Timestamp in milliseconds (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Convert symbol format if needed (BTC-USDT -> BTC/USDT:USDT for perpetuals)
            if '/' not in symbol:
                # Strip 'M' suffix if present (KuCoin WebSocket format)
                if symbol.endswith('M'):
                    symbol = symbol[:-1]
                if '-USDT' in symbol:
                    base = symbol.replace('-USDT', '')
                    symbol = f"{base}/USDT:USDT"
                elif symbol.endswith('USDT'):
                    base = symbol[:-4]  # Remove 'USDT'
                    symbol = f"{base}/USDT:USDT"
                else:
                    symbol = f"{symbol}/USDT:USDT"
            
            logger.debug(f"Fetching Kucoin data for {symbol} ({timeframe}), limit={limit}")
            
            # Fetch OHLCV data using CCXT
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=min(limit, 1500),  # Kucoin max is 1500
                since=since
            )
            
            if not ohlcv:
                logger.warning(f"No OHLCV data returned for {symbol} ({timeframe})")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp from milliseconds to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            logger.info(f"Successfully fetched {len(df)} candles for {symbol} ({timeframe})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Kucoin data for {symbol} ({timeframe}): {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_timeframes(self) -> list:
        """Get list of supported timeframes for Kucoin"""
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '1w']
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is available on Kucoin futures"""
        try:
            # Convert symbol format if needed (same logic as fetch_historical_data)
            if '/' not in symbol:
                # Strip 'M' suffix if present (KuCoin WebSocket format)
                if symbol.endswith('M'):
                    symbol = symbol[:-1]
                if '-USDT' in symbol:
                    base = symbol.replace('-USDT', '')
                    symbol = f"{base}/USDT:USDT"
                elif symbol.endswith('USDT'):
                    base = symbol[:-4]  # Remove 'USDT'
                    symbol = f"{base}/USDT:USDT"
                else:
                    symbol = f"{symbol}/USDT:USDT"
            
            markets = self.exchange.load_markets()
            return symbol in markets and markets[symbol].get('swap', False)
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
