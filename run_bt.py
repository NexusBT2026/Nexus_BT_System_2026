#!/usr/bin/env python3
"""
Nexus Backtesting System - Quick Start Script
Run this script to perform a complete backtesting workflow
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pipeline.pipeline_BT_unified_async import (
    discover_symbols_async,
    fetch_ohlcv_data_async,
    run_strategy_optimization,  # Use the sync version that actually works
    NUMEXPR_MAX_THREADS
)
from src.backtest.dashboard_monitor import show_initialization_screen
import logging
import sys
import os
from contextlib import contextmanager

# Suppress logs IMMEDIATELY before any imports
logging.basicConfig(level=logging.ERROR, format='%(message)s')

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
        # Professional initialization
        show_initialization_screen('symbol_discovery', {
            'Exchanges': '10 (Binance, Hyperliquid, KuCoin, etc.)',
            'Process': 'Async symbol discovery with caching',
            'Workers': f'{NUMEXPR_MAX_THREADS} threads'
        })
        
        # Step 1: Discover symbols with progress indicator
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn
            
            console = Console()
            
            # Show progress with updates
            console.print("[cyan]⏳ Scanning exchanges for tradable symbols...[/cyan]\n")
            
            # Run discovery with silence but show results
            with silent_operation():
                symbols = await discover_symbols_async()
            
            # Show what was found per exchange
            total_symbols = 0
            console.print("[green]Symbol Discovery Complete:[/green]")
            
            exchange_display = {
                'hyperliquid': 'Hyperliquid',
                'phemex': 'Phemex',
                'coinbase_unmatched': 'Coinbase',
                'unmatched_binance': 'Binance',
                'unmatched_kucoin': 'KuCoin',
                'unmatched_bybit': 'Bybit',
                'unmatched_okx': 'OKX',
                'unmatched_bitget': 'Bitget',
                'unmatched_gateio': 'Gate.io',
                'unmatched_mexc': 'MEXC'
            }
            
            for key, display_name in exchange_display.items():
                if key in symbols and symbols[key]:
                    count = len(symbols[key]) if isinstance(symbols[key], list) else 0
                    if count > 0:
                        total_symbols += count
                        console.print(f"  [dim]•[/dim] [cyan]{display_name}:[/cyan] {count} symbols")
            
            console.print(f"\n[green]✓[/green] Total: [bold]{total_symbols}[/bold] trading symbols discovered\n")
            
        except ImportError:
            # Fallback if rich not available
            print("⏳ Scanning exchanges for tradable symbols...")
            with silent_operation():
                symbols = await discover_symbols_async()
            total_symbols = sum(len(v) if isinstance(v, list) else 0 for v in symbols.values())
            print(f"✅ Discovered {total_symbols} trading symbols\n")

        # Step 2: Fetch data
        timeframes = ['5m'] # , '15m', '30m', '1h', '2h', '4h', '12h', '1d'
        show_initialization_screen('data_fetch', {
            'Symbols': total_symbols,
            'Timeframes': ', '.join(timeframes),
            'Data Source': 'Multi-exchange (Hyperliquid primary)',
            'Caching': 'CSV format with staleness detection',
            'Force Refresh': '✓ YES' if force_refresh else '✗ Use cache'
        })
        
        # Fetch with progress indicator
        try:
            from rich.console import Console
            console = Console()
            
            console.print("[cyan]⏳ Fetching historical OHLCV data from exchanges...[/cyan]")
            console.print(f"[dim]   Timeframes: {', '.join(timeframes)}[/dim]\n")
            
            # Run with complete silence
            with silent_operation():
                await fetch_ohlcv_data_async(symbols, timeframes=timeframes)
            
            console.print("[green]✓[/green] Historical data fetched and cached\n")
        except ImportError:
            print("⏳ Fetching historical OHLCV data...")
            with silent_operation():
                await fetch_ohlcv_data_async(symbols, timeframes=timeframes)
            print("✅ Historical data fetched and cached\n")

        # Step 3: Run optimization with dashboard
        from src.strategy import strategies
        
        # For testing, select a subset of strategies (both with and without hold versions if available)
        test_strategies = []
        available_strategies = list(strategies.keys())
        
        # Select some common strategies for testing
        preferred_test_strategies = ['rsi_divergence', 'rsi_divergence_with_hold', 'macd_ema_atr', 'macd_ema_atr_with_hold']
        for strat in preferred_test_strategies:
            if strat in available_strategies:
                test_strategies.append(strat)
        
        # If no preferred strategies found, use first 4 available
        if not test_strategies:
            test_strategies = available_strategies[:4]
        
        # Calculate total tasks for dashboard
        import glob
        csv_files = glob.glob(os.path.join('data', '*_candle_data.csv'))
        total_tasks = len(csv_files) * len(test_strategies)
        
        show_initialization_screen('optimization_start', {
            'Strategies': ', '.join(test_strategies),
            'Data Files': len(csv_files),
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
        
        # NOTE: Dashboard is now integrated into run_strategy_optimization
        # It will automatically display during execution
        results = run_strategy_optimization(
            symbols,
            target_strategies=test_strategies,
            max_workers=max_workers,
            n_trials=n_trials,
            optimizer=optimizer,
            force_rerun=not scheduler_mode  # Scheduler = resume mode
        )
        
        print("\n✅ Optimization completed")
        print(f"📊 Total optimizations: {results.get('total_optimizations', 0)}")
        print(f"✅ Successful: {results.get('successful_optimizations', 0)}")
        print(f"📁 Results saved to: {results.get('output_dir', 'results/')}")

    except KeyboardInterrupt:
        # User pressed Ctrl+C during async operations (symbol discovery, data fetch)
        print("\n\n⚠️  Interrupted by user")
        print(f"💡 To resume optimization, run:")
        print(f"   python run_bt.py --scheduler --workers {max_workers} --trials {n_trials}")
        input("\nPress Enter to close...")
        return 130
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("🎉 Backtesting workflow completed successfully!")
    return 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Nexus Backtesting System')
    parser.add_argument('--workers', type=int, default=25, help='Number of workers')
    parser.add_argument('--trials', type=int, default=300, help='Number of trials')
    parser.add_argument('--optimizer', choices=['hyperopt', 'optuna', 'backtesting'], default='hyperopt')
    parser.add_argument('--scheduler', action='store_true', help='Resume mode')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh data')
    
    args = parser.parse_args()
    
    # Store CLI args globally so main() can access them
    import types
    global cli_args
    cli_args = args
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)