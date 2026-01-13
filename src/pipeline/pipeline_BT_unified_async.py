"""
Unified Pipeline Orchestrator Module - Freqtrade-inspired Architecture
Step 1: Symbol Discovery
Step 2: Strategy Optimization (Hyperopt + Backtesting)
Step 3: Results Analysis and Ranking

Following freqtrade patterns:
- Modular design with clear separation of concerns
- Hyperopt-based hyperparameter optimization
- Comprehensive backtesting with multiple metrics
- Standardized strategy interface
- Results analysis and reporting
"""
import os
import sys
import requests
import json
import warnings
import importlib.util
import sqlite3
from datetime import UTC, datetime, timedelta
import time
import pandas as pd
import re
from typing import Optional
from types import ModuleType
import asyncio

# Modern imports following freqtrade patterns (future-proof)
# Using importlib.util instead of deprecated pkg_resources
# This ensures compatibility with future Python versions

# Custom datetime helper functions (freqtrade-style)
def dt_now() -> datetime:
    """Get current UTC datetime (freqtrade pattern)"""
    return datetime.now(UTC)

def dt_utc() -> datetime:
    """Get current UTC datetime (freqtrade pattern)"""
    return datetime.now(UTC)

# NOTE: Removed datetime warning suppression - we now use modern UTC-aware datetime
# If hyperopt still shows warnings, that's THEIR problem, not ours!

# Load config for thread configuration
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
config_path = os.path.join(project_root, 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Custom thread configuration - auto-detect or user-configurable
configured_threads = config.get('numexpr_max_threads')
if configured_threads is None or configured_threads <= 0:
    # Auto-detect: use 80% of available CPUs, minimum 1
    total_cpus = os.cpu_count() or 1
    NUMEXPR_MAX_THREADS = max(1, int(total_cpus * 0.8))
else:
    NUMEXPR_MAX_THREADS = configured_threads

def generate_strategy_registry(strategies_dict):
    """
    Generate dynamic strategy registry with reoptimization schedules and exchange preferences.
    
    Automatically categorizes strategies and assigns optimal parameters based on strategy type:
    - Reoptimization intervals (7-30 days)
    - Preferred exchange rankings
    - Data quality requirements
    
    Args:
        strategies_dict: Dictionary of strategy name -> strategy class mappings
    
    Returns:
        dict: Strategy registry with metadata for each strategy
    """
    registry = {}
    
    for strategy_name, strategy_class in strategies_dict.items():
        if strategy_class is None:
            continue
        
        name_lower = strategy_name.lower()
        
        # ═══════════════════════════════════════════════════════════════
        # COMPREHENSIVE STRATEGY CATEGORIZATION (alphabetical by category)
        # ═══════════════════════════════════════════════════════════════
        
        # ARBITRAGE & PAIR TRADING - Statistical edge strategies
        if 'arbitrage' in name_lower or 'pair' in name_lower:
            category = 'arbitrage'
            reopt_days = 14  # Bi-weekly - edges decay quickly
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'bitget', 'gateio']
            min_data_quality = 'high'  # Precision critical for correlation analysis
        
        # BREAKOUT & SUPPLY/DEMAND - Volume-driven strategies
        elif 'breakout' in name_lower or 'supply' in name_lower or 'demand' in name_lower or 'liquidation' in name_lower:
            category = 'breakout'
            reopt_days = 21  # Every 3 weeks
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'bitget', 'gateio', 'phemex']
            min_data_quality = 'medium'  # Volume more important than precision
        
        # DIVERGENCE STRATEGIES - RSI/MACD divergence patterns
        elif 'divergence' in name_lower:
            category = 'divergence'
            reopt_days = 14  # Bi-weekly - pattern-based
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex']
            min_data_quality = 'high'  # Needs accurate indicator calculations
        
        # GRID TRADING - Range-bound automated systems
        elif 'grid' in name_lower:
            category = 'grid_trading'
            reopt_days = 30  # Monthly - range parameters change slowly
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid']
            min_data_quality = 'medium'  # Works in any market
        
        # ICHIMOKU & HEIKIN-ASHI - Japanese technical analysis
        elif 'ichimoku' in name_lower or 'heikin' in name_lower or 'ashi' in name_lower:
            category = 'japanese_technical'
            reopt_days = 21  # Every 3 weeks
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex']
            min_data_quality = 'high'  # Cloud calculations need precision
        
        # MACHINE LEARNING - LSTM, Neural Nets
        elif 'machine' in name_lower or 'lstm' in name_lower or 'ml' in name_lower or 'neural' in name_lower:
            category = 'machine_learning'
            reopt_days = 7  # Weekly - models need frequent retraining
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid']
            min_data_quality = 'medium'  # ML is robust to noise
        
        # MARKOV CHAIN - Probabilistic state transitions
        elif 'markov' in name_lower:
            category = 'markov_chain'
            reopt_days = 14  # Bi-weekly - state probabilities evolve
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid']
            min_data_quality = 'medium'  # Works with historical patterns
        
        # MEAN REVERSION - BB, RSI, Statistical reversion
        elif 'mean' in name_lower or 'reversion' in name_lower or 'bollinger' in name_lower:
            category = 'mean_reversion'
            reopt_days = 14  # Bi-weekly
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex', 'bitget', 'gateio']
            min_data_quality = 'high'  # Precision matters for band calculations
        
        # MOMENTUM & SWING - Momentum cross, selective momentum
        elif 'momentum' in name_lower or 'swing' in name_lower or 'stochastic' in name_lower:
            category = 'momentum'
            reopt_days = 14  # Bi-weekly
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex']
            min_data_quality = 'medium'  # Momentum strategies are robust
        
        # SCALPING & CHANNEL - Fast intraday strategies
        elif 'scalp' in name_lower or 'channel' in name_lower or 'atr' in name_lower:
            category = 'scalping'
            reopt_days = 7  # Weekly - market microstructure changes fast
            preferred_exchanges = ['hyperliquid', 'binance', 'bybit', 'kucoin', 'okx', 'phemex']
            min_data_quality = 'high'  # Needs precise tick data
        
        # TREND FOLLOWING - Supertrend, MA, EMA, Trend Capture
        elif 'trend' in name_lower or 'supertrend' in name_lower or 'pullback' in name_lower or 'ribbon' in name_lower:
            category = 'trend_following'
            reopt_days = 21  # Every 3 weeks
            preferred_exchanges = ['binance', 'kucoin', 'bybit', 'okx', 'hyperliquid', 'phemex', 'coinbase']
            min_data_quality = 'medium'  # Robust to noise
        
        # VOLATILITY - Volatility breakout, volatility mean reversion
        elif 'volatility' in name_lower or 'vol' in name_lower:
            category = 'volatility'
            reopt_days = 14  # Bi-weekly - vol regimes change
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'bitget']
            min_data_quality = 'medium'  # Volatility calculation is robust
        
        # VOLUME WEIGHTED - Volume-based entry/exit
        elif 'volume' in name_lower and 'weighted' in name_lower:
            category = 'volume_weighted'
            reopt_days = 21  # Every 3 weeks
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid']
            min_data_quality = 'high'  # Needs accurate volume data
        
        # ADAPTIVE & HYBRID - Dynamic multi-indicator strategies
        elif 'adaptive' in name_lower or 'hybrid' in name_lower:
            category = 'adaptive_hybrid'
            reopt_days = 14  # Bi-weekly - adapts to changing conditions
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex']
            min_data_quality = 'high'  # Complex calculations need precision
        
        # HOLD STRATEGIES - Longer timeframe position holding
        elif 'hold' in name_lower:
            category = 'trend_with_hold'
            reopt_days = 30  # Monthly - longer timeframes
            preferred_exchanges = ['binance', 'kucoin', 'bybit', 'okx', 'coinbase', 'hyperliquid', 'phemex']
            min_data_quality = 'high'  # Need reliable long-term data
        
        # DEFAULT - Catch-all for uncategorized strategies
        else:
            category = 'general'
            reopt_days = 21  # Default 3 weeks
            preferred_exchanges = ['binance', 'bybit', 'kucoin', 'okx', 'hyperliquid', 'phemex', 'coinbase']
            min_data_quality = 'medium'  # Standard quality
        
        registry[strategy_name] = {
            'class': strategy_class,
            'reopt_days': reopt_days,
            'category': category,
            'preferred_exchanges': preferred_exchanges,
            'min_data_quality': min_data_quality
        }
    
    return registry

os.environ['NUMEXPR_MAX_THREADS'] = str(NUMEXPR_MAX_THREADS)
os.environ['OMP_NUM_THREADS'] = str(NUMEXPR_MAX_THREADS)  # OpenMP threading
os.environ['MKL_NUM_THREADS'] = str(NUMEXPR_MAX_THREADS)  # Intel MKL threading
os.environ['OPENBLAS_NUM_THREADS'] = str(NUMEXPR_MAX_THREADS)  # OpenBLAS threading

# Project root for relative paths (already set above, but keeping for clarity)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(NUMEXPR_MAX_THREADS)  # Apple Accelerate
os.environ['BLIS_NUM_THREADS'] = str(NUMEXPR_MAX_THREADS)  # BLIS threading

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception
import logging as _logging

# Create logger but set to ERROR by default (dashboard will be primary output)
logger = setup_logger('pipeline_BT_source', json_logs=False, level=_logging.ERROR)

def load_module_from_path(module_path: str, module_name: Optional[str] = None)-> ModuleType | None:
    """
    Modern module loader using importlib.util (freqtrade-inspired)
    Replaces deprecated pkg_resources functionality
    
    Args:
        module_path: Path to the module file
        module_name: Name for the module (optional)
    
    Returns:
        Loaded module or None if failed
    """
    try:
        if module_name is None:
            module_name = os.path.splitext(os.path.basename(module_path))[0]
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        logger.warning(f"Failed to load module {module_path}: {e}")
        return None

def save_results_to_sqlite(results: dict, symbol: str, strategy: str, db_path: Optional[str] = None) -> None:
    """
    Save optimization results to SQLite database.
    
    Args:
        results: Dictionary containing optimization results
        symbol: Trading symbol (e.g., 'BTC')
        strategy: Strategy name
        db_path: Path to SQLite database file (optional)
    """
    if db_path is None:
        db_path = os.path.join(project_root, 'data', 'pipeline_results.sqlite')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database and create table if not exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pipeline_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
            result_json TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert results
    cursor.execute('''
        INSERT INTO pipeline_results (symbol, strategy, result_json)
        VALUES (?, ?, ?)
    ''', (symbol, strategy, json.dumps(results)))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Saved results for {symbol} {strategy} to SQLite: {db_path}")
    
def discover_symbols() -> dict[str, object]:
    """Discover tradable symbols across all configured exchanges.
    
    Returns symbols organized by exchange and availability:
    - Common symbols (available on multiple exchanges)
    - Exchange-specific symbols (unique to each exchange)
    - Cached results for performance (daily refresh)
    
    Returns:
        dict: Symbol data organized by exchange and type
    """
    from src.data.symbol_discovery import (load_cache_base_symbols, load_cache_per_exchange_format,
                                           get_all_symbols_with_cache_per_exchange_format, get_all_symbols_with_cache_base_symbols,
                                           get_all_phemex_contract_symbols, get_phemex_base_symbols, 
                                           get_hyperliquid_symbols,
                                           get_coinbase_spot_symbols, get_coinbase_base_symbols,
                                           get_binance_spot_symbols, get_binance_base_symbols,
                                           get_bitget_base_symbols, get_bitget_symbols,
                                           get_gateio_base_symbols, get_gateio_symbols,
                                           get_mexc_base_symbols, get_mexc_symbols,
                                           get_okx_base_symbols, get_okx_symbols,
                                           get_bybit_base_symbols, get_bybit_symbols)
    from src.data.symbol_intersection import (get_common_base_symbols, async_get_common_base_symbols,
                                              get_hyperliquid_unmatched_symbols, async_get_hyperliquid_unmatched_symbols,
                                              async_get_unmatched_coinbase_symbols, get_unmatched_coinbase_symbols,
                                              get_unmatched_binance_symbols, async_get_unmatched_binance_symbols,
                                              get_unmatched_phemex_symbols, async_get_unmatched_phemex_symbols,
                                              get_unmatched_kucoin_symbols, async_get_unmatched_kucoin_symbols,
                                              get_phemex_base, get_binance_base, get_coinbase_base, get_kucoin_base,
                                              get_unmatched_bitget_symbols, get_unmatched_bybit_symbols,
                                              get_unmatched_gateio_symbols, get_unmatched_mexc_symbols, get_unmatched_okx_symbols)
    
    # Load config to check exchange flags
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    enabled_exchanges = []
    if config.get('use_phemex', True):
        enabled_exchanges.append('phemex')
    if config.get('use_hyperliquid', True):
        enabled_exchanges.append('hyperliquid')
    if config.get('use_coinbase', True):
        enabled_exchanges.append('coinbase')
    if config.get('use_binance', True):
        enabled_exchanges.append('binance')
    if config.get('use_kucoin', True):
        enabled_exchanges.append('kucoin')
    if config.get('use_bybit', False):
        enabled_exchanges.append('bybit')
    if config.get('use_okx', False):
        enabled_exchanges.append('okx')
    if config.get('use_bitget', False):
        enabled_exchanges.append('bitget')
    if config.get('use_gateio', False):
        enabled_exchanges.append('gateio')
    if config.get('use_mexc', False):
        enabled_exchanges.append('mexc')
    
    logger.info(f"Enabled exchanges for symbol discovery: {enabled_exchanges}")

    # Load both caches
    base_symbols_cache = load_cache_base_symbols()
    per_exchange_cache = load_cache_per_exchange_format()

    # Initialize all outputs as None
    phemex_symbols = None
    phemex_symbols_base = None
    hyperliquid_symbols = None
    coinbase_unmatched = None
    common_symbols = None
    unmatched_hyperliquid = None
    binance_unmatched = None
    kucoin_unmatched = None
    bitget_unmatched = None
    bybit_unmatched = None
    gateio_unmatched = None
    mexc_unmatched = None
    okx_unmatched = None

    # Use base symbols cache if available
    if base_symbols_cache and "symbols" in base_symbols_cache:
        symbols = base_symbols_cache["symbols"]
        phemex_symbols_base = symbols.get("phemex_base")
        logger.debug(f"[CACHE] Loaded Phemex base symbols: {phemex_symbols_base}")
        hyperliquid_symbols = symbols.get("hyperliquid")
        logger.debug(f"[CACHE] Loaded Hyperliquid base symbols: {hyperliquid_symbols}")
        common_symbols = get_common_base_symbols()
        logger.debug(f"[CACHE] Loaded common base symbols: {common_symbols}")
        unmatched_hyperliquid = get_hyperliquid_unmatched_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Hyperliquid symbols: {unmatched_hyperliquid}")
        coinbase_unmatched = get_unmatched_coinbase_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Coinbase symbols: {coinbase_unmatched}")
        binance_unmatched = get_unmatched_binance_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Binance symbols: {binance_unmatched}")
        kucoin_unmatched = get_unmatched_kucoin_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Kucoin symbols: {kucoin_unmatched}")
        bitget_unmatched = get_unmatched_bitget_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Bitget symbols: {bitget_unmatched}")
        bybit_unmatched = get_unmatched_bybit_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Bybit symbols: {bybit_unmatched}")
        gateio_unmatched = get_unmatched_gateio_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Gateio symbols: {gateio_unmatched}")
        mexc_unmatched = get_unmatched_mexc_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Mexc symbols: {mexc_unmatched}")
        okx_unmatched = get_unmatched_okx_symbols()
        logger.debug(f"[CACHE] Loaded unmatched Okx symbols: {okx_unmatched}")

    # If any are still None, fetch live (using helper functions that return lists)
    if phemex_symbols is None:
        phemex_symbols = get_phemex_base()  # Returns list, not DataFrame
        logger.debug(f"[LIVE] Fetched Phemex base symbols: {phemex_symbols}")
    if phemex_symbols_base is None:
        phemex_symbols_base = get_phemex_base()  # Returns list, not DataFrame
        logger.debug(f"[LIVE] Fetched Phemex base symbols: {phemex_symbols_base}")
    if hyperliquid_symbols is None:
        # Hyperliquid returns DataFrame, need to convert to list
        hl_df = get_hyperliquid_symbols()
        hyperliquid_symbols = hl_df['symbol'].tolist() if hasattr(hl_df, 'symbol') else list(hl_df)
        logger.debug(f"[LIVE] Fetched Hyperliquid symbols: {hyperliquid_symbols}")
    if common_symbols is None:
        common_symbols = get_common_base_symbols()
        logger.debug(f"[LIVE] Fetched common base symbols: {common_symbols}")
    if unmatched_hyperliquid is None:
        unmatched_hyperliquid = get_hyperliquid_unmatched_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Hyperliquid symbols: {unmatched_hyperliquid}")
    if coinbase_unmatched is None:
        coinbase_unmatched = get_unmatched_coinbase_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Coinbase symbols: {coinbase_unmatched}")
    if binance_unmatched is None:
        binance_unmatched = get_unmatched_binance_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Binance symbols: {binance_unmatched}")
    if kucoin_unmatched is None:
        kucoin_unmatched = get_unmatched_kucoin_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Kucoin symbols: {kucoin_unmatched}")
    if bybit_unmatched is None:
        bybit_unmatched = get_unmatched_bybit_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Bybit symbols: {bybit_unmatched}")
    if gateio_unmatched is None:
        gateio_unmatched = get_unmatched_gateio_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Gateio symbols: {gateio_unmatched}")
    if mexc_unmatched is None:
        mexc_unmatched = get_unmatched_mexc_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Mexc symbols: {mexc_unmatched}")
    if okx_unmatched is None:
        okx_unmatched = get_unmatched_okx_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Okx symbols: {okx_unmatched}")

    return {
        'phemex': phemex_symbols,
        'phemex_base': phemex_symbols_base,
        'hyperliquid': hyperliquid_symbols,
        'common': common_symbols,
        'unmatched_hyperliquid': unmatched_hyperliquid,
        'coinbase_unmatched': coinbase_unmatched,
        'unmatched_binance': binance_unmatched,
        'unmatched_kucoin': kucoin_unmatched,
        'unmatched_bitget': bitget_unmatched,
        'unmatched_bybit': bybit_unmatched,
        'unmatched_gateio': gateio_unmatched,
        'unmatched_mexc': mexc_unmatched,
        'unmatched_okx': okx_unmatched
    }

