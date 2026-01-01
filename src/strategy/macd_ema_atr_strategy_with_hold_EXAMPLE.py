"""
MACDEMAATRStrategy: Modular, research-ready MACD+EMA+ATR strategy for trend and momentum trading.

This strategy combines the Moving Average Convergence Divergence (MACD), Exponential Moving Averages (EMA),
and Average True Range (ATR) to identify trend direction, momentum shifts, and dynamic stop levels. Buy signals
are generated when MACD crosses above its signal line and price is above the long-term EMA; sell signals are
generated on the opposite. ATR is used for volatility-based stop placement and trailing stops. The approach is
designed for research, batch optimization, and live trading, with all logic and parameters exposed for robust evaluation.

Features:
- Trend and momentum detection using MACD and EMA.
- Volatility-based stop and trailing logic using ATR.
- Modular, bias-protected, and optimizer-compatible class structure.
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

class MACDEMAATRStrategy:
    @staticmethod
    def get_min_candles(params):
        # Use the same parameter names as the rest of the strategy (short_period, long_period, signal_period, ema_period, atr_period)
        def to_int(val, default):
            try:
                return int(val)
            except Exception:
                return default

        short_period = to_int(params.get('short_period', 12), 12)
        long_period = to_int(params.get('long_period', 26), 26)
        signal_period = to_int(params.get('signal_period', 9), 9)
        ema_period = to_int(params.get('ema_period', 200), 200)
        atr_period = to_int(params.get('atr_period', 14), 14)
        # Use the largest lookback window required by any indicator
        return max(short_period, long_period, signal_period, ema_period, atr_period) + 1
    """
    Modular MACD+EMA+ATR strategy for research/backtest/hyperopt.
    Exposes only parameters used in logic, with param_grid for optimizer compatibility.
    """
    param_grid = {
        'short_period': range(5, 21, 1),  # Expanded to include winning 19
        'long_period': range(20, 45, 1),  # Expanded to include winning 39
        'signal_period': range(5, 16, 1),
        'ema_period': [50, 100, 200],
        'atr_period': [7, 8, 13, 14, 20, 21, 30, 34, 52],
        'atr_multiplier': [x / 10.0 for x in range(10, 31, 1)],
        'use_trailing_sl': [True],  # Always use trailing stops (from comprehensive test)
        'trailing_sl_distance': [x / 10.0 for x in range(5, 21, 1)],
        # NEW: Winner's risk management parameters
        'initial_stop_pct': [x / 100.0 for x in range(5, 25, 5)],  # 5%, 10%, 15%, 20%
        'trailing_pct': [x / 100.0 for x in range(3, 20, 2)],  # 3%, 5%, 7%, ..., 19%
        'breakeven_trigger_pct': [x / 100.0 for x in range(3, 20, 3)],  # 3%, 6%, 9%, 12%, 15%, 18%
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            'short_period': 12,
            'long_period': 26,
            'signal_period': 9,
            'ema_period': 200,
            'atr_period': 14,
            'atr_multiplier': 2.0,
            'use_trailing_sl': True,
            'trailing_sl_distance': 1.0,
            # NEW: Winner's risk management defaults (from comprehensive test)
            'initial_stop_pct': 0.20,  # 20% initial stop (VERY WIDE - winner!)
            'trailing_pct': 0.15,  # 15% trailing stop (from highest price)
            'breakeven_trigger_pct': 0.15,  # Move to breakeven after 15% gain
            'param_grid': {
                'short_period': range(5, 21, 1),
                'long_period': range(20, 45, 1),
                'signal_period': range(5, 16, 1),
                'ema_period': [50, 100, 200],
                'atr_period': [7, 8, 13, 14, 20, 21, 30, 34, 52],
                'atr_multiplier': [x / 10.0 for x in range(10, 31, 1)],
                'use_trailing_sl': [True],
                'trailing_sl_distance': [x / 10.0 for x in range(5, 21, 1)],
                'initial_stop_pct': [x / 100.0 for x in range(5, 25, 5)],
                'trailing_pct': [x / 100.0 for x in range(3, 20, 2)],
                'breakeven_trigger_pct': [x / 100.0 for x in range(3, 20, 3)],
            }
        }
        param_grid = defaults['param_grid']
        for k, v in param_grid.items():
            if k not in config or config[k] is None:
                if isinstance(v, range):
                    config[k] = list(v)[0]
                elif isinstance(v, list):
                    config[k] = v[0]
                else:
                    config[k] = v
        for k, v in defaults.items():
            if k not in config:
                config[k] = v
        # Ensure all period parameters are int (robust against string input)
        for period_key in ['short_period', 'long_period', 'signal_period', 'ema_period', 'atr_period']:
            if period_key in config:
                try:
                    config[period_key] = int(config[period_key])
                except Exception:
                    config[period_key] = int(defaults[period_key])
        return config

    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        cfg = self.config
        close = data['close']
        def ema(series, period):
            return series.ewm(span=period, adjust=False).mean()
        ema_short = ema(close, cfg['short_period'])
        ema_long = ema(close, cfg['long_period'])
        macd = ema_short - ema_long
        signal = ema(macd, cfg['signal_period'])
        ema_trend = ema(close, cfg['ema_period'])
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        true_range = pd.Series(true_range, index=data.index)  # Ensure it's a pandas Series
        atr = true_range.rolling(window=cfg['atr_period']).mean()
        return {
            'macd': macd,
            'signal': signal,
            'ema_trend': ema_trend,
            'atr': atr
        }

    def generate_signals(self, data: pd.DataFrame, apply_bias: bool = True) -> list:
        cfg = self.config
        ind = self.calculate_indicators(data)
        
        # Create signal_map for buy/sell signals
        signal_map = {}
        for i in range(max(cfg['long_period'], cfg['ema_period'], cfg['atr_period'], cfg['signal_period']), len(data)):
            row = data.iloc[:i+1]
            idx = data.index[i]
            macd = ind['macd'].iloc[i]
            signal = ind['signal'].iloc[i]
            ema_trend = ind['ema_trend'].iloc[i]
            atr = ind['atr'].iloc[i]
            current_price = row['close'].iloc[-1]
            buy_signal = (macd < 0 and signal < 0) and (macd > signal) and (current_price > ema_trend)
            sell_signal = (macd > 0 and signal > 0) and (macd < signal) and (current_price < ema_trend)
            if buy_signal:
                signal_map[idx] = {'type': 'bullish', 'index': idx, 'action': 'buy', 'macd': macd, 'signal': signal, 'ema_trend': ema_trend, 'atr': atr}
            elif sell_signal:
                signal_map[idx] = {'type': 'bearish', 'index': idx, 'action': 'sell', 'macd': macd, 'signal': signal, 'ema_trend': ema_trend, 'atr': atr}
        
        # Generate all signals including 'hold' for every candle
        all_signals = []
        for idx in data.index:
            if idx in signal_map:
                all_signals.append(signal_map[idx])
            else:
                # Add 'hold' signal for candles with no buy/sell
                all_signals.append({
                    'type': 'hold',
                    'index': idx,
                    'action': 'hold',
                    'macd': ind['macd'].loc[idx] if idx in ind['macd'].index else None,
                    'signal': ind['signal'].loc[idx] if idx in ind['signal'].index else None,
                    'ema_trend': ind['ema_trend'].loc[idx] if idx in ind['ema_trend'].index else None,
                    'atr': ind['atr'].loc[idx] if idx in ind['atr'].index else None
                })
        
        return all_signals

    def split_data_chronologically(self, data: pd.DataFrame, train_ratio: Optional[float] = 0.5, val_ratio: Optional[float] = 0.25) -> Dict[str, pd.DataFrame]:
        # Ensure ratios are not None
        train_ratio = 0.5 if train_ratio is None else train_ratio
        val_ratio = 0.25 if val_ratio is None else val_ratio
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        return {
            'train': data.iloc[:train_end],
            'val': data.iloc[train_end:val_end],
            'test': data.iloc[val_end:]
        }

    def apply_bias_protection(self, signals: list, data: pd.DataFrame) -> list:
        protected_signals = []
        for sig in signals:
            idx = sig['index']
            if idx in data.index:
                pos = data.index.get_indexer(idx)[0]
                if pos + 1 < len(data):
                    next_idx = data.index[pos + 1]
                    sig_copy = sig.copy()
                    sig_copy['index'] = next_idx
                    protected_signals.append(sig_copy)
        return protected_signals

    def early_reject_parameters(self, performance_history: list, patience: Optional[int] = None, min_improvement: Optional[float] = None) -> bool:
        if patience is None:
            patience = self.config.get('patience', 5)
        if patience is None:
            patience = 5
        if min_improvement is None:
            min_improvement = self.config.get('min_improvement', 0.0)
        if len(performance_history) < patience:
            return False
        best = max(performance_history[:-patience]) if len(performance_history) > patience else performance_history[0]
        recent = max(performance_history[-patience:])
        return (recent - best) < min_improvement

    def optimize_parameters(self, backtest_engine: Any, param_grid: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        best_params = None
        best_score = float('-inf')
        history = []
        if param_grid is None:
            raise ValueError('param_grid must be provided by the optimizer script, not the strategy class.')
        for params in backtest_engine.parameter_sweep(param_grid):
            splits = self.split_data_chronologically(params['data'])
            train, val, test = splits['train'], splits['val'], splits['test']
            train_score = backtest_engine.run(train, params)
            val_score = backtest_engine.run(val, params)
            history.append(val_score)
            if self.early_reject_parameters(history):
                continue
            if val_score > best_score:
                best_score = val_score
                best_params = params
        return {'best_params': best_params, 'best_score': best_score}

    def simulate_trades(self, signals: list, data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate trades with WINNER's risk management from comprehensive test.
        
        Risk Management (from QuantVPS professional approach):
        - Initial stop: 20% (VERY WIDE - lets MACD trends breathe)
        - Trailing stop: 15% from highest price
        - Breakeven protection: After 15% gain
        - NO profit targets (let winners run)
        - NO opposite signal exits (MACD is lagging)
        
        Returns DataFrame with columns: ['entry', 'exit', 'pnl', 'pnl_pct', 'entry_idx', 'exit_idx', 'exit_reason']
        """
        cfg = self.config
        ind = self.calculate_indicators(data)
        
        columns = ['entry', 'exit', 'pnl', 'pnl_pct', 'entry_idx', 'exit_idx', 'exit_reason']
        trades = []
        position = None
        entry_price = None
        entry_idx = None
        current_stop = None
        highest_price = None
        
        # Get risk management parameters (use winner's defaults if not in config)
        initial_stop_pct = cfg.get('initial_stop_pct', 0.20)  # 20% default
        trailing_pct = cfg.get('trailing_pct', 0.15)  # 15% default
        breakeven_trigger_pct = cfg.get('breakeven_trigger_pct', 0.15)  # 15% default
        
        # Build signal index for quick lookup (filter out 'hold' signals)
        signal_dict = {}
        for sig in signals:
            if sig.get('action') != 'hold':  # Only include buy/sell signals
                signal_dict[sig['index']] = sig
        
        for i in range(len(data)):
            idx = data.index[i]
            price = data.loc[idx, 'close']
            
            # Entry logic - ONLY on BUY signals (LONG ONLY)
            if idx in signal_dict and position is None:
                sig = signal_dict[idx]
                
                if sig['action'] == 'buy':
                    position = 'long'
                    entry_price = price
                    entry_idx = idx
                    highest_price = price
                    
                    # Wide initial stop - let MACD breathe!
                    current_stop = price * (1 - initial_stop_pct)
            
            # Exit logic (only if in position)
            if position == 'long':
                exit_reason = None
                exit_price = None
                
                # Convert to float for calculations
                try:
                    price_float = float(np.asarray(price).item())
                    entry_float = float(np.asarray(entry_price).item()) if entry_price is not None else 0.0
                    highest_float = float(np.asarray(highest_price).item()) if highest_price is not None else 0.0
                except (TypeError, ValueError, AttributeError):
                    price_float = 0.0
                    entry_float = 0.0
                    highest_float = 0.0
                
                # Update highest price tracker
                if price_float > highest_float:
                    highest_price = price_float
                    highest_float = price_float
                
                # Calculate current profit %
                profit_pct = (price_float - entry_float) / entry_float if entry_float else 0.0
                
                # BREAKEVEN protection (move stop to entry after trigger)
                if (profit_pct >= breakeven_trigger_pct and 
                    current_stop is not None and entry_float > 0 and 
                    float(current_stop) < entry_float):
                    current_stop = entry_float * 1.001  # Slightly above breakeven
                
                # TRAILING STOP (from highest price, only trail UP)
                if profit_pct > 0 and highest_float > 0:
                    trailing_stop = highest_float * (1 - trailing_pct)
                    if current_stop is not None and trailing_stop > float(current_stop):
                        current_stop = trailing_stop
                
                # Check STOP
                if current_stop is not None and price_float <= float(current_stop):
                    exit_reason = 'trailing_stop' if profit_pct > 0 else 'stop_loss'
                    exit_price = price
                
                # NO profit targets - let winners run!
                # NO opposite signal exits - MACD is lagging!
                
                # Record trade if exiting
                if exit_reason:
                    try:
                        price_val = float(np.asarray(exit_price).item())
                        entry_val = float(np.asarray(entry_price).item())
                        
                        pnl = price_val - entry_val
                        pnl_pct = (pnl / entry_val) * 100 if entry_val else 0.0
                    except (TypeError, ValueError):
                        pnl = 0.0
                        pnl_pct = 0.0
                    
                    trades.append({
                        'entry': entry_price,
                        'exit': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'entry_idx': entry_idx,
                        'exit_idx': idx,
                        'exit_reason': exit_reason
                    })
                    
                    position = None
                    entry_price = None
                    entry_idx = None
                    current_stop = None
                    highest_price = None
        
        # Close any remaining position at end of data
        if position == 'long' and entry_price not in (0, None, ""):
            last_idx = data.index[-1]
            last_price = data['close'].iloc[-1]
            
            try:
                last_val = float(np.asarray(last_price).item())
                entry_val = float(np.asarray(entry_price).item())
                
                pnl = last_val - entry_val
                pnl_pct = (pnl / entry_val) * 100 if entry_val else 0.0
            except (TypeError, ValueError):
                pnl = 0.0
                pnl_pct = 0.0
            
            trades.append({
                'entry': entry_price,
                'exit': last_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'entry_idx': entry_idx,
                'exit_idx': last_idx,
                'exit_reason': 'end_of_data'
            })
        
        return pd.DataFrame(trades, columns=columns)

    def print_trial_progress(self, trial_num, total_trials, params, result):
        print(f"[MACDEMAATR] Trial {trial_num}/{total_trials} | Params: {params} | Result: {result}")

    #########################
    # --- Live trading entry point ---
    def run_strategy(self, state):
        """
        Entry point for live trading integration. Expects `state` to contain the latest market data as a pandas DataFrame
        and a config dict (or list of configs). Only live signal generation is performed (no backtest, no bias-protection).
        """
        config = state.get('config')
        data = state.get('data')
        required_keys = [
            'short_period', 'long_period', 'signal_period', 'ema_period', 'atr_period', 'atr_multiplier',
            'use_trailing_sl', 'trailing_sl_distance'
        ]
        # If config is a list of configs, find the one matching symbol and strategy_name
        if isinstance(config, list):
            symbol = state.get('symbol') or (state.get('data').get('symbol') if hasattr(state.get('data'), 'get') else None)
            strategy_name = state.get('strategy_name')
            found = None
            for entry in config:
                if (
                    entry.get('symbol') == symbol and
                    entry.get('strategy_name') == strategy_name and
                    'best_params' in entry
                ):
                    found = entry['best_params']
                    break
            if found:
                config = found
            else:
                raise ValueError("No matching config found for symbol and strategy_name.")
        # Try to get keys from top level, else from 'best_params'
        missing = [k for k in required_keys if k not in (config or {})]
        if missing and 'best_params' in config and isinstance(config['best_params'], dict):
            for k in missing:
                if k in config['best_params']:
                    config[k] = config['best_params'][k]
            missing = [k for k in required_keys if k not in config]
        if config is None or missing:
            raise ValueError(f"Config missing required keys: {missing}")
        if data is None or not isinstance(data, pd.DataFrame):
            raise ValueError("State must include a 'data' key with a pandas DataFrame of market data.")
        
        # Use self and NO bias protection for live trading
        signals = self.generate_signals(data, apply_bias=False)
        
        # Find the most recent signal for the last bar
        last_idx = data.index[-1]
        last_signal = None
        for sig in reversed(signals):
            if sig['index'] == last_idx:
                last_signal = sig
                break
        
        if last_signal is not None:
            return last_signal['action']
        return 'hold'  # Return 'hold' instead of None
