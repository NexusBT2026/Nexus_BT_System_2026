# Nexus Backtesting System - User Manual

## 📖 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Adding New Strategies](#adding-new-strategies)
- [How Automatic Discovery Works](#how-automatic-discovery-works)
- [Running Backtests](#running-backtests)
- [Configuration](#configuration)
- [Understanding Results](#understanding-results)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Nexus Backtesting System is a **dynamic, modular framework** that automatically discovers and integrates trading strategies. Unlike traditional systems that require manual registration, Nexus uses **intelligent discovery** to find strategies and adapt the entire pipeline automatically.

### Key Benefits

- **🔄 Zero Configuration**: Drop a strategy file and it works immediately
- **📈 Auto-Scaling**: System grows with your strategy library
- **🎯 Smart Categorization**: Strategies are automatically classified and scheduled
- **⚡ Performance Optimized**: Concurrent processing across all strategies

## 🚀 Quick Start

### 1. Basic Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run test backtest (downloads data + tests strategies)
python run_bt.py --test
```

### 2. Full Backtest

```bash
# Run complete optimization pipeline
python run_bt.py
```

## 🧠 Adding New Strategies

### Strategy File Structure

Create a new file in `src/strategy/` following this template:

```python
# src/strategy/my_awesome_strategy.py

import pandas as pd
import numpy as np
from src.strategy.base_strategy import BaseStrategy

class MyAwesomeStrategy(BaseStrategy):
    """
    My Awesome Trading Strategy

    Description of what this strategy does and its logic.
    """

    # Strategy metadata (used by the system)
    strategy_name = "my_awesome_strategy"
    timeframe = "1h"  # Preferred timeframe

    # Hyperopt parameter spaces
    buy_params = {
        'rsi_period': {'type': 'int', 'min': 10, 'max': 30, 'step': 2},
        'rsi_overbought': {'type': 'int', 'min': 65, 'max': 80, 'step': 5},
        'ema_short': {'type': 'int', 'min': 5, 'max': 20, 'step': 1},
        'ema_long': {'type': 'int', 'min': 20, 'max': 50, 'step': 5},
    }

    sell_params = {
        'rsi_oversold': {'type': 'int', 'min': 20, 'max': 35, 'step': 5},
        'stop_loss': {'type': 'float', 'min': 0.01, 'max': 0.10, 'step': 0.01},
    }

    def __init__(self, config=None):
        super().__init__(config)
        self.minimal_roi = {"0": 0.10, "60": 0.05, "120": 0.01, "240": 0}
        self.stoploss = -0.10
        self.timeframe = self.timeframe

    def populate_indicators(self, dataframe, metadata):
        """Add technical indicators to the dataframe."""

        # RSI
        dataframe['rsi'] = self.ta.RSI(dataframe, timeperiod=self.buy_params['rsi_period'])

        # EMAs
        dataframe['ema_short'] = self.ta.EMA(dataframe, timeperiod=self.buy_params['ema_short'])
        dataframe['ema_long'] = self.ta.EMA(dataframe, timeperiod=self.buy_params['ema_long'])

        # Additional indicators...
        dataframe['atr'] = self.ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_signal(self, dataframe, metadata):
        """Define buy conditions."""

        # Example conditions
        buy_condition_1 = (
            (dataframe['rsi'] < self.buy_params['rsi_overbought']) &
            (dataframe['ema_short'] > dataframe['ema_long']) &
            (dataframe['volume'] > dataframe['volume'].rolling(20).mean())
        )

        buy_condition_2 = (
            (dataframe['close'] < dataframe['bb_lower']) &
            (dataframe['rsi'] < 30)
        )

        dataframe.loc[:, 'buy'] = buy_condition_1 | buy_condition_2

        return dataframe

    def populate_sell_signal(self, dataframe, metadata):
        """Define sell conditions."""

        sell_condition_1 = (
            (dataframe['rsi'] > 70) |
            (dataframe['close'] > dataframe['bb_upper'])
        )

        sell_condition_2 = (
            (dataframe['close'] < dataframe['close'].shift(1) * (1 - self.sell_params['stop_loss']))
        )

        dataframe.loc[:, 'sell'] = sell_condition_1 | sell_condition_2

        return dataframe
```

### Strategy Naming Convention

- **File name**: `snake_case.py` (e.g., `my_strategy.py`)
- **Class name**: `CamelCaseStrategy` (e.g., `MyStrategy`)
- **Strategy name**: Matches file name without `.py`

### Special Strategy Types

#### With Hold Strategies

For strategies that can hold positions longer:

```python
# src/strategy/my_strategy_with_hold.py

class MyStrategyWithHold(MyAwesomeStrategy):
    """
    Same as MyAwesomeStrategy but with hold capability.
    """

    strategy_name = "my_strategy_with_hold"

    # Override ROI and stoploss for longer holds
    def __init__(self, config=None):
        super().__init__(config)
        self.minimal_roi = {"0": 0.05, "120": 0.10, "240": 0.05, "480": 0}
        self.stoploss = -0.05  # Tighter stop loss
```

#### Reinforcement Learning Strategies

```python
# src/strategy/rl_trading_agent.py

from src.strategy.rl_trading_agent import RLTradingAgent

class RLTradingAgent(RLTradingAgent):
    """Reinforcement learning based strategy."""

    strategy_name = "rl_trading_agent"

    # RL-specific parameters
    rl_params = {
        'learning_rate': {'type': 'float', 'min': 0.001, 'max': 0.1},
        'gamma': {'type': 'float', 'min': 0.8, 'max': 0.99},
        'epsilon_decay': {'type': 'float', 'min': 0.995, 'max': 0.999},
    }
```

## 🔍 How Automatic Discovery Works

### The Discovery Process

1. **File Scanning**: System scans `src/strategy/` directory
2. **Class Detection**: Finds all classes ending with `Strategy`
3. **Registration**: Maps strategy names to classes
4. **Categorization**: Assigns categories and schedules based on naming

### Dynamic Registry Generation

```python
# This happens automatically - no manual configuration needed!

STRATEGIES = {
    'my_awesome_strategy': {
        'class': MyAwesomeStrategy,
        'reopt_days': 30,  # Monthly reoptimization
        'category': 'trend'
    },
    'my_strategy_with_hold': {
        'class': MyStrategyWithHold,
        'reopt_days': 30,  # Monthly for hold strategies
        'category': 'trend_with_hold'
    },
    'rl_trading_agent': {
        'class': RLTradingAgent,
        'reopt_days': 7,   # Weekly for RL
        'category': 'reinforcement_learning'
    }
}
```

### Smart Categorization Rules

| Strategy Name Pattern | Category | Reoptimization |
|----------------------|----------|---------------|
| `*_with_hold` | `trend_with_hold` | 30 days |
| `rl_*`, `reinforcement*` | `reinforcement_learning` | 7 days |
| `mean_reversion*`, `statistical*` | `mean_reversion` | 14 days |
| `scalping*`, `channel*` | `scalping` | 7 days |
| `breakout*`, `supply_demand*` | `breakout` | 21 days |
| `supertrend*`, `adaptive*` | `trend_following` | 21 days |
| Default | `trend` | 30 days |

## 🎮 Running Backtests

### Test Mode (Recommended for New Strategies)

```bash
# Test with a few strategies and limited trials
python run_bt.py --test
```

This will:
- Download sample data
- Test 4 strategies with 100 trials each
- Complete in ~30-60 minutes

### Full Optimization

```bash
# Optimize all strategies
python run_bt.py
```

### Custom Strategy Selection

```bash
# Run specific strategies
python run_bt.py --strategies my_strategy,rsi_divergence

# Run with custom workers and trials
python run_bt.py --workers 8 --trials 200
```

### Scheduler Mode

```bash
# Run optimization scheduler
python src/backtest/scheduler.py

# Run only RL optimization
python src/backtest/scheduler.py --rl-only

# Force re-run all optimizations
python src/backtest/scheduler.py --run-now --force
```

## ⚙️ Configuration

### Config File (`config.json`)

```json
{
  "exchanges": {
    "binance": {
      "api_key": "your_api_key",
      "api_secret": "your_api_secret"
    },
    "hyperliquid": {
      "wallet_address": "your_wallet_address"
    }
  },
  "optimization": {
    "max_workers": 4,
    "n_trials": 500,
    "timeframes": ["1h", "4h", "1d"]
  },
  "data": {
    "cache_dir": "data/",
    "max_age_days": 7
  }
}
```

### Environment Variables

```bash
# Set API keys
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"

# Configure optimization
export NEXUS_MAX_WORKERS=8
export NEXUS_N_TRIALS=1000
```

## 📊 Understanding Results

### Results Structure

```
results/
├── optimization_results/
│   ├── strategy_name/
│   │   ├── symbol_timeframe/
│   │   │   ├── best_params.json
│   │   │   ├── optimization_history.csv
│   │   │   └── backtest_results.pkl
│   │   └── summary.json
│   └── portfolio_optimization.json
├── analysis/
│   ├── correlation_matrix.png
│   ├── performance_comparison.html
│   └── risk_metrics.json
└── logs/
    └── optimization_20241231.log
```

### Key Metrics Explained

- **Sharpe Ratio**: Risk-adjusted returns (higher > 2.0 is excellent)
- **Sortino Ratio**: Downside risk-adjusted returns
- **Calmar Ratio**: Annual return / Maximum drawdown
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Largest peak-to-valley decline

### Viewing Results

```bash
# Launch interactive dashboard
python src/backtest/BT_dashboard.py

# Analyze specific results
python src/backtest/results_analyzer.py --strategy my_strategy --symbol BTCUSDT
```

## 🔧 Advanced Usage

### Custom Data Sources

Add new exchange support in `src/data/`:

```python
# src/data/my_exchange_ohlcv_source.py

class MyExchangeOHLCVSource(BaseOHLCVSource):
    def __init__(self):
        super().__init__("my_exchange")

    def fetch_ohlcv(self, symbol, timeframe, since=None, limit=None):
        # Implement data fetching logic
        pass
```

### Custom Optimizers

```python
# src/optimizers/my_optimizer.py

from src.optimizers.optimizer import BaseOptimizer

class MyOptimizer(BaseOptimizer):
    def optimize(self, strategy, data, params):
        # Custom optimization logic
        pass
```

### Pipeline Extensions

```python
# Extend pipeline in pipeline_BT_unified_async.py

def my_custom_analysis(results):
    """Add custom analysis to results."""
    # Your analysis code
    return enhanced_results
```

## 🐛 Troubleshooting

### Common Issues

#### Strategy Not Found

**Error**: `Strategy 'my_strategy' not found`

**Solution**:
- Check file name matches class name
- Ensure class inherits from `BaseStrategy`
- Verify file is in `src/strategy/` directory
- Check for syntax errors in strategy file

#### Import Errors

**Error**: `ModuleNotFoundError`

**Solution**:
- Run `pip install -r requirements.txt`
- Check Python path: `python -c "import sys; print(sys.path)"`
- Ensure you're in the project root directory

#### Memory Issues

**Error**: `MemoryError` during optimization

**Solution**:
- Reduce `max_workers` in config
- Increase system RAM
- Use smaller `n_trials`
- Run strategies individually

#### Data Download Failures

**Error**: `ConnectionError` or API limits

**Solution**:
- Check API keys in `config.json`
- Wait for API rate limits to reset
- Use different exchange endpoints
- Check network connectivity

### Debug Mode

```bash
# Enable verbose logging
python run_bt.py --debug

# Test single strategy
python src/backtest/scheduler.py --strategy my_strategy --test
```

### Performance Tuning

```json
{
  "optimization": {
    "max_workers": 4,        // Match CPU cores
    "n_trials": 500,         // Start with 500, increase gradually
    "early_stopping": 50     // Stop if no improvement after N trials
  },
  "data": {
    "chunk_size": 1000,      // Process data in chunks
    "cache_compression": true // Save disk space
  }
}
```

## 📞 Support

### Getting Help

1. **Check the logs**: `logs/optimization_*.log`
2. **Run diagnostics**: `python -c "from src.strategy import strategies; print(strategies)"`
3. **Test individual components**:
   ```bash
   # Test data fetching
   python -c "from src.data.binance_ohlcv_source import BinanceOHLCVSource; print('Data source OK')"

   # Test strategy loading
   python -c "from src.strategy.my_strategy import MyStrategy; print('Strategy OK')"
   ```

### Contributing

When adding new strategies:

1. Follow the naming conventions
2. Add comprehensive docstrings
3. Include parameter validation
4. Test with sample data first
5. Update this manual if needed

---

**🎉 Congratulations!** You now understand how to harness the full power of the Nexus Backtesting System. The automatic discovery and adaptation capabilities mean your system grows smarter with every strategy you add. Happy trading! 🚀
