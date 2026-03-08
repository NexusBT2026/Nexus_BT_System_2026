"""
YFinance OHLCV Data Source
Provides clean interface for fetching stock/ETF OHLCV data via yfinance.
Completely free — no API key required.
"""

import logging
import pandas as pd
import yfinance as yf
from typing import Optional

logger = logging.getLogger(__name__)

# Map Nexus timeframe strings to yfinance interval strings
TIMEFRAME_MAP = {
    '1m':  '1m',
    '5m':  '5m',
    '15m': '15m',
    '30m': '30m',
    '1h':  '60m',
    '1d':  '1d',
    '1w':  '1wk',
}

# Default lookback period per yfinance interval (yfinance enforces per-interval history limits)
PERIOD_MAP = {
    '1m':  '7d',    # yfinance max for 1m data
    '5m':  '60d',   # yfinance max for sub-daily intervals
    '15m': '60d',
    '30m': '60d',
    '60m': '730d',  # ~2 years for hourly
    '1d':  '5y',
    '1wk': '10y',
}


class YFinanceOHLCVDataSource:
    """Fetches OHLCV data from Yahoo Finance via yfinance — completely free, no API key required."""

    def __init__(self):
        logger.info("Initialized YFinanceOHLCVDataSource (free, no auth required)")

    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str = '1d',
        limit: Optional[int] = None,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Yahoo Finance.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL', 'MSFT', 'SPY')
            timeframe: Nexus timeframe string ('1m', '5m', '15m', '30m', '1h', '1d', '1w')
            limit: Unused — yfinance uses period-based fetching
            since: Start timestamp in milliseconds (optional)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        interval = TIMEFRAME_MAP.get(timeframe)
        if interval is None:
            logger.warning(f"[YFINANCE] Unsupported timeframe '{timeframe}' for {symbol}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        period = PERIOD_MAP.get(interval, '1y')

        try:
            ticker = yf.Ticker(symbol)

            if since is not None:
                start_dt = pd.Timestamp(since, unit='ms', tz='UTC')
                df = ticker.history(start=start_dt, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df is None or df.empty:
                logger.warning(f"[YFINANCE] No data returned for {symbol} ({timeframe})")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Reset index so the datetime index becomes a regular column
            df = df.reset_index()

            # Daily data uses 'Date'; intraday uses 'Datetime'
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            elif 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})

            # Normalize to lowercase OHLCV column names
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
            })

            # Keep only the columns we need
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()

            # Ensure numeric types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Drop rows with NaN OHLC values
            df = df.dropna(subset=['open', 'high', 'low', 'close'])

            # Strip timezone info for consistency with other data sources
            if hasattr(df['timestamp'], 'dt') and df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)

            logger.info(f"[YFINANCE] Fetched {len(df)} candles for {symbol} ({timeframe})")
            return df

        except Exception as e:
            logger.error(f"[YFINANCE] Error fetching data for {symbol} ({timeframe}): {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    def get_available_timeframes(self) -> list:
        """Get list of supported Nexus timeframe strings for yfinance."""
        return list(TIMEFRAME_MAP.keys())

    def validate_symbol(self, symbol: str) -> bool:
        """Check if a ticker symbol has data available on Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='5d', interval='1d')
            return df is not None and not df.empty
        except Exception:
            return False