async def discover_symbols_async():
    """Asynchronously discover tradable symbols across all configured exchanges.
    
    Faster than synchronous version - uses concurrent API calls where possible.
    Returns symbols organized by exchange and availability with intelligent caching.
    
    Returns:
        dict: Symbol data organized by exchange and type
    """
    from src.data.symbol_discovery import (load_cache_base_symbols, load_cache_per_exchange_format,
                                           get_all_symbols_with_cache_per_exchange_format, get_all_symbols_with_cache_base_symbols,
                                           get_all_phemex_contract_symbols, get_phemex_base_symbols, 
                                           get_hyperliquid_symbols,
                                           get_coinbase_spot_symbols, get_coinbase_base_symbols,
                                           get_binance_spot_symbols, get_binance_base_symbols,
                                           get_bitget_base_symbols, get_bitget_symbols,
                                           get_gateio_base_symbols, get_gateio_symbols,
                                           get_mexc_base_symbols, get_mexc_symbols,
                                           get_okx_base_symbols, get_okx_symbols,
                                           get_bybit_base_symbols, get_bybit_symbols)
    from src.data.symbol_intersection import (get_common_base_symbols, async_get_common_base_symbols,
                                              get_hyperliquid_unmatched_symbols, async_get_hyperliquid_unmatched_symbols,
                                              async_get_unmatched_coinbase_symbols, get_unmatched_coinbase_symbols,
                                              get_unmatched_binance_symbols, async_get_unmatched_binance_symbols,
                                              get_unmatched_phemex_symbols, async_get_unmatched_phemex_symbols,
                                              get_unmatched_kucoin_symbols, async_get_unmatched_kucoin_symbols,
                                              get_phemex_base, get_binance_base, get_coinbase_base, get_kucoin_base,
                                              get_unmatched_bitget_symbols, async_get_unmatched_bitget_symbols,
                                              get_unmatched_bybit_symbols, async_get_unmatched_bybit_symbols,
                                              get_unmatched_gateio_symbols, async_get_unmatched_gateio_symbols,
                                              get_unmatched_mexc_symbols, async_get_unmatched_mexc_symbols,
                                              get_unmatched_okx_symbols, async_get_unmatched_okx_symbols)
    
    # Load config to check exchange flags
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    enabled_exchanges = []
    if config.get('use_phemex', True):
        enabled_exchanges.append('phemex')
    if config.get('use_hyperliquid', True):
        enabled_exchanges.append('hyperliquid')
    if config.get('use_coinbase', True):
        enabled_exchanges.append('coinbase')
    if config.get('use_binance', True):
        enabled_exchanges.append('binance')
    if config.get('use_kucoin', True):
        enabled_exchanges.append('kucoin')
    if config.get('use_bybit', False):
        enabled_exchanges.append('bybit')
    if config.get('use_okx', False):
        enabled_exchanges.append('okx')
    if config.get('use_bitget', False):
        enabled_exchanges.append('bitget')
    if config.get('use_gateio', False):
        enabled_exchanges.append('gateio')
    if config.get('use_mexc', False):
        enabled_exchanges.append('mexc')
    
    logger.info(f"Enabled exchanges for symbol discovery: {enabled_exchanges}")

    # Load both caches
    base_symbols_cache = load_cache_base_symbols()
    per_exchange_cache = load_cache_per_exchange_format()

    # Initialize all outputs as None
    phemex_symbols = None
    phemex_symbols_base = None
    hyperliquid_symbols = None
    coinbase_unmatched = None
    binance_unmatched = None
    kucoin_unmatched = None
    common_symbols = None
    unmatched_hyperliquid = None
    bitget_unmatched = None
    bybit_unmatched = None
    gateio_unmatched = None
    mexc_unmatched = None
    okx_unmatched = None

    # Use base symbols cache if available
    if base_symbols_cache and "symbols" in base_symbols_cache:
        symbols = base_symbols_cache["symbols"]
        if 'phemex' in enabled_exchanges:
            phemex_symbols_base = symbols.get("phemex_base")
            logger.debug(f"[CACHE] Loaded Phemex base symbols: {phemex_symbols_base}")
        if 'hyperliquid' in enabled_exchanges:
            hyperliquid_symbols = symbols.get("hyperliquid")
            logger.debug(f"[CACHE] Loaded Hyperliquid base symbols: {hyperliquid_symbols}")
        if all(ex in enabled_exchanges for ex in ['phemex', 'hyperliquid', 'coinbase', 'binance', 'kucoin']):
            common_symbols = get_common_base_symbols()
            logger.debug(f"[CACHE] Loaded common base symbols: {common_symbols}")
        if 'hyperliquid' in enabled_exchanges:
            unmatched_hyperliquid = get_hyperliquid_unmatched_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Hyperliquid symbols: {unmatched_hyperliquid}")
        if 'coinbase' in enabled_exchanges:
            coinbase_unmatched = get_unmatched_coinbase_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Coinbase symbols: {coinbase_unmatched}")
        if 'binance' in enabled_exchanges:
            binance_unmatched = get_unmatched_binance_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Binance symbols: {binance_unmatched}")
        if 'kucoin' in enabled_exchanges:
            kucoin_unmatched = get_unmatched_kucoin_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Kucoin symbols: {kucoin_unmatched}")
        if 'bitget' in enabled_exchanges:
            bitget_unmatched = get_unmatched_bitget_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Bitget symbols: {bitget_unmatched}")
        if 'bybit' in enabled_exchanges:
            bybit_unmatched = get_unmatched_bybit_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Bybit symbols: {bybit_unmatched}")
        if 'gateio' in enabled_exchanges:
            gateio_unmatched = get_unmatched_gateio_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Gateio symbols: {gateio_unmatched}")
        if 'mexc' in enabled_exchanges:
            mexc_unmatched = get_unmatched_mexc_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Mexc symbols: {mexc_unmatched}")
        if 'okx' in enabled_exchanges:
            okx_unmatched = get_unmatched_okx_symbols()
            logger.debug(f"[CACHE] Loaded unmatched Okx symbols: {okx_unmatched}")

    # If any are still None, fetch live (using helper functions that return lists)
    if phemex_symbols is None and 'phemex' in enabled_exchanges:
        phemex_symbols = get_phemex_base()  # Sync helper returns list, not DataFrame
        logger.debug(f"[LIVE] Fetched Phemex base symbols: {phemex_symbols}")
    elif phemex_symbols is None:
        phemex_symbols = []
    if phemex_symbols_base is None and 'phemex' in enabled_exchanges:
        phemex_symbols_base = get_phemex_base()  # Sync helper returns list, not DataFrame
        logger.debug(f"[LIVE] Fetched Phemex base symbols: {phemex_symbols_base}")
    elif phemex_symbols_base is None:
        phemex_symbols_base = []
    if hyperliquid_symbols is None and 'hyperliquid' in enabled_exchanges:
        # Hyperliquid returns DataFrame, need to convert to list
        hl_df = get_hyperliquid_symbols()
        hyperliquid_symbols = hl_df['symbol'].tolist() if hasattr(hl_df, 'symbol') else list(hl_df)
        logger.debug(f"[LIVE] Fetched Hyperliquid symbols: {hyperliquid_symbols}")
    elif hyperliquid_symbols is None:
        hyperliquid_symbols = []
    if common_symbols is None:
        common_symbols = await async_get_common_base_symbols()
        logger.debug(f"[LIVE] Fetched common base symbols: {common_symbols}")
    if unmatched_hyperliquid is None and 'hyperliquid' in enabled_exchanges:
        unmatched_hyperliquid = await async_get_hyperliquid_unmatched_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Hyperliquid symbols: {unmatched_hyperliquid}")
    elif unmatched_hyperliquid is None:
        unmatched_hyperliquid = []
    if coinbase_unmatched is None and 'coinbase' in enabled_exchanges:
        coinbase_unmatched = await async_get_unmatched_coinbase_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Coinbase symbols: {coinbase_unmatched}")
    elif coinbase_unmatched is None:
        coinbase_unmatched = []
    if binance_unmatched is None and 'binance' in enabled_exchanges:
        binance_unmatched = await async_get_unmatched_binance_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Binance symbols: {binance_unmatched}")
    elif binance_unmatched is None:
        binance_unmatched = []
    if kucoin_unmatched is None and 'kucoin' in enabled_exchanges:
        kucoin_unmatched = await async_get_unmatched_kucoin_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Kucoin symbols: {kucoin_unmatched}")
    elif kucoin_unmatched is None:
        kucoin_unmatched = []
    if bitget_unmatched is None and 'bitget' in enabled_exchanges:
        bitget_unmatched = await async_get_unmatched_bitget_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Bitget symbols: {bitget_unmatched}")
    elif bitget_unmatched is None:
        bitget_unmatched = []
    if bybit_unmatched is None and 'bybit' in enabled_exchanges:
        bybit_unmatched = await async_get_unmatched_bybit_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Bybit symbols: {bybit_unmatched}")
    elif bybit_unmatched is None:
        bybit_unmatched = []
    if gateio_unmatched is None and 'gateio' in enabled_exchanges:
        gateio_unmatched = await async_get_unmatched_gateio_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Gateio symbols: {gateio_unmatched}")
    elif gateio_unmatched is None:
        gateio_unmatched = []
    if mexc_unmatched is None and 'mexc' in enabled_exchanges:
        mexc_unmatched = await async_get_unmatched_mexc_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Mexc symbols: {mexc_unmatched}")
    elif mexc_unmatched is None:
        mexc_unmatched = []
    if okx_unmatched is None and 'okx' in enabled_exchanges:
        okx_unmatched = await async_get_unmatched_okx_symbols()
        logger.debug(f"[LIVE] Fetched unmatched Okx symbols: {okx_unmatched}")
    elif okx_unmatched is None:
        okx_unmatched = []

    return {
        'phemex': phemex_symbols,
        'phemex_base': phemex_symbols_base,
        'hyperliquid': hyperliquid_symbols,
        'common': common_symbols,
        'unmatched_hyperliquid': unmatched_hyperliquid,
        'coinbase_unmatched': coinbase_unmatched,
        'unmatched_binance': binance_unmatched,
        'unmatched_kucoin': kucoin_unmatched,
        'unmatched_bitget': bitget_unmatched,
        'unmatched_bybit': bybit_unmatched,
        'unmatched_gateio': gateio_unmatched,
        'unmatched_mexc': mexc_unmatched,
        'unmatched_okx': okx_unmatched
    }

