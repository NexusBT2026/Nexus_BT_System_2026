"""
RSIDivergenceStrategy: Modular, research-ready RSI divergence strategy for mean reversion and momentum reversal.

This strategy systematically detects bullish and bearish RSI divergences between price and the RSI indicator.
Buy signals are generated on bullish divergence (price makes a lower low, RSI makes a higher low);
sell signals are generated on bearish divergence (price makes a higher high, RSI makes a lower high).
The approach is designed for research, batch optimization, and live trading, with all logic and parameters exposed for robust evaluation.

Features:
- Quantitative detection of bullish and bearish RSI divergences.
- Configurable lookback, threshold, and confirmation logic.
- Modular, bias-protected, and optimizer-compatible class structure.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

class RSIDivergenceStrategy:
    @staticmethod
    def get_min_candles(params):
        rsi = params.get('rsi_length', 14)
        atr = params.get('atr_length', 14)
        swing = params.get('swing_window', 5)
        return max(rsi, atr, swing) + 1
    """
    RSI Divergence strategy for research/backtest/hyperopt.
    Includes core logic (signal generation, indicator calculation, config validation)
    and research/backtest helpers (bias protection, splits, optimization).
    """
    # Legacy hyperopt space definition (expanded ranges for realistic trading)
    param_grid = {
        'rsi_length': range(4, 26, 1),  # hp.quniform('RSI_LENGTH', 4, 25, 1)
        'atr_length': range(4, 26, 1),  # hp.quniform('ATR_LENGTH', 4, 25, 1) 
        'atr_multiplier': [round(x, 2) for x in [1.0 + i*0.05 for i in range(20)]],  # hp.uniform('ATR_MULTIPLIER', 1.0, 2.0) - expanded for more cushion
        'profit_target_pct': [round(x, 3) for x in [0.02 + i*0.004 for i in range(21)]],  # hp.uniform('PROFIT_TARGET_PCT', 0.02, 0.10) - expanded, min 2%
        'stop_loss_pct': [round(x, 3) for x in [0.01 + i*0.002 for i in range(21)]],  # hp.uniform('STOP_LOSS_PCT', 0.01, 0.05) - expanded, min 1%
        'swing_window': range(2, 9, 1),  # hp.quniform('SWING_WINDOW', 2, 8, 1)
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            'rsi_length': 14,  # Use working BTC parameters from legacy bot
            'atr_length': 14,
            'atr_multiplier': 1.5,
            'profit_target_pct': 0.03,  # Increased default to account for trading costs
            'stop_loss_pct': 0.02,  # Increased default to account for trading costs
            'swing_window': 5,
            'param_grid': {
                'rsi_length': range(4, 26, 1),  # hp.quniform('RSI_LENGTH', 4, 25, 1)
                'atr_length': range(4, 26, 1),  # hp.quniform('ATR_LENGTH', 4, 25, 1) 
                'atr_multiplier': [round(x, 2) for x in [1.0 + i*0.05 for i in range(20)]],  # hp.uniform('ATR_MULTIPLIER', 1.0, 2.0) - expanded for more cushion
                'profit_target_pct': [round(x, 3) for x in [0.02 + i*0.004 for i in range(21)]],  # hp.uniform('PROFIT_TARGET_PCT', 0.02, 0.10) - expanded, min 2%
                'stop_loss_pct': [round(x, 3) for x in [0.01 + i*0.002 for i in range(21)]],  # hp.uniform('STOP_LOSS_PCT', 0.01, 0.05) - expanded, min 1%
                'swing_window': range(2, 9, 1),  # hp.quniform('SWING_WINDOW', 2, 8, 1)
            }
        }
        param_grid = defaults['param_grid']
        # Always use first value from param grid for config, never range object
        for k, v in param_grid.items():
            if k not in config or config[k] is None:
                if isinstance(v, range):
                    config[k] = list(v)[0]
                elif isinstance(v, list):
                    config[k] = v[0]
                else:
                    config[k] = v
        # For defaults, if value is a range, use first value
        for k, v in defaults.items():
            if k not in config:
                if isinstance(v, range):
                    config[k] = list(v)[0]
                else:
                    config[k] = v
        # Final pass: ensure no config value is a range or list
        for k in config:
            if isinstance(config[k], range):
                config[k] = list(config[k])[0]
            elif isinstance(config[k], list):
                config[k] = config[k][0]
        return config

    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        try:
            import pandas_ta as ta
            rsi = ta.rsi(prices, length=period)
            if rsi is not None:
                if isinstance(rsi, pd.DataFrame):
                    rsi = rsi.squeeze()
                if isinstance(rsi, pd.Series):
                    return rsi
        except ImportError:
            pass
        prices = prices.astype(float)
        delta = prices.diff().astype(float)
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def find_swing_points(self, data: pd.DataFrame, window_size: Optional[int] = None) -> tuple[pd.Series, pd.Series]:
        """Find swing points using scipy.signal method (matching original hyperopt script)"""
        if window_size is None:
            window_size = self.config.get('swing_window', 5)
        # Ensure window_size is always an int and not None
        if window_size is None:
            window_size = 5
        window_size = int(window_size)
        
        try:
            from scipy.signal import argrelextrema
            import numpy as np
            
            # Use scipy method like original
            highs = data['high'].values
            lows = data['low'].values
            
            # Find local maxima and minima
            max_idx = argrelextrema(highs, np.greater_equal, order=window_size)[0]
            min_idx = argrelextrema(lows, np.less_equal, order=window_size)[0]
            
            # Create boolean series
            swing_highs = pd.Series(index=data.index, dtype=bool)
            swing_lows = pd.Series(index=data.index, dtype=bool)
            swing_highs[:] = False
            swing_lows[:] = False
            
            # Mark swing points
            for idx in max_idx:
                if idx < len(data):
                    swing_highs.iloc[idx] = True
                    
            for idx in min_idx:
                if idx < len(data):
                    swing_lows.iloc[idx] = True
                    
            return swing_highs, swing_lows
            
        except ImportError:
            # Fallback to manual method if scipy not available
            highs = data['high']
            lows = data['low']
            swing_highs = pd.Series(index=data.index, dtype=bool)
            swing_lows = pd.Series(index=data.index, dtype=bool)
            swing_highs[:] = False
            swing_lows[:] = False
            
            if len(data) < window_size * 2 + 1:
                return swing_highs, swing_lows
                
            # Manual swing point detection
            for i in range(window_size, len(data) - window_size):
                # Check if current point is a swing high
                window_highs = highs.iloc[i-window_size:i+window_size+1]
                if highs.iloc[i] == window_highs.max():
                    swing_highs.iloc[i] = True
                    
                # Check if current point is a swing low  
                window_lows = lows.iloc[i-window_size:i+window_size+1]
                if lows.iloc[i] == window_lows.min():
                    swing_lows.iloc[i] = True
                    
            return swing_highs, swing_lows

    def detect_divergence(self, data: pd.DataFrame, rsi: pd.Series, align_window: int = 3) -> List[Dict[str, Any]]:
        """Detect RSI divergences (matching original hyperopt script logic exactly)"""
        df = data.copy()
        df['rsi'] = rsi
        
        # Find swing points using original method
        swing_highs, swing_lows = self.find_swing_points(df)
        
        # Convert boolean series to indices (matching original)
        df['local_max'] = swing_highs
        df['local_min'] = swing_lows
        df['rsi_local_max'] = swing_highs  # Use same swing points for RSI
        df['rsi_local_min'] = swing_lows   # Use same swing points for RSI
        
        df['bullish_div'] = False
        df['bearish_div'] = False
        
        # Get indices where swing points occur
        price_min_idx = np.where(df['local_min'].to_numpy())[0]
        price_max_idx = np.where(df['local_max'].to_numpy())[0]
        rsi_min_idx = np.where(df['rsi_local_min'].to_numpy())[0]
        rsi_max_idx = np.where(df['rsi_local_max'].to_numpy())[0]
        
        # Detect bullish divergence (matching original logic exactly)
        for i in price_min_idx:
            # Look for nearby RSI swing points within align_window
            rsi_nearby = rsi_min_idx[(rsi_min_idx >= i - align_window) & (rsi_min_idx <= i)]
            if len(rsi_nearby) == 0:
                continue
            rsi_idx = rsi_nearby[np.argmin(np.abs(rsi_nearby - i))]
            
            # Find previous price swing point
            prev_price = price_min_idx[price_min_idx < i]
            if len(prev_price) == 0:
                continue
            prev_price_idx = prev_price[-1]
            
            # Find previous RSI swing point
            prev_rsi = rsi_min_idx[rsi_min_idx < rsi_idx]
            if len(prev_rsi) == 0:
                continue
            prev_rsi_idx = prev_rsi[-1]
            
            # Check for bullish divergence: price lower low, RSI higher low
            if (df['close'].iloc[i] < df['close'].iloc[prev_price_idx] and 
                df['rsi'].iloc[rsi_idx] > df['rsi'].iloc[prev_rsi_idx]):
                df.at[df.index[i], 'bullish_div'] = True
        
        # Detect bearish divergence (matching original logic exactly)
        for i in price_max_idx:
            # Look for nearby RSI swing points within align_window
            rsi_nearby = rsi_max_idx[(rsi_max_idx >= i - align_window) & (rsi_max_idx <= i)]
            if len(rsi_nearby) == 0:
                continue
            rsi_idx = rsi_nearby[np.argmin(np.abs(rsi_nearby - i))]
            
            # Find previous price swing point
            prev_price = price_max_idx[price_max_idx < i]
            if len(prev_price) == 0:
                continue
            prev_price_idx = prev_price[-1]
            
            # Find previous RSI swing point
            prev_rsi = rsi_max_idx[rsi_max_idx < rsi_idx]
            if len(prev_rsi) == 0:
                continue
            prev_rsi_idx = prev_rsi[-1]
            
            # Check for bearish divergence: price higher high, RSI lower high
            if (df['close'].iloc[i] > df['close'].iloc[prev_price_idx] and 
                df['rsi'].iloc[rsi_idx] < df['rsi'].iloc[prev_rsi_idx]):
                df.at[df.index[i], 'bearish_div'] = True
        
        # Convert to signals format
        signals = []
        
        # Add bullish divergence signals
        bullish_indices = df[df['bullish_div'] == True].index
        for idx in bullish_indices:
            signals.append({
                'type': 'bullish',
                'index': idx,
                'price': df.loc[idx, 'close'],
                'rsi': df.loc[idx, 'rsi']
            })
        
        # Add bearish divergence signals
        bearish_indices = df[df['bearish_div'] == True].index
        for idx in bearish_indices:
            signals.append({
                'type': 'bearish',
                'index': idx,
                'price': df.loc[idx, 'close'],
                'rsi': df.loc[idx, 'rsi']
            })
        
        # Sort signals by index to maintain chronological order
        signals.sort(key=lambda x: x['index'])
        
        return signals

    def apply_bias_protection(self, signals: List[Dict[str, Any]], data: pd.DataFrame) -> List[Dict[str, Any]]:
        # Shift signals forward by one bar to prevent lookahead bias
        protected_signals = []
        for sig in signals:
            idx = sig['index']
            if idx in data.index:
                loc = data.index.get_loc(idx)
                if isinstance(loc, slice):
                    # If loc is a slice, use its start as the integer location
                    loc = loc.start
                if isinstance(loc, (np.ndarray, list)):
                    # If loc is an array, use the first element
                    loc = loc[0]
                if isinstance(loc, int) and loc + 1 < len(data):
                    next_idx = data.index[loc + 1]
                    sig_copy = sig.copy()
                    sig_copy['index'] = next_idx
                    protected_signals.append(sig_copy)
        return protected_signals

    def generate_signals(self, data: pd.DataFrame, apply_bias: bool = True) -> List[Dict[str, Any]]:
        rsi = self.calculate_rsi(data['close'], self.config['rsi_length'])
        divergence_signals = self.detect_divergence(data, rsi)
        
        # Create signal_map for buy/sell signals
        signal_map = {}
        for sig in divergence_signals:
            sig['action'] = 'buy' if sig['type'] == 'bullish' else 'sell'
            signal_map[sig['index']] = sig
        
        # Apply bias protection to buy/sell signals BEFORE adding hold signals
        if apply_bias:
            protected_signals = self.apply_bias_protection(list(signal_map.values()), data)
            signal_map = {sig['index']: sig for sig in protected_signals}
        
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
                    'price': data.loc[idx, 'close'],
                    'rsi': rsi.loc[idx] if idx in rsi.index else None
                })
        
        return all_signals

    def split_data_chronologically(self, data: pd.DataFrame, train_ratio: Optional[float] = None, val_ratio: Optional[float] = None) -> Dict[str, pd.DataFrame]:
        # Provide default ratios if not set in config or arguments
        default_train_ratio = 0.7
        default_val_ratio = 0.15
        if train_ratio is None:
            train_ratio = self.config.get('train_ratio', default_train_ratio)
        if val_ratio is None:
            val_ratio = self.config.get('val_ratio', default_val_ratio)
        # Ensure ratios are not None and are floats
        if train_ratio is None:
            train_ratio = default_train_ratio
        if val_ratio is None:
            val_ratio = default_val_ratio
        n = len(data)
        train_end = int(n * float(train_ratio))
        val_end = train_end + int(n * float(val_ratio))
        return {
            'train': data.iloc[:train_end],
            'val': data.iloc[train_end:val_end],
            'test': data.iloc[val_end:]
        }

    def early_reject_parameters(self, performance_history: List[float], patience: Optional[int] = None, min_improvement: Optional[float] = None) -> bool:
        if patience is None:
            patience = self.config.get('patience', 5)
        if min_improvement is None:
            min_improvement = self.config.get('min_improvement', 0.0)
        if patience is None:
            patience = 5
        if len(performance_history) < patience:
            return False
        best = max(performance_history[:-patience]) if len(performance_history) > patience else performance_history[0]
        recent = max(performance_history[-patience:])
        if min_improvement is None:
            min_improvement = 0.0
        return (recent - best) < min_improvement

    def optimize_parameters(self, backtest_engine: Any) -> Dict[str, Any]:
        param_grid = self.config['param_grid']
        best_params = None
        best_score = float('-inf')
        history = []
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

    def print_trial_progress(self, trial_num, total_trials, params, result):
        print(f"[RSIDivergence] Trial {trial_num}/{total_trials} | Params: {params} | Result: {result}")

    def calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR)"""
        try:
            import pandas_ta as ta
            atr = ta.atr(data['high'], data['low'], data['close'], length=period)
            if atr is not None:
                return atr
        except ImportError:
            pass
        
        # Manual ATR calculation
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift(1))
        low_close = abs(data['low'] - data['close'].shift(1))
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=period).mean()
        return atr

    def simulate_trades(self, signals: list, data: pd.DataFrame) -> pd.DataFrame:
        """
        Simulate trades with ATR-based stops and profit targets (matching original hyperopt script exactly)
        """
        # Calculate ATR for stop loss management
        atr = self.calculate_atr(data, self.config['atr_length'])
        
        trades = []
        position = None
        entry_price = 0.0
        current_stop = 0.0
        entry_idx = None
        
        # Sort signals by index to ensure chronological order
        signals_sorted = sorted(signals, key=lambda x: x['index'])
        
        for sig in signals_sorted:
            # SKIP 'hold' signals - only process buy/sell
            if sig.get('action') == 'hold':
                continue
                
            idx = sig['index']
            if idx not in data.index:
                continue
                
            price_val = data.loc[idx, 'close']
            # Always convert to float, but reject complex or invalid types
            try:
                # If price_val is a numpy scalar, get its Python value
                import numpy as np
                import datetime
                if isinstance(price_val, np.generic):
                    price_val = price_val.item()
                # Reject complex numbers and non-numeric types
                if (
                    price_val is None
                    or isinstance(price_val, complex)
                    or isinstance(price_val, (datetime.date, datetime.datetime, datetime.timedelta, pd.Timestamp, pd.Timedelta))
                    or isinstance(price_val, bool)
                    or isinstance(price_val, (bytes, bytearray, memoryview))
                    or isinstance(price_val, str)
                ):
                    continue
                try:
                    price = float(price_val)
                except (TypeError, ValueError):
                    continue
            except Exception:
                continue
            atr_val = atr.loc[idx] if idx in atr.index and not pd.isna(atr.loc[idx]) else price * 0.02
            
            # Check for valid price and ATR
            if not (isinstance(price, (int, float, np.number)) and isinstance(atr_val, (int, float, np.number))):
                continue
            if price <= 0 or not np.isfinite(price) or atr_val <= 0 or not np.isfinite(atr_val):
                continue
            
            # Exit logic (check first, before new entries)
            if position == 'long':
                # Check trailing stop
                new_stop = price - atr_val * self.config['atr_multiplier']
                min_stop = price * (1 - self.config['stop_loss_pct'])  # Use configured stop loss %
                new_stop = max(new_stop, min_stop)
                new_stop = min(new_stop, price - price * 0.001)  # At least 0.1% below
                
                if new_stop > current_stop:
                    current_stop = new_stop
                
                # Check exit conditions
                exit_trade = False
                exit_reason = ""
                
                # Stop loss hit
                if price <= current_stop:
                    exit_trade = True
                    exit_reason = "stop_loss"
                
                # Profit target hit
                elif price >= entry_price * (1 + self.config['profit_target_pct']):
                    exit_trade = True
                    exit_reason = "profit_target"
                
                # Bearish divergence signal (sell)
                elif sig['action'] == 'sell':
                    exit_trade = True
                    exit_reason = "signal"
                
                if exit_trade:
                    pnl = price - entry_price
                    pnl_pct = (price / entry_price - 1) * 100
                    trades.append({
                        'entry': entry_price,
                        'exit': price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'entry_idx': entry_idx,
                        'exit_idx': idx,
                        'exit_reason': exit_reason
                    })
                    position = None
                    entry_price = 0.0
                    current_stop = 0.0
                    entry_idx = None
                    
            elif position == 'short':
                # Check trailing stop for short
                new_stop = price + atr_val * self.config['atr_multiplier']
                max_stop = price * (1 + self.config['stop_loss_pct'])  # Use configured stop loss %
                new_stop = min(new_stop, max_stop)
                new_stop = max(new_stop, price + price * 0.001)  # At least 0.1% above
                
                if new_stop < current_stop:
                    current_stop = new_stop
                
                # Check exit conditions
                exit_trade = False
                exit_reason = ""
                
                # Stop loss hit
                if price >= current_stop:
                    exit_trade = True
                    exit_reason = "stop_loss"
                
                # Profit target hit
                elif price <= entry_price * (1 - self.config['profit_target_pct']):
                    exit_trade = True
                    exit_reason = "profit_target"
                
                # Bullish divergence signal (buy)
                elif sig['action'] == 'buy':
                    exit_trade = True
                    exit_reason = "signal"
                
                if exit_trade:
                    pnl = entry_price - price
                    pnl_pct = (entry_price / price - 1) * 100
                    trades.append({
                        'entry': entry_price,
                        'exit': price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'entry_idx': entry_idx,
                        'exit_idx': idx,
                        'exit_reason': exit_reason
                    })
                    position = None
                    entry_price = 0.0
                    current_stop = 0.0
                    entry_idx = None
            
            # Entry logic (only if no position)
            if position is None:
                if sig['action'] == 'buy':  # Bullish divergence
                    initial_stop = price - atr_val * self.config['atr_multiplier']
                    min_stop = price * (1 - self.config['stop_loss_pct'])  # Use configured stop loss %
                    initial_stop = max(initial_stop, min_stop)
                    initial_stop = min(initial_stop, price - price * 0.001)  # At least 0.1% below
                    
                    position = 'long'
                    entry_price = price
                    current_stop = initial_stop
                    entry_idx = idx
                    
                elif sig['action'] == 'sell':  # Bearish divergence
                    initial_stop = price + atr_val * self.config['atr_multiplier']
                    max_stop = price * (1 + self.config['stop_loss_pct'])  # Use configured stop loss %
                    initial_stop = min(initial_stop, max_stop)
                    initial_stop = max(initial_stop, price + price * 0.001)  # At least 0.1% above
                    
                    position = 'short'
                    entry_price = price
                    current_stop = initial_stop
                    entry_idx = idx
        
        # Close any remaining position at end
        if position is not None and entry_price != 0:
            last_price = data['close'].iloc[-1]
            if position == 'long':
                pnl = last_price - entry_price
            else:
                pnl = entry_price - last_price
            
            pnl_pct = (pnl / entry_price) * 100
            trades.append({
                'entry': entry_price,
                'exit': last_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'entry_idx': entry_idx,
                'exit_idx': data.index[-1],
                'exit_reason': 'end_of_data'
            })
        
        return pd.DataFrame(trades)

    # --- Live trading entry point ---
    def run_strategy(self, state: dict):
        """
        Live trading entry point for RSIDivergenceStrategy.
        Expects state dict with keys: config, data, symbol, strategy_name.
        Uses config as-is (supports list of dicts, best_params, etc.).
        Returns the most recent actionable signal (buy/sell/hold) for the latest bar based on the ask/bid.
        """
        config = state.get('config')
        symbol = state.get('symbol')
        strategy_name = state.get('strategy_name')
        data = state.get('data')

        # Robust config selection (matches other strategies)
        selected_config = None
        if isinstance(config, list):
            # Look for config dict matching symbol and strategy_name
            for c in config:
                if (
                    (c.get('symbol') == symbol or c.get('pair') == symbol)
                    and (c.get('strategy_name') == strategy_name or c.get('name') == strategy_name)
                ):
                    selected_config = c
                    break
            if selected_config is None and len(config) > 0:
                selected_config = config[0]
        elif isinstance(config, dict):
            if 'best_params' in config and isinstance(config['best_params'], dict):
                selected_config = config['best_params']
            else:
                selected_config = config
        else:
            raise ValueError('Invalid config format for live trading')

        if selected_config is None:
            raise ValueError('No valid config found for live trading')

        if data is None:
            raise ValueError('No data provided in state for live trading')
        
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
