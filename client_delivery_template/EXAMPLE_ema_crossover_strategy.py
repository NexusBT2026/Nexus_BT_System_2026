"""
EMA Crossover Strategy - EXAMPLE
A simple trend-following strategy using fast and slow EMA crossovers.

Entry: Fast EMA crosses above Slow EMA (bullish)
Exit: Fast EMA crosses below Slow EMA (bearish) OR stop loss/take profit

This is a complete working example you can customize for clients.
"""
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator
from typing import Dict, List, Optional


class EMA_Crossover_Strategy:
    """
    Simple EMA Crossover Strategy
    
    Parameters:
    - fast_period: Fast EMA period (default: 9)
    - slow_period: Slow EMA period (default: 21)
    - stop_loss_pct: Stop loss percentage (default: 2.0)
    - take_profit_pct: Take profit percentage (default: 3.0)
    - position_size_pct: Position size as % of capital (default: 10.0)
    """
    
    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
        stop_loss_pct: float = 2.0,
        take_profit_pct: float = 3.0,
        position_size_pct: float = 10.0
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.position_size_pct = position_size_pct
        
        # Trading state
        self.in_position = False
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        self.capital = 0.0
        self.position_size = 0.0
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA indicators"""
        df = df.copy()
        
        # Calculate EMAs
        ema_fast = EMAIndicator(close=df['close'], window=self.fast_period)
        ema_slow = EMAIndicator(close=df['close'], window=self.slow_period)
        
        df['ema_fast'] = ema_fast.ema_indicator()
        df['ema_slow'] = ema_slow.ema_indicator()
        
        # Crossover signals
        df['fast_above_slow'] = df['ema_fast'] > df['ema_slow']
        df['crossover_up'] = (df['fast_above_slow'] == True) & (df['fast_above_slow'].shift(1) == False)
        df['crossover_down'] = (df['fast_above_slow'] == False) & (df['fast_above_slow'].shift(1) == True)
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals"""
        df = df.copy()
        df['signal'] = 0
        
        for i in range(len(df)):
            if pd.isna(df['ema_fast'].iloc[i]) or pd.isna(df['ema_slow'].iloc[i]):
                continue
            
            current_price = df['close'].iloc[i]
            
            # Check stop loss and take profit if in position
            if self.in_position:
                if current_price <= self.stop_loss:
                    df.loc[df.index[i], 'signal'] = -1  # Exit on stop loss
                    self.in_position = False
                elif current_price >= self.take_profit:
                    df.loc[df.index[i], 'signal'] = -1  # Exit on take profit
                    self.in_position = False
                elif df['crossover_down'].iloc[i]:
                    df.loc[df.index[i], 'signal'] = -1  # Exit on bearish crossover
                    self.in_position = False
            
            # Entry signal: Bullish crossover
            if not self.in_position and df['crossover_up'].iloc[i]:
                df.loc[df.index[i], 'signal'] = 1
                self.in_position = True
                self.entry_price = current_price
                self.stop_loss = self.entry_price * (1 - self.stop_loss_pct / 100)
                self.take_profit = self.entry_price * (1 + self.take_profit_pct / 100)
        
        return df
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 10000) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            df: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            initial_capital: Starting capital in USD
            
        Returns:
            Dictionary with performance metrics
        """
        # Reset state
        self.in_position = False
        self.capital = initial_capital
        self.entry_price = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0
        
        # Calculate indicators and signals
        df = self.calculate_indicators(df)
        df = self.generate_signals(df)
        
        # Simulate trades
        trades: List[Dict] = []
        equity_curve = [initial_capital]
        current_equity = initial_capital
        
        for i in range(len(df)):
            if df['signal'].iloc[i] == 1:  # Entry
                entry_price = df['close'].iloc[i]
                position_value = current_equity * (self.position_size_pct / 100)
                position_size = position_value / entry_price
                
                trades.append({
                    'entry_time': df['timestamp'].iloc[i],
                    'entry': entry_price,
                    'position_size': position_size,
                    'exit': None,
                    'exit_time': None,
                    'pnl': 0,
                    'pnl_pct': 0
                })
                
            elif df['signal'].iloc[i] == -1 and len(trades) > 0 and trades[-1]['exit'] is None:  # Exit
                exit_price = df['close'].iloc[i]
                trade = trades[-1]
                trade['exit'] = exit_price
                trade['exit_time'] = df['timestamp'].iloc[i]
                
                pnl = (exit_price - trade['entry']) * trade['position_size']
                pnl_pct = ((exit_price - trade['entry']) / trade['entry']) * 100
                
                trade['pnl'] = pnl
                trade['pnl_pct'] = pnl_pct
                
                current_equity += pnl
                equity_curve.append(current_equity)
        
        # Calculate metrics
        if len(trades) == 0:
            return {
                'total_return_pct': 0,
                'final_capital': initial_capital,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'trades': []
            }
        
        completed_trades = [t for t in trades if t['exit'] is not None]
        
        if len(completed_trades) == 0:
            return {
                'total_return_pct': 0,
                'final_capital': initial_capital,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'trades': []
            }
        
        # Win rate
        winning_trades = [t for t in completed_trades if t['pnl'] > 0]
        win_rate = (len(winning_trades) / len(completed_trades)) * 100 if completed_trades else 0
        
        # Profit factor
        gross_profit = sum([t['pnl'] for t in completed_trades if t['pnl'] > 0])
        gross_loss = abs(sum([t['pnl'] for t in completed_trades if t['pnl'] < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Max drawdown
        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        # Sharpe ratio (annualized, assuming 252 trading days)
        trades_df = pd.DataFrame(completed_trades)
        returns_array = np.array(trades_df['pnl_pct'].tolist(), dtype=np.float64)
        if len(returns_array) > 1 and np.std(returns_array) > 0:
            sharpe = (np.mean(returns_array) / np.std(returns_array)) * np.sqrt(252)
        else:
            sharpe = 0
        
        total_return_pct = ((current_equity - initial_capital) / initial_capital) * 100
        
        return {
            'total_return_pct': round(total_return_pct, 2),
            'final_capital': round(current_equity, 2),
            'total_trades': len(completed_trades),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_dd, 2),
            'sharpe_ratio': round(sharpe, 2),
            'trades': completed_trades
        }


if __name__ == "__main__":
    print("="*60)
    print("EMA CROSSOVER STRATEGY - EXAMPLE")
    print("="*60)
    print("\nStrategy Configuration:")
    print(f"  Fast EMA: 9")
    print(f"  Slow EMA: 21")
    print(f"  Stop Loss: 2%")
    print(f"  Take Profit: 3%")
    print(f"  Position Size: 10%")
    print("\nEntry: Fast EMA crosses above Slow EMA")
    print("Exit: Fast EMA crosses below Slow EMA OR SL/TP")
    print("\n✅ EMA Crossover Strategy - Ready for Testing!")
    print("="*60)