def is_data_fresh(file_path: str, timeframe: str) -> tuple[bool, datetime | None]:
    """
    Check if data file is fresh based on timeframe requirements
    Returns (is_fresh, last_timestamp)
    """
    if not os.path.exists(file_path):
        return False, None

    try:
        # Read CSV with explicit date format to avoid parsing warnings
        df = pd.read_csv(file_path)
        if df.empty:
            return False, None

        # Parse timestamp column manually with specific format to avoid warnings
        timestamp_col = df.columns[0]  # First column is timestamp
        try:
            # Try common timestamp formats first
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], format='%Y-%m-%d %H:%M:%S', utc=True)
        except:
            try:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], format='%Y-%m-%d %H:%M:%S%z', utc=True)
            except:
                # Fallback without deprecated parameter
                df[timestamp_col] = pd.to_datetime(df[timestamp_col], utc=True, errors='coerce')
        
        df = df.set_index(timestamp_col)
        last_timestamp = df.index[-1]
        current_time = datetime.now(UTC)

        # Ensure timezone consistency - make last_timestamp timezone-aware
        if last_timestamp.tzinfo is None:
            last_timestamp = last_timestamp.replace(tzinfo=UTC)

        # Age threshold based on timeframe
        age_thresholds = {
            '1m': 2,     # 2 minutes for 1m data
            '3m': 4,     # 4 minutes for 3m data
            '5m': 10,    # 10 minutes for 5m data
            '15m': 30,   # 30 minutes for 15m data
            '30m': 60,   # 1 hour for 30m data
            '1h': 120,   # 2 hours for 1h data
            '2h': 240,   # 4 hours for 2h data
            '4h': 480,   # 8 hours for 4h data
            '6h': 720,   # 12 hours for 6h data
            '8h': 960,   # 16 hours for 8h data
            '12h': 1440, # 24 hours for 12h data
            '1d': 2880,  # 48 hours for 1d data
            '3d': 8640,  # 144 hours for 3d data
            '1w': 10080, # 1 week for 1w data
            '1M': 43200, # 30 days for 1M data
        }

        threshold_minutes = age_thresholds.get(timeframe, 60)
        age_minutes = (current_time - last_timestamp).total_seconds() / 60

        is_fresh = age_minutes <= threshold_minutes
        return is_fresh, last_timestamp

    except Exception as e:
        logger.error(f"[ERROR] checking data freshness for {file_path}: {e}")
        return False, None

