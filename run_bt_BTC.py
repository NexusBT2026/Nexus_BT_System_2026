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
    NUMEXPR_MAX_THREADS
)
from src.backtest.dashboard_monitor import show_initialization_screen
import logging
import sys
import os
from contextlib import contextmanager

# Suppress logs IMMEDIATELY before any imports
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# ── BTC config ────────────────────────────────────────────────────────────────
TARGET_SYMBOL    = 'BTC'
TARGET_TIMEFRAME = '15m'   # change to match your CSV e.g. '15m'
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

        # Step 1: locate BTC CSV
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        csv_file = os.path.join(data_dir, f'{TARGET_SYMBOL}_{TARGET_TIMEFRAME}_candle_data.csv')

        try:
            from rich.console import Console
            console = Console()
            console.print(f"[cyan]🔶 BTC single-symbol mode[/cyan]\n")
            console.print(f"[dim]   Data file: {os.path.basename(csv_file)}[/dim]\n")
        except ImportError:
            print(f"🔶 BTC single-symbol mode")
            print(f"   Data file: {os.path.basename(csv_file)}")

        if not os.path.exists(csv_file):
            print(f"❌ No data file found: {csv_file}")
            print(f"   Run run_bt.py first to fetch data, or check TARGET_TIMEFRAME in this script.")
            return 1

        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} candles for {TARGET_SYMBOL}")

        if len(df) < 200:
            print(f"Warning: only {len(df)} candles (minimum 200 required)")
            return 1

        # Step 2: pick strategies
        from src.strategy import strategies

        test_strategies = []
        available_strategies = list(strategies.keys())

        # Select strategies to run
        preferred_test_strategies = ['multi_confirmation_40x'] #, 'rsi_divergence', 'rsi_divergence_with_hold', 'macd_ema_atr', 'macd_ema_atr_with_hold'
        for strat in preferred_test_strategies:
            if strat in available_strategies:
                test_strategies.append(strat)

        # If no preferred strategies found, use first 4 available
        if not test_strategies:
            test_strategies = available_strategies[:4]

        total_tasks = len(test_strategies)

        show_initialization_screen('optimization_start', {
            'Symbol': TARGET_SYMBOL,
            'Timeframe': TARGET_TIMEFRAME,
            'Candles': len(df),
            'Strategies': ', '.join(test_strategies),
            'Total Optimizations': total_tasks,
            'Workers': max_workers,
            'Optimizer': f'{optimizer.capitalize()} (Bayesian)',
            'Trials per Strategy': n_trials
        })

        # Suppress pipeline logger to keep dashboard clean (no JSON logs scrolling)
        # But allow ERROR level to show critical issues below dashboard
        pipeline_logger = logging.getLogger('pipeline_BT_source')
        pipeline_logger.setLevel(logging.ERROR)  # Show errors below dashboard
        # Remove JSON handlers, add simple error handler
        pipeline_logger.handlers = []
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('\n[ERROR] %(message)s\n'))
        pipeline_logger.addHandler(error_handler)

        # Step 3: run optimize_strategy_task per strategy — same as pipeline's test_single_symbol
        output_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(output_dir, exist_ok=True)

        successful = 0
        failed = 0

        for strategy_name in test_strategies:
            strategy_class = strategies.get(strategy_name)
            if strategy_class is None:
                print(f"⚠️  Strategy not found: {strategy_name}")
                continue

            result_file = os.path.join(output_dir, TARGET_SYMBOL, TARGET_TIMEFRAME,
                                       f'results_{strategy_name}_strategy.json')
            if os.path.exists(result_file) and not force_refresh:
                try:
                    import json
                    with open(result_file, 'r') as f:
                        existing = json.load(f)
                    if existing.get('success', False):
                        print(f"SKIPPING (already completed): {TARGET_SYMBOL} {TARGET_TIMEFRAME} {strategy_name}")
                        continue
                except Exception:
                    pass

            task = {
                'symbol':            TARGET_SYMBOL,
                'timeframe':         TARGET_TIMEFRAME,
                'strategy_name':     strategy_name,
                'strategy_class':    strategy_class,
                'strategy_category': 'custom',
                'reopt_days':        7,
                'data':              df.copy(),
                'csv_file':          csv_file,
                'optimizer':         optimizer,
                'n_trials':          n_trials,
            }

            print(f"\n{'='*60}")
            print(f"Running: {strategy_name} | {TARGET_SYMBOL} {TARGET_TIMEFRAME} | {optimizer} {n_trials} trials")
            print(f"{'='*60}")

            result = optimize_strategy_task(task)

            if result and result.get('success'):
                save_individual_result(result, output_dir)
                successful += 1
                print(f"✅ Optimization successful!")
                print(f"   Return:      {result.get('return_pct', 0):.2f}%")
                print(f"   Win Rate:    {result.get('win_rate', 0):.1f}%")
                print(f"   Trades:      {result.get('trades', 0)}")
                print(f"   Sharpe:      {result.get('sharpe', 0):.3f}")
                print(f"   Max DD:      {result.get('max_drawdown', 0):.2f}")
                print(f"   Score:       {result.get('composite_score', 0):.3f}")
                print(f"   Best params: {result.get('best_params', {})}")
            else:
                failed += 1
                print(f"❌ Optimization failed: {result.get('error', 'unknown') if result else 'no result'}")

        print(f"\n✅ Optimization completed")
        print(f"📊 Total optimizations: {total_tasks}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
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
