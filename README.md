# Nexus Backtesting System

A comprehensive, modular backtesting framework inspired by Freqtrade, featuring multi-exchange support, async data fetching, and advanced strategy optimization.

## 🚀 Features

### Performance Optimized
- **Async/await data fetching** with concurrent processing
- **Multi-threaded optimization** with configurable workers
- **Smart data freshness checking** to avoid unnecessary fetches
- **GPU-accelerated computations** where available

### Multi-Exchange Support
- **Binance** - Spot trading (USDC pairs)
- **Coinbase** - Spot trading (USDC pairs)
- **Hyperliquid** - Perpetual futures
- **KuCoin** - Perpetual swap futures (USDT pairs)
- **Phemex** - Perpetual futures with unique contract formats

**Pending Integration (Phase 3):**
- **Bybit** - Perpetual swaps (+38 unique symbols)
- **OKX** - Perpetual swaps (+3 unique symbols)
- **Bitget** - Perpetual swaps (+15 unique symbols)
- **Gate.io** - Perpetual swaps (+46 unique symbols)
- **MEXC** - Perpetual swaps (+118 unique symbols)
- **Total**: +169 NEW unique symbols beyond current coverage

### Strategy Optimization
- **12+ built-in strategies** including RSI Divergence, MACD+EMA+ATR, EMA Channel Scalping, Adaptive RSI, Mean Reversion BB+RSI, Supply/Demand Spot, RL Trading Agent, SuperTrend, Markov Chain, EMA Ribbon Pullback, Breakout, and Statistical Arbitrage
- **Hyperopt/Optuna integration** for parameter optimization
- **Comprehensive metrics**: Sharpe, Sortino, Calmar, Omega, Information Ratio, Tail Ratio
- **Monte Carlo validation** and statistical testing

### Advanced Analysis
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
  "use_hyperliquid": false,
  "use_phemex": true,
  "use_coinbase": false,
  "use_binance": false,
  "use_kucoin": false,
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

```bash
python run_bt.py [options]

Options:
  --mode {full,test,scheduler}    Pipeline mode
  --strategy STRATEGY            Specific strategy to optimize
  --symbol SYMBOL                 Specific symbol to test
  --exchange EXCHANGE             Specific exchange to use
  --workers INT                   Number of worker threads
  --trials INT                    Number of optimization trials
  --force-refresh                 Force data refresh
  --async-mode                    Use async processing
  --scheduler                     Run reoptimization cycle
  --optimizer {hyperopt,optuna}   Optimization algorithm
```

### Common Workflows

#### 1. First-Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API keys in config.json
# Then run a test
python run_bt.py --mode test
```

#### 2. Full Backtesting Pipeline
```bash
# Fetch fresh data and run optimization
python run_bt.py --mode full --workers 8 --trials 100

# Use async mode for better performance
python run_bt.py --mode full --async-mode --workers 12
```

#### 3. Strategy-Specific Optimization
```bash
# Optimize only RSI Divergence strategy
python run_bt.py --mode full --strategy rsi_divergence --trials 200

# Test on specific symbol
python run_bt.py --mode test --strategy macd_ema_atr --symbol BTCUSDT
```

#### 4. Reoptimization Scheduler
```bash
# Run periodic reoptimization
python run_bt.py --scheduler --trials 50
```

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
  "binance_enabled": true,
  "coinbase_enabled": false,
  "hyperliquid_enabled": true,
  "kucoin_enabled": true,
  "phemex_enabled": true
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
- Run `python run_bt.py --help` for all available options

## 💼 Custom Development Services

Need a custom trading strategy or backtesting system tailored to your specific requirements?

**[Hire me on Fiverr](https://www.fiverr.com/viwarshawski/develop-custom-python-cryptocurrency-trading-strategies-and-backtesting)** for professional development services:

- Custom strategy development
- Multi-exchange integration
- Parameter optimization
- Live trading setup
- Consultation and support

3+ years of experience building production-grade trading systems. All communication via written messages for clear, precise requirements.

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
- [ ] **Additional exchanges (Phase 3 - In Progress)**
  - **Current**: 5 exchanges (Phemex, Hyperliquid, Coinbase, Binance, KuCoin)
  - **Pending Integration**: 5 new exchanges (Bybit, OKX, Bitget, Gate.io, MEXC)
  - **Impact**: +169 NEW unique perpetual swap symbols
  - **Total After Integration**: 1600+ existing + 169 new = 1769+ total symbols
  - **Status**: Symbol discovery complete, OHLCV modules ready, pipeline integration pending
- [ ] Machine learning-based strategy generation
- [ ] Portfolio optimization features
- [ ] Advanced risk management modules

## 📊 Client Delivery Features

### Professional Reporting
- **Institutional-grade tear sheets** with 40+ metrics and visualizations
- **Benchmark comparison** (strategy vs buy-and-hold performance)
- **Interactive HTML dashboards** with 6 comprehensive charts
- **Separate candlestick charts** showing price action with trade entry/exit markers
- **Advanced risk metrics** including Sharpe, Sortino, Calmar, VaR, CVaR
- **Clean, professional design** optimized for client presentations
- **Real-time browser preview** for immediate validation

### Quick Tear Sheet Generation
```python
# Generate professional tear sheet (basic example)
from src.reporting_demo import generate_basic_tearsheet
import pandas as pd

# Your strategy returns
returns = pd.Series([...], index=dates)

# Generate institutional report
generate_basic_tearsheet(returns, "strategy_report.html")
# Opens HTML with 40+ charts: equity curve, drawdown, monthly heatmap, risk metrics, etc.
```

**Note:** Full production implementation with automatic benchmark loading, batch processing, and advanced features available to clients.

### Automated Chart Generation
```python
# Generate dashboard and candlestick chart for client
from generate_professional_charts import create_professional_charts, create_candlestick_chart

# Dashboard with metrics
create_professional_charts(results, symbol, strategy_name, "dashboard.html")

# Candlestick with trade signals
create_candlestick_chart(results, symbol, strategy_name, ohlcv_data, "candlestick.html")
```

### Tear Sheet Components
**Professional tear sheets include:**
- Cumulative returns vs benchmark
- Drawdown analysis with underwater plot
- Monthly/yearly returns heatmap
- Rolling Sharpe and volatility
- Return distribution analysis
- Risk metrics table (Sharpe, Sortino, Calmar, VaR, CVaR)
- Win/loss statistics
- Best/worst periods analysis
- Trade duration analysis
- Correlation matrix

### Chart Components
**Dashboard includes:**
- Equity curve with capital growth
- Win/Loss trade distribution
- Cumulative P&L timeline
- Win/Loss ratio pie chart
- Drawdown analysis
- Performance metrics table

**Candlestick chart includes:**
- OHLCV candlestick display
- Green triangle markers for trade entries
- Red triangle markers for trade exits
- Interactive hover details
- Date range selector
