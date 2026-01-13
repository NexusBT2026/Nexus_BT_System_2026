"""
engine.py: Backtest and hyperopt engine for modular strategies.
"""
import logging
from typing import Any, Dict, Callable
import pandas as pd

try:
    from backtesting import Backtest, Strategy
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False
    logging.warning("backtesting library not available. Install with: pip install backtesting")

class BacktestEngine:
    def run_optuna(self, param_grid: Dict[str, Any], n_trials: int = 100) -> Dict[str, Any]:
        """
        Run hyperparameter optimization using Optuna.
        """
        import optuna
        logging.info(f"Running Optuna optimization for {self.symbol} with {self.strategy_cls.__name__} (n_trials={n_trials})")

        # Convert param_grid to Optuna search space
        def suggest_params(trial):
            params = {}
            for param_name, param_values in param_grid.items():
                if isinstance(param_values, range):
                    params[param_name] = trial.suggest_int(param_name, param_values.start, param_values.stop - 1, step=param_values.step)
                elif isinstance(param_values, list):
                    # If all values are numeric and evenly spaced, use suggest_float
                    if len(param_values) > 1 and all(isinstance(x, (int, float)) for x in param_values):
                        diffs = [round(param_values[i+1] - param_values[i], 6) for i in range(len(param_values)-1)]
                        if len(set(diffs)) == 1:
                            params[param_name] = trial.suggest_float(param_name, min(param_values), max(param_values))
                        else:
                            params[param_name] = trial.suggest_categorical(param_name, param_values)
                    else:
                        params[param_name] = trial.suggest_categorical(param_name, param_values)
                else:
                    params[param_name] = param_values
            return params

        def objective(trial):
            try:
                params = suggest_params(trial)
                config = self.config.copy()
                config.update(params)
                strategy = self.strategy_cls(config)
                signals = strategy.generate_signals(self.data)
                trades = strategy.simulate_trades(signals, self.data)
                metrics = self._calculate_metrics(trades)
                score = self._evaluate(metrics)
                return -score  # Optuna minimizes
            except Exception as e:
                logging.error(f"Error in Optuna objective: {e}")
                return float('inf')

        study = optuna.create_study(direction="minimize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

        best_params = study.best_params
        best_config = self.config.copy()
        best_config.update(best_params)
        # Run final backtest with best parameters
        strategy = self.strategy_cls(best_config)
        signals = strategy.generate_signals(self.data)
        trades = strategy.simulate_trades(signals, self.data)
        metrics = self._calculate_metrics(trades)

        return {
            'parameters': best_params,
            'score': -study.best_value,
            'metrics': metrics,
            'trials_completed': len(study.trials),
            'trades': trades.to_dict('records') if trades is not None and hasattr(trades, 'to_dict') else []
        }
    def __init__(self, strategy_cls: Callable, symbol: str, config: Dict[str, Any], data: pd.DataFrame):
        self.strategy_cls = strategy_cls
        self.symbol = symbol
        self.config = config
        self.data = data
        self.strategy = strategy_cls(config)

    def run_backtest(self) -> Dict[str, Any]:
        logging.info(f"Running backtest for {self.symbol} with {self.strategy_cls.__name__}")
        # Generic backtest logic for any strategy class
        # 1. Generate signals
        signals = self.strategy.generate_signals(self.data)
        # 2. Simulate trades
        trades = self.strategy.simulate_trades(signals, self.data)
        # 3. Calculate metrics (this will filter out end_of_data trades internally)
        metrics = self._calculate_metrics(trades)
        
        # Keep ALL trades in results (including end_of_data) for analysis
        # But metrics are calculated only on complete strategy-driven trades
        results = {
            'symbol': self.symbol,
            'strategy': self.strategy_cls.__name__,
            'metrics': metrics,
            'parameters': self.config,
            'trades': trades.to_dict('records') if trades is not None and hasattr(trades, 'to_dict') else []
        }
        return results

    def run_backtest_engine(self) -> Dict[str, Any]:
        logging.info(f"Running backtest for {self.symbol} with {self.strategy_cls.__name__} using engine method")
        # Generic backtest logic for any strategy class
        # 1. Generate signals
        signals = self.strategy.generate_signals(self.data)
        # 2. Simulate trades
        trades = self.strategy.simulate_trades(signals, self.data)
        # 3. Calculate metrics (this will filter out end_of_data trades internally)
        metrics = self._calculate_metrics(trades)
        
        # Keep ALL trades in results (including end_of_data) for analysis
        # But metrics are calculated only on complete strategy-driven trades
        results = {
            'symbol': self.symbol,
            'strategy': self.strategy_cls.__name__,
            'metrics': metrics,
            'parameters': self.config,
            'trades': trades.to_dict('records') if trades is not None and hasattr(trades, 'to_dict') else []
        }
        return results

    def run_backtest_library(self) -> Dict[str, Any]:
        """
        Run backtest using backtesting.py library.
        This provides an alternative backtest method using an external library.
        """
        if not BACKTESTING_AVAILABLE:
            logging.error("backtesting library not available. Install with: pip install backtesting")
            return self.run_backtest()  # Fallback to our custom method

        logging.info(f"Running backtesting.py backtest for {self.symbol} with {self.strategy_cls.__name__}")

        # Create a backtesting.py compatible strategy class dynamically
        strategy_cls = self.strategy_cls
        config = self.config

        class BacktestingPyStrategy(Strategy):
            def init(self):
                # Store reference to our strategy
                self.nexus_strategy = strategy_cls(config)
                # Pre-calculate indicators and signals using backtesting.py data format
                # Convert backtesting.py data to DataFrame
                df = pd.DataFrame({
                    'open': self.data.Open,
                    'high': self.data.High,
                    'low': self.data.Low,
                    'close': self.data.Close,
                    'volume': self.data.Volume
                })
                
                # Generate signals using the strategy's generate_signals method
                signals_df = self.nexus_strategy.generate_signals(df)
                
                # Convert signals to a series indexed by position
                self.signals = pd.Series(0, index=df.index)
                if isinstance(signals_df, pd.DataFrame) and 'signal' in signals_df.columns:
                    # Handle dataframe interface (signal column with 1=buy, -1=sell, 0=hold)
                    for i, signal in enumerate(signals_df['signal']):
                        self.signals.iloc[i] = signal
                elif isinstance(signals_df, list):
                    # Handle list of dictionaries interface
                    for signal_dict in signals_df:
                        idx = signal_dict['index']
                        action = signal_dict.get('action', 'hold')
                        if action == 'buy':
                            self.signals.iloc[idx] = 1
                        elif action == 'sell':
                            self.signals.iloc[idx] = -1
                        # hold = 0 (default)

            def next(self):
                # Get current signal from pre-calculated signals
                current_idx = len(self.data) - 1
                if current_idx < len(self.signals):
                    signal = self.signals.iloc[current_idx]

                    # Execute trades based on signal
                    if signal == 1 and not self.position:
                        # Buy signal
                        self.buy()
                    elif signal == -1 and self.position:
                        # Sell signal
                        self.position.close()

        # Prepare data for backtesting.py (ensure proper OHLCV format and DateTimeIndex)
        df = self.data.copy()
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            # Convert from lowercase to proper case
            col_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            df = df.rename(columns=col_mapping)

        # Ensure we have a DateTimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.date_range(start='2020-01-01', periods=len(df), freq='D')

        # Run backtest
        bt = Backtest(df, BacktestingPyStrategy, cash=self.config.get('initial_capital', 10000),
                     commission=self.config.get('commission', 0.001))

        # Execute backtest
        result = bt.run()

        # Convert backtesting.py results to our format
        trades = []
        if hasattr(result, '_trades') and result._trades is not None:
            for trade in result._trades.itertuples():
                trades.append({
                    'entry_time': getattr(trade, 'EntryTime', None),
                    'exit_time': getattr(trade, 'ExitTime', None),
                    'entry_price': getattr(trade, 'EntryPrice', 0),
                    'exit_price': getattr(trade, 'ExitPrice', 0),
                    'pnl': getattr(trade, 'PnL', 0),
                    'size': getattr(trade, 'Size', 0),
                    'exit_reason': 'signal'  # backtesting.py doesn't track exit reasons like we do
                })

        # Convert metrics to our format, handling NaN values
        def safe_get(result_dict, key, default=0.0):
            val = result_dict.get(key, default)
            return default if pd.isna(val) else val

        metrics = {
            'pnl': safe_get(result, 'Return [%]', 0.0) * self.config.get('initial_capital', 10000) / 100,
            'sharpe': safe_get(result, 'Sharpe Ratio', 0.0),
            'win_rate': safe_get(result, 'Win Rate [%]', 0.0) / 100,
            'total_trades': int(safe_get(result, '# Trades', 0)),
            'winning_trades': int(safe_get(result, '# Trades', 0) * safe_get(result, 'Win Rate [%]', 0.0) / 100),
            'losing_trades': int(safe_get(result, '# Trades', 0) * (1 - safe_get(result, 'Win Rate [%]', 0.0) / 100)),
            'max_drawdown': safe_get(result, 'Max. Drawdown [%]', 0.0),
            'profit_factor': safe_get(result, 'Profit Factor', 0.0),
            'kelly': 0.0,  # backtesting.py doesn't calculate Kelly
            'sqn': 0.0     # backtesting.py doesn't calculate SQN
        }

        # Return in our standard format
        results = {
            'symbol': self.symbol,
            'strategy': self.strategy_cls.__name__,
            'metrics': metrics,
            'parameters': self.config,
            'trades': trades
        }
        return results

    def run_hyperopt(self, param_grid: Dict[str, Any], max_evals: int = 100) -> Dict[str, Any]:
        """
        Run Bayesian optimization using hyperopt library (matching legacy system)
        """
        logging.info(f"Running hyperopt for {self.symbol} with {self.strategy_cls.__name__} (max_evals={max_evals})")
        
        try:
            from hyperopt import fmin, tpe, hp, Trials, STATUS_OK
        except ImportError:
            logging.error("hyperopt library not found. Please install: pip install hyperopt")
            return self._fallback_random_search(param_grid, max_evals)
        
        # Convert param_grid to hyperopt space (matching legacy format)
        space = self._convert_param_grid_to_hyperopt_space(param_grid)
        
        if not space:
            logging.warning("No valid hyperopt space created, falling back to random search")
            return self._fallback_random_search(param_grid, max_evals)
        
        trials = Trials()
        
        def objective(params):
            try:
                # Convert float parameters to integers where needed (for range-based params)
                processed_params = {}
                for key, value in params.items():
                    # Check if this parameter was defined as a range in param_grid
                    if key in param_grid and isinstance(param_grid[key], range):
                        # Convert to integer for range-based parameters
                        processed_params[key] = int(round(value))
                    else:
                        processed_params[key] = value
                
                # Create config with these parameters
                config = self.config.copy()
                config.update(processed_params)
                
                # Create strategy instance with these parameters
                strategy = self.strategy_cls(config)
                
                # Run backtest
                signals = strategy.generate_signals(self.data)
                trades = strategy.simulate_trades(signals, self.data)
                metrics = self._calculate_metrics(trades)
                
                # Use negative score because hyperopt minimizes
                score = self._evaluate(metrics)
                return {'loss': -score, 'status': STATUS_OK, 'eval_time': None}
                
            except Exception as e:
                logging.error(f"Error in hyperopt objective: {e}")
                return {'loss': float('inf'), 'status': STATUS_OK, 'eval_time': None}
        
        # print(f"Starting Bayesian optimization with {max_evals} trials...")
        
        try:
            best = fmin(
                fn=objective,
                space=space,
                algo=tpe.suggest,
                max_evals=max_evals,
                trials=trials,
                verbose=False
            )
            
            # Get best result
            best_trial = min(trials.trials, key=lambda x: x['result']['loss'])
            
            # Convert best parameters to proper types (integers for range-based params)
            best_params = {}
            if best is not None:
                for key, value in best.items():
                    if key in param_grid and isinstance(param_grid[key], range):
                        best_params[key] = int(round(value))
                    else:
                        best_params[key] = value
            else:
                logging.error("No best parameters found from hyperopt. Falling back to random search.")
                return self._fallback_random_search(param_grid, max_evals)
            
            best_config = self.config.copy()
            best_config.update(best_params)
            
            # Run final backtest with best parameters
            strategy = self.strategy_cls(best_config)
            signals = strategy.generate_signals(self.data)
            trades = strategy.simulate_trades(signals, self.data)
            metrics = self._calculate_metrics(trades)
            
            return {
                'parameters': best_params,
                'score': -best_trial['result']['loss'],
                'metrics': metrics,
                'trials_completed': len(trials.trials),
                'trades': trades.to_dict('records') if trades is not None and hasattr(trades, 'to_dict') else []
            }
            
        except Exception as e:
            logging.error(f"Hyperopt failed: {e}, falling back to random search")
            return self._fallback_random_search(param_grid, max_evals)

    def _grid_search(self, param_grid: Dict[str, Any]):
        # Generic grid search over all parameter combinations
        from itertools import product
        keys = list(param_grid.keys())
        values = []
        for k in keys:
            if isinstance(param_grid[k], range):
                # Convert range to list
                values.append(list(param_grid[k]))
            elif isinstance(param_grid[k], list):
                values.append(param_grid[k])
            else:
                # Single value
                values.append([param_grid[k]])
        for combo in product(*values):
            params = dict(zip(keys, combo))
            yield params

    def _evaluate(self, result: Dict[str, Any]) -> float:
        # Generic scoring: use Sharpe ratio if available, else PnL
        metrics = result.get('metrics', {})
        return metrics.get('sharpe', metrics.get('pnl', 0.0))

    def _calculate_metrics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        # Calculate PnL, Sharpe ratio, win rate, etc. from trades DataFrame
        if trades is None or trades.empty:
            return {
                'pnl': 0.0, 
                'sharpe': 0.0, 
                'win_rate': 0.0, 
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'kelly': 0.0,
                'sqn': 0.0
            }
        
        # PROFESSIONAL BACKTEST PRACTICE: Filter out 'end_of_data' trades
        # These are incomplete trades forced to close when backtest data ends
        # Including them skews optimization results
        if 'exit_reason' in trades.columns:
            trades = trades[trades['exit_reason'] != 'end_of_data'].copy()
            logging.info(f"Filtered out end_of_data trades. Remaining: {len(trades)} trades")
        
        # Re-check if we have any trades left after filtering
        if trades.empty:
            return {
                'pnl': 0.0, 
                'sharpe': 0.0, 
                'win_rate': 0.0, 
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'kelly': 0.0,
                'sqn': 0.0
            }
        
        pnl = trades['pnl'].sum() if 'pnl' in trades else 0.0
        returns = trades['pnl'] if 'pnl' in trades else pd.Series([0.0])
        sharpe = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() != 0 else 0.0
        wins = (returns > 0).sum()
        total_trades = len(trades)
        win_rate = wins / total_trades if total_trades > 0 else 0.0
        
        # Calculate max_drawdown from cumulative returns as percentage
        cumulative = returns.cumsum()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max)
        
        # Convert to percentage based on initial capital
        initial_capital = self.config.get('initial_capital', 10000)
        max_drawdown_pct = (abs(drawdown.min()) / initial_capital * 100) if len(drawdown) > 0 and initial_capital > 0 else 0.0
        
        # Calculate profit_factor (gross profit / gross loss)
        gross_profit = returns[returns > 0].sum() if (returns > 0).any() else 0.0
        gross_loss = abs(returns[returns < 0].sum()) if (returns < 0).any() else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        # Calculate average win and average loss
        avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0.0
        avg_loss = returns[returns < 0].mean() if (returns < 0).any() else 0.0  # Keep negative
        
        # Calculate Kelly Criterion: f = (p*b - q) / b where p=win_rate, q=loss_rate, b=avg_win/avg_loss
        if wins > 0 and (total_trades - wins) > 0:
            avg_win_abs = returns[returns > 0].mean()
            avg_loss_abs = abs(returns[returns < 0].mean())
            if avg_loss_abs > 0:
                b = avg_win_abs / avg_loss_abs
                p = win_rate
                q = 1 - win_rate
                kelly = (p * b - q) / b
                kelly = max(0.0, min(kelly, 1.0))  # Clamp between 0 and 1
            else:
                kelly = 0.0
        else:
            kelly = 0.0
        
        # Calculate SQN (System Quality Number): (avg_trade / std_trade) * sqrt(num_trades)
        avg_trade = returns.mean()
        std_trade = returns.std()
        sqn = (avg_trade / std_trade) * (total_trades ** 0.5) if std_trade > 0 else 0.0
        
        return {
            'pnl': pnl, 
            'sharpe': sharpe, 
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': wins,
            'losing_trades': total_trades - wins,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown_pct,
            'profit_factor': profit_factor,
            'kelly': kelly,
            'sqn': sqn
        }

    def _convert_param_grid_to_hyperopt_space(self, param_grid: Dict[str, Any]) -> Dict[str, Any]:
        """Convert param_grid to hyperopt space definitions.
        
        ALWAYS uses hp.choice for lists to ensure discrete value selection.
        Using hp.uniform generates continuous floats which breaks strategies.
        """
        try:
            from hyperopt import hp
        except ImportError:
            return {}
        
        space = {}
        
        for param_name, param_values in param_grid.items():
            if isinstance(param_values, range):
                # Convert range to hp.quniform for integer ranges
                start, stop, step = param_values.start, param_values.stop - 1, param_values.step
                space[param_name] = hp.quniform(param_name, start, stop, step)
                
            elif isinstance(param_values, list):
                # ALWAYS use hp.choice for lists - ensures exact discrete values
                space[param_name] = hp.choice(param_name, param_values)
            else:
                # Single value - use hp.choice with one option
                space[param_name] = hp.choice(param_name, [param_values])
        
        return space
    
    def _fallback_random_search(self, param_grid: Dict[str, Any], max_evals: int) -> Dict[str, Any]:
        """Fallback random search if hyperopt fails"""
        import random
        
        # print(f"Running fallback random search with {max_evals} trials...")
        
        best_params = None
        best_score = float('-inf')
        
        for trial in range(max_evals):
            # Sample random parameters
            params = {}
            for key, values in param_grid.items():
                if isinstance(values, range):
                    params[key] = random.choice(list(values))
                elif isinstance(values, list):
                    params[key] = random.choice(values)
                else:
                    params[key] = values
            
            try:
                # Create config with these parameters
                config = self.config.copy()
                config.update(params)
                
                # Create strategy instance with these parameters
                strategy = self.strategy_cls(config)
                
                # Run backtest
                signals = strategy.generate_signals(self.data)
                trades = strategy.simulate_trades(signals, self.data)
                metrics = self._calculate_metrics(trades)
                
                score = self._evaluate(metrics)
                
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    
            except Exception as e:
                logging.error(f"Error in random search trial {trial}: {e}")
                continue
            
            # Progress update
            if (trial + 1) % 10 == 0:
                pass  # print(f"Random search progress: {trial + 1}/{max_evals} trials")
        
        if best_params is None:
            return {}
        
        # Run final backtest with best parameters
        config = self.config.copy()
        config.update(best_params)
        strategy = self.strategy_cls(config)
        signals = strategy.generate_signals(self.data)
        trades = strategy.simulate_trades(signals, self.data)
        metrics = self._calculate_metrics(trades)
        
        return {
            'parameters': best_params,
            'score': best_score,
            'metrics': metrics,
            'trials_completed': max_evals
        }

# Example usage (to be called from pipeline):
# from src.strategy.rsi_divergence import RSIDivergenceStrategy
# import pandas as pd
# data = pd.read_csv('path_to_data.csv')
# config = {...}
# param_grid = {...}
# engine = BacktestEngine(RSIDivergenceStrategy, 'BTCUSDT', config, data)
# backtest_result = engine.run_backtest()
# backtest_library_result = engine.run_backtest_library()  # Using backtesting.py library
# hyperopt_result = engine.run_hyperopt(param_grid)
#
# Note: Each strategy must implement generate_signals(data) and simulate_trades(data, signals)
# and return metrics as a dict (e.g., {'pnl': ..., 'sharpe': ...})
# This engine is now generic for all modular strategies.
