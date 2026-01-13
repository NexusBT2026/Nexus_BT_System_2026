# Nexus Backtesting System

A comprehensive, modular backtesting framework inspired by Freqtrade, featuring multi-exchange support, async data fetching, and advanced strategy optimization.

## 🚀 Features

<img src="Nexus.png" alt="Nexus Logo" width="200" align="right" style="margin-left: 20px;"/>

### Performance Optimized
- **Async/await data fetching** with concurrent processing
- **Multi-threaded optimization** with configurable workers
- **Real-time dashboard monitoring** with live progress tracking and system metrics
- **Smart data freshness checking** to avoid unnecessary fetches
- **GPU-accelerated computations** where available

### Multi-Exchange Support (10 Exchanges Integrated)
- **Hyperliquid** - Perpetual futures (~200 symbols) - PRIMARY DATA SOURCE
- **Phemex** - Perpetual futures with unique contract formats
- **Binance** - Spot trading (USDT pairs)
- **Coinbase** - Spot trading (USDC pairs)
- **KuCoin** - Perpetual swap futures (USDT pairs)
- **Bybit** - Perpetual swaps (USDT pairs)
- **OKX** - Perpetual swaps (USDT pairs)
- **Bitget** - Perpetual swaps (USDT pairs)
- **Gate.io** - Perpetual swaps (USDT pairs)
- **MEXC** - Perpetual swaps (USDT pairs)

**📊 Total Coverage: 1,140+ unique trading symbols**
- Hyperliquid provides ~90% of symbol coverage (comprehensive market)
- Recently added: Bybit, OKX, Bitget, Gate.io, MEXC for expanded coverage
- Smart symbol intersection to avoid duplicate data fetching
- Automatic staleness detection and refresh

### Strategy Optimization
- **6 production-ready strategies** (RSI Divergence, MACD+EMA+ATR, Base Strategy - each with/without hold variants)
- **17 strategy categories** with automatic classification (divergence, scalping, breakout, mean reversion, etc.)
- **Exchange-specific preferences** - strategies matched to optimal exchanges
- **Three Backtest Engines**: 
  - **Custom Engine** (`run_backtest`) - Original high-performance engine with async processing
  - **Hyperopt/Optuna Integration** - Bayesian optimization for parameter tuning
  - **backtesting.py Library** (`run_backtest_library`) - External library validation with professional metrics
- **Comprehensive metrics**: Sharpe, Sortino, Calmar, Omega, Information Ratio, Tail Ratio
- **Monte Carlo validation** and statistical testing

### Advanced Analysis
- **Real-time optimization dashboard** - Live progress tracking with profitability metrics
- **Interactive dashboards** with Plotly charts
- **Professional tear sheets** with institutional-grade metrics
- **3D parameter surface plots** for optimization visualization
- **Correlation analysis** and portfolio optimization
- **Kelly Criterion** position sizing
- **Walk-forward validation** and overfitting detection

## 📋 Prerequisites

- **Python 3.8+**
- **Conda** (recommended) or **pip** package manager
- **Git** (optional, for cloning)

## 🛠️ Quick Setup

### 1. Clone & Install Dependencies

```bash
git clone <repository-url>
cd nexus_bt_system

# Install dependencies
pip install -r requirements.txt

# Or with conda (recommended)
conda create -n nexus python=3.12
conda activate nexus
pip install -r requirements.txt
```

### 2. Run Setup Script

```bash
# Validate your environment
python setup.py

# If using conda
conda run -n nexus python setup.py
```

### 3. Configure API Keys

Edit `config.json` with your exchange API credentials:

