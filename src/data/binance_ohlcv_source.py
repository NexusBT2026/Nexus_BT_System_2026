"""
Binance OHLCV Data Source
Provides clean interface for fetching Binance Futures OHLCV data using CCXT
"""

import logging
import pandas as pd
import ccxt
import time
from datetime import datetime, timedelta
from typing import Optional
import json
try:
    from src.exchange.config import load_config
except Exception:
    # Fallback: simple loader from repo config.json
    def load_config(config_path: str = 'config.json'):
        import json, os
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
import os

logger = logging.getLogger(__name__)


class BinanceOHLCVDataSource:
    """Fetches OHLCV data from Binance using CCXT - supports both futures and spot"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, market_type: str = 'spot'):
        """Initialize Binance CCXT client for futures or spot"""
        # Load credentials from parameters, env, or central config loader
        self.api_key = api_key or os.environ.get('BINANCE_API_KEY')
        self.api_secret = api_secret or os.environ.get('BINANCE_API_SECRET')
        if not self.api_key or not self.api_secret:
            try:
                config = load_config()
                self.api_key = self.api_key or config.get('binance_api_key')
                self.api_secret = self.api_secret or config.get('binance_api_secret')
            except Exception as e:
                logger.warning(f'Could not load Binance API credentials from central config loader: {e}')        
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
                'defaultType': market_type,  # 'future' for USDT-M futures, 'spot' for spot
            },
        }
        self.exchange = ccxt.binance(config)  # type: ignore
        logger.info(f"Initialized BinanceOHLCVDataSource for {market_type}")
    
    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Binance futures
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', etc.)
            limit: Number of candles to fetch (max 1500 for Binance)
            since: Timestamp in milliseconds (optional)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Convert symbol format if needed (BTC -> BTC/USDT or BTC/USDC)
            if '/' not in symbol:
                if self.market_type == 'future':
                    if not symbol.endswith('USDT'):
                        symbol = f"{symbol}/USDT"
                elif self.market_type == 'spot':
                    if not symbol.endswith('USDC'):
                        symbol = f"{symbol}/USDC"
            
            logger.debug(f"Fetching Binance data for {symbol} ({timeframe}), limit={limit}")
            
            # Fetch OHLCV data using CCXT
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=min(limit, 1500),  # Binance max is 1500
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
            logger.error(f"Error fetching Binance data for {symbol} ({timeframe}): {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_timeframes(self) -> list:
        """Get list of supported timeframes for Binance"""
        return ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is available on Binance futures"""
        try:
            # Convert symbol format if needed
            if '/' not in symbol:
                if not symbol.endswith('USDT'):
                    symbol = f"{symbol}/USDT"
            
            markets = self.exchange.load_markets()
            return symbol in markets and markets[symbol].get('future', False)
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