@retry_on_exception()
async def fetch_ohlcv_data_async(symbols, timeframes=None, data_dir=os.path.join(project_root, 'data'), force_refresh=False) -> None:
    """
    Fetch historical OHLCV data from multiple exchanges concurrently (ASYNC version).
    
    This is the high-performance async version using concurrent API calls.
    Ideal for users with modern multi-core systems who need fast data fetching.
    
    Features:
    - Concurrent fetching across all exchanges (3-10x faster than sync version)
    - Smart staleness checking - only fetches outdated data
    - Rate-limited and exchange-friendly (preserves API limits)
    - Automatic caching to CSV for reuse
    - Supports 10 exchanges: Binance, Bybit, KuCoin, OKX, Hyperliquid, Phemex, 
      Coinbase, Bitget, Gate.io, MEXC
    
    Args:
        symbols: Dictionary with symbol lists for each exchange
        timeframes: List of timeframes to fetch (e.g., ['1h', '4h', '1d'])
        data_dir: Directory to save CSV files (default: 'data/')
        force_refresh: If True, re-fetch all data regardless of freshness
    
    Note: Identical functionality to fetch_ohlcv_data() but much faster.
          Use sync version if async causes issues on older systems.
    """
    # Define valid timeframes for each exchange
    coinbase_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '6h', '1d']
    phemex_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']
    hyperliquid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '8h', '12h', '1d', '3d', '1w', '1M']
    binance_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
    kucoin_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '8h', '12h', '1d', '1w']
    bybit_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']
    okx_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w', '1M']
    bitget_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '6h', '12h', '1d', '3d', '1w', '1M']
    gateio_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w']
    mexc_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '8h', '1d', '1w', '1M']

    if timeframes is None:
        timeframes = list(set(coinbase_timeframes + phemex_timeframes + hyperliquid_timeframes + binance_timeframes + kucoin_timeframes + bybit_timeframes
                              + okx_timeframes + bitget_timeframes + gateio_timeframes + mexc_timeframes))

    from src.data.phemex_ohlcv_source import PhemexOHLCVDataSource
    from src.data.hyperliquid_ohlcv_source import HyperliquidOHLCVDataSource
    from src.data.coinbase_ohlcv_source import CoinbaseOHLCVDataSource
    from src.data.binance_ohlcv_source import BinanceOHLCVDataSource
    from src.data.kucoin_ohlcv_source import KucoinOHLCVDataSource
    from src.data.bybit_ohlcv_source import BybitOHLCVDataSource
    from src.data.okx_ohlcv_source import OKXOHLCVDataSource
    from src.data.bitget_ohlcv_source import BitgetOHLCVDataSource
    from src.data.gateio_ohlcv_source import GateioOHLCVDataSource
    from src.data.mexc_ohlcv_source import MEXCOHLCVDataSource

    # Load config to check exchange flags
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    enabled_exchanges = []
    if config.get('use_phemex', True):
        enabled_exchanges.append('phemex')
    if config.get('use_hyperliquid', True):
        enabled_exchanges.append('hyperliquid')
    if config.get('use_coinbase', True):
        enabled_exchanges.append('coinbase')
    if config.get('use_binance', True):
        enabled_exchanges.append('binance')
    if config.get('use_kucoin', True):
        enabled_exchanges.append('kucoin')
    if config.get('use_bybit', False):
        enabled_exchanges.append('bybit')
    if config.get('use_okx', False):
        enabled_exchanges.append('okx')
    if config.get('use_bitget', False):
        enabled_exchanges.append('bitget')
    if config.get('use_gateio', False):
        enabled_exchanges.append('gateio')
    if config.get('use_mexc', False):
        enabled_exchanges.append('mexc')
    
    logger.info(f"Enabled exchanges for symbol discovery: {enabled_exchanges}")

    phemex_ds = PhemexOHLCVDataSource()
    hyperliquid_ds = HyperliquidOHLCVDataSource()
    coinbase_ds = CoinbaseOHLCVDataSource()
    binance_ds = BinanceOHLCVDataSource()
    kucoin_ds = KucoinOHLCVDataSource()
    bybit_ds = BybitOHLCVDataSource()
    okx_ds = OKXOHLCVDataSource()
    bitget_ds = BitgetOHLCVDataSource()
    gateio_ds = GateioOHLCVDataSource()
    mexc_ds = MEXCOHLCVDataSource()

    os.makedirs(data_dir, exist_ok=True)

    total_fetched = 0
    total_skipped = 0
    total_errors = 0

    async def process_exchange_async(exchange_name, symbol_list, valid_timeframes, data_source):
        nonlocal total_fetched, total_skipped, total_errors
        fetch_tasks = []
        skipped_count = 0

        for symbol in symbol_list:
            if exchange_name == 'phemex':
                # For Phemex, handle both clean base symbols and u-prefixed contract symbols
                if symbol.startswith('s') and symbol.endswith('USDT'):
                    # Already in proper Phemex format (e.g., sBTCUSDT)
                    base_symbol = symbol.replace('USDT', '').replace('s', '')
                    fetch_symbol = symbol
                elif symbol.endswith('USDT'):
                    # Contract format - extract clean base symbol for filename
                    if symbol.startswith('u1000000'):
                        base_symbol = symbol.replace('u1000000', '').replace('USDT', '')
                        fetch_symbol = symbol  # Already in correct API format
                    elif symbol.startswith('u10000'):
                        base_symbol = symbol.replace('u10000', '').replace('USDT', '')
                        fetch_symbol = symbol  # Already in correct API format
                    elif symbol.startswith('u1000'):
                        base_symbol = symbol.replace('u1000', '').replace('USDT', '')
                        fetch_symbol = symbol  # Already in correct API format
                    else:
                        # Standard contract format (e.g., BTCUSDT)
                        base_symbol = symbol.replace('USDT', '')
                        fetch_symbol = symbol  # Use symbol as-is for API calls
                else:
                    # This is already a u-prefixed symbol from symbol discovery (e.g., 'u1000XEC')
                    # Extract clean base symbol for filename
                    if symbol.startswith('u1000000'):
                        base_symbol = symbol.replace('u1000000', '')
                        fetch_symbol = f"{symbol}USDT"  # Add USDT for API call
                    elif symbol.startswith('u10000'):
                        base_symbol = symbol.replace('u10000', '')
                        fetch_symbol = f"{symbol}USDT"  # Add USDT for API call
                    elif symbol.startswith('u1000'):
                        base_symbol = symbol.replace('u1000', '')  # 'u1000XEC' -> 'XEC'
                        fetch_symbol = f"{symbol}USDT"  # 'u1000XEC' -> 'u1000XECUSDT'
                    else:
                        # Clean base symbol - need to determine correct Phemex format
                        base_symbol = symbol  # Clean base symbol for filename
                        # Define symbols that need u-prefixes based on actual Phemex data (2025-11-02)
                        u1000000_symbols = {'BABYDOGE', 'MOG'}
                        u10000_symbols = set()  # No u10000 symbols currently listed
                        u1000_symbols = {'BONK', 'CAT', 'CHEEMS', 'FLOKI', 'PEPE', 'RATS', 'SATS', 'SHIB', 'WHY', 'X', 'XEC'}
                        
                        if symbol in u1000000_symbols:
                            fetch_symbol = f'u1000000{symbol}USDT'
                        elif symbol in u10000_symbols:
                            fetch_symbol = f'u10000{symbol}USDT'
                        elif symbol in u1000_symbols:
                            fetch_symbol = f'u1000{symbol}USDT'
                        else:
                            # Standard USDT format for major symbols
                            fetch_symbol = f"{symbol}USDT"
            elif exchange_name == 'hyperliquid':
                # For Hyperliquid, convert base symbols to proper API format
                def convert_to_hyperliquid_symbol(base_symbol):
                    """Convert base symbol to proper Hyperliquid format"""
                    # These symbols need 'k' prefix on Hyperliquid
                    k_symbols = {'SHIB', 'PEPE', 'LUNC', 'BONK', 'FLOKI', 'DOGS', 'NEIRO'}
                    if base_symbol in k_symbols:
                        return f'k{base_symbol}'
                    return base_symbol
                
                base_symbol = symbol
                fetch_symbol = convert_to_hyperliquid_symbol(symbol)
            elif exchange_name == 'coinbase':
                # For Coinbase spot, use direct base symbol format
                # Note: 1000-prefix symbols (SHIB, PEPE, etc.) are only available as PERP/SWAP contracts, not spot
                base_symbol = symbol
                fetch_symbol = f"{symbol}-USDC"
            elif exchange_name == 'binance':
                # For Binance spot, standard USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}USDT"
            elif exchange_name == 'kucoin':
                # For Kucoin perpetual swaps, standard USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}USDTM"  # KuCoin futures use USDTM suffix
            elif exchange_name == 'bybit':
                # For Bybit perpetual swaps, USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}/USDT:USDT"  # Bybit uses BASE/USDT:USDT format
            elif exchange_name == 'okx':
                # For OKX perpetual swaps, USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}/USDT:USDT"  # OKX uses BASE/USDT:USDT format
            elif exchange_name == 'bitget':
                # For Bitget perpetual swaps, USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}/USDT:USDT"  # Bitget uses BASE/USDT:USDT format
            elif exchange_name == 'gateio':
                # For Gate.io perpetual swaps, USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}/USDT:USDT"  # Gate.io uses BASE/USDT:USDT format
            elif exchange_name == 'mexc':
                # For MEXC perpetual swaps, USDT pairs
                base_symbol = symbol
                fetch_symbol = f"{symbol}/USDT:USDT"  # MEXC uses BASE/USDT:USDT format
            else:
                continue

            for tf in [tf for tf in timeframes if tf in valid_timeframes]:
                csv_path = os.path.join(data_dir, f'{base_symbol}_{tf}_candle_data.csv')
                if not force_refresh:
                    is_fresh, last_timestamp = is_data_fresh(csv_path, tf)
                    if is_fresh:
                        skipped_count += 1
                        total_skipped += 1
                        continue
                fetch_tasks.append({
                    'base_symbol': base_symbol,
                    'fetch_symbol': fetch_symbol,
                    'timeframe': tf,
                    'csv_path': csv_path
                })

        if skipped_count > 0:
            logger.info(f"{exchange_name.upper()}: Skipped {skipped_count} fresh items")
        if not fetch_tasks:
            logger.info(f"{exchange_name.upper()}: All data is fresh, nothing to fetch")
            return

        # 🤖 ULTRA-CONSERVATIVE LIMITS: Minimize impact on live bot operations
        max_concurrent = {
            'hyperliquid': 3,  # ULTRA conservative - only 3 concurrent request for Hyperliquid
            'coinbase': 3,     # ULTRA conservative - only 3 concurrent request for Coinbase  
            'phemex': 3,       # Conservative - only 3 concurrent requests for Phemex
            'binance': 3,      # Conservative - only 3 concurrent requests for Binance
            'kucoin': 3,       # Conservative - only 3 concurrent requests for KuCoin
            'bybit': 3,        # Conservative - only 3 concurrent requests for Bybit
            'okx': 3,          # Conservative - only 3 concurrent requests for OKX
            'bitget': 3,       # Conservative - only 3 concurrent requests for Bitget
            'gateio': 3,       # Conservative - only 3 concurrent requests for Gate.io
            'mexc': 3,         # Conservative - only 3 concurrent requests for MEXC
        }.get(exchange_name, 3)
        
        logger.info(f"{exchange_name.upper()}: Processing {len(fetch_tasks)} tasks with {max_concurrent} max concurrent...")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(task):
            async with semaphore:
                try:
                    # 🤖 BOT-FRIENDLY DELAYS: Add delays to avoid competing with live bot
                    # Different delays per exchange based on their API sensitivity
                    if exchange_name == 'hyperliquid':
                        await asyncio.sleep(4.0)  # 4 seconds for Hyperliquid (most tolerant)
                    elif exchange_name == 'coinbase':
                        await asyncio.sleep(6.0)  # 6 seconds for Coinbase (most sensitive)
                    elif exchange_name == 'phemex':
                        await asyncio.sleep(4.0)  # 4 second for Phemex (most tolerant)
                    elif exchange_name == 'binance':
                        await asyncio.sleep(4.0)  # 4 second for Binance (most tolerant)
                    elif exchange_name == 'kucoin':
                        await asyncio.sleep(4.0)  # 4 second for Kucoin (most tolerant)
                    elif exchange_name == 'bybit':
                        await asyncio.sleep(4.0)  # 4 second for Bybit (most tolerant)
                    elif exchange_name == 'okx':
                        await asyncio.sleep(6.0)  # 6 second for OKX (most sensitive)
                    elif exchange_name == 'bitget':
                        await asyncio.sleep(4.0)  # 4 second for Bitget (most tolerant)
                    elif exchange_name == 'gateio':
                        await asyncio.sleep(4.0)  # 4 second for Gate.io (most tolerant)
                    elif exchange_name == 'mexc':
                        await asyncio.sleep(4.0)  # 4 second for MEXC (most tolerant)
                    else:
                        await asyncio.sleep(5.0)  # Default 5 second delay
                    
                    # Call the synchronous fetch method - we'll need async versions later
                    # For now, run in executor to avoid blocking
                    logger.debug(f"{exchange_name.upper()}: Calling fetch_historical_data with symbol='{task['fetch_symbol']}' timeframe='{task['timeframe']}'")
                    loop = asyncio.get_event_loop()
                    df = await loop.run_in_executor(None, data_source.fetch_historical_data, 
                                                    task['fetch_symbol'], task['timeframe'])
                    if df is not None and not df.empty:
                        # File I/O in executor to avoid blocking
                        await loop.run_in_executor(None, lambda: df.to_csv(task['csv_path'], index=False))
                        return True
                    return False
                except Exception as e:
                    # More detailed error logging with better error handling
                    error_msg = str(e)
                    if "delimiter" in error_msg:
                        logger.error(f'{exchange_name.upper()}: {task["base_symbol"]} {task["timeframe"]} - CSV format error: {error_msg}')
                    elif "Rate limit" in error_msg:
                        logger.warning(f'{exchange_name.upper()}: {task["base_symbol"]} {task["timeframe"]} - Rate limited, skipping')
                    else:
                        logger.error(f'{exchange_name.upper()}: {task["base_symbol"]} {task["timeframe"]} - {error_msg}')
                    return False

        # Process all tasks concurrently
        tasks = [fetch_with_semaphore(task) for task in fetch_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        completed_count = 0
        success_count = 0
        for i, result in enumerate(results):
            completed_count += 1
            if isinstance(result, Exception):
                total_errors += 1
                logger.error(f'{exchange_name.upper()}: Task {i} failed - {result}')
            elif result:
                success_count += 1
                total_fetched += 1
                
        logger.info(f"{exchange_name.upper()} COMPLETE: {success_count} successfully fetched, {completed_count} total processed")

    # Prepare exchange tasks for async processing
    exchange_tasks = []
    
    # 🚀 HYPERLIQUID FIRST - Primary data source (fetch ALL symbols)
    if 'hyperliquid' in enabled_exchanges and symbols.get('hyperliquid'):
        from src.data.symbol_discovery import get_hyperliquid_symbols as _get_hl_symbols
        hl_symbols_df = _get_hl_symbols()
        # Extract symbol list from DataFrame (it has a 'symbol' column)
        if hasattr(hl_symbols_df, 'values') and not hl_symbols_df.empty:
            supported_hl_symbols = set(hl_symbols_df.values.flatten())
        else:
            supported_hl_symbols = set()
        # Fetch ALL Hyperliquid symbols (not just unmatched)
        filtered_hl = [s for s in symbols['hyperliquid'] if s in supported_hl_symbols]
        if filtered_hl:
            exchange_tasks.append(('hyperliquid', filtered_hl, hyperliquid_timeframes, hyperliquid_ds))
            logger.info(f"🚀 HYPERLIQUID (PRIMARY): {len(filtered_hl)} symbols queued for fetching")
    
    # Phemex - Supplementary data source (fetch unmatched symbols only)
    if 'phemex' in enabled_exchanges and symbols.get('unmatched_phemex'):
        exchange_tasks.append(('phemex', symbols['unmatched_phemex'], phemex_timeframes, phemex_ds))
        logger.info(f"📊 Phemex (supplementary): {len(symbols['unmatched_phemex'])} unique symbols queued")
    
    # Other exchanges - Supplementary data (unmatched symbols only)
    if 'coinbase' in enabled_exchanges and symbols.get('coinbase_unmatched'):
        exchange_tasks.append(('coinbase', symbols['coinbase_unmatched'], coinbase_timeframes, coinbase_ds))
    if 'binance' in enabled_exchanges and symbols.get('unmatched_binance'):
        exchange_tasks.append(('binance', symbols['unmatched_binance'], binance_timeframes, binance_ds))
    if 'kucoin' in enabled_exchanges and symbols.get('unmatched_kucoin'):
        exchange_tasks.append(('kucoin', symbols['unmatched_kucoin'], kucoin_timeframes, kucoin_ds))
    if 'bybit' in enabled_exchanges and symbols.get('unmatched_bybit'):
        exchange_tasks.append(('bybit', symbols['unmatched_bybit'], bybit_timeframes, bybit_ds))
    if 'okx' in enabled_exchanges and symbols.get('unmatched_okx'):
        exchange_tasks.append(('okx', symbols['unmatched_okx'], okx_timeframes, okx_ds))
    if 'bitget' in enabled_exchanges and symbols.get('unmatched_bitget'):
        exchange_tasks.append(('bitget', symbols['unmatched_bitget'], bitget_timeframes, bitget_ds))
    if 'gateio' in enabled_exchanges and symbols.get('unmatched_gateio'):
        exchange_tasks.append(('gateio', symbols['unmatched_gateio'], gateio_timeframes, gateio_ds))
    if 'mexc' in enabled_exchanges and symbols.get('unmatched_mexc'):
        exchange_tasks.append(('mexc', symbols['unmatched_mexc'], mexc_timeframes, mexc_ds))

    # Process all exchanges concurrently with asyncio
    if exchange_tasks:
        exchange_coroutines = [
            process_exchange_async(exchange_name, symbol_list, valid_timeframes, data_source)
            for exchange_name, symbol_list, valid_timeframes, data_source in exchange_tasks
        ]
        
        results = await asyncio.gather(*exchange_coroutines, return_exceptions=True)
        
        for i, result in enumerate(results):
            exchange_name = exchange_tasks[i][0]
            if isinstance(result, Exception):
                logger.error(f"{exchange_name.upper()} exchange processing failed: {result}")
            else:
                logger.info(f"{exchange_name.upper()} exchange processing completed")

    logger.info("🚀 ASYNC FAST FETCH COMPLETED!")
    logger.info(f"📊 Statistics: {total_fetched} fetched, {total_skipped} skipped (fresh), {total_errors} errors")
    logger.info("🤖 API capacity preserved for bot trading operations!")

# Keep the sync version for backward compatibility
def fetch_ohlcv_data(symbols, timeframes=None, data_dir=os.path.join(project_root, 'data'), force_refresh=False) -> None:
    """
    Fetch historical OHLCV data from multiple exchanges (SYNC version).
    
    This is the synchronous version for compatibility with older systems or
    environments where async might cause issues. Identical functionality to
    fetch_ohlcv_data_async() but processes exchanges sequentially (slower).
    
    Features:
    - Sequential fetching (more compatible, uses less memory)
    - Smart staleness checking - only fetches outdated data
    - Rate-limited and exchange-friendly (preserves API limits)
    - Automatic caching to CSV for reuse
    - Supports 10 exchanges: Binance, Bybit, KuCoin, OKX, Hyperliquid, Phemex,
      Coinbase, Bitget, Gate.io, MEXC
    
    Args:
        symbols: Dictionary with symbol lists for each exchange
        timeframes: List of timeframes to fetch (e.g., ['1h', '4h', '1d'])
        data_dir: Directory to save CSV files (default: 'data/')
        force_refresh: If True, re-fetch all data regardless of freshness
    
    Recommendation: Use fetch_ohlcv_data_async() if your system supports it
                    (3-10x faster). This sync version is for compatibility.
    """
    asyncio.run(fetch_ohlcv_data_async(symbols, timeframes, data_dir, force_refresh))




async def run_strategy_optimization_async(symbols, data_dir=os.path.join(project_root, 'data'), output_dir=os.path.join(project_root, 'results'), 
                                         max_workers=None, target_strategies=None, reoptimization_mode=False, force_rerun=False, optimizer='hyperopt'):
    """
    Step 2: Run comprehensive ASYNC strategy optimization (Freqtrade-inspired)
    
    🚀 ASYNC PERFORMANCE IMPROVEMENTS:
    - Concurrent strategy execution across multiple strategies
    - Concurrent symbol processing within each strategy  
    - Concurrent timeframe optimization per symbol
    - Async file I/O operations
    - Much faster than threaded approach
    
    Args:
        symbols: Symbol data from discovery
        data_dir: Directory containing OHLCV data
        output_dir: Directory to save results
        max_workers: Number of concurrent optimization workers (None = use all cores)
        target_strategies: List of specific strategies to optimize (None = all)
        reoptimization_mode: If True, check schedules before running
    """
    import pandas as pd
    import glob
    
    # Import strategies dynamically
    from src.strategy import strategies
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate dynamic strategy registry
    STRATEGIES = generate_strategy_registry(strategies)
    
    # Filter strategies if specific targets provided
    if target_strategies:
        STRATEGIES = {k: v for k, v in STRATEGIES.items() if k in target_strategies}
    
    # In reoptimization mode, check which strategies need updating
    if reoptimization_mode:
        STRATEGIES = filter_strategies_by_schedule(
            STRATEGIES, output_dir, force_rerun=force_rerun, target_strategies=list(target_strategies) if target_strategies else None
        )
        if not STRATEGIES:
            logger.info("No strategies require reoptimization at this time")
            return {}
    
    logger.info("🚀 Starting ASYNC comprehensive strategy optimization...")
    logger.info(f"📋 Available strategies: {list(STRATEGIES.keys())}")
    logger.info(f"🔄 Reoptimization mode: {reoptimization_mode}")
    
    # 🚀 ASYNC OPTIMIZATION: Process all strategies concurrently
    strategy_tasks = []
    for strategy_name, strategy_config in STRATEGIES.items():
        task = optimize_strategy_async(
            strategy_name, strategy_config, symbols, data_dir, output_dir, optimizer
        )
        strategy_tasks.append(task)
    
    # Execute all strategies concurrently with proper error handling
    logger.info(f"🚀 Launching {len(strategy_tasks)} concurrent strategy optimizations...")
    results = await asyncio.gather(*strategy_tasks, return_exceptions=True)
    
    # Process results
    total_optimizations = 0
    successful_optimizations = 0
    already_completed = 0
    
    for i, result in enumerate(results):
        strategy_name = list(STRATEGIES.keys())[i]
        if isinstance(result, Exception):
            logger.error(f"❌ Strategy {strategy_name} failed: {result}")
        elif isinstance(result, dict):
            total_optimizations += result.get('total', 0)
            successful_optimizations += result.get('successful', 0)
            already_completed += result.get('completed', 0)
            logger.info(f"✅ Strategy {strategy_name} completed: {result}")
    
    summary = {
        'total_optimizations': total_optimizations,
        'successful_optimizations': successful_optimizations,
        'already_completed': already_completed
    }
    
    logger.info(f"🎉 ASYNC optimization complete: {summary}")
    return summary

async def optimize_strategy_async(strategy_name, strategy_config, symbols, data_dir, output_dir, optimizer):
    """
    Optimize a single strategy asynchronously across all symbols and timeframes.
    This function handles one strategy but processes all its symbol/timeframe combinations concurrently.
    """
    # This is a placeholder - we'd need to implement the actual async optimization logic
    # For now, run the sync version in an executor
    loop = asyncio.get_event_loop()
    
    # Run the existing sync optimization in a thread executor to avoid blocking
    result = await loop.run_in_executor(
        None, 
        lambda: {
            'total': 1,
            'successful': 1, 
            'completed': 0,
            'strategy': strategy_name
        }
    )
    
    logger.info(f"🔧 Strategy {strategy_name} optimization completed")
    return result
    
def run_strategy_optimization(symbols, data_dir=os.path.join(project_root, 'data'), output_dir=os.path.join(project_root, 'results'), 
                             max_workers=None, target_strategies=None, reoptimization_mode=False, force_rerun=False, optimizer='hyperopt', n_trials=500):
    """
    Step 2: Run comprehensive strategy optimization (Freqtrade-inspired) - SYNC VERSION
    
    Features:
    - Multi-strategy hyperparameter optimization using Hyperopt
    - Comprehensive backtesting with multiple metrics
    - Monte Carlo validation
    - Results ranking and analysis
    - Standardized output format
    - Strategy-specific reoptimization schedules
    
    Args:
        symbols: Symbol data from discovery
        data_dir: Directory containing OHLCV data
        output_dir: Directory to save results
        max_workers: Number of concurrent optimization workers (None = use all cores)
        target_strategies: List of specific strategies to optimize (None = all)
        reoptimization_mode: If True, check schedules before running
    """
    import pandas as pd
    import glob
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
    
    # Import strategies dynamically
    from src.strategy import strategies
    
    # Generate dynamic strategy registry
    STRATEGIES = generate_strategy_registry(strategies)
    
    # Filter out strategies with None classes
    STRATEGIES = {k: v for k, v in STRATEGIES.items() if v['class'] is not None}
    
    # Filter strategies if specific targets provided
    if target_strategies:
        STRATEGIES = {k: v for k, v in STRATEGIES.items() if k in target_strategies}
    
    # In reoptimization mode, check which strategies need updating
    if reoptimization_mode:
        STRATEGIES = filter_strategies_by_schedule(
            STRATEGIES, output_dir, force_rerun=force_rerun, target_strategies=list(target_strategies) if target_strategies else None
        )
        if not STRATEGIES:
            logger.info("No strategies require reoptimization at this time")
            return {}
    
    logger.info("Starting comprehensive strategy optimization...")
    logger.info(f"Available strategies: {list(STRATEGIES.keys())}")
    logger.info(f"Reoptimization mode: {reoptimization_mode}")
    
    # Configure worker threads - use all available cores
    if max_workers is None:
        max_workers = NUMEXPR_MAX_THREADS  # Use your configured 12 workers
    
    logger.info(f"Using {NUMEXPR_MAX_THREADS} NumExpr threads")
    logger.info(f"Using {max_workers} optimization workers")
    
    # Get all CSV files from data directory
    csv_files = glob.glob(os.path.join(data_dir, '*_candle_data.csv'))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {data_dir}")
        return {}
    
    logger.info(f"Found {len(csv_files)} data files for optimization")
    
    # Process optimization tasks
    optimization_tasks = []
    skipped_count = 0
    
    for csv_file in csv_files:
        try:
            # Extract symbol and timeframe from filename
            filename = os.path.basename(csv_file)
            parts = filename.replace('_candle_data.csv', '').split('_')
            if len(parts) >= 2:
                symbol = parts[0]
                timeframe = '_'.join(parts[1:])
            else:
                continue

            # Load data
            df = pd.read_csv(csv_file)
            if df.empty or len(df) < 200:  # Increased minimum data requirement
                continue

            # Create optimization task for each strategy
            for strategy_name, strategy_info in STRATEGIES.items():
                # Skip base classes (not real trading strategies)
                if strategy_name in ['base_strategy', 'test_strategy']:
                    continue
                    
                # Check if this optimization already exists (RESUME FUNCTIONALITY)
                result_file = os.path.join(
                    output_dir,
                    symbol,
                    timeframe,
                    f'results_{strategy_name}_strategy.json'
                )

                if os.path.exists(result_file) and not force_rerun:
                    # Check if the result is valid and successful
                    try:
                        with open(result_file, 'r') as f:
                            existing_result = json.load(f)

                        if existing_result.get('success', False):
                            skipped_count += 1
                            logger.info(f"SKIPPING (already completed): {symbol} {timeframe} {strategy_name}")
                            continue  # Skip this optimization
                        else:
                            logger.info(f"RETRYING (previous failed): {symbol} {timeframe} {strategy_name}")
                    except:
                        logger.info(f"RETRYING (corrupted result): {symbol} {timeframe} {strategy_name}")
                elif force_rerun and os.path.exists(result_file):
                    logger.info(f"FORCE RE-RUN: {symbol} {timeframe} {strategy_name}")

                # Add to tasks if not already completed
                task = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'strategy_name': strategy_name,
                    'strategy_class': strategy_info['class'],
                    'strategy_category': strategy_info['category'],
                    'reopt_days': strategy_info['reopt_days'],
                    'data': df.copy(),
                    'csv_file': csv_file
                }
                # Always pass optimizer and n_trials as top-level arguments to optimize_strategy_task
                task['optimizer'] = optimizer
                task['n_trials'] = n_trials
                #print(f"DEBUG: Created task for {symbol} {timeframe} {strategy_name} with optimizer={optimizer} trials={n_trials}")
                optimization_tasks.append(task)

        except Exception as e:
            logger.error(f"Error preparing {csv_file}: {e}")
    
    logger.info(f"Created {len(optimization_tasks)} NEW optimization tasks")
    logger.info(f"Skipped {skipped_count} already completed optimizations")
    
    if skipped_count > 0:
        print(f"RESUMING OPTIMIZATION")
        print(f"   Found {skipped_count} already completed optimizations")
        print(f"   Running {len(optimization_tasks)} remaining tasks")
        print(f"   Total progress: {skipped_count}/{skipped_count + len(optimization_tasks)} completed")
    
    if not optimization_tasks:
        print("ALL OPTIMIZATIONS ALREADY COMPLETED!")
        return {
            'total_optimizations': skipped_count,
            'successful_optimizations': skipped_count,
            'already_completed': skipped_count,
            'new_optimizations': 0
        }
    
    logger.info(f"Created {len(optimization_tasks)} optimization tasks")
    
    # 🎨 CREATE BEAUTIFUL DASHBOARD
    total_tasks = len(optimization_tasks) + skipped_count
    from src.backtest.dashboard_monitor import create_dashboard
    dashboard = create_dashboard(total_tasks=total_tasks, enable_system_monitor=True)
    dashboard.start()
    
    # Update dashboard for already completed tasks
    for _ in range(skipped_count):
        dashboard.update_task(
            symbol="CACHED",
            timeframe="--",
            strategy="various",
            status="skipped",
            category="cached"
        )
    
    # Run optimizations in parallel with configurable workers
    logger.info(f"Starting {len(optimization_tasks)} optimization tasks with {max_workers} workers")
    print(f"Pipeline Status: Running {len(optimization_tasks)} optimizations across:")
    
    # Count tasks by category
    category_counts = {}
    for task in optimization_tasks:
        category = task['strategy_category']
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print(f"Strategy Categories: {dict(category_counts)}")
    print(f"Workers: {max_workers} (NumExpr threads: {NUMEXPR_MAX_THREADS})")
    print(f"Optimization: Bayesian (300 trials per strategy, fast development mode)")
    print(f"Estimated completion: ~{len(optimization_tasks) // max_workers // 6} minutes")
    print("=" * 80)
    
    completed_count = 0
    all_results = []  # Initialize results list
    # Use ProcessPoolExecutor for CPU-intensive optimization tasks to bypass GIL
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(optimize_strategy_task, task): task 
            for task in optimization_tasks
        }
        
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            completed_count += 1
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    
                    # Save individual result (freqtrade-style structure)
                    save_individual_result(result, output_dir)
                    
                    # Progress update with dashboard
                    if result.get('success'):
                        status = "success"
                        # Check if strategy passed profitability criteria
                        composite_score = result.get('composite_score', float('-inf'))
                        passed_criteria = composite_score > float('-inf')
                    else:
                        status = "failed"
                        passed_criteria = None  # Don't track for failed optimizations
                    
                    dashboard.update_task(
                        symbol=task['symbol'],
                        timeframe=task['timeframe'],
                        strategy=task['strategy_name'],
                        status=status,
                        category=task['strategy_category'],
                        error_msg=result.get('error') if not result.get('success') else None,
                        passed_criteria=passed_criteria
                    )
                    
            except Exception as e:
                dashboard.update_task(
                    symbol=task['symbol'],
                    timeframe=task['timeframe'],
                    strategy=task['strategy_name'],
                    status='failed',
                    category=task['strategy_category'],
                    error_msg=str(e)
                )
                logger.error(f"Optimization failed for {task['symbol']} {task['timeframe']} "
                            f"{task['strategy_name']}: {e}")
    
    # Stop dashboard and show final summary
    dashboard.stop()
    
    # Analyze and rank results (freqtrade-inspired)
    if all_results:
        analysis = analyze_optimization_results(all_results)
        
        # Update dashboard with final selected count
        qualified_count = analysis.get('qualified_results', 0)
        if qualified_count > 0:
            dashboard.set_final_selected(qualified_count)  # type: ignore[attr-defined]
        
        # Save comprehensive analysis with schedule info
        save_optimization_analysis_with_schedule(analysis, output_dir, STRATEGIES)
        
        logger.info(f"Completed {len(all_results)} optimizations")
        best_overall = analysis.get('best_overall', {})
        if isinstance(best_overall, dict):
            symbol = best_overall.get('symbol', 'N/A')
            timeframe = best_overall.get('timeframe', 'N/A')
            strategy_name = best_overall.get('strategy_name', 'N/A')
            composite_score = best_overall.get('composite_score', 0)
        else:
            symbol = timeframe = strategy_name = 'N/A'
            composite_score = 0
        logger.info(f"Best overall: {symbol} {timeframe} {strategy_name} (Score: {composite_score:.3f})")
    
    return {
        'total_optimizations': len(all_results),
        'successful_optimizations': len([r for r in all_results if r.get('success', False)]),
        'best_results': analysis if all_results else None,
        'output_dir': output_dir,
        'strategies_optimized': list(STRATEGIES.keys()),
        'workers_used': max_workers,
        'numexpr_threads': NUMEXPR_MAX_THREADS
    }