```json
{
  "secret_key": "YOUR_HYPERLIQUID_SECRET_KEY",
  "account_address": "YOUR_HYPERLIQUID_ACCOUNT_ADDRESS",
  "phemex_api_key": "YOUR_PHEMEX_API_KEY",
  "phemex_api_secret": "YOUR_PHEMEX_API_SECRET",
  "coinbase_api_key": "YOUR_COINBASE_API_KEY",
  "coinbase_api_key_secret": "YOUR_COINBASE_API_SECRET",
  "coinbase_api_passphrase": "YOUR_COINBASE_PASSPHRASE",
  "binance_api_key": "YOUR_BINANCE_API_KEY",
  "binance_api_secret": "YOUR_BINANCE_API_SECRET",
  "kucoin_api_key": "YOUR_KUCOIN_API_KEY",
  "kucoin_api_secret": "YOUR_KUCOIN_API_SECRET",
  "kucoin_api_passphrase": "YOUR_KUCOIN_PASSPHRASE",
  "bybit_api_key": "YOUR_BYBIT_API_KEY",
  "bybit_api_secret": "YOUR_BYBIT_API_SECRET",
  "okx_api_key": "YOUR_OKX_API_KEY",
  "okx_api_secret": "YOUR_OKX_API_SECRET",
  "okx_api_passphrase": "YOUR_OKX_API_PASSPHRASE",
  "bitget_api_key": "YOUR_BITGET_API_KEY",
  "bitget_api_secret": "YOUR_BITGET_API_SECRET",
  "gateio_api_key": "YOUR_GATEIO_API_KEY",
  "gateio_api_secret": "YOUR_GATEIO_API_SECRET",
  "mexc_api_key": "YOUR_MEXC_API_KEY",
  "mexc_api_secret": "YOUR_MEXC_API_SECRET",
  "use_hyperliquid": true,
  "use_phemex": true,
  "use_coinbase": false,
  "use_binance": true,
  "use_kucoin": true,
  "use_bybit": true,
  "use_okx": true,
  "use_bitget": true,
  "use_gateio": true,
  "use_mexc": true,
  "numexpr_max_threads": null
}
```

**Security Note:** The config file contains placeholder values. Replace with your actual API keys for live data fetching. The `config.json` file is already in `.gitignore` to prevent accidental commits.

### 3. Run Your First Backtest

```bash
# Using conda (recommended for Windows emoji support)
conda activate nexus
python run_bt.py

# Or with pip
python run_bt.py
```

**Note for Windows Users**: For proper emoji display in output, use Windows Terminal or CMD instead of PowerShell, or run with:
```bash
conda run -n nexus python setup.py
```

## �️ Utility Tools

Nexus includes several utility scripts to help with development and maintenance:

### Setup & Validation

```bash
# Automated setup and environment validation
python setup.py

# System health monitoring
python health_check.py

# Strategy validation and testing
python validate_strategies.py
```

### Key Tools

- **`setup.py`** - Complete environment setup and validation
- **`health_check.py`** - System resource monitoring and diagnostics
- **`validate_strategies.py`** - Automated strategy testing and validation
- **`run_bt.py`** - Main backtesting interface

## 📖 Documentation

- **[MANUAL.md](MANUAL.md)** - Complete user guide for adding strategies and system usage
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines and contribution workflow
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

## 🎯 Adding Strategies

Nexus features **automatic strategy discovery** - just drop a strategy file in `src/strategy/` and it works immediately!

### Quick Strategy Template

```python
# src/strategy/my_strategy.py
from src.strategy.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    strategy_name = "my_strategy"
    timeframe = "1h"

    buy_params = {
        'rsi_period': {'type': 'int', 'min': 10, 'max': 30},
        'rsi_overbought': {'type': 'int', 'min': 65, 'max': 80},
    }

    def populate_indicators(self, dataframe, metadata):
        dataframe['rsi'] = self.ta.RSI(dataframe, timeperiod=self.buy_params['rsi_period'])
        return dataframe

    def populate_buy_signal(self, dataframe, metadata):
        dataframe.loc[:, 'buy'] = dataframe['rsi'] < self.buy_params['rsi_overbought']
        return dataframe

    def populate_sell_signal(self, dataframe, metadata):
        dataframe.loc[:, 'sell'] = dataframe['rsi'] > 70
        return dataframe
```

**That's it!** The system automatically discovers, categorizes, and optimizes your strategy.

See [MANUAL.md](MANUAL.md) for detailed instructions.
│   │   └── symbol_intersection.py
│   ├── exchange/
│   │   ├── logging_utils.py
│   │   └── retry.py
│   ├── optimizers/
│   │   └── optimizer.py
│   └── utils/
│       ├── analyze_results.py
│       ├── bot_integration.py
│       ├── check_status.py
│       ├── generate_configs.py
│       └── live_tracker.py
└── __pycache__/                 # Python bytecode (auto-generated)
```

## 🎯 Usage Guide

### Command Line Options

The Nexus system provides two main CLI entry points with different capabilities:

#### Main Pipeline (`src/pipeline/pipeline_BT_unified_async.py`)

```bash
python src/pipeline/pipeline_BT_unified_async.py [mode] [options]
```

**Modes:**
- `test` - Single strategy testing on 0G symbol with detailed output
- (no mode) - Full pipeline: data fetching + optimization across all strategies/symbols

**Options:**
- `--optimizer {hyperopt,optuna,backtesting}` - Optimization algorithm (default: hyperopt)
- `--trials TRIALS` - Number of optimization trials (default: 500)
- `--scheduler` - Run reoptimization cycle instead of full pipeline
- `--strategy STRATEGY` - Optimize only specified strategy (e.g., `rsi_divergence`)
- `--force-rerun` - Force reoptimization even if already completed
- `--force-refresh` - Force refresh all data files, ignoring staleness checks
- `--test-async` - Test async fetch with minimal data
- `--workers WORKERS` - Number of worker threads (default: 12)

#### Quick Start Script (`run_bt.py`)

```bash
python run_bt.py [options]
```

**Options:**
- `--optimizer {hyperopt,optuna,backtesting}` - Optimization algorithm (default: hyperopt)
- `--trials TRIALS` - Number of trials (default: 300)
- `--scheduler` - Resume mode for reoptimization
- `--force-refresh` - Force refresh data
- `--workers WORKERS` - Number of workers (default: 25)

### Common Workflows

#### 1. First-Time Setup & Full Pipeline
```bash
# Complete setup and first run (recommended)
conda activate nexus
python run_bt.py

