"""
CLIENT DELIVERY STRATEGY TEMPLATE

INSTRUCTIONS FOR WARSHAWSKI:
1. Copy this file to new folder: client_[CLIENT_NAME]_[DATE]/
2. Rename to: strategy_[TYPE].py (e.g., strategy_rsi_macd.py)
3. Fill in the [BRACKETS] with client-specific details
4. Customize the generate_signals() method based on client requirements
5. Test thoroughly before delivery

REUSABLE FOR ALL ORDERS - JUST MODIFY THE [BRACKETS]
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

class [CLIENT_STRATEGY_NAME]:
    """
    [STRATEGY_DESCRIPTION - 2-3 sentences about what this strategy does]
    
    Strategy Type: [MOMENTUM/MEAN_REVERSION/BREAKOUT/SCALPING/CUSTOM]
    
    Entry Conditions:
    - [CONDITION 1]
    - [CONDITION 2]
    - [CONDITION 3]
    
    Exit Conditions:
    - [EXIT_CONDITION 1]
    - [EXIT_CONDITION 2]
    
    Risk Management:
    - Stop Loss: [X]%
    - Take Profit: [X]%
    - Position Sizing: [FIXED/DYNAMIC/KELLY]
    """
    
    def __init__(self, 
                 # [ADD CLIENT-SPECIFIC PARAMETERS HERE]
                 param1: float = [DEFAULT_VALUE],
                 param2: int = [DEFAULT_VALUE],
                 param3: float = [DEFAULT_VALUE],
                 
                 # Risk Management (customize as needed)
                 stop_loss_pct: float = [DEFAULT_SL],
                 take_profit_pct: float = [DEFAULT_TP],
                 position_size_pct: float = [DEFAULT_POSITION_SIZE],
                 
                 # Advanced (optional)
                 use_trailing_stop: bool = False,
                 trailing_stop_pct: float = 2.0):
        """
        Initialize strategy with client-specified parameters.
        
        Args:
            param1: [DESCRIPTION]
            param2: [DESCRIPTION]
            param3: [DESCRIPTION]
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            position_size_pct: Position size as % of capital
        """
        # Store parameters
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3
        
        # Risk management
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_pct = trailing_stop_pct
        
        # Strategy state
        self.position = None
        self.entry_price = None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators needed for the strategy.
        
        [CUSTOMIZE THIS BASED ON CLIENT REQUIREMENTS]
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()
        
        # [EXAMPLE - REPLACE WITH CLIENT INDICATORS]
        # RSI
        from ta.momentum import RSIIndicator
        rsi = RSIIndicator(close=df['close'], window=self.param2)
        df['rsi'] = rsi.rsi()
        
        # MACD (if needed)
        # from ta.trend import MACD
        # macd = MACD(close=df['close'])
        # df['macd'] = macd.macd()
        # df['macd_signal'] = macd.macd_signal()
        
        # EMA (if needed)
        # df['ema_fast'] = df['close'].ewm(span=self.param1, adjust=False).mean()
        # df['ema_slow'] = df['close'].ewm(span=self.param2, adjust=False).mean()
        
        # Bollinger Bands (if needed)
        # from ta.volatility import BollingerBands
        # bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        # df['bb_upper'] = bb.bollinger_hband()
        # df['bb_lower'] = bb.bollinger_lband()
        # df['bb_middle'] = bb.bollinger_mavg()
        
        # ATR (if needed for dynamic stops)
        # from ta.volatility import AverageTrueRange
        # atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
        # df['atr'] = atr.average_true_range()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals based on strategy logic.
        
        [THIS IS THE CORE - CUSTOMIZE BASED ON CLIENT REQUIREMENTS]
        
        Args:
            df: DataFrame with OHLCV data and indicators
            
        Returns:
            DataFrame with 'signal' column (1=buy, -1=sell, 0=hold)
        """
        df = df.copy()
        df['signal'] = 0
        
        # [EXAMPLE LOGIC - REPLACE WITH CLIENT-SPECIFIC STRATEGY]
        
        # BUY SIGNAL CONDITIONS
        buy_condition = (
            # [ADD CLIENT BUY CONDITIONS HERE]
            # Example: (df['rsi'] < 30) & (df['macd'] > df['macd_signal'])
            [CONDITION_1] &
            [CONDITION_2] &
            [CONDITION_3]
        )
        
        # SELL SIGNAL CONDITIONS
        sell_condition = (
            # [ADD CLIENT SELL CONDITIONS HERE]
            # Example: (df['rsi'] > 70) | (df['macd'] < df['macd_signal'])
            [CONDITION_1] |
            [CONDITION_2]
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000) -> Dict:
        """
        Run backtest and return performance metrics.
        
        [MOSTLY REUSABLE - MINIMAL CUSTOMIZATION NEEDED]
        
        Args:
            df: DataFrame with OHLCV data
            initial_capital: Starting capital in USD
            
        Returns:
            Dictionary with backtest results
        """
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Generate signals
        df = self.generate_signals(df)
        
        # Initialize tracking
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity = [initial_capital]
        
        # Simulate trading
        for i in range(1, len(df)):
            current_price = df.iloc[i]['close']
            signal = df.iloc[i]['signal']
            
            # Entry logic
            if signal == 1 and position == 0:
                position_size = (capital * self.position_size_pct / 100) / current_price
                position = position_size
                entry_price = current_price
                capital -= position_size * current_price
            
            # Exit logic
            elif signal == -1 and position > 0:
                pnl = (current_price - entry_price) * position
                capital += position * current_price
                
                trades.append({
                    'entry': entry_price,
                    'exit': current_price,
                    'pnl': pnl,
                    'pnl_pct': (current_price - entry_price) / entry_price * 100
                })
                
                position = 0
                entry_price = 0
            
            # Track equity
            total_equity = capital + (position * current_price if position > 0 else 0)
            equity.append(total_equity)
        
        # Calculate metrics
        trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
        
        if len(trades_df) > 0:
            total_return = ((equity[-1] - initial_capital) / initial_capital) * 100
            win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if (trades_df['pnl'] > 0).any() else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if (trades_df['pnl'] < 0).any() else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # Max drawdown
            equity_series = pd.Series(equity)
            cummax = equity_series.cummax()
            drawdown = (equity_series - cummax) / cummax * 100
            max_drawdown = drawdown.min()
            
            # Sharpe ratio (simplified)
            returns = trades_df['pnl_pct'].values
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            total_return = 0
            win_rate = 0
            profit_factor = 0
            max_drawdown = 0
            sharpe = 0
        
        return {
            'total_return_pct': total_return,
            'final_capital': equity[-1],
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'trades': trades,
            'equity_curve': equity
        }


# [EXAMPLE USAGE FOR CLIENT]
if __name__ == "__main__":
    # Load data (client provides or you fetch)
    # df = pd.read_csv('data.csv')
    
    # Initialize strategy with optimized parameters
    strategy = [CLIENT_STRATEGY_NAME](
        param1=[VALUE],
        param2=[VALUE],
        param3=[VALUE],
        stop_loss_pct=[VALUE],
        take_profit_pct=[VALUE]
    )
    
    # Run backtest
    # results = strategy.backtest(df, initial_capital=10000)
    # print(results)