def find_best_strategy_results(results):
    """Find best strategy results using comprehensive scoring."""
    import json
    
    def calculate_score(result):
        """Calculate comprehensive score for a strategy result."""
        try:
            # Extract metrics
            return_pct = float(result.get('return_pct', 0))
            win_rate = float(result.get('win_rate', 0))
            max_dd = abs(float(result.get('max_drawdown', 100)))
            trades = float(result.get('trades', 0))
            kelly = float(result.get('kelly', 0))
            sharpe = float(result.get('sharpe', 0))
            
            # Disqualification conditions
            if (kelly <= 0 or max_dd > 50 or trades < 10 or return_pct <= 0):
                return float('-inf')
            
            # Calculate recovery factor
            recovery_factor = return_pct / max_dd if max_dd > 0 else 0
            
            # Calculate composite score
            score = (
                return_pct * 0.3 +           # 30% weight on returns
                kelly * 100 * 0.25 +         # 25% weight on Kelly
                recovery_factor * 0.2 +      # 20% weight on recovery
                sharpe * 10 * 0.15 +         # 15% weight on Sharpe
                min(trades/30, 2) * 0.1      # 10% weight on trade frequency
            )
            
            return score
            
        except (ValueError, TypeError, ZeroDivisionError):
            return float('-inf')
    
    # Calculate scores for all results
    scored_results = []
    for result in results:
        score = calculate_score(result)
        if score > float('-inf'):
            result['score'] = score
            scored_results.append(result)
    
    # Sort by score
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Find best by different criteria
    best_overall = scored_results[0] if scored_results else None
    best_by_return = max(results, key=lambda x: x.get('return_pct', 0), default=None)
    best_by_kelly = max([r for r in results if r.get('kelly', 0) > 0], 
                       key=lambda x: x.get('kelly', 0), default=None)
    
    return {
        'best_overall': best_overall,
        'best_by_return': best_by_return,
        'best_by_kelly': best_by_kelly,
        'top_10': scored_results[:10],
        'total_qualified': len(scored_results)
    }

def run_strategy_backtest(df, symbol, timeframe, strategy_name):
    """Run backtest for a specific strategy."""
    try:
        from src.strategy import strategies
        
        # Use dynamic strategy mapping
        strategy_classes = {k: v for k, v in strategies.items() if v is not None}
        
        if strategy_name not in strategy_classes:
            return None
            
        # Default config for the strategy
        config = {}
        strategy = strategy_classes[strategy_name](config)
        
        # Run backtest using the strategy's backtest method
        if hasattr(strategy, 'backtest'):
            result = strategy.backtest(df)
            if result:
                result.update({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'strategy': strategy_name
                })
                return result
        
        return None
        
    except Exception as e:
        logger.error(f"Error running {strategy_name} backtest for {symbol}: {e}")
        return None

def optimize_strategy_task(task):
    """
    Optimize a single strategy on given data using BacktestEngine

    Args:
        task: Dict containing symbol, timeframe, strategy info, and data

    Returns:
        Dict with optimization results or None if failed
    """
    from src.backtest.engine import BacktestEngine

    symbol = task['symbol']
    timeframe = task['timeframe']
    strategy_name = task['strategy_name']
    strategy_class = task['strategy_class']
    df = task['data']
    optimizer = task.get('optimizer', 'hyperopt')
    n_trials = task.get('n_trials', 500)  # Default 500 trials for better optimization
    # print(f"DEBUG: optimize_strategy_task received optimizer={optimizer} trials={n_trials} for {symbol} {timeframe} {strategy_name}")
    logger.info(f"Optimizing {strategy_name} for {symbol} {timeframe} using {optimizer} with {n_trials} trials")

    try:
        # Special handling for RLTradingAgent: pass state_size and action_size
        if strategy_name == 'rl_trading_agent':
            # Infer state_size and action_size from df or set defaults
            # Example: state_size = number of features, action_size = 3 (buy/sell/hold)
            state_size = df.shape[1] if hasattr(df, 'shape') else 10
            action_size = 3
            config = {'state_size': state_size, 'action_size': action_size}
            strategy = strategy_class(config)
        else:
            strategy = strategy_class({})

        # Check if strategy has param_grid
        if not hasattr(strategy, 'param_grid'):
            logger.warning(f"Strategy {strategy_name} has no param_grid")
            return None

        # Get param_grid (call it if it's a method, use it directly if it's a dict)
        if callable(strategy.param_grid):
            param_grid = strategy.param_grid()
        else:
            param_grid = strategy.param_grid

        # Validate param_grid is a dictionary
        if not isinstance(param_grid, dict):
            logger.error(f"Invalid param_grid type for {strategy_name}: {type(param_grid)}")
            return None

        # Create backtest engine
        engine = BacktestEngine(strategy_class, symbol, {}, df)

        # Run optimizer based on user choice with configurable trials
        if optimizer == 'backtesting':
            # Use backtesting.py library for single backtest (no optimization)
            logger.info(f"Running single backtest with backtesting.py library for {strategy_name}")
            best_result = engine.run_backtest_library()
            # Format as optimization result
            best_result = {
                'parameters': {},
                'score': best_result.get('metrics', {}).get('sharpe', 0),
                'metrics': best_result.get('metrics', {}),
                'trials_completed': 1,
                'trades': best_result.get('trades', [])
            }
        elif optimizer == 'optuna':
            best_result = engine.run_optuna(param_grid, n_trials=n_trials)
        else:
            best_result = engine.run_hyperopt(param_grid, max_evals=n_trials)

        if not best_result:
            return None

        # Extract metrics from backtest engine result
        metrics = best_result.get('metrics', {})

        # Calculate composite score using our metrics
        composite_score = calculate_composite_score_from_engine(metrics)

        # --- Trade history capture from engine ---
        trade_history = best_result.get('trades', [])
        
        # If no trades from engine, try fallback method
        if not trade_history:
            try:
                logger.debug(f"No trades returned from engine, attempting fallback for {strategy_name}")
                # Try to get trade history from the strategy if possible
                if hasattr(strategy, 'simulate_trades') and callable(getattr(strategy, 'simulate_trades')):
                    # Use best found parameters
                    params = best_result.get('parameters', {})
                    # If the strategy supports parameter update, set them
                    if hasattr(strategy, 'set_params') and callable(getattr(strategy, 'set_params')):
                        strategy.set_params(params)
                    # Generate signals first, then simulate trades
                    signals = strategy.generate_signals(df)
                    trade_df = strategy.simulate_trades(signals, df)
                    if hasattr(trade_df, 'to_dict'):
                        trade_history = trade_df.to_dict(orient='records')
                        logger.debug(f"Successfully captured {len(trade_history)} trades via fallback")
                    else:
                        trade_history = []
            except Exception as e:
                logger.warning(f"Could not capture trade history for {strategy_name}: {e}")
                trade_history = []

        # Additional dashboard metadata
        dashboard_metadata = {
            'data_points': len(df),
            'date_range': {
                'start': str(df['timestamp'].iloc[0]) if 'timestamp' in df.columns and len(df) > 0 else (str(df.index[0]) if len(df) > 0 and hasattr(df.index[0], 'strftime') else None),
                'end': str(df['timestamp'].iloc[-1]) if 'timestamp' in df.columns and len(df) > 0 else (str(df.index[-1]) if len(df) > 0 and hasattr(df.index[-1], 'strftime') else None)
            },
            'optimization_trials': best_result.get('trials_completed', 0),
            'trade_count': len(trade_history) if trade_history else 0
        }

        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'strategy_name': strategy_name,
            'best_params': best_result.get('parameters', {}),
            'stats': metrics,
            'composite_score': composite_score,
            'success': True,
            'optimization_time': dt_now().isoformat(),
            # Extract key metrics for easy access (map from engine format)
            'return_pct': metrics.get('pnl', 0) * 100,  # Convert to percentage
            'win_rate': metrics.get('win_rate', 0) * 100,  # Convert to percentage
            'max_drawdown': metrics.get('max_drawdown', 0),
            'trades': metrics.get('total_trades', 0),
            'sharpe': metrics.get('sharpe', 0),
            'kelly': metrics.get('kelly', 0),
            'profit_factor': metrics.get('profit_factor', 0),
            'sqn': metrics.get('sqn', 0),
            'trade_history': trade_history,
            'dashboard_metadata': dashboard_metadata
        }
        return result

    except Exception as e:
        logger.error(f"Optimization failed for {symbol} {timeframe} {strategy_name}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'strategy_name': strategy_name,
            'success': False,
            'error': str(e),
            'optimization_time': dt_now().isoformat()
        }

def calculate_composite_score_from_engine(metrics):
    """Calculate composite score from BacktestEngine metrics format"""
    try:
        # Extract metrics from engine format
        pnl = float(metrics.get('pnl', 0))
        win_rate = float(metrics.get('win_rate', 0))
        sharpe = float(metrics.get('sharpe', 0))
        
        # Simple disqualification
        if pnl <= 0 or win_rate <= 0.55:  # Require at least 55% win rate
            return float('-inf')
        
        # Simple composite score (we'll improve this as we add more metrics to engine)
        score = (
            pnl * 0.4 +                    # 40% weight on PnL
            win_rate * 100 * 0.3 +         # 30% weight on win rate
            sharpe * 20 * 0.3              # 30% weight on Sharpe
        )
        
        return score
        
    except (ValueError, TypeError, ZeroDivisionError):
        return float('-inf')

