"""
data.py: Data loading utilities for backtesting OHLCV data.
"""

import os
from typing import Optional

import pandas as pd


class DataLoader:
    """
    Loads and normalizes historical OHLCV data for backtesting.
    """

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir

    def load_ohlcv(self, symbol: str, timeframe: str = "1h") -> pd.DataFrame:
        """
        Load OHLCV data from CSV. Expects columns: timestamp, open, high, low, close, volume.
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT').
            timeframe (str): Timeframe string (e.g., '1h').
        Returns:
            pd.DataFrame: Loaded and sorted OHLCV data.
        Raises:
            FileNotFoundError: If the data file does not exist.
        """
        file_path = os.path.join(self.data_dir, f"{symbol}_{timeframe}.csv")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        df = pd.read_csv(file_path, parse_dates=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df
