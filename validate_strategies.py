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
    """Validate a single strategy."""
    issues = []
    warnings = []

    try:
        # Test instantiation
        strategy = strategy_class(config={})
        print(f"✅ {strategy_name}: Instantiation OK")

        # Check required attributes
        required_attrs = ['strategy_name', 'timeframe', 'minimal_roi', 'stoploss']
        for attr in required_attrs:
            if hasattr(strategy, attr):
                print(f"✅ {strategy_name}: Has {attr}")
            else:
                issues.append(f"Missing required attribute: {attr}")

        # Check buy/sell parameters
        if hasattr(strategy, 'buy_params') and hasattr(strategy, 'sell_params'):
            print(f"✅ {strategy_name}: Has buy/sell parameters")
        else:
            warnings.append("No buy_params/sell_params defined - using defaults")

        # Test indicator population with sample data
        sample_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000, 1100, 1200, 1300, 1400],
            'timestamp': pd.date_range('2023-01-01', periods=5, freq='1H')
        })

        try:
            # Test populate_indicators
            if hasattr(strategy, 'populate_indicators'):
                result = strategy.populate_indicators(sample_data.copy(), {})
                print(f"✅ {strategy_name}: populate_indicators OK")
            else:
                issues.append("Missing populate_indicators method")

            # Test populate_buy_signal
            if hasattr(strategy, 'populate_buy_signal'):
                result = strategy.populate_buy_signal(sample_data.copy(), {})
                if 'buy' in result.columns:
                    print(f"✅ {strategy_name}: populate_buy_signal OK")
                else:
                    issues.append("populate_buy_signal didn't create 'buy' column")
            else:
                issues.append("Missing populate_buy_signal method")

            # Test populate_sell_signal
            if hasattr(strategy, 'populate_sell_signal'):
                result = strategy.populate_sell_signal(sample_data.copy(), {})
                if 'sell' in result.columns:
                    print(f"✅ {strategy_name}: populate_sell_signal OK")
                else:
                    issues.append("populate_sell_signal didn't create 'sell' column")
            else:
                issues.append("Missing populate_sell_signal method")

        except Exception as e:
            issues.append(f"Error in signal population: {e}")

        # Check for common issues
        if hasattr(strategy, 'minimal_roi'):
            roi = strategy.minimal_roi
            if not isinstance(roi, dict):
                warnings.append("minimal_roi should be a dictionary")
            elif not all(isinstance(k, (int, str)) and isinstance(v, (int, float)) for k, v in roi.items()):
                warnings.append("minimal_roi values should be numbers")

        if hasattr(strategy, 'stoploss'):
            sl = strategy.stoploss
            if not isinstance(sl, (int, float)):
                warnings.append("stoploss should be a number")
            elif sl > 0:
                warnings.append("stoploss should be negative (percentage loss)")

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