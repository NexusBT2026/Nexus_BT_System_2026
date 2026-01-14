# Changelog

All notable changes to the Nexus Backtesting System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/SemVer).

## [Unreleased]

### Added (January 2026)
- **Real-Time Optimization Dashboard** with Rich UI library:
  - Live progress bars with ETA and time elapsed
  - System resource monitoring (CPU, memory)
  - Success/failure/skipped task tracking
  - Profitability criteria tracking (passed/failed criteria, pass rate)
  - Final selection metrics after filtering
  - Recent tasks log with timestamps
  - Strategy performance breakdown
  - Beautiful color-coded output for client presentations
- **5 New Exchange Integrations**:
  - Bybit perpetual swaps (USDT pairs)
  - OKX perpetual swaps (USDT pairs)
  - Bitget perpetual swaps (USDT pairs)
  - Gate.io perpetual swaps (USDT pairs)
  - MEXC perpetual swaps (USDT pairs)
  - Total coverage now 1,110+ unique trading symbols
- **Enhanced Strategy Categorization**: 17 categories with exchange-specific preferences
- **Professional Initialization Screens**: Phase-by-phase status with clean client-ready output
- **CLI Argument Support**: `--workers`, `--trials`, `--optimizer`, `--scheduler`, `--force-refresh`
- **Silent Logging Mode**: Clean output during data fetch for professional demonstrations

### Added (Previous)
- **Dynamic Strategy Discovery**: Automatic loading and categorization of trading strategies
- **Setup & Validation Script** (`setup.py`): Automated environment setup and health checks
- **Health Check Tool** (`health_check.py`): System monitoring and resource usage tracking
- **Strategy Validator** (`validate_strategies.py`): Automated testing and validation of strategies
- **Comprehensive Manual** (`MANUAL.md`): User guide for adding strategies and system usage
- **Contributing Guidelines** (`CONTRIBUTING.md`): Development workflow and contribution standards
- **MIT License**: Open source licensing
- **Multi-Exchange Support**: Binance, Coinbase, Hyperliquid, KuCoin, Phemex, Bybit, OKX, Bitget, Gate.io, MEXC
- **Async Data Fetching**: Concurrent data collection with smart caching
- **GPU Acceleration**: CuPy and CUDA support for performance optimization
- **Interactive Dashboards**: Plotly-based result visualization
- **Reinforcement Learning**: RL agent integration with Stable Baselines3

### Changed
- **Dashboard Output**: Replaced basic print statements with professional Rich UI dashboard
- **Pipeline Logging**: Silent mode during symbol discovery and data fetch for clean client demos
- **Strategy Filtering**: Automatically skip base_strategy and test_strategy from optimization
- **README Documentation**: Updated with accurate feature counts and new exchange listings
- **Modular Architecture**: Refactored for better extensibility and maintainability
- **Configuration Management**: Centralized config with environment variable support
- **Error Handling**: Improved error messages and recovery mechanisms
- **Performance**: Optimized async processing and memory usage

### Fixed
- **Debug Output Cleanup**: Commented out verbose task received messages
- **Unicode Encoding**: Improved emoji handling for Windows PowerShell compatibility

### Technical Improvements
- **Profitability Criteria Integration**: Composite score tracking (PnL > 0, Win Rate > 55%)
- **Final Selection Tracking**: Dashboard shows strategies passing all filtering stages
- **Strategy Registry**: Dynamic generation with smart categorization (17 categories)
- **Exchange Preferences**: Strategies matched to optimal exchanges for better data quality
- **Pipeline Orchestration**: Freqtrade-inspired modular design
- **Data Pipeline**: Robust OHLCV fetching with fallback mechanisms
- **Optimization Engine**: Hyperopt/Optuna integration with custom metrics
- **Results Analysis**: Comprehensive statistical validation and reporting

## [1.0.0] - 2025-01-01

### Added
- Initial release of Nexus Backtesting System
- Core backtesting engine with pandas-ta integration
- Basic strategy framework with RSI Divergence example
- SQLite result storage with JSON export
- Basic logging and error handling
- Requirements management and dependency tracking

### Known Issues
- Limited exchange support (primarily Phemex)
- Basic optimization (random search only)
- No interactive visualization
- Manual strategy registration required
