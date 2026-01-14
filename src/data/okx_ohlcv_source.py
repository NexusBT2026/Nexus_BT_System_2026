"""
OKX OHLCV Data Source
Provides clean interface for fetching OKX OHLCV data using CCXT
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


class OKXOHLCVDataSource:
    """Fetches OHLCV data from OKX using CCXT - uses SWAP (perpetuals) for high liquidity"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, market_type: str = 'swap'):
        """Initialize OKX CCXT client for swap (perpetuals) - 12x higher volume than spot"""
        # Load credentials from parameters, env, or central config loader
        self.api_key = api_key or os.environ.get('OKX_API_KEY')
        self.api_secret = api_secret or os.environ.get('OKX_API_SECRET')
        if not self.api_key or not self.api_secret:
            try:
                config = load_config()
                self.api_key = self.api_key or config.get('okx_api_key')
                self.api_secret = self.api_secret or config.get('okx_api_secret')
            except Exception as e:
                logger.warning(f'Could not load OKX API credentials from central config loader: {e}')        
        # Treat placeholder strings as None for public API access
        if self.api_key and ('YOUR_' in self.api_key.upper() or self.api_key == ''):
            self.api_key = None
        if self.api_secret and ('YOUR_' in self.api_secret.upper() or self.api_secret == ''):
            self.api_secret = None        
        self.market_type = market_type
        config = {
            'apiKey': self.api_key,  # None = public API access (no auth required for OHLCV)
            'secret': self.api_secret,  # None = public API access
            'enableRateLimit': True,
            'options': {
                'defaultType': market_type,  # 'swap' for perpetuals, 'spot' for spot
            },
        }
        self.exchange = ccxt.okx(config)  # type: ignore
        logger.info(f"Initialized OKXOHLCVDataSource for {market_type}")
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from OKX
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT' for spot, 'BTC/USDT:USDT' for perpetuals)
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', etc.)
            limit: Number of candles to fetch (max 300 for OKX)
            since: Timestamp in milliseconds (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Convert symbol format if needed
            if '/' not in symbol:
                if self.market_type == 'swap':
                    symbol = f"{symbol}/USDT:USDT"  # Perpetuals format
                elif self.market_type == 'spot':
                    symbol = f"{symbol}/USDT"
            elif self.market_type == 'swap' and ':USDT' not in symbol:
                # Convert spot format to perp format
                symbol = f"{symbol}:USDT"
            
            logger.debug(f"Fetching OKX data for {symbol} ({timeframe}), limit={limit}")
            
            # Fetch OHLCV data using CCXT
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=min(limit, 300),  # OKX max is 300
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
            logger.error(f"Error fetching OKX data for {symbol} ({timeframe}): {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_timeframes(self) -> list:
        """Get list of supported timeframes for OKX SWAP"""
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is available on OKX"""
        try:
            # Convert symbol format if needed
            if '/' not in symbol:
                if self.market_type == 'swap':
                    symbol = f"{symbol}/USDT:USDT"
                else:
                    symbol = f"{symbol}/USDT"
            elif self.market_type == 'swap' and ':USDT' not in symbol:
                symbol = f"{symbol}:USDT"
            
            markets = self.exchange.load_markets()
            return symbol in markets
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