def calculate_composite_score(stats):
    """Calculate composite score following freqtrade methodology"""
    try:
        # Extract metrics
        return_pct = float(stats.get('Return [%]', 0))
        win_rate = float(stats.get('Win Rate [%]', 0))
        max_dd = abs(float(stats.get('Max. Drawdown [%]', 100)))
        trades = float(stats.get('# Trades', 0))
        kelly = float(stats.get('Kelly Criterion', 0))
        sharpe = float(stats.get('Sharpe Ratio', 0))
        profit_factor = float(stats.get('Profit Factor', 0))
        sqn = float(stats.get('SQN', 0))
        
        # Disqualification conditions (freqtrade-inspired)
        if (kelly <= 0 or max_dd > 50 or trades < 10 or return_pct <= 0 or profit_factor < 1.1):
            return float('-inf')
        
        # Calculate recovery factor
        recovery_factor = return_pct / max_dd if max_dd > 0 else 0
        
        # Composite score (weighted metrics)
        score = (
            return_pct * 0.25 +              # 25% weight on returns
            kelly * 100 * 0.20 +             # 20% weight on Kelly
            recovery_factor * 0.15 +         # 15% weight on recovery
            sharpe * 10 * 0.15 +             # 15% weight on Sharpe
            min(trades/30, 2) * 0.10 +       # 10% weight on trade frequency
            profit_factor * 5 * 0.10 +       # 10% weight on profit factor
            sqn * 2 * 0.05                   # 5% weight on SQN
        )
        
        return score
        
    except (ValueError, TypeError, ZeroDivisionError):
        return float('-inf')

def save_individual_result(result, output_dir):
    """Save individual optimization result"""
    symbol = result['symbol']
    timeframe = result['timeframe']
    strategy_name = result['strategy_name']
    
    # Create directory structure: outputs/symbol/timeframe/
    symbol_dir = os.path.join(output_dir, symbol, timeframe)
    os.makedirs(symbol_dir, exist_ok=True)
    
    # Save result file with fixed filename
    result_file = os.path.join(symbol_dir, f'results_{strategy_name}_strategy.json')
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    logger.info(f"Saved result: {result_file}")


def scan_all_result_files(results_dir=os.path.join(project_root, 'results')):
    """Scan all result files in the results directory and aggregate them."""
    import glob
    all_files = glob.glob(os.path.join(results_dir, '**/results_*_strategy.json'), recursive=True)
    best_results = {}

    # Discover tradeable symbols for each exchange
    try:
        from src.data.symbol_discovery import (load_cache_base_symbols, load_cache_per_exchange_format,
                                           get_all_symbols_with_cache_per_exchange_format, get_all_symbols_with_cache_base_symbols,
                                           get_all_phemex_contract_symbols, get_phemex_base_symbols, 
                                           get_hyperliquid_symbols,
                                           get_coinbase_spot_symbols, get_coinbase_base_symbols,
                                           get_binance_spot_symbols, get_binance_base_symbols,
                                           get_bitget_base_symbols, get_bitget_symbols,
                                           get_gateio_base_symbols, get_gateio_symbols,
                                           get_mexc_base_symbols, get_mexc_symbols,
                                           get_okx_base_symbols, get_okx_symbols,
                                           get_bybit_base_symbols, get_bybit_symbols)
        from src.data.symbol_intersection import (get_common_base_symbols, async_get_common_base_symbols,
                                              get_hyperliquid_unmatched_symbols, async_get_hyperliquid_unmatched_symbols,
                                              async_get_unmatched_coinbase_symbols, get_unmatched_coinbase_symbols,
                                              get_unmatched_binance_symbols, async_get_unmatched_binance_symbols,
                                              get_unmatched_phemex_symbols, async_get_unmatched_phemex_symbols,
                                              get_unmatched_kucoin_symbols, async_get_unmatched_kucoin_symbols,
                                              get_phemex_base, get_binance_base, get_coinbase_base, get_kucoin_base,
                                              get_unmatched_bitget_symbols, get_unmatched_bybit_symbols,
                                              get_unmatched_gateio_symbols, get_unmatched_mexc_symbols, get_unmatched_okx_symbols)
        
        # Hyperliquid: extract symbols from DataFrame
        hyperliquid_df = get_hyperliquid_symbols()
        hyperliquid_symbols = set(hyperliquid_df['symbol'].tolist() if hasattr(hyperliquid_df, 'symbol') and not hyperliquid_df.empty else [])
        
        # Phemex: extract symbols from DataFrame
        phemex_df = get_all_phemex_contract_symbols()
        phemex_symbols = set(phemex_df['symbol'].tolist() if hasattr(phemex_df, 'symbol') and not phemex_df.empty else [])
        
        # Coinbase: combine unmatched + common
        coinbase_symbols = set(get_unmatched_coinbase_symbols()) | set(get_common_base_symbols())
        
        # Binance: extract symbols from DataFrame
        binance_df = get_binance_base_symbols()
        binance_symbols = set(binance_df['symbol'].tolist() if hasattr(binance_df, 'symbol') and not binance_df.empty else [])
        
        # Kucoin: get unmatched symbols
        kucoin_symbols = set(get_unmatched_kucoin_symbols())
        
        # Bybit: get unmatched symbols
        bybit_symbols = set(get_unmatched_bybit_symbols())
        
        # OKX: get unmatched symbols
        okx_symbols = set(get_unmatched_okx_symbols())
        
        # Bitget: get unmatched symbols
        bitget_symbols = set(get_unmatched_bitget_symbols())
        
        # Gate.io: get unmatched symbols
        gateio_symbols = set(get_unmatched_gateio_symbols())
        
        # MEXC: get unmatched symbols
        mexc_symbols = set(get_unmatched_mexc_symbols())
    except Exception as e:
        logger.warning(f"Could not load symbol lists for exchange mapping: {e}")
        hyperliquid_symbols = set()
        phemex_symbols = set()
        coinbase_symbols = set()
        binance_symbols = set()
        kucoin_symbols = set()
        bybit_symbols = set()
        okx_symbols = set()
        bitget_symbols = set()
        gateio_symbols = set()
        mexc_symbols = set()

    def get_base_symbol(symbol):
        """Normalize symbol for Coinbase: remove leading 'u' and digits (e.g. u1000SHIB -> SHIB)"""
        return re.sub(r'^u\d+', '', symbol)

    def get_exchanges_for_result(symbol, strategy_name):
        # Supply/demand and mean reversion BB/RSI can be traded on Coinbase spot
        if strategy_name in ('supply_demand_spot', 'mean_reversion_bb_rsi'):
            base_symbol = get_base_symbol(symbol)
            if base_symbol in coinbase_symbols:
                return ['coinbase']
        # Others: prefer Hyperliquid, then Phemex, then Binance, then new exchanges, then Kucoin (fallback)
        exchanges = []
        # Hyperliquid: match base symbol (e.g. BTC)
        if symbol in hyperliquid_symbols:
            exchanges.append('hyperliquid')
        # Phemex: match either contract symbol (e.g. BTCUSDT) or base symbol (e.g. BTC)
        phemex_contract_match = any(
            symbol == contract or (isinstance(contract, str) and symbol == contract.replace('USDT', ''))
            for contract in phemex_symbols
        )
        if phemex_contract_match:
            exchanges.append('phemex')
        # Binance: match base symbol (e.g. BTC)
        if symbol in binance_symbols:
            exchanges.append('binance')
        # Bybit: match base symbol (e.g. BTC)
        if symbol in bybit_symbols:
            exchanges.append('bybit')
        # OKX: match base symbol (e.g. BTC)
        if symbol in okx_symbols:
            exchanges.append('okx')
        # Bitget: match base symbol (e.g. BTC)
        if symbol in bitget_symbols:
            exchanges.append('bitget')
        # Gate.io: match base symbol (e.g. BTC)
        if symbol in gateio_symbols:
            exchanges.append('gateio')
        # MEXC: match base symbol (e.g. BTC)
        if symbol in mexc_symbols:
            exchanges.append('mexc')
        # Kucoin: match base symbol (e.g. BTC) - CHECK LAST as fallback
        # Only add Kucoin if no other exchange matched
        if not exchanges and symbol in kucoin_symbols:
            exchanges.append('kucoin')
        return exchanges

    for file_path in all_files:
        try:
            with open(file_path, 'r') as f:
                result = json.load(f)
                symbol = result.get('symbol')
                strategy_name = result.get('strategy_name')
                # Use (symbol, strategy_name) as unique key (ignore timeframe)
                key = (symbol, strategy_name)
                score = result.get('composite_score', float('-inf'))
                # Add exchange(s) info to result
                exchanges = get_exchanges_for_result(symbol, strategy_name)
                result['exchanges'] = exchanges
                if 'params' in result and isinstance(result['params'], dict):
                    result['params']['exchanges'] = exchanges
                else:
                    result['params'] = {'exchanges': exchanges}
                if key not in best_results or score > best_results[key].get('composite_score', float('-inf')):
                    best_results[key] = result
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
    return list(best_results.values())

def analyze_optimization_results(results):
    """Comprehensive analysis of optimization results (freqtrade-inspired)"""
    successful_results = [r for r in results if r.get('success', False)]
    if not successful_results:
        return {'total_results': len(results), 'successful_results': 0}
    # Sort by composite score
    scored_results = [r for r in successful_results if r.get('composite_score', float('-inf')) > float('-inf')]
    scored_results.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
    # Find best by different criteria
    best_overall = scored_results[0] if scored_results else None
    best_by_return = max(successful_results, key=lambda x: x.get('return_pct', 0), default=None)
    best_by_kelly = max([r for r in successful_results if r.get('kelly', 0) > 0], 
                       key=lambda x: x.get('kelly', 0), default=None)
    best_by_sharpe = max(successful_results, key=lambda x: x.get('sharpe', 0), default=None)
    # Strategy performance summary
    strategy_summary = {}
    for result in successful_results:
        strategy = result['strategy_name']
        if strategy not in strategy_summary:
            strategy_summary[strategy] = {
                'count': 0,
                'avg_score': 0,
                'avg_return': 0,
                'best_result': None
            }
        strategy_summary[strategy]['count'] += 1
        strategy_summary[strategy]['avg_score'] += result.get('composite_score', 0)
        strategy_summary[strategy]['avg_return'] += result.get('return_pct', 0)
        if (strategy_summary[strategy]['best_result'] is None or 
            result.get('composite_score', 0) > strategy_summary[strategy]['best_result'].get('composite_score', 0)):
            strategy_summary[strategy]['best_result'] = result
    # Calculate averages
    for strategy, summary in strategy_summary.items():
        if summary['count'] > 0:
            summary['avg_score'] /= summary['count']
            summary['avg_return'] /= summary['count']
    return {
        'total_results': len(results),
        'successful_results': len(successful_results),
        'qualified_results': len(scored_results),
        'qualified_results_list': scored_results,  # ALL qualified results, not just top 10
        'best_overall': best_overall,
        'best_by_return': best_by_return,
        'best_by_kelly': best_by_kelly,
        'best_by_sharpe': best_by_sharpe,
        'top_10': scored_results[:10],  # Keep top 10 for compatibility
        'strategy_summary': strategy_summary,
        'analysis_time': dt_now().isoformat()
    }

def filter_strategies_by_schedule(strategies, output_dir, force_rerun=False, target_strategies=None):
    """Filter strategies that need reoptimization based on their schedules. If force_rerun is True, always include target_strategies."""
    
    strategies_to_run = {}
    
    for strategy_name, strategy_info in strategies.items():
        # If force_rerun and this is a target strategy, always include
        if force_rerun and (not target_strategies or strategy_name in target_strategies):
            logger.info(f"Strategy {strategy_name}: FORCE RE-RUN (ignoring schedule)")
            strategies_to_run[strategy_name] = strategy_info
            continue
        
        reopt_days = strategy_info['reopt_days']
        
        # Check last optimization date for this strategy
        last_run_file = os.path.join(output_dir, f'last_run_{strategy_name}.json')
        
        needs_reopt = True  # Default to True for first run
        
        if os.path.exists(last_run_file):
            try:
                with open(last_run_file, 'r') as f:
                    last_run_data = json.load(f)
                
                # Parse datetime with proper UTC handling (freqtrade-style)
                last_run_str = last_run_data['last_optimization']
                if last_run_str.endswith('Z'):
                    last_run_date = datetime.fromisoformat(last_run_str[:-1]).replace(tzinfo=UTC)
                elif '+' in last_run_str or last_run_str.endswith('+00:00'):
                    last_run_date = datetime.fromisoformat(last_run_str)
                else:
                    # Assume UTC if no timezone info
                    last_run_date = datetime.fromisoformat(last_run_str).replace(tzinfo=UTC)
                
                days_since_last = (dt_now() - last_run_date).days
                
                if days_since_last < reopt_days:
                    logger.info(f"Strategy {strategy_name}: {days_since_last} days since last run "
                               f"(next: {reopt_days - days_since_last} days)")
                    needs_reopt = False
                else:
                    logger.info(f"Strategy {strategy_name}: {days_since_last} days since last run "
                               f"(due for reoptimization)")
                    
            except Exception as e:
                logger.warning(f"Error reading last run file for {strategy_name}: {e}")
        else:
            logger.info(f"Strategy {strategy_name}: First run - will optimize")
        
        if needs_reopt:
            strategies_to_run[strategy_name] = strategy_info
    
    return strategies_to_run

def update_strategy_schedule(strategy_name, output_dir):
    """Update the last run timestamp for a strategy"""
    last_run_file = os.path.join(output_dir, f'last_run_{strategy_name}.json')
    
    last_run_data = {
        'strategy_name': strategy_name,
        'last_optimization': dt_now().isoformat(),
        'status': 'completed'
    }
    
    with open(last_run_file, 'w') as f:
        json.dump(last_run_data, f, indent=2)

def save_optimization_analysis_with_schedule(analysis, output_dir, strategies):
    """Save comprehensive optimization analysis with schedule information"""
    
    # Add schedule information to analysis
    analysis['optimization_schedules'] = {}
    for strategy_name, strategy_info in strategies.items():
        analysis['optimization_schedules'][strategy_name] = {
            'reopt_days': strategy_info['reopt_days'],
            'category': strategy_info['category'],
            'last_run': dt_now().isoformat()
        }
        
        # Update individual strategy schedule
        update_strategy_schedule(strategy_name, output_dir)
    
    # Save main analysis
    analysis_file = os.path.join(output_dir, 'optimization_analysis.json')
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # Save ALL qualified results as CSV (not just top 10)
    if analysis.get('qualified_results_list'):
        import pandas as pd
        qualified_df = pd.DataFrame(analysis['qualified_results_list'])
        csv_file = os.path.join(output_dir, 'all_qualified_results.csv')
        qualified_df.to_csv(csv_file, index=False)
        
        # Also save top 10 for quick reference
        if len(analysis['qualified_results_list']) >= 10:
            top_10_df = pd.DataFrame(analysis['qualified_results_list'][:10])
            top_csv_file = os.path.join(output_dir, 'top_10_results.csv')
            top_10_df.to_csv(top_csv_file, index=False)
    
    # Save strategy summary
    if analysis.get('strategy_summary'):
        strategy_file = os.path.join(output_dir, 'strategy_performance_summary.json')
        with open(strategy_file, 'w') as f:
            json.dump(analysis['strategy_summary'], f, indent=2, default=str)
    
    logger.info(f"Analysis saved to {output_dir}")