# Full pipeline with custom settings
python src/pipeline/pipeline_BT_unified_async.py --trials 1000 --workers 16 --optimizer hyperopt
```

#### 2. Strategy Testing & Validation
```bash
# Test single strategy with hyperopt (fast, detailed output)
python src/pipeline/pipeline_BT_unified_async.py test --strategy rsi_divergence --optimizer hyperopt --trials 100

# Test with optuna optimizer
python src/pipeline/pipeline_BT_unified_async.py test --strategy macd_ema_atr --optimizer optuna --trials 200

# Test with backtesting.py library
python src/pipeline/pipeline_BT_unified_async.py test --strategy rsi_divergence --optimizer backtesting --trials 50
```

#### 3. Reoptimization & Updates
```bash
# Reoptimize existing strategies (scheduler mode)
python run_bt.py --scheduler --trials 200 --optimizer hyperopt

# Force refresh all data and re-run
python run_bt.py --force-refresh --trials 500

# Reoptimize specific strategy only
python src/pipeline/pipeline_BT_unified_async.py --scheduler --strategy rsi_divergence --force-rerun
```

#### 4. Performance Optimization
```bash
# High-performance run with many workers
python run_bt.py --workers 32 --trials 1000 --optimizer optuna

# Minimal test run for development
python src/pipeline/pipeline_BT_unified_async.py test --trials 10 --optimizer hyperopt
```

#### 5. Data Management
```bash
# Force refresh all market data
python run_bt.py --force-refresh

# Test async data fetching
python src/pipeline/pipeline_BT_unified_async.py --test-async
```

### Optimizer Comparison

| Optimizer | Best For | Speed | Exploration | Library |
|-----------|----------|-------|-------------|---------|
| **hyperopt** | General use, fast results | Fast | Good | Custom TPE |
| **optuna** | Advanced optimization, large parameter spaces | Medium | Excellent | Optuna framework |
| **backtesting** | External validation, professional metrics | Fast | Good | backtesting.py library |

**Quick Optimizer Guide:**
- **Start with hyperopt** for most use cases - fast and reliable
- **Use optuna** when you have many parameters or need advanced optimization
- **Use backtesting** for external validation and professional-grade metrics

### Results Analysis

After optimization completes, results are stored in the `results/` directory:

- `all_qualified_results.csv` - All optimization results
- `absolute_params.csv` - Top-performing parameter sets
- Individual strategy result files

#### View Results Dashboard
```bash
# Launch interactive dashboard
streamlit run src/backtest/BT_dashboard.py
```

#### Analyze Results Programmatically
```python
from src.utils.analyze_results import OptimizationAnalyzer

analyzer = OptimizationAnalyzer()
analyzer.load_results()
analyzer.generate_report()
```

## 🔧 Advanced Configuration

### Threading Configuration

The system automatically configures threading based on your CPU cores, but you can override in `config.json`:

```json
{
  "numexpr_max_threads": 16
}
```

### Exchange-Specific Settings

Enable/disable exchanges in `config.json`:

```json
{
  "use_hyperliquid": true,
  "use_phemex": true,
  "use_binance": true,
  "use_coinbase": false,
  "use_kucoin": true,
  "use_bybit": true,
  "use_okx": true,
  "use_bitget": true,
  "use_gateio": true,
  "use_mexc": true
}
```

### Custom Strategy Development

Create new strategies by extending `BaseStrategy`:

```python
from src.strategy.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        # Your parameters here
        self.param1 = config.get('param1', 10)
        self.param2 = config.get('param2', 20)

    def generate_signals(self, df):
        # Implement your trading logic
        signals = []
        # ... signal generation logic ...
        return signals

    @property
    def param_grid(self):
        # Define optimization parameters
        return {
            'param1': [5, 10, 15, 20],
            'param2': [10, 20, 30, 40]
        }
