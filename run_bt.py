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

async def main():
    print("🚀 Starting Nexus Backtesting System")
    print(f"⚙️  NUMEXPR_MAX_THREADS: {NUMEXPR_MAX_THREADS}")
    print("=" * 50)

    try:
        # Step 1: Discover symbols
        print("📊 Step 1: Discovering trading symbols...")
        symbols = await discover_symbols_async()
        print(f"✅ Found symbols across {len(symbols)} categories")

        # Step 2: Fetch data
        print("📥 Step 2: Fetching OHLCV data...")
        timeframes = ['5m'] # , '15m', '30m', '1h', '2h', '4h', '12h', '1d'
        await fetch_ohlcv_data_async(symbols, timeframes=timeframes)
        print("✅ Data fetching completed")

        # Step 3: Run optimization
        print("🎯 Step 3: Running strategy optimization...")
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
        
        print(f"Testing with strategies: {test_strategies}")
        results = run_strategy_optimization(
            symbols,
            target_strategies=test_strategies,
            max_workers=25,
            n_trials=100  # Reduced for faster testing
        )
        print("✅ Optimization completed")
        print(f"📊 Results: {results}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("🎉 Backtesting workflow completed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)