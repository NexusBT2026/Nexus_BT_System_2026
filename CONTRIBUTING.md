# Contributing to Nexus Backtesting System

Thank you for your interest in contributing to the Nexus Backtesting System! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/nexus_bt_system.git`
3. **Set up** the environment: `python setup.py`
4. **Create** a feature branch: `git checkout -b feature/your-feature-name`
5. **Make** your changes
6. **Validate** your changes: `python validate_strategies.py`
7. **Test** your changes: `python run_bt.py --test`
8. **Submit** a pull request

## 📋 Development Workflow

### 1. Environment Setup

```bash
# Run the automated setup
python setup.py

# Or manual setup
pip install -r requirements.txt
cp config.json.example config.json  # Add your API keys
```

### 2. Code Quality

- **Run validation**: `python validate_strategies.py`
- **Check health**: `python health_check.py`
- **Test compilation**: `python -m py_compile src/**/*.py`
- **Follow PEP 8** style guidelines

### 3. Testing

```bash
# Quick test with sample data
python run_bt.py --test

# Full system test (requires API keys)
python run_bt.py

# Strategy-specific testing
python src/backtest/scheduler.py --strategy your_strategy --test
```

## 🎯 Adding New Strategies

### Strategy Requirements

- **Inherit** from `BaseStrategy`
- **Implement** required methods: `populate_indicators`, `populate_buy_signal`, `populate_sell_signal`
- **Define** parameters in `buy_params` and `sell_params`
- **Follow** naming convention: `snake_case.py` for files, `CamelCaseStrategy` for classes
- **Add** comprehensive docstrings

### Strategy Template

```python
# src/strategy/my_strategy.py

from src.strategy.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    """
    Description of your strategy.
    What market conditions it works in, expected performance, etc.
    """

    strategy_name = "my_strategy"
    timeframe = "1h"

    buy_params = {
        'param1': {'type': 'int', 'min': 1, 'max': 100},
        'param2': {'type': 'float', 'min': 0.1, 'max': 1.0},
    }

    sell_params = {
        'stop_loss': {'type': 'float', 'min': 0.01, 'max': 0.10},
    }

    def populate_indicators(self, dataframe, metadata):
        # Add your indicators here
        return dataframe

    def populate_buy_signal(self, dataframe, metadata):
        # Define buy conditions
        dataframe.loc[:, 'buy'] = condition
        return dataframe

    def populate_sell_signal(self, dataframe, metadata):
        # Define sell conditions
        dataframe.loc[:, 'sell'] = condition
        return dataframe
```

### Strategy Validation

Before submitting, ensure your strategy passes validation:

```bash
python validate_strategies.py
```

## 🔧 Adding New Features

### Code Organization

- **Data sources**: `src/data/`
- **Strategies**: `src/strategy/`
- **Backtesting engine**: `src/backtest/`
- **Optimizers**: `src/optimizers/`
- **Pipeline**: `src/pipeline/`
- **Utilities**: `src/utils/`

### Adding Exchange Support

1. Create new data source in `src/data/your_exchange_ohlcv_source.py`
2. Inherit from `BaseOHLCVSource`
3. Implement `fetch_ohlcv` method
4. Add to `config.json` template
5. Update documentation

### Adding Optimizer Support

1. Create new optimizer in `src/optimizers/your_optimizer.py`
2. Inherit from `BaseOptimizer`
3. Implement `optimize` method
4. Add configuration options
5. Update pipeline integration

## 📝 Documentation

### Updating Documentation

- **README.md**: High-level overview and features
- **MANUAL.md**: User guide and tutorials
- **Code comments**: Comprehensive docstrings for all public methods
- **Type hints**: Use type annotations where possible

### Documentation Standards

```python
def my_function(param1: str, param2: int = 0) -> dict:
    """
    Brief description of what the function does.

    Args:
        param1 (str): Description of param1
        param2 (int, optional): Description of param2. Defaults to 0.

    Returns:
        dict: Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> result = my_function("test", 42)
        >>> print(result)
        {'status': 'ok'}
    """
```

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to reproduce**: Step-by-step instructions
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant log output
- **Screenshots**: If applicable

### Feature Requests

For new features, please provide:

- **Use case**: Why this feature is needed
- **Proposed solution**: How it should work
- **Alternatives**: Other approaches considered
- **Impact**: How it affects existing functionality

## 📊 Performance Guidelines

- **Memory usage**: Monitor with `python health_check.py`
- **Execution time**: Test with representative data sizes
- **Scalability**: Ensure features work with multiple strategies/symbols
- **Resource efficiency**: Avoid unnecessary computations

## 🔒 Security Considerations

- **API keys**: Never commit real API keys
- **Data validation**: Validate all inputs
- **Error handling**: Don't expose sensitive information in errors
- **Dependencies**: Keep dependencies updated and secure

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🙏 Recognition

Contributors will be recognized in the project documentation and release notes. Thank you for helping make Nexus better!

---

**Questions?** Open an issue or start a discussion in the repository.