```

### Backtest Engine Options

Nexus supports three different backtest engines for comprehensive validation:

1. **Custom Engine** (`--optimizer hyperopt`): Original high-performance engine with async processing and custom metrics
2. **Optuna Engine** (`--optimizer optuna`): Bayesian optimization with advanced parameter search
3. **backtesting.py Engine** (`--optimizer backtesting`): External library validation with professional-grade metrics and visualizations

Each engine produces consistent results with standardized metrics for reliable strategy comparison.

## 📈 Performance Tips

- **Use SSD storage** for data caching
- **Configure NUMEXPR_MAX_THREADS** for your CPU cores
- **Enable GPU acceleration** with CuPy for large datasets
- **Use `force_refresh=False`** for incremental updates
- **Run async mode** for better performance on multi-core systems

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**No data fetched:**
- Check API keys in `config.json`
- Verify exchange is enabled
- Check internet connection

**Optimization not starting:**
- Ensure data exists in `data/` directory
- Check strategy name spelling
- Verify symbol availability

**Memory errors:**
- Reduce `--workers` count
- Use smaller `--trials` value
- Process fewer symbols at once

### Getting Help

- Check the `src/utils/check_status.py` for current optimization status
- Use `src/utils/analyze_results.py` for detailed result analysis
- Run `python run_bt.py --help` or `python src/pipeline/pipeline_BT_unified_async.py --help` for all available options

## 🐛 Troubleshooting

### Common CLI Issues

**"unrecognized arguments" error:**
```bash
# Wrong script - use the correct entry point
python run_bt.py --scheduler  # ✅ Correct
python src/pipeline/pipeline_BT_unified_async.py --scheduler  # ✅ Also correct

# Wrong arguments - check available options
python run_bt.py --help  # See valid options for run_bt.py
python src/pipeline/pipeline_BT_unified_async.py --help  # See valid options for pipeline
```

**"backtesting optimizer not available":**
```bash
# Ensure backtesting.py is installed
pip install backtesting
# Or reinstall requirements
pip install -r requirements.txt
```

**Optimization not starting:**
- Ensure data exists in `data/` directory (run full pipeline first)
- Check strategy name spelling in `--strategy` parameter
- Verify symbol availability on configured exchanges
- Use `--force-refresh` to update stale data

**Memory/Performance issues:**
- Reduce `--workers` count (try 4-8 instead of 32)
- Use smaller `--trials` value (start with 50-100)
- Process fewer strategies at once with `--strategy` parameter
- Close other applications to free up RAM

**Test mode shows "No result returned":**
- The `base_strategy` is not optimizable - use a real strategy like `--strategy rsi_divergence`
- Check that the strategy has proper `param_grid` defined
- Ensure strategy file is in `src/strategy/` directory

## 💼 Professional Services

Need custom strategy development or comprehensive backtesting analysis?

**[Hire me on Fiverr](https://www.fiverr.com/viwarshawski/develop-custom-python-cryptocurrency-trading-strategies-and-backtesting)** for professional quantitative analysis services.

### Service Tiers Available

**🥉 Basic Tier** - Single strategy analysis with comprehensive metrics
- Complete backtest with position sizing optimization
- Professional performance reports
- Strategy code and configuration files

**🥈 Standard Tier** - Multi-strategy comparison (up to 3 combinations)
- Side-by-side performance analysis
- Institutional-grade tear sheets with 50+ metrics
- Master summary with ranked results

**🥇 Premium Tier** - Unlimited strategy combinations
- Complete portfolio analysis
- Strategy quality assessment (Gold/Silver/Bronze grading)
- Advanced risk analytics with Monte Carlo simulations
- Trade timing analysis (optimal entry/exit hours)
- Walk-forward validation (anti-overfitting proof)

All tiers include professional HTML reports, interactive visualizations, and comprehensive documentation.

*Contact via Fiverr for detailed pricing and custom requirements.*

---

## 🤝 Contributing

This is a standalone BT system extracted from the larger Nexus trading platform. Contributions welcome:

- **New Strategies**: Add trading strategies following the `BaseStrategy` interface
- **Exchange Support**: Add new exchange integrations
- **Performance**: Optimize algorithms and data processing
- **Analysis**: Enhance result visualization and metrics

## 📄 License

Same as the original Nexus project.

## 🔮 Future Enhancements

- [ ] Web-based dashboard GUI
- [ ] Live trading integration
- [ ] Machine learning-based strategy generation
- [ ] Portfolio optimization features
- [ ] Advanced risk management modules
