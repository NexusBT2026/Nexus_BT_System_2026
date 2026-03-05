#!/usr/bin/env python3
"""
Nexus Backtesting System - BTC Single Symbol
Exact copy of run_bt.py adapted to run BTC only using the pipeline's
single-symbol test approach (optimize_strategy_task + save_individual_result).
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.pipeline_BT_unified_async import (
    optimize_strategy_task,
    save_individual_result,
    fetch_ohlcv_data_async,
    NUMEXPR_MAX_THREADS
)
from src.backtest.dashboard_monitor import show_initialization_screen, create_dashboard
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import sys
import os
from contextlib import contextmanager

# Suppress logs IMMEDIATELY before any imports
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# ── BTC config ────────────────────────────────────────────────────────────────
TARGET_SYMBOL     = 'BTC'
TARGET_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h']
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def silent_operation():
    """Context manager to silence logging output only (not stdout/stderr for spinner)."""
    # Disable ALL logging temporarily
    logging.disable(logging.CRITICAL)
    
    try:
        yield
    finally:
        # Re-enable logging
        logging.disable(logging.NOTSET)

# Suppress noisy loggers during symbol discovery and data fetch
def suppress_noisy_logs():
    """Suppress JSON and verbose logging for clean client display."""
    # Suppress all INFO, DEBUG and WARNING level logs globally for clean output
    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    
    loggers_to_quiet = [
        'symbol_discovery_source',
        'pipeline_BT_source',
        'src.data.api_rate_monitor',
        'hyperliquid_ohlcv_source',
        'phemex_ohlcv_source',
        'coinbase_ohlcv_source',
        'binance_ohlcv_source',
        'kucoin_ohlcv_source',
        'bybit_ohlcv_source',
        'okx_ohlcv_source',
        'bitget_ohlcv_source',
        'gateio_ohlcv_source',
        'mexc_ohlcv_source',
        ''  # Root logger
    ]
    
    for logger_name in loggers_to_quiet:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)  # Only show errors
        # Remove all handlers to prevent duplicate output
        logger.handlers = []
        logger.propagate = False

async def main():
    # Get CLI arguments if available
    max_workers = getattr(cli_args, 'workers', 25)
    n_trials = getattr(cli_args, 'trials', 300)
    optimizer = getattr(cli_args, 'optimizer', 'hyperopt')
    scheduler_mode = getattr(cli_args, 'scheduler', False)
    force_refresh = getattr(cli_args, 'force_refresh', False)

    # Suppress noisy logs for clean client display
    suppress_noisy_logs()

    try:
        import pandas as pd
        import glob

        data_dir = os.path.join(os.path.dirname(__file__), 'data')

        try:
            from rich.console import Console
            console = Console()
            console.print(f"[cyan]🔶 BTC multi-timeframe mode[/cyan]\n")
            console.print(f"[dim]   Timeframes: {', '.join(TARGET_TIMEFRAMES)}[/dim]\n")
        except ImportError:
            print(f"🔶 BTC multi-timeframe mode")
            print(f"   Timeframes: {', '.join(TARGET_TIMEFRAMES)}")

        # ── Step 1: Fetch data for BTC across all timeframes (like run_bt.py) ────
        show_initialization_screen('data_fetch', {
            'Symbol': TARGET_SYMBOL,
            'Timeframes': ', '.join(TARGET_TIMEFRAMES),
            'Data Source': 'Multi-exchange (Hyperliquid primary)',
            'Caching': 'CSV format with staleness detection',
            'Force Refresh': 'YES' if force_refresh else 'Use cache'
        })

        # Build a BTC-only symbols dict so fetch_ohlcv_data_async only pulls BTC
        btc_symbols = {
            'hyperliquid': [TARGET_SYMBOL],
            'unmatched_binance': [TARGET_SYMBOL],
            'phemex': [TARGET_SYMBOL],
        }

        try:
            from rich.console import Console
            console = Console()
            console.print("[cyan]Fetching BTC historical OHLCV data...[/cyan]")
            with silent_operation():
                await fetch_ohlcv_data_async(btc_symbols, timeframes=TARGET_TIMEFRAMES,
                                             data_dir=data_dir, force_refresh=force_refresh)
            console.print("[green]Data fetch complete[/green]\n")
        except ImportError:
            print("Fetching BTC historical OHLCV data...")
            with silent_operation():
                await fetch_ohlcv_data_async(btc_symbols, timeframes=TARGET_TIMEFRAMES,
                                             data_dir=data_dir, force_refresh=force_refresh)
            print("Data fetch complete\n")

        # ── Step 2: Discover which BTC CSVs are available after fetch ────────────
        available_csvs = {}
        for tf in TARGET_TIMEFRAMES:
            csv_file = os.path.join(data_dir, f'{TARGET_SYMBOL}_{tf}_candle_data.csv')
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                if len(df) >= 200:
                    available_csvs[tf] = (csv_file, df)
                else:
                    print(f"Skipping {tf}: only {len(df)} candles")
            else:
                print(f"Skipping {tf}: no data file found")

        if not available_csvs:
            print("No BTC data files found for any timeframe. Run with --force-refresh.")
            return 1

        print(f"Available timeframes: {list(available_csvs.keys())}")

        # ── Step 3: Pick strategies ───────────────────────────────────────────────
        from src.strategy import strategies

        test_strategies = []
        available_strategies = list(strategies.keys())
        preferred_test_strategies = ['multi_confirmation_40x']
        for strat in preferred_test_strategies:
            if strat in available_strategies:
                test_strategies.append(strat)
        if not test_strategies:
            test_strategies = available_strategies[:4]

        # ── Step 4: Build all (timeframe × strategy) tasks ───────────────────────
        output_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(output_dir, exist_ok=True)

        optimization_tasks = []
        skipped_count = 0

        for tf, (csv_file, df) in available_csvs.items():
            for strategy_name in test_strategies:
                strategy_class = strategies.get(strategy_name)
                if strategy_class is None:
                    continue

                result_file = os.path.join(output_dir, TARGET_SYMBOL, tf,
                                           f'results_{strategy_name}_strategy.json')
                if os.path.exists(result_file) and not force_refresh:
                    try:
                        import json
                        with open(result_file, 'r') as f:
                            existing = json.load(f)
                        if existing.get('success', False):
                            skipped_count += 1
                            continue
                    except Exception:
                        pass

                optimization_tasks.append({
                    'symbol':            TARGET_SYMBOL,
                    'timeframe':         tf,
                    'strategy_name':     strategy_name,
                    'strategy_class':    strategy_class,
                    'strategy_category': 'custom',
                    'reopt_days':        7,
                    'data':              df.copy(),
                    'csv_file':          csv_file,
                    'optimizer':         optimizer,
                    'n_trials':          n_trials,
                })

        total_tasks = len(optimization_tasks) + skipped_count

        show_initialization_screen('optimization_start', {
            'Symbol': TARGET_SYMBOL,
            'Timeframes': ', '.join(available_csvs.keys()),
            'Strategies': ', '.join(test_strategies),
            'Total Optimizations': total_tasks,
            'Skipped (cached)': skipped_count,
            'Workers': max_workers,
            'Optimizer': f'{optimizer.capitalize()} (Bayesian)',
            'Trials per Strategy': n_trials
        })

        # Suppress pipeline logger
        pipeline_logger = logging.getLogger('pipeline_BT_source')
        pipeline_logger.setLevel(logging.ERROR)
        pipeline_logger.handlers = []
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('\n[ERROR] %(message)s\n'))
        pipeline_logger.addHandler(error_handler)

        # ── Step 5: Run all tasks in parallel (ProcessPoolExecutor like pipeline) ─
        dashboard = create_dashboard(total_tasks)
        dashboard.start()

        for _ in range(skipped_count):
            dashboard.update_task(TARGET_SYMBOL, '--', 'various', 'skipped', category='cached')

        successful = 0
        failed = 0

        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_task = {
                    executor.submit(optimize_strategy_task, task): task
                    for task in optimization_tasks
                }
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    tf = task['timeframe']
                    strategy_name = task['strategy_name']
                    try:
                        result = future.result()
                        if result and result.get('success'):
                            save_individual_result(result, output_dir)
                            successful += 1
                            dashboard.update_task(TARGET_SYMBOL, tf, strategy_name, 'success',
                                                  passed_criteria=True)
                        else:
                            failed += 1
                            err = result.get('error', 'unknown') if result else 'no result'
                            dashboard.update_task(TARGET_SYMBOL, tf, strategy_name, 'failed',
                                                  error_msg=err)
                    except Exception as exc:
                        failed += 1
                        dashboard.update_task(TARGET_SYMBOL, tf, strategy_name, 'failed',
                                              error_msg=str(exc))
        finally:
            dashboard.stop()

        print(f"\n✅ Optimization completed")
        print(f"📊 Total optimizations: {total_tasks}  ({len(available_csvs)} timeframes × {len(test_strategies)} strategies)")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped (cached): {skipped_count}")
        print(f"📁 Results saved to: {output_dir}")

    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print("\n\n⚠️  Interrupted by user")
        print(f"💡 To resume optimization, run:")
        print(f"   python run_bt_BTC.py --scheduler --workers {max_workers} --trials {n_trials}")
        input("\nPress Enter to close...")
        return 130
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("🎉 Backtesting workflow completed successfully!")
    return 0

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Nexus Backtesting System - BTC Only")
    parser.add_argument('--optimizer', choices=['hyperopt', 'optuna', 'backtesting'], default='hyperopt', help='Choose optimizer: hyperopt or optuna (default: hyperopt)')
    parser.add_argument('--trials', type=int, default=300, help='Number of optimization trials (default: 300)')
    parser.add_argument('--scheduler', action='store_true', help='Run scheduler (reoptimization cycle) instead of full pipeline')
    parser.add_argument('--strategy', type=str, default=None, help='Specify a single strategy to run (by name, e.g. multi_confirmation_40x)')
    parser.add_argument('--force-rerun', action='store_true', help='Force reoptimization even if already completed')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all data files, ignoring staleness checks')
    parser.add_argument('--workers', type=int, default=25, help='Number of worker threads (default: 25)')
    parser.add_argument('mode', nargs='?', default=None, help='Mode: test or None for full BTC run')
    args = parser.parse_args()

    if args.mode == 'test':
        # Use the pipeline's own single-symbol test runner pointed at BTC
        from src.pipeline.pipeline_BT_unified_async import test_single_symbol
        test_single_symbol(strategy_name=args.strategy, optimizer=args.optimizer, trials=args.trials)
    else:
        # Store CLI args globally so main() can access them
        import types
        global cli_args
        cli_args = args
        # mirror force-rerun → force_refresh flag so main() picks it up
        if not hasattr(cli_args, 'force_refresh'):
            cli_args.force_refresh = args.force_rerun

        exit_code = asyncio.run(main())
        sys.exit(exit_code)
