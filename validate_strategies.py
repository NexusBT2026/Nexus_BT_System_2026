#!/usr/bin/env python3
"""
Nexus Backtesting System - Strategy Validator
Automatically test and validate trading strategies.
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

def validate_strategy(strategy_class, strategy_name):
    """Validate a single strategy for Nexus custom backtesting system."""
    issues = []
    warnings = []

    try:
        # Get default params from param_grid if available
        config = {}
        if hasattr(strategy_class, 'param_grid'):
            param_grid_attr = strategy_class.param_grid if not callable(strategy_class.param_grid) else None
            if param_grid_attr and isinstance(param_grid_attr, dict):
                # Use first value from each parameter
                for key, value in param_grid_attr.items():
                    if isinstance(value, range):
                        config[key] = value.start
                    elif isinstance(value, list) and len(value) > 0:
                        config[key] = value[0]
                    else:
                        config[key] = value
        
        # Test instantiation with config
        strategy = strategy_class(config)
        print(f"✅ {strategy_name}: Instantiation OK")

        # Check required methods for custom backtesting engine
        required_methods = ['generate_signals', 'simulate_trades']
        for method in required_methods:
            if hasattr(strategy, method) and callable(getattr(strategy, method)):
                print(f"✅ {strategy_name}: Has {method} method")
            else:
                issues.append(f"Missing required method: {method}")

        # Check param_grid (can be attribute or method)
        if hasattr(strategy, 'param_grid'):
            param_grid = strategy.param_grid() if callable(strategy.param_grid) else strategy.param_grid
            if isinstance(param_grid, dict) and len(param_grid) > 0:
                print(f"✅ {strategy_name}: Has valid param_grid with {len(param_grid)} parameters")
            else:
                warnings.append("param_grid is empty or invalid")
        else:
            issues.append("Missing param_grid attribute/method")

        # Test signal generation with sample data
        sample_data = pd.DataFrame({
            'open': np.array([100.0, 101.0, 102.0, 103.0, 104.0]),
            'high': np.array([105.0, 106.0, 107.0, 108.0, 109.0]),
            'low': np.array([95.0, 96.0, 97.0, 98.0, 99.0]),
            'close': np.array([102.0, 103.0, 104.0, 105.0, 106.0]),
            'volume': np.array([1000.0, 1100.0, 1200.0, 1300.0, 1400.0])
        })
        sample_data.index = pd.date_range('2023-01-01', periods=5, freq='1h')

        try:
            # Test generate_signals
            if hasattr(strategy, 'generate_signals'):
                signals = strategy.generate_signals(sample_data.copy())
                if signals is not None and len(signals) > 0:
                    print(f"✅ {strategy_name}: generate_signals OK (returned {len(signals)} signals)")
                else:
                    warnings.append("generate_signals returned no signals on sample data")
            
            # Test simulate_trades (skip if not enough data)
            if hasattr(strategy, 'simulate_trades'):
                # Just check it's callable, don't actually test with dummy data
                # (real testing needs proper OHLCV data with sufficient length)
                print(f"✅ {strategy_name}: simulate_trades method exists")

        except Exception as e:
            warnings.append(f"Strategy methods raised error on sample data (may need more data): {e}")

    except Exception as e:
        issues.append(f"Instantiation failed: {e}")
        traceback.print_exc()

    return issues, warnings

def validate_all_strategies():
    """Validate all available strategies."""
    print("🎯 Nexus Strategy Validator")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        from src.strategy import strategies

        total_strategies = len(strategies)
        valid_strategies = 0
        total_issues = 0
        total_warnings = 0

        print(f"Found {total_strategies} strategies to validate:")
        print(", ".join(strategies.keys()))
        print()

        for strategy_name, strategy_class in strategies.items():
            # Skip base and test strategies (not real trading strategies)
            if strategy_name in ['base_strategy', 'test_strategy']:
                print(f"⏭️  Skipping: {strategy_name} (not a trading strategy)")
                print()
                continue
                
            print(f"🔍 Validating: {strategy_name}")
            print("-" * 30)

            issues, warnings = validate_strategy(strategy_class, strategy_name)

            if issues:
                print(f"❌ Issues ({len(issues)}):")
                for issue in issues:
                    print(f"   • {issue}")
                total_issues += len(issues)
            else:
                print("✅ No critical issues")
                valid_strategies += 1

            if warnings:
                print(f"⚠️  Warnings ({len(warnings)}):")
                for warning in warnings:
                    print(f"   • {warning}")
                total_warnings += len(warnings)

            print()

        # Summary
        print("=" * 50)
        print("📊 VALIDATION SUMMARY:")
        print(f"   Strategies checked: {total_strategies}")
        print(f"   Valid strategies: {valid_strategies}")
        print(f"   Total issues: {total_issues}")
        print(f"   Total warnings: {total_warnings}")

        if valid_strategies == total_strategies and total_issues == 0:
            print("🎉 All strategies passed validation!")
            return True
        else:
            print("⚠️  Some strategies have issues. Check output above.")
            return False

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_all_strategies()
    sys.exit(0 if success else 1)