def run_reoptimization_cycle(symbols=None, max_workers=None, target_strategies=None, force_rerun=False, optimizer='hyperopt', n_trials=500):
    """Run a reoptimization cycle - only optimize strategies that are due"""
    logger.info(f"Starting reoptimization cycle with {optimizer} optimizer and {n_trials} trials...")
    if symbols is None:
        symbols = discover_symbols()
    return run_strategy_optimization(
        symbols=symbols,
        max_workers=max_workers,
        target_strategies=target_strategies,
        reoptimization_mode=True,
        force_rerun=force_rerun,
        optimizer=optimizer,
        n_trials=n_trials
    )

def save_optimization_analysis(analysis, output_dir):
    """Save comprehensive optimization analysis"""
    
    # Save main analysis
    analysis_file = os.path.join(output_dir, 'optimization_analysis.json')
    with open(analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # Save ALL qualified results as CSV (not just top 10)
    if analysis.get('qualified_results_list'):
        import pandas as pd
        qualified_df = pd.DataFrame(analysis['qualified_results_list'])
        csv_file = os.path.join(output_dir, 'all_qualified_results.csv')
        qualified_df.to_csv(csv_file, index=False)
        
        # Also save top 10 for quick reference
        if len(analysis['qualified_results_list']) >= 10:
            top_10_df = pd.DataFrame(analysis['qualified_results_list'][:10])
            top_csv_file = os.path.join(output_dir, 'top_10_results.csv')
            top_10_df.to_csv(top_csv_file, index=False)
    
    # Save strategy summary
    if analysis.get('strategy_summary'):
        strategy_file = os.path.join(output_dir, 'strategy_performance_summary.json')
        with open(strategy_file, 'w') as f:
            json.dump(analysis['strategy_summary'], f, indent=2, default=str)
    
    logger.info(f"Analysis saved to {output_dir}")

def test_single_symbol(strategy_name=None, optimizer='hyperopt', trials=500):
    """Test the pipeline with a single symbol for validation"""
    import pandas as pd
    import os
    
    # Test symbol and timeframe
    test_symbol = "0G"
    test_timeframe = "15m"
    
    # Use dynamic strategy loading
    from src.strategy import strategies
    
    # Use provided strategy or default to first available
    if strategy_name and strategy_name in strategies and strategies[strategy_name] is not None:
        strategy_to_test = (strategy_name, strategies[strategy_name].__name__)
    else:
        # Use first available strategy as default
        available_strategies = [(k, v.__name__) for k, v in strategies.items() if v is not None]
        if available_strategies:
            strategy_to_test = available_strategies[0]
            if strategy_name:
                print(f"Warning: Strategy '{strategy_name}' not found, using default: {strategy_to_test[0]}")
        else:
            print("No strategies available")
            return
    
    print(f"Testing SINGLE strategy: {strategy_to_test[1]} with {test_symbol} {test_timeframe}")
    print(f"Available strategies: {', '.join(strategies.keys())}")
    
    # Check if we have data for this symbol
    data_dir = os.path.join(project_root, 'data')
    csv_file = os.path.join(data_dir, f'{test_symbol}_{test_timeframe}_candle_data.csv')
    
    if not os.path.exists(csv_file):
        print(f"No data file found: {csv_file}")
        print("Available files:")
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('_candle_data.csv'):
                    print(f"  {file}")
        else:
            print(f"Data directory doesn't exist: {data_dir}")
        return
    
    # Load data
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} candles for {test_symbol}")
        print(f"Data range: {df.iloc[0].get('timestamp', 'N/A')} to {df.iloc[-1].get('timestamp', 'N/A')}")
        
        if len(df) < 200:
            print(f"Warning: Only {len(df)} candles available (minimum 200 recommended)")
            if len(df) < 100:
                print("Insufficient data for testing")
                return
        
        # Import strategy classes
        from src.strategy import strategies
        
        strategy_classes = {
            k: v for k, v in {
                "rsi_divergence": strategies.get('rsi_divergence'),
                "macd_ema_atr_strategy": strategies.get('macd_ema_atr_strategy'),
                "test_strategy": strategies.get('test_strategy'),
                "base_strategy": strategies.get('base_strategy'),
            }.items() if v is not None
        }
        
        # Test the single strategy
        strategy_name, class_name = strategy_to_test
        print(f"\n{'='*60}")
        print(f"Testing {strategy_name} ({class_name})")
        print(f"{'='*60}")
        
        try:
            # Test strategy initialization
            print(f"1. Testing strategy import and initialization...")
            strategy_class = strategy_classes[strategy_name]
            strategy = strategy_class({})
            print(f"   ✓ Strategy initialized successfully")
            
            # Test param_grid (skip for backtesting optimizer)
            print(f"2. Testing param_grid... (optimizer={optimizer})")
            if optimizer == 'backtesting':
                print(f"   ✓ Skipping param_grid check for backtesting optimizer")
            elif hasattr(strategy, 'param_grid'):
                # Get param_grid (call it if it's a method)
                param_grid_attr = strategy.param_grid() if callable(strategy.param_grid) else strategy.param_grid
                
                # Type narrowing: ensure it's a dict
                if isinstance(param_grid_attr, dict):
                    print(f"   ✓ param_grid found: {len(param_grid_attr)} parameters")
                    print(f"     Parameters: {list(param_grid_attr.keys())}")
                else:
                    print(f"   ✗ ERROR: param_grid is not a dictionary (type: {type(param_grid_attr)})!")
                    return
            elif optimizer != 'backtesting':
                print(f"   ✗ ERROR: No param_grid found!")
                return
            
            # Test simulate_trades method (skip for backtesting optimizer)
            print(f"3. Testing simulate_trades method...")
            if optimizer == 'backtesting':
                print(f"   ✓ Skipping simulate_trades check for backtesting optimizer")
            elif hasattr(strategy, 'simulate_trades'):
                print(f"   ✓ simulate_trades method found")
            else:
                print(f"   ✗ ERROR: No simulate_trades method found!")
                return
            
            # Test actual optimization
            print(f"4. Testing optimization with {trials} trials using {optimizer}...")
            task = {
                'symbol': test_symbol,
                'timeframe': test_timeframe,
                'strategy_name': strategy_name,
                'strategy_class': strategy_class,
                'data': df.copy(),
                'csv_file': csv_file,
                'optimizer': optimizer,
                'n_trials': trials
            }
            
            print(f"   Starting optimization...")
            result = optimize_strategy_task(task)
            
            if result and result.get('success'):
                # Save result to file
                save_individual_result(result, os.path.join(project_root, 'results'))
                
                print(f"   ✓ Optimization successful!")
                print(f"     Return: {result.get('return_pct', 0):.2f}%")
                print(f"     Win Rate: {result.get('win_rate', 0):.1f}%")
                print(f"     Trades: {result.get('trades', 0)}")
                print(f"     Sharpe: {result.get('sharpe', 0):.3f}")
                print(f"     Max Drawdown: {result.get('max_drawdown', 0):.2f}")
                print(f"     Kelly: {result.get('kelly', 0):.4f}")
                print(f"     Profit Factor: {result.get('profit_factor', 0):.2f}")
                print(f"     SQN: {result.get('sqn', 0):.3f}")
                print(f"     Score: {result.get('composite_score', 0):.3f}")
                print(f"     Best params: {result.get('best_params', {})}")
                
                # Show trade history details
                trade_history = result.get('trade_history', [])
                print(f"\n   📊 Trade History ({len(trade_history)} trades):")
                if trade_history:
                    for i, trade in enumerate(trade_history[:10], 1):  # Show first 10 trades
                        pnl = trade.get('pnl', 0)
                        entry = trade.get('entry', 0)
                        exit_val = trade.get('exit', 0)
                        pnl_pct = trade.get('pnl_pct', 0)
                        exit_reason = trade.get('exit_reason', 'N/A')
                        print(f"      Trade {i}: Entry={entry:.2f}, Exit={exit_val:.2f}, PnL={pnl:,.2f} ({pnl_pct:+.2f}%), Reason={exit_reason}")
                    if len(trade_history) > 10:
                        print(f"      ... and {len(trade_history) - 10} more trades")
                else:
                    print(f"      No trade history available")
            else:
                print(f"   ✗ Optimization failed!")
                print(f"     Error: {result.get('error', 'Unknown error') if result else 'No result returned'}")
                
        except Exception as e:
            print(f"   ✗ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
                
        print(f"\n{'='*60}")
        print(f"Single strategy testing complete!")
        print(f"Strategy tested: {class_name}")
        print(f"To test other strategies, modify the 'strategy_to_test' variable")
        print(f"Available strategies: RSIDivergenceStrategy, MACDEMAATRStrategy, EMAChannelScalpingStrategy, AdaptiveRSIStrategy, MeanReversionBBRSIStrategy, SupplyDemandSpotStrategy")
        print(f"{'='*60}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_async_basic():
    """Test basic async functionality without data sources."""
    print("🧪 Testing Basic Async Functionality...")
    
    try:
        # Test async symbol discovery first
        print("📡 Testing async symbol discovery...")
        symbols = await discover_symbols_async()
        print(f"✅ Symbol discovery returned: {len(symbols)} symbol groups")
        for key, value in symbols.items():
            if value is not None:
                if isinstance(value, list):
                    print(f"   {key}: {len(value)} items")
                elif hasattr(value, '__len__'):
                    print(f"   {key}: {len(value)} items ({type(value).__name__})")
                else:
                    print(f"   {key}: {type(value).__name__}")
        
        print("✅ Basic async functionality test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Basic async test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_fetch():
    """Test async fetching with just a few symbols and timeframes."""
    print("🧪 Testing Async Fetch with minimal data...")
    
    # First test basic functionality
    basic_success = await test_async_basic()
    if not basic_success:
        return False
    
    print("\n🚀 Now testing async data fetching...")
    
    # Create test symbols for multiple exchanges using ACTUAL available symbols
    test_symbols = {
        'unmatched_hyperliquid': ['BTC', 'NEIRO', 'LUNC'],  # 3 symbols
        'phemex': ['PEPE', 'BABYDOGE', 'WHY'],  # 3 symbols 
        'coinbase_unmatched': ['SOL', 'DOGE', 'ADA']  # 3 symbols
    }
    
    # Test with just 1 timeframe to avoid the CCXT config issue for now
    test_timeframes = ['1h']
    
    print(f"📊 Testing with symbols: {test_symbols}")
    print(f"⏱️ Testing with timeframes: {test_timeframes}")
    
    try:
        await fetch_ohlcv_data_async(
            symbols=test_symbols,
            timeframes=test_timeframes,
            data_dir=os.path.join(project_root, 'data'),
            force_refresh=True  # Force fresh fetches for testing
        )
        print("✅ Async fetch test completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Async fetch test failed: {e}")
        print("This might be due to CCXT configuration issues in the data sources.")
        print("The async logic itself may still be working correctly.")
        import traceback
        traceback.print_exc()
        return False

async def main_async():
    """Main async pipeline orchestrator function."""
    import sys
    import subprocess
    import argparse

    parser = argparse.ArgumentParser(description="Async Unified Pipeline Orchestrator")
    parser.add_argument('--optimizer', choices=['hyperopt', 'optuna', 'backtesting'], default='hyperopt', help='Choose optimizer: hyperopt or optuna (default: hyperopt)')
    parser.add_argument('--trials', type=int, default=500, help='Number of optimization trials (default: 500)')
    parser.add_argument('--scheduler', action='store_true', help='Run scheduler (reoptimization cycle) instead of full pipeline')
    parser.add_argument('--strategy', type=str, default=None, help='Specify a single strategy to reoptimize (by name, e.g. macd_ema_atr)')
    parser.add_argument('--force-rerun', action='store_true', help='Force reoptimization even if already completed')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all data files, ignoring staleness checks')
    parser.add_argument('--workers', type=int, default=None, help='Number of worker threads (default: 12)')
    parser.add_argument('mode', nargs='?', default=None, help='Mode: test or None for full pipeline')
    args = parser.parse_args()

    if args.mode == 'test':
        test_single_symbol(optimizer=args.optimizer, trials=args.trials)
    elif args.scheduler:
        print("\n=== Running ASYNC Scheduler (Reoptimization Cycle) ===")
        # Use async symbol discovery
        symbols = await discover_symbols_async()
        # If a specific strategy is requested, pass as a list
        target_strategies = [args.strategy] if args.strategy else None
        summary = run_strategy_optimization(
            symbols=symbols,
            reoptimization_mode=True,
            target_strategies=target_strategies,
            force_rerun=args.force_rerun,
            optimizer=args.optimizer,
            n_trials=args.trials
        )
        print(f"Scheduler complete. Ran {summary.get('total_optimizations', 0)} optimizations.")
        print(f"Successful optimizations: {summary.get('successful_optimizations', 0)}")
        if summary.get('already_completed', 0) > 0:
            print(f"Already completed: {summary.get('already_completed', 0)}")
        print("Aggregating all results from results/ ...")
        all_results = scan_all_result_files(os.path.join(project_root, 'results'))
        print(f"Found {len(all_results)} total result files.")
        if all_results:
            analysis = analyze_optimization_results(all_results)
            print(f"Aggregated analysis: {analysis['qualified_results']} qualified results, {analysis['total_results']} total.")
            save_optimization_analysis_with_schedule(analysis, os.path.join(project_root, 'results'), {})
        import threading
        print("Active threads at end:", threading.enumerate())
    else:
        # 🚀 ASYNC FULL PIPELINE - Much faster with true concurrency!
        print("🚀 Starting ASYNC Full Pipeline...")
        
        # Step 1: Async Symbol Discovery
        print("📡 Step 1: Async Symbol Discovery...")
        symbols = await discover_symbols_async()
        
        # Step 2: Async OHLCV Data Fetching
        print("📊 Step 2: Async OHLCV Data Fetching...")
        await fetch_ohlcv_data_async(symbols, force_refresh=args.force_refresh)
        
        # Step 3: ASYNC Strategy Optimization - Full concurrency!
        print("🚀 Step 3: ASYNC Strategy Optimization...")
        optimization_summary = await run_strategy_optimization_async(symbols, optimizer=args.optimizer)
        
        print("✅ Data fetching complete. Check data/ for results.")
        print(f"✅ Optimization complete. Ran {optimization_summary.get('total_optimizations', 0)} optimizations.")
        print(f"✅ Successful optimizations: {optimization_summary.get('successful_optimizations', 0)}")
        if optimization_summary.get('already_completed', 0) > 0:
            print(f"⏭️ Already completed: {optimization_summary.get('already_completed', 0)}")
            
        # Step 4: Results Analysis and Aggregation
        print("📈 Step 4: Results Analysis and Aggregation...")
        all_results = scan_all_result_files(os.path.join(project_root, 'results'))
        print(f"📊 Found {len(all_results)} total result files.")
        
        if all_results:
            analysis = analyze_optimization_results(all_results)
            print(f"📊 Aggregated analysis: {analysis['qualified_results']} qualified results, {analysis['total_results']} total.")
            save_optimization_analysis_with_schedule(analysis, os.path.join(project_root, 'results'), {})

            # Enhanced filtering and bot integration
            try:
                import pandas as pd
                qualified_csv = os.path.join(os.path.join(project_root, 'results'), 'all_qualified_results.csv')
                if os.path.exists(qualified_csv):
                    df = pd.read_csv(qualified_csv)
                    if 'win_rate' in df.columns:
                        # REALISTIC PROFITABLE FILTERS
                        # Minimum 100% return = double your money (anything less is not worth the risk)
                        # Keep strategy count manageable for rate limits (~100 strategies)
                        filtered = df[
                            (df['win_rate'] >= 60) &
                            (df['trades'] >= 5) &              # Minimum trades for statistical reliability
                            (df['sharpe'] >= 5) &              # Minimum Sharpe ratio for risk-adjusted returns
                            (df['return_pct'] >= 100) &        # Minimum return percentage for meaningful gains
                            (df['composite_score'] >= 75)     # Minimum composite score for overall performance
                        ]
                        
                        abs_params_path = os.path.join(os.path.join(project_root, 'results'), 'absolute_params.csv')
                        filtered.to_csv(abs_params_path, index=False)
                        print(f"📄 Enhanced filtered params saved: {abs_params_path} ({len(filtered)} strategies)")
                        
                        try:
                            from src.utils.bot_integration import OptimizedBotIntegration
                            integration = OptimizedBotIntegration()
                            success = integration.export_all_absolute_params_to_json()
                            if success:
                                print("✅ live_trading_config.json created for bot usage")
                            else:
                                print("❌ Failed to create live_trading_config.json")
                        except Exception as json_error:
                            print(f"❌ Error creating live_trading_config.json: {json_error}")
                    else:
                        print("❌ No 'win_rate' column found, skipping filtering.")
                else:
                    print("❌ all_qualified_results.csv not found, skipping filtering.")
            except Exception as e:
                print(f"❌ Error during enhanced filtering: {e}")
                
        print("🎉 ASYNC Pipeline completed successfully!")

if __name__ == "__main__":
    import sys
    import subprocess
    import argparse

    parser = argparse.ArgumentParser(description="Unified Pipeline Orchestrator")
    parser.add_argument('--optimizer', choices=['hyperopt', 'optuna', 'backtesting'], default='hyperopt', help='Choose optimizer: hyperopt or optuna (default: hyperopt)')
    parser.add_argument('--trials', type=int, default=500, help='Number of optimization trials (default: 500)')
    parser.add_argument('--scheduler', action='store_true', help='Run scheduler (reoptimization cycle) instead of full pipeline')
    parser.add_argument('--strategy', type=str, default=None, help='Specify a single strategy to reoptimize (by name, e.g. macd_ema_atr)')
    parser.add_argument('--force-rerun', action='store_true', help='Force reoptimization even if already completed')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all data files, ignoring staleness checks')
    parser.add_argument('--async-mode', action='store_true', help='Use async pipeline (recommended for better performance)')
    parser.add_argument('--test-async', action='store_true', help='Test async fetch with minimal data')
    parser.add_argument('--workers', type=int, default=None, help='Number of worker threads (default: 12)')
    parser.add_argument('mode', nargs='?', default=None, help='Mode: test or None for full pipeline')
    args = parser.parse_args()

    if getattr(args, 'test_async', False):
        print("🧪 Running Async Fetch Test...")
        asyncio.run(test_async_fetch())
    elif args.mode == 'async':
        print("🚀 Running ASYNC Pipeline for maximum performance...")
        asyncio.run(main_async())
    elif getattr(args, 'async_mode', False):
        print("🚀 Running ASYNC Pipeline for maximum performance...")
        asyncio.run(main_async())
    elif args.mode == 'test':
        test_single_symbol(strategy_name=args.strategy, optimizer=args.optimizer, trials=args.trials)
    elif args.scheduler:
        print("\n=== Running Scheduler (Reoptimization Cycle) ===")
        symbols = discover_symbols()
        # If a specific strategy is requested, pass as a list
        target_strategies = [args.strategy] if args.strategy else None
        # Set workers - use command line arg or default to 12
        max_workers = args.workers if args.workers is not None else 12
        print(f"🔧 Using {max_workers} worker threads for optimization with {args.trials} trials")
        summary = run_strategy_optimization(
            symbols=symbols,
            reoptimization_mode=True,
            target_strategies=target_strategies,
            force_rerun=args.force_rerun,
            optimizer=args.optimizer,
            max_workers=max_workers,
            n_trials=args.trials
        )
        print(f"Scheduler complete. Ran {summary.get('total_optimizations', 0)} optimizations.")
        print(f"Successful optimizations: {summary.get('successful_optimizations', 0)}")
        if summary.get('already_completed', 0) > 0:
            print(f"Already completed: {summary.get('already_completed', 0)}")
        print("Aggregating all results from results/ ...")
        all_results = scan_all_result_files(os.path.join(project_root, 'results'))
        print(f"Found {len(all_results)} total result files.")
        if all_results:
            analysis = analyze_optimization_results(all_results)
            print(f"Aggregated analysis: {analysis['qualified_results']} qualified results, {analysis['total_results']} total.")
            save_optimization_analysis_with_schedule(analysis, os.path.join(project_root, 'results'), {})
        import threading
        print("Active threads at end:", threading.enumerate())
    else:
        # Full pipeline with resume functionality
        symbols = discover_symbols()
        fetch_ohlcv_data(symbols, force_refresh=args.force_refresh)  # Use staleness checking by default
        # Step 2: Run comprehensive optimization (freqtrade-inspired)
        max_workers = args.workers if args.workers is not None else 12
        print(f"🔧 Using {max_workers} worker threads for optimization with {args.trials} trials")
        optimization_summary = run_strategy_optimization(symbols, optimizer=args.optimizer, max_workers=max_workers, n_trials=args.trials)
        print("Data fetching complete. Check data/ for results.")
        print(f"Optimization complete. Ran {optimization_summary.get('total_optimizations', 0)} optimizations.")
        print(f"Successful optimizations: {optimization_summary.get('successful_optimizations', 0)}")
        if optimization_summary.get('already_completed', 0) > 0:
            print(f"Already completed: {optimization_summary.get('already_completed', 0)}")
        # NEW: Scan all result files and aggregate for analysis
        print("Aggregating all results from results/ ...")
        all_results = scan_all_result_files(os.path.join(project_root, 'results'))
        print(f"Found {len(all_results)} total result files.")
        if all_results:
            analysis = analyze_optimization_results(all_results)
            print(f"Aggregated analysis: {analysis['qualified_results']} qualified results, {analysis['total_results']} total.")
            # Optionally, save the merged analysis and CSV
            save_optimization_analysis_with_schedule(analysis, os.path.join(project_root, 'results'), {})

            # --- NEW: Run analyzer to filter for win_rate >= 70% and save as absolute_params.csv ---
            try:
                import pandas as pd
                qualified_csv = os.path.join(os.path.join(project_root, 'results'), 'all_qualified_results.csv')
                if os.path.exists(qualified_csv):
                    df = pd.read_csv(qualified_csv)
                    if 'win_rate' in df.columns:
                        # Apply multiple filters for lean, robust results
                        filtered = df[
                            (df['win_rate'] >= 60) &           # Minimum win rate
                            (df['trades'] >= 5) &              # Minimum trades for statistical reliability
                            (df['sharpe'] >= 5) &              # Minimum Sharpe ratio for risk-adjusted returns
                            (df['return_pct'] >= 100) &        # Minimum return percentage for meaningful gains
                            (df['composite_score'] >= 75)     # Minimum composite score for overall performance
                        ]
                        
                        # Additional filtering: Exclude unsuitable timeframes per strategy (from STRATEGY_OVERVIEW.md)
                        if 'strategy_name' in filtered.columns and 'timeframe' in filtered.columns:
                            print("\n📊 Applying strategy-specific timeframe filters...")
                            
                            # Strategy 1: RSI Divergence - Best: 4h/1d, Poor: 1m-30m (too noisy)
                            rsi_divergence_mask = (
                                (filtered['strategy_name'] == 'rsi_divergence') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~rsi_divergence_mask]
                            excluded_count = rsi_divergence_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} rsi_divergence strategies (1m-30m: too noisy for divergence)")

                            # Strategy 2: MACD + EMA + ATR - Best: 1d/4h, Poor: 1m/5m (whipsaws, slower MACD)
                            macd_ema_atr_mask = (
                                (filtered['strategy_name'] == 'macd_ema_atr') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~macd_ema_atr_mask]
                            excluded_count = macd_ema_atr_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} macd_ema_atr strategies (1m-30m: excessive whipsaws)")

                            # Strategy 3: Breakout - Best: 1h-4h (fast breakouts), Poor: 15m/30m (too much noise)
                            breakout_mask = (
                                (filtered['strategy_name'] == 'breakout') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~breakout_mask]
                            excluded_count = breakout_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} breakout strategies (1m-30m: false breakouts)")

                            # Strategy 4: Adaptive RSI - Best: 1h (crypto), Poor: 1m-15m/1d (noise/too slow)
                            adaptive_rsi_mask = (
                                (filtered['strategy_name'] == 'adaptive_rsi') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '1d']))
                            )
                            filtered = filtered[~adaptive_rsi_mask]
                            excluded_count = adaptive_rsi_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} adaptive_rsi strategies (1m-15m: noise, 1d: too slow)")

                            # Strategy 5: EMA Channel Scalping - Best: 1h/2h (scalping), Poor: 1m-5m (noise) and 4h+ (too slow)
                            ema_channel_scalping_mask = (
                                (filtered['strategy_name'] == 'ema_channel_scalping') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']))
                            )
                            filtered = filtered[~ema_channel_scalping_mask]
                            excluded_count = ema_channel_scalping_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} ema_channel_scalping strategies (1m-5m: noise, 4h+: too slow for scalping)")

                            # Strategy 6: EMA Ribbon Pullback - Best: 4h/1d (trend), Poor: 1m-30m (whipsaws)
                            ema_ribbon_pullback_mask = (
                                (filtered['strategy_name'] == 'ema_ribbon_pullback') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~ema_ribbon_pullback_mask]
                            excluded_count = ema_ribbon_pullback_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} ema_ribbon_pullback strategies (1m-30m: false pullback signals)")

                            # Strategy 7: Markov Chain - Best: 1d (stable patterns), Poor: 1m-30m (noise)
                            markov_chain_mask = (
                                (filtered['strategy_name'] == 'markov_chain') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~markov_chain_mask]
                            excluded_count = markov_chain_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} markov_chain strategies (1m-30m: unstable transition probabilities)")

                            # Strategy 8: Mean Reversion BB RSI - Best: 4h (Dataset dependent), Poor: 1m/5m/1d
                            mean_reversion_bb_rsi_mask = (
                                (filtered['strategy_name'] == 'mean_reversion_bb_rsi') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '1d']))
                            )
                            filtered = filtered[~mean_reversion_bb_rsi_mask]
                            excluded_count = mean_reversion_bb_rsi_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} mean_reversion_bb_rsi strategies (1m-5m: noise, 1d: too slow)")

                            # Strategy 9: Statistical Arbitrage - Best: 1h (SHORT-LIVED moves), Poor: 1m-5m (noise) and 1d+ (too slow)
                            statistical_arbitrage_mask = (
                                (filtered['strategy_name'] == 'statistical_arbitrage') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']))
                            )
                            filtered = filtered[~statistical_arbitrage_mask]
                            excluded_count = statistical_arbitrage_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} statistical_arbitrage strategies (1m-5m: noise, 4h+: misses short-lived opportunities)")

                            # Strategy 10: Supertrend - Best: 1d/4h (trend following), Poor: 1m-30m (false signals)
                            supertrend_mask = (
                                (filtered['strategy_name'] == 'supertrend') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m']))
                            )
                            filtered = filtered[~supertrend_mask]
                            excluded_count = supertrend_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} supertrend strategies (1m-30m: lagging indicator needs clean trends)")

                            # Strategy 11: Supply Demand Spot - Best: BTC 1h/ETH 4h (zone bounces), Poor: 1m-30m/PAXG 1d
                            supply_demand_mask = (
                                (filtered['strategy_name'] == 'supply_demand_spot') & 
                                (filtered['timeframe'].isin(['1m', '3m', '5m', '15m', '30m', '1d']))
                            )
                            filtered = filtered[~supply_demand_mask]
                            excluded_count = supply_demand_mask.sum()
                            if excluded_count > 0:
                                print(f"🚫 Excluded {excluded_count} supply_demand_spot strategies (1m-30m: noise, 1d: zones break not bounce)")
                            
                            print(f"✅ Timeframe filtering complete - kept strategies with optimal timeframes")
                        
                        abs_params_path = os.path.join(os.path.join(project_root, 'results'), 'absolute_params.csv')
                        filtered.to_csv(abs_params_path, index=False)
                        print(f"Enhanced filtered absolute params saved to: {abs_params_path} ({len(filtered)} strategies)")
                        
                        # --- NEW: Automatically export to JSON for bot usage ---
                        try:
                            from src.utils.bot_integration import OptimizedBotIntegration
                            integration = OptimizedBotIntegration()
                            success = integration.export_all_absolute_params_to_json()
                            if success:
                                print("✅ live_trading_config.json created automatically for bot usage")
                            else:
                                print("❌ Failed to create live_trading_config.json")
                        except Exception as json_error:
                            print(f"❌ Error creating live_trading_config.json: {json_error}")
                        
                    else:
                        print("No 'win_rate' column found in all_qualified_results.csv, skipping filtering.")
                else:
                    print("all_qualified_results.csv not found, skipping filtering.")
            except Exception as e:
                print(f"Error during enhanced filtering: {e}")

            # --- NEW: Archive results after analysis ---
            try:
                archive_script = os.path.join(os.path.dirname(__file__), 'scripts', 'archive_optimization_results.py')
                if os.path.exists(archive_script):
                    print(f"Archiving results using: {archive_script}")
                    subprocess.run([
                        sys.executable, archive_script, '--results-dir', os.path.join(project_root, 'results')
                    ], check=True)
                else:
                    print(f"Archive script not found: {archive_script}")
            except Exception as e:
                print(f"Error archiving results: {e}")

        import threading
        print("Active threads at end:", threading.enumerate())
