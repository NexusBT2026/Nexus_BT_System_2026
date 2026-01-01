#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nexus Backtesting System - Setup and Validation Script
Run this script to set up and validate your environment.
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path

# Configure UTF-8 encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")

def check_python_version():
    """Check Python version compatibility."""
    print(f"🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_dependencies():
    """Check if all required packages are installed."""
    print(f"📦 Checking dependencies...")

    required_packages = [
        'pandas', 'numpy', 'ccxt', 'hyperopt', 'optuna',
        'plotly', 'matplotlib', 'torch', 'gymnasium'
    ]

    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    print(f"✅ All dependencies installed")
    return True

def check_config():
    """Check if config.json exists and is valid."""
    print(f"⚙️  Checking configuration...")

    config_path = Path("config.json")
    if not config_path.exists():
        print(f"❌ config.json not found")
        print("Copy config.json.example to config.json and add your API keys")
        return False

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Check for placeholder values
        placeholders = []
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("YOUR_"):
                placeholders.append(key)

        if placeholders:
            print(f"⚠️  Found placeholder API keys: {', '.join(placeholders)}")
            print("Add your real API keys to config.json")
        else:
            print(f"✅ Configuration file looks complete")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False

def check_directories():
    """Create necessary directories."""
    print(f"📁 Checking directories...")

    dirs = ['data', 'results', 'logs', 'src/strategy']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ {dir_name}/")

    return True

def test_imports():
    """Test core imports."""
    print(f"🔧 Testing core imports...")

    imports = [
        ('src.strategy', 'strategies'),
        ('src.pipeline.pipeline_BT_unified_async', 'run_strategy_optimization_async'),
        ('src.backtest.engine', 'BacktestEngine'),
        ('src.data.binance_ohlcv_source', 'BinanceOHLCVDataSource'),
    ]

    for module, attr in imports:
        try:
            mod = importlib.import_module(module)
            getattr(mod, attr)
            print(f"✅ {module}.{attr}")
        except Exception as e:
            print(f"❌ {module}.{attr}: {e}")
            return False

    return True

def test_strategy_discovery():
    """Test automatic strategy discovery."""
    print(f"🎯 Testing strategy discovery...")

    try:
        from src.strategy import strategies
        count = len(strategies)
        print(f"✅ Found {count} strategies: {list(strategies.keys())}")
        return True
    except Exception as e:
        print(f"❌ Strategy discovery failed: {e}")
        return False

def create_example_config():
    """Create example config if it doesn't exist."""
    example_config = Path("config.json.example")
    if not example_config.exists():
        print("📝 Creating config.json.example...")

        example = {
            "comments": "Example config - copy to config.json and add your API keys",
            "secret_key": "YOUR_HYPERLIQUID_SECRET_KEY",
            "account_address": "YOUR_HYPERLIQUID_ACCOUNT_ADDRESS",
            "phemex_api_key": "YOUR_PHEMEX_API_KEY",
            "phemex_api_secret": "YOUR_PHEMEX_API_SECRET",
            "coinbase_api_key": "YOUR_COINBASE_API_KEY",
            "coinbase_api_key_secret": "YOUR_COINBASE_API_KEY_SECRET",
            "coinbase_api_passphrase": "YOUR_COINBASE_PASSPHRASE",
            "binance_api_key": "YOUR_BINANCE_API_KEY",
            "binance_api_secret": "YOUR_BINANCE_API_SECRET",
            "kucoin_api_key": "YOUR_KUCOIN_API_KEY",
            "kucoin_api_secret": "YOUR_KUCOIN_API_SECRET",
            "kucoin_api_passphrase": "YOUR_KUCOIN_PASSPHRASE",
            "use_hyperliquid": False,
            "use_phemex": True,
            "use_coinbase": False,
            "use_binance": False,
            "use_kucoin": False,
            "numexpr_max_threads": None
        }

        with open(example_config, 'w') as f:
            json.dump(example, f, indent=2)

        print("✅ Created config.json.example")
        print("Copy this to config.json and add your real API keys")

def main():
    """Main setup and validation function."""
    print_header("NEXUS BACKTESTING SYSTEM - SETUP & VALIDATION")

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Configuration", check_config),
        ("Directories", check_directories),
        ("Core Imports", test_imports),
        ("Strategy Discovery", test_strategy_discovery),
    ]

    results = []
    for name, check_func in checks:
        print_header(f"CHECKING: {name}")
        result = check_func()
        results.append((name, result))

    # Create example config if needed
    create_example_config()

    # Summary
    print_header("SETUP SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"✅ PASS" if result else f"❌ FAIL"
        print(f"{status} {name}")

    print(f"\n📊 Results: {passed}/{total} checks passed")

    if passed == total:
        print(f"\n🎉 System is ready! Run 'python run_bt.py --test' to get started.")
    else:
        print(f"\n⚠️  Some checks failed. Please fix the issues above before running the system.")
        sys.exit(1)

if __name__ == "__main__":
    main()
    