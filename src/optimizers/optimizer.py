import os
os.environ['PYTHONUNBUFFERED'] = '1'
print("[OPTIMIZER] Script entrypoint reached.", flush=True)
"""
Optimizer script for running hyperparameter optimization on any strategy and symbol.
Usage:
    python src/optimizers/optimizer.py --strategy rsi_divergence --symbol BTCUSDT --exchange phemex
"""
import argparse
import logging
import os
import sys
import importlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.backtest.engine import BacktestEngine
from src.data.symbol_discovery import get_phemex_base_symbols, get_hyperliquid_symbols
from src.data.symbol_intersection import get_common_base_symbols
import pandas as pd

# Import all strategies dynamically
from src.strategy import strategies

# Use dynamic strategy mapping
STRATEGY_MAP = strategies

# Create reverse mapping for module name lookup
STRATEGY_MODULE_MAP = {strategy_class.__name__: strategy_name for strategy_name, strategy_class in strategies.items() if strategy_class is not None}

def load_ohlcv(symbol, exchange, timeframe='1d', source='csv', sqlite_path=None):
    """
    Loads OHLCV data from CSV or SQLite. Always returns DataFrame with required columns.
    """
    import pandas as pd
    import os
    
    # Define project_root at the start
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    if sqlite_path is None:
        sqlite_path = os.path.join(project_root, 'data', 'pipeline_results.sqlite')
    required_cols = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
    if source == 'csv':
        csv_path = os.path.join(project_root, 'data', f'{symbol}_{timeframe}_candle_data.csv')
        print(f"[optimizer] Looking for OHLCV file: {csv_path}", flush=True)
        if os.path.exists(csv_path):
            print(f"[optimizer] File exists: {csv_path}", flush=True)
            try:
                df = pd.read_csv(csv_path)
                print(f"[optimizer] Columns found: {list(df.columns)}", flush=True)
                # Validate columns
                for col in required_cols:
                    if col not in df.columns:
                        print(f"[optimizer] Missing column '{col}' in {csv_path}", flush=True)
                        logging.warning(f"Missing column '{col}' in {csv_path}")
                        return pd.DataFrame()
                return df
            except Exception as e:
                print(f"[optimizer] Failed to load OHLCV from {csv_path}: {e}", flush=True)
                logging.warning(f"Failed to load OHLCV from {csv_path}: {e}")
                return pd.DataFrame()
        else:
            print(f"[optimizer] OHLCV file not found: {csv_path}", flush=True)
            logging.warning(f"OHLCV file not found: {csv_path}")
            return pd.DataFrame()
    elif source == 'sqlite':
        import sqlite3
        try:
            conn = sqlite3.connect(sqlite_path)
            query = f"SELECT open, high, low, close, volume, timestamp FROM ohlcv WHERE symbol=? AND exchange=? AND timeframe=?"
            df = pd.read_sql_query(query, conn, params=(symbol, exchange, timeframe))
            conn.close()
            print(f"[optimizer] Loaded OHLCV from SQLite for {symbol}", flush=True)
            print(f"[optimizer] Columns found: {list(df.columns)}", flush=True)
            # Validate columns
            for col in required_cols:
                if col not in df.columns:
                    print(f"[optimizer] Missing column '{col}' in SQLite for {symbol}", flush=True)
                    logging.warning(f"Missing column '{col}' in SQLite for {symbol}")
                    return pd.DataFrame()
            return df
        except Exception as e:
            print(f"[optimizer] Failed to load OHLCV from SQLite: {e}", flush=True)
            logging.warning(f"Failed to load OHLCV from SQLite: {e}")
            return pd.DataFrame()
    else:
        print(f"[optimizer] Unknown data source: {source}", flush=True)
        logging.error(f"Unknown data source: {source}")
        return pd.DataFrame()

print(f"[OPTIMIZER] Started optimizer for symbol/strategy CLI args: {sys.argv}", flush=True)
def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    parser = argparse.ArgumentParser(description='Run strategy optimizer')
    parser.add_argument('--strategy', required=True, help='Strategy name (e.g., RSIDivergenceStrategy or rsi_divergence)')
    parser.add_argument('--symbol', required=True, help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--exchange', required=True, help='Exchange (phemex or hyperliquid)')
    parser.add_argument('--timeframe', default='5m', help='Timeframe (e.g., 5m, 15m, 1h, 1d)')
    parser.add_argument('--data-source', default='csv', choices=['csv', 'sqlite'], help='OHLCV data source (csv or sqlite)')
    parser.add_argument('--sqlite-path', default=os.path.join(project_root, 'data', 'pipeline_results.sqlite'), help='SQLite DB path if using sqlite')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    print(f"[OPTIMIZER] Starting optimizer for {args.symbol} with {args.strategy} on {args.exchange}", flush=True)
    # Try class name first, then snake_case
    strategy_cls = None
    module_name = STRATEGY_MODULE_MAP.get(args.strategy)
    if module_name:
        try:
            strategy_module = importlib.import_module(f'src.strategy.{module_name}')
            strategy_cls = getattr(strategy_module, args.strategy)
        except Exception as e:
            logging.error(f"Failed to import strategy class {args.strategy} from module {module_name}: {e}")
    if not strategy_cls:
        # Fallback to snake_case
        strategy_cls = STRATEGY_MAP.get(args.strategy.lower())
    if not strategy_cls:
        logging.error(f"Strategy '{args.strategy}' not found.")
        sys.exit(1)

    print(f"[OPTIMIZER] About to load OHLCV data for symbol: {args.symbol}, data source: {args.data_source}, path: {args.sqlite_path if args.data_source == 'sqlite' else 'CSV'}", flush=True)
    ohlcv = load_ohlcv(args.symbol, args.exchange, timeframe=args.timeframe, source=args.data_source, sqlite_path=args.sqlite_path)
    print(f"[OPTIMIZER] OHLCV data loaded. Shape: {ohlcv.shape if hasattr(ohlcv, 'shape') else 'N/A'} Columns: {list(ohlcv.columns) if hasattr(ohlcv, 'columns') else 'N/A'}", flush=True)
    if ohlcv.empty:
        logging.error(f"No valid OHLCV data for {args.symbol} from {args.data_source}. Skipping.")
        sys.exit(1)
    config = {}  # TODO: Load config for strategy/symbol
    engine = BacktestEngine(strategy_cls, args.symbol, config, ohlcv)
    param_grid = getattr(strategy_cls, 'param_grid', {})
    print("[OPTIMIZER] Starting hyperopt loop...", flush=True)
    # Instantiate strategy for progress printing
    strategy_instance = strategy_cls(config)
    results = engine.run_hyperopt(param_grid)
    print(results, flush=True)

if __name__ == "__main__":
    main()
