"""
AdaptiveRSIStrategy: Modular, research-ready adaptive RSI breakout strategy.

This strategy adapts RSI and volatility breakout logic to changing market conditions. Buy signals are generated
on price breakouts above a dynamic channel with RSI and volume confirmation; sell signals are generated on the
opposite. ATR, Bollinger Bands, and Donchian Channels are used for volatility and breakout detection. The approach
is designed for research, batch optimization, and live trading, with all logic and parameters exposed for robust evaluation.

Features:
- Adaptive breakout detection using RSI, ATR, BB, and Donchian Channels.
- Volume and volatility confirmation logic.
- Modular, bias-protected, and optimizer-compatible class structure.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

class AdaptiveRSIStrategy:
    @staticmethod
    def get_min_candles(params):
        rsi_length = params.get('rsi_length', 14)
        return rsi_length + 1
    """
    Adaptive RSI breakout strategy for research/backtest/hyperopt.
    Includes core logic (signal generation, indicator calculation, config validation)
    and research/backtest helpers (bias protection, splits, optimization).
    """
    # param_grid as a class attribute for optimizer compatibility
    param_grid = {
        'breakout_length': range(10, 31, 2),
        'atr_length': range(7, 21, 1),
        'atr_multiplier': [x / 10.0 for x in range(10, 31, 1)],
        'rsi_length': range(7, 21, 1),
        'bb_length': range(10, 31, 2),
        'bb_multiple': [1.0, 1.5, 2.0, 2.5, 3.0],
        'use_volume_confirmation': [True, False],
        'profit_target': [x / 10.0 for x in range(10, 31, 1)],
        'max_holding': range(10, 31, 2),
        'rsi_oversold': range(20, 41, 2),
        'rsi_overbought': range(60, 81, 2),
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = self.validate_config(config)

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            'breakout_length': 20,
            'atr_length': 14,
            'atr_multiplier': 2.0,
            'rsi_length': 14,
            'bb_length': 20,
            'bb_multiple': 2.0,
            'use_volume_confirmation': True,
            'profit_target': 2.0,
            'max_holding': 20,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'param_grid': {
                'breakout_length': range(10, 31, 2),
                'atr_length': range(7, 21, 1),
                'atr_multiplier': [x / 10.0 for x in range(10, 31, 1)],
                'rsi_length': range(7, 21, 1),
                'bb_length': range(10, 31, 2),
                'bb_multiple': [1.0, 1.5, 2.0, 2.5, 3.0],
                'use_volume_confirmation': [True, False],
                'profit_target': [x / 10.0 for x in range(10, 31, 1)],
                'max_holding': range(10, 31, 2),
                'rsi_oversold': range(20, 41, 2),
                'rsi_overbought': range(60, 81, 2),
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
        return config

    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        cfg = self.config
        if len(data) < max(cfg['breakout_length'], cfg['atr_length'], cfg['rsi_length'], cfg['bb_length']):
            return {}
        dc_upper = data['high'].rolling(window=cfg['breakout_length']).max()
        dc_lower = data['low'].rolling(window=cfg['breakout_length']).min()
        dc_mid = (dc_upper + dc_lower) / 2
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        true_range = pd.Series(true_range, index=data.index)
        atr = true_range.rolling(window=cfg['atr_length']).mean()
        delta = pd.to_numeric(data['close'].diff(), errors='coerce')
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=cfg['rsi_length']).mean()
        avg_loss = loss.rolling(window=cfg['rsi_length']).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        bb_sma = data['close'].rolling(window=cfg['bb_length']).mean()
        bb_std = data['close'].rolling(window=cfg['bb_length']).std()
        bb_upper = bb_sma + (bb_std * cfg['bb_multiple'])
        bb_lower = bb_sma - (bb_std * cfg['bb_multiple'])
        volume_sma = None
        if 'volume' in data.columns:
            volume_sma = data['volume'].rolling(window=20).mean()
        return {
            'rsi': rsi,
            'atr': atr,
            'bb_sma': bb_sma,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'dc_upper': dc_upper,
            'dc_lower': dc_lower,
            'dc_mid': dc_mid,
            'volume_sma': volume_sma
        }

    def generate_signals(self, data: pd.DataFrame, apply_bias: bool = True) -> List[Dict[str, Any]]:
        indicators = self.calculate_indicators(data)
        
        # Create signal_map for buy/sell signals
        signal_map = {}
        for i in range(max(self.config['breakout_length'], self.config['atr_length'], self.config['rsi_length'], self.config['bb_length']), len(data)):
            idx = data.index[i]
            row = data.iloc[:i+1]
            ind = {k: v.iloc[i] if isinstance(v, pd.Series) else v for k, v in indicators.items()}
            current_price = row['close'].iloc[-1]
            previous_price = row['close'].iloc[-2]
            volume_ok = True
            if self.config['use_volume_confirmation'] and 'volume' in row.columns and ind['volume_sma']:
                current_volume = row['volume'].iloc[-1]
                volume_ok = current_volume > ind['volume_sma'] * 0.8
            bb_width = (ind['bb_upper'] - ind['bb_lower']) / ind['bb_sma'] if ind['bb_sma'] else 0
            bb_squeeze = bb_width < 0.1
            long_conditions = [
                current_price >= ind['dc_upper'],
                ind['rsi'] < 85,
                current_price > previous_price,
                volume_ok
            ]
            short_conditions = [
                current_price <= ind['dc_lower'],
                ind['rsi'] > 15,
                current_price < previous_price,
                volume_ok
            ]
            if all(long_conditions):
                signal_map[idx] = {'type': 'bullish', 'index': idx, 'action': 'buy', 'rsi': ind['rsi'], 'bb_squeeze': bb_squeeze, 'volume_confirmed': volume_ok}
            elif all(short_conditions):
                signal_map[idx] = {'type': 'bearish', 'index': idx, 'action': 'sell', 'rsi': ind['rsi'], 'bb_squeeze': bb_squeeze, 'volume_confirmed': volume_ok}
        
        # Apply bias protection if enabled (for backtesting) BEFORE adding hold signals
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
                ind_idx = data.index.get_loc(idx)
                if isinstance(ind_idx, int) and ind_idx < len(indicators['rsi']):
                    rsi_val = indicators['rsi'].iloc[ind_idx]
                else:
                    rsi_val = None
                    
                all_signals.append({
                    'type': 'hold',
                    'index': idx,
                    'action': 'hold',
                    'rsi': rsi_val,
                    'bb_squeeze': False,
                    'volume_confirmed': False
                })
        
        return all_signals

    def apply_bias_protection(self, signals: List[Dict[str, Any]], data: pd.DataFrame) -> List[Dict[str, Any]]:
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

    def split_data_chronologically(self, data: pd.DataFrame, train_ratio: Optional[float] = None, val_ratio: Optional[float] = None) -> Dict[str, pd.DataFrame]:
        if train_ratio is None:
            train_ratio = self.config.get('train_ratio', 0.7)
        if val_ratio is None:
            val_ratio = self.config.get('val_ratio', 0.15)
        # Ensure ratios are floats and not None
        train_ratio = float(train_ratio) if train_ratio is not None else 0.7
        val_ratio = float(val_ratio) if val_ratio is not None else 0.15
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        return {
            'train': data.iloc[:train_end],
            'val': data.iloc[train_end:val_end],
            'test': data.iloc[val_end:]
        }

    def early_reject_parameters(self, performance_history: List[float], patience: Optional[int] = None, min_improvement: Optional[float] = None) -> bool:
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
        if best is None or recent is None or min_improvement is None:
            return False
        return (recent - best) < float(min_improvement)

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
        Simulate trades based on provided signals with proper risk management.
        
        Exit priority (FIXED - was broken before):
        1. Profit target (lock in gains when hit)
        2. Max holding period (prevent extended drawdowns)
        3. Opposite signal (strategy says exit)
        4. End of data (forced close)
        
        Returns a DataFrame with unified columns for all strategies.
        Columns: ['entry', 'exit', 'pnl', 'pnl_pct', 'entry_idx', 'exit_idx', 'exit_reason']
        """
        cfg = self.config
        columns = ['entry', 'exit', 'pnl', 'pnl_pct', 'entry_idx', 'exit_idx', 'exit_reason']
        trades = []
        position = None
        entry_price = None
        entry_idx = None
        take_profit = None
        holding_period = 0
        max_holding = cfg.get('max_holding', 20)
        profit_target_pct = cfg.get('profit_target', 2.0)
        
        # Build signal map for faster lookups (filter out 'hold' signals)
        signal_map = {}
        for sig in signals:
            if sig.get('action') != 'hold':  # Only include buy/sell signals
                signal_map[sig['index']] = sig
        
        for i, idx in enumerate(data.index):
            price = data.loc[idx, 'close']
            
            # Check exits if in position
            if position is not None:
                exit_reason = None
                exit_price = None
                
                # Priority 1: Profit target
                if take_profit is not None and price >= take_profit:
                    exit_reason = 'profit_target'
                    exit_price = price
                
                # Priority 2: Max holding period
                elif holding_period >= max_holding:
                    exit_reason = 'max_holding'
                    exit_price = price
                
                # Priority 3: Opposite signal
                elif idx in signal_map and signal_map[idx]['action'] == 'sell':
                    exit_reason = 'signal'
                    exit_price = price
                
                # Execute exit if triggered
                if exit_reason:
                    try:
                        price_val = float(np.asarray(exit_price).item()) if exit_price is not None else 0.0
                        entry_val = float(np.asarray(entry_price).item()) if entry_price not in (0, None, "") else 0.0
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
                    
                    # Reset position
                    position = None
                    entry_price = None
                    entry_idx = None
                    take_profit = None
                    holding_period = 0
            
            # Check for new entry
            if position is None and idx in signal_map and signal_map[idx]['action'] == 'buy':
                position = 'long'
                entry_price = price
                entry_idx = idx
                take_profit = price * (1 + profit_target_pct / 100)
                holding_period = 0
            
            # Increment holding period
            if position is not None:
                holding_period += 1
        
        # Priority 4: Close remaining position at end
        if position == 'long' and entry_price not in (0, None, ""):
            last_idx = data.index[-1]
            last_price = data['close'].iloc[-1]
            try:
                last_val = float(np.asarray(last_price).item()) if last_price is not None else 0.0
                entry_val = float(np.asarray(entry_price).item()) if entry_price is not None else 0.0
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
        print(f"[AdaptiveRSI] Trial {trial_num}/{total_trials} | Params: {params} | Result: {result}")

    # --- Live trading entry point ---
    def run_strategy(self, state):
        """
        Entry point for live trading integration. Expects `state` to contain the latest market data as a pandas DataFrame
        and a config dict. Only live signal generation is performed (no backtest, no bias-protection).
        """
        config = state.get('config')
        data = state.get('data')
        required_keys = [
            'breakout_length', 'atr_length', 'atr_multiplier', 'rsi_length', 'bb_length', 'bb_multiple',
            'use_volume_confirmation', 'profit_target', 'max_holding', 'rsi_oversold', 'rsi_overbought'
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
