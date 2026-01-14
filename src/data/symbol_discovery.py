"""
symbol_discovery.py

Fetches and caches tradable symbols from Phemex, Hyperliquid, and Coinbase via API.
Supports per-exchange and base-symbol formats, with daily caching to minimize API calls.
Intended for use in intersection/filtering modules and for robust, rate-limited symbol discovery.

Cache files:
    - markets_info/symbols_discovery/symbols_per_exchange_format_cache.json
    - markets_info/symbols_discovery/base_symbols_cache.json
"""

import os
import sys
import asyncio
import ccxt
from hyperliquid.info import Info
from hyperliquid.utils import constants
import json
from datetime import datetime, timedelta
import time
import pandas as pd
from typing import Any, Hashable

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

BASE_DATA_PATH = os.path.join(project_root, 'markets_info')

# Enhanced TokenBucket Rate Limiting (updated with official Hyperliquid specs)
from src.utils.token_bucket import TokenBucket
from src.data.api_rate_monitor import record_api_call

from src.exchange.logging_utils import setup_logger
from src.exchange.retry import retry_on_exception

logger = setup_logger('symbol_discovery_source', json_logs=True)

# Load config for exchange flags
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

HYPERLIQUID_META_DATA = os.path.join(BASE_DATA_PATH, 'hyperliquid', 'hyperliquid_meta.json')
HYPERLIQUID_META_DATA_SAVED = os.path.join(BASE_DATA_PATH, 'hyperliquid', 'hyperliquid_symbols_meta_data_bot.json')

PHEMEX_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'phemex', 'phemex_markets.json')
PHEMEX_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'phemex', 'phemex_markets_loads_data_bot.json')

COINBASE_MARKET_LOADS = os.path.join(BASE_DATA_PATH, 'coinbase', 'coinbase_markets.json')
COINBASE_MARKET_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'coinbase', 'coinbase_markets_loads_data_bot.json')

BINANCE_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'binance', 'binance_markets.json')
BINANCE_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'binance', 'binance_markets_loads_data_bot.json')

KUCOIN_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'kucoin', 'kucoin_markets.json')
KUCOIN_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'kucoin', 'kucoin_markets_loads_data_bot.json')

BYBIT_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'bybit', 'bybit_markets.json')
BYBIT_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'bybit', 'bybit_markets_loads_data_bot.json')

OKX_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'okx', 'okx_markets.json')
OKX_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'okx', 'okx_markets_loads_data_bot.json')

BITGET_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'bitget', 'bitget_markets.json')
BITGET_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'bitget', 'bitget_markets_loads_data_bot.json')

GATEIO_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'gateio', 'gateio_markets.json')
GATEIO_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'gateio', 'gateio_markets_loads_data_bot.json')

MEXC_MARKETS_LOADS = os.path.join(BASE_DATA_PATH, 'mexc', 'mexc_markets.json')
MEXC_MARKETS_LOADS_SAVED = os.path.join(BASE_DATA_PATH, 'mexc', 'mexc_markets_loads_data_bot.json')

CACHE_FILE_PER_EXCHANGE_FORMAT = os.path.join(BASE_DATA_PATH, 'symbols_discovery', 'symbols_per_exchange_format_cache.json')
CACHE_FILE_BASE_SYMBOLS = os.path.join(BASE_DATA_PATH, 'symbols_discovery', 'base_symbols_cache.json')
CACHE_TTL_HOURS = 24

def load_cache_per_exchange_format() -> Any | None:
    """
    Load cached symbols in per-exchange format from disk if the cache is valid.

    Returns:
        dict or None: Cached data if present and not expired, otherwise None.
    """
    if not os.path.exists(CACHE_FILE_PER_EXCHANGE_FORMAT):
        return None
    with open(CACHE_FILE_PER_EXCHANGE_FORMAT, "r") as f:
        data = json.load(f)
    cache_time = datetime.fromisoformat(data.get("timestamp"))
    if datetime.now() - cache_time > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return data

def load_cache_base_symbols() -> Any | None:
    """
    Load cached base symbols from disk if the cache is valid.

    Returns:
        dict or None: Cached data if present and not expired, otherwise None.
    """
    if not os.path.exists(CACHE_FILE_BASE_SYMBOLS):
        return None
    with open(CACHE_FILE_BASE_SYMBOLS, "r") as f:
        data = json.load(f)
    cache_time = datetime.fromisoformat(data.get("timestamp"))
    if datetime.now() - cache_time > timedelta(hours=CACHE_TTL_HOURS):
        return None
    return data

def save_cache_per_exchange_format(symbols_dict_per_exchange_format)  -> None:
    """
    Save symbols in per-exchange format to the cache file with a timestamp.

    Args:
        symbols_dict_per_exchange_format (dict): Symbols to cache, keyed by exchange.
    """
    os.makedirs(os.path.dirname(CACHE_FILE_PER_EXCHANGE_FORMAT), exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "symbols": symbols_dict_per_exchange_format
    }
    with open(CACHE_FILE_PER_EXCHANGE_FORMAT, "w") as f:
        json.dump(data, f, indent=2)

def save_cache_base_symbols(symbols_dict_base_symbols)  -> None:
    """
    Save base symbols to the cache file with a timestamp.

    Args:
        symbols_dict_base_symbols (dict): Base symbols to cache, keyed by exchange.
    """
    os.makedirs(os.path.dirname(CACHE_FILE_BASE_SYMBOLS), exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "symbols": symbols_dict_base_symbols
    }
    with open(CACHE_FILE_BASE_SYMBOLS, "w") as f:
        json.dump(data, f, indent=2)                              

def get_all_symbols_with_cache_per_exchange_format() -> Any | dict[str, dict[Hashable, Any]]:
    """
    Retrieve all symbols in per-exchange format, using cache if available and valid.

    Returns:
        dict: Symbols per exchange, either from cache or freshly fetched and cached.
    """
    cache = load_cache_per_exchange_format()
    if cache:
        logger.info("Loaded symbols from cache.")
        return cache["symbols"]
    # Fetch fresh data
    symbols = {
        "phemex_contracts": get_all_phemex_contract_symbols().to_dict(orient="list"),
        "hyperliquid": get_hyperliquid_symbols().to_dict(orient="list"),
        "coinbase": get_coinbase_spot_symbols().to_dict(orient="list"),
        "binance": get_binance_spot_symbols().to_dict(orient="list"),
        "kucoin": get_kucoin_symbols(),
        "bybit": get_bybit_symbols(),
        "okx": get_okx_symbols(),
        "bitget": get_bitget_symbols(),
        "gateio": get_gateio_symbols(),
        "mexc": get_mexc_symbols(),
    }
    save_cache_per_exchange_format(symbols)
    logger.info("Fetched and cached new symbols.")
    return symbols

def get_all_symbols_with_cache_base_symbols() -> Any | dict[str, dict[Hashable, Any]]:
    """
    Retrieve all base symbols, using cache if available and valid.

    Returns:
        dict: Base symbols per exchange, either from cache or freshly fetched and cached.
    """
    cache = load_cache_base_symbols()
    if cache:
        logger.info("Loaded symbols from cache.")
        return cache["symbols"]
    # Fetch fresh data
    symbols = {
        "phemex_base": get_phemex_base_symbols().to_dict(orient="list"),
        "hyperliquid": get_hyperliquid_symbols().to_dict(orient="list"),
        "coinbase": get_coinbase_base_symbols().to_dict(orient="list"),
        "binance": get_binance_spot_symbols().to_dict(orient="list"),
        "kucoin": get_kucoin_base_symbols(),
        "bybit_base": get_bybit_base_symbols(),
        "okx_base": get_okx_base_symbols(),
        "bitget_base": get_bitget_base_symbols(),
        "gateio_base": get_gateio_base_symbols(),
        "mexc_base": get_mexc_base_symbols(),
    }
    save_cache_base_symbols(symbols)
    logger.info("Fetched and cached new symbols.")
    return symbols

# Hyperliquid: Official SDK specs = 100 capacity, 10 tokens/sec (NOT using CCXT)
# Formula: 10,000 base + (1 per USDC traded), IP: 1,200 weight/min = 60 info req/min
hyperliquid_symbol_discovery_bucket = TokenBucket(100, 10.0, "Hyperliquid_Order", enable_caching=True, cache_ttl=120)  # Official SDK

# Coinbase: CCXT rateLimit 34ms = 29.41 req/sec (VERIFIED 2025-11-07)
coinbase_symbol_discovery_bucket = TokenBucket(100, 29.41, "Coinbase_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# Phemex: CCXT rateLimit 120.5ms = 8.30 req/sec (VERIFIED 2025-11-07)
phemex_symbol_discovery_bucket = TokenBucket(100, 8.30, "Phemex_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# Binance: CCXT rateLimit 50ms = 20.00 req/sec (VERIFIED 2025-11-07)
binance_symbol_discovery_bucket = TokenBucket(100, 20.0, "Binance_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# KuCoin: CCXT rateLimit 75ms = 13.33 req/sec (VERIFIED 2025-11-07)
kucoin_symbol_discovery_bucket = TokenBucket(100, 13.33, "KuCoin_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# Bybit: CCXT rateLimit 20ms = 50.00 req/sec (VERIFIED 2026-01-03)
bybit_symbol_discovery_bucket = TokenBucket(100, 50.0, "Bybit_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# OKX: CCXT rateLimit 110ms = 9.09 req/sec (VERIFIED 2026-01-03)
okx_symbol_discovery_bucket = TokenBucket(100, 9.09, "OKX_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# Bitget: CCXT rateLimit 50ms = 20.00 req/sec (VERIFIED 2026-01-03)
bitget_symbol_discovery_bucket = TokenBucket(100, 20.0, "Bitget_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# Gate.io: CCXT rateLimit 50ms = 20.00 req/sec (VERIFIED 2026-01-03)
gateio_symbol_discovery_bucket = TokenBucket(100, 20.0, "Gateio_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# MEXC: CCXT rateLimit 50ms = 20.00 req/sec (VERIFIED 2026-01-03)
mexc_symbol_discovery_bucket = TokenBucket(100, 20.0, "MEXC_Order", enable_caching=True, cache_ttl=120)  # CCXT verified

# ============================================================================
# PHEMEX SYMBOLS (All Markets)
# ============================================================================

def extract_phemex_swap_contracts_info(file_path=PHEMEX_MARKETS_LOADS, output_path=PHEMEX_MARKETS_LOADS_SAVED) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Extract swap contracts info
    swap_contracts = []
    for symbol, info in data.items():
        # Only process swap contracts that are USDT-margined and active
        if (info.get('type') == 'swap' and 
            info.get('swap') == True and 
            info.get('settle') == 'USDT' and 
            info.get('active') == True):
            
            # Extract the key parameters you want
            contract_info = {
                "symbol": info.get('info', {}).get('symbol'),
                "precision_amount": info.get('precision', {}).get('amount'),
                "precision_price": info.get('precision', {}).get('price'),
                "price_precision": info.get('info', {}).get('pricePrecision'),
                "max_leverage": info.get('limits', {}).get('leverage', {}).get('max')
            }
            swap_contracts.append(contract_info)

    # Save to file (same structure as Hyperliquid)
    output = {
        "symbols": swap_contracts
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved {len(swap_contracts)} active USDT-margined swap contracts to {output_path}")

@retry_on_exception()
# --- All Phemex contract symbols (e.g., BTCUSDT, ETHUSDT) ---
def get_all_phemex_contract_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all Phemex contract symbols (e.g., BTCUSDT, ETHUSDT) for USDT-margined swap contracts.
    """
    wait = phemex_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not phemex_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[PHEMEX] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.phemex()
            # API call symbol_discovery_Phemex_markets consume 1 if it worked!!!
            # If rate limited! Try again!!! And again consume 1, 
            # also if fail consume 1!!!
            markets = exchange.load_markets()
            os.makedirs(os.path.dirname(PHEMEX_MARKETS_LOADS), exist_ok=True)
            with open(PHEMEX_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            extract_phemex_swap_contracts_info(file_path=PHEMEX_MARKETS_LOADS, output_path=PHEMEX_MARKETS_LOADS_SAVED)
            logger.info(f"[PHEMEX] Success fetching load_markets in symbol_discovery")
            logger.debug(f"[PHEMEX] Success fetching load_markets in symbol_discovery: {markets}")
            success = True
            record_api_call('phemex', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            contract_symbols = set()
            delisted_symbols = set()
            for m in markets.values():
                if m.get('type') == 'swap' and m.get('settle') == 'USDT' and m.get('active') == True:
                    contract_symbols.add(m['id'])
                if m.get('type') == 'swap' and m.get('settle') == 'USDT' and m.get('active') == False:
                    delisted_symbols.add(m['id'])
            logger.debug(f'PHEMEX SYMBOLS: {contract_symbols}')
            logger.debug(f'PHEMEX SYMBOLS DELISTED: {delisted_symbols}')
            return pd.DataFrame({'symbol': sorted(contract_symbols)})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('phemex', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[PHEMEX] Error fetching load_markets in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

@retry_on_exception()
# --- Phemex base symbol discovery ---
def get_phemex_base_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all normalized Phemex base symbols (e.g., BTC, ETH, etc.) for USDT-margined contracts.
    """
    if 'phemex' not in enabled_exchanges:
        logger.info("[PHEMEX] Exchange disabled in config, skipping")
        return pd.DataFrame()
    
    wait = phemex_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not phemex_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[PHEMEX] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.phemex()
            # API call symbol_discovery_Phemex_markets consume 1 if it worked!!!
            # If rate limited! Try again!!! And again consume 1, 
            # also if fail consume 1!!!
            markets = exchange.load_markets()
            logger.info(f"Phemex full markets saved! {PHEMEX_MARKETS_LOADS}")
            logger.info(f"[PHEMEX] Success fetching load_markets in symbol_discovery")
            success = True
            record_api_call('phemex', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            # ONLY extract base symbols from SWAP contracts (not spot markets)
            base_symbols = set()
            for m in markets.values():
                if m.get('type') == 'swap' and m.get('settle') == 'USDT' and m.get('active') == True:
                    symbol_id = m.get('id', '')
                    base = symbol_id.replace('USDT', '').upper()
                    base = ''.join([c for c in base if c.isalpha()])
                    if base:
                        base_symbols.add(base)
            # Return a DataFrame with a single 'symbol' column to satisfy the annotated return type
            logger.debug(f'[PHEMEX] Base symbols: {base_symbols}')
            return pd.DataFrame({'symbol': sorted(base_symbols)})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('phemex', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[PHEMEX] Error fetching load_markets in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

# ============================================================================
# HYPERLIQUID SYMBOLS (All Markets)
# ============================================================================

@retry_on_exception()
# --- Hyperliquid base symbol discovery ---
def get_hyperliquid_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all *active* Hyperliquid base symbols (exclude delisted ones)
    """
    if 'hyperliquid' not in enabled_exchanges:
        logger.info("[HYPERLIQUID] Exchange disabled in config, skipping")
        return pd.DataFrame()
    
    wait = hyperliquid_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not hyperliquid_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[HYPERLIQUID] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            # API call symbol_discovery_Hyperliquid_meta consume 1 if it worked!!!
            # If rate limited! Try again!!! And again consume 1, 
            # also if fail consume 1!!!
            meta = info.meta()
            os.makedirs(os.path.dirname(HYPERLIQUID_META_DATA), exist_ok=True)
            with open(HYPERLIQUID_META_DATA, "w") as f:
                json.dump(meta, f, indent=2, default=str)
            extract_hyperliquid_symbol_and_margin_info(file_path=HYPERLIQUID_META_DATA, output_path=HYPERLIQUID_META_DATA_SAVED)
            logger.info(f"Hyperliquid full meta saved! {HYPERLIQUID_META_DATA}")
            success = True
            record_api_call('hyperliquid', '/meta', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[HYPERLIQUID] Success fetching load_markets in symbol_discovery")
            logger.debug(f'[HYPERLIQUID] MARKETS: {meta}')

            # Extract only active markets (not delisted)
            active = [
                coin['name'][1:] if isinstance(coin['name'], str) and coin['name'].startswith('k') else coin['name']
                for coin in meta.get('universe', [])
                if not coin.get('isDelisted', False)  # Only include if not delisted
            ]

            delisted = [
                coin['name']
                for coin in meta.get('universe', [])
                if coin.get('isDelisted', False)
            ]

            logger.debug(f"ACTIVE: {sorted(active)}")
            logger.debug(f"DELISTED: {sorted(delisted)}")

            return pd.DataFrame({'symbol': sorted(active)})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('hyperliquid', '/meta', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[HYPERLIQUID] Error fetching meta in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

def extract_hyperliquid_symbol_and_margin_info(file_path=HYPERLIQUID_META_DATA, output_path=HYPERLIQUID_META_DATA_SAVED) -> None:
    os.makedirs(os.path.dirname(HYPERLIQUID_META_DATA), exist_ok=True)
    # Load the JSON data
    with open(file_path, "r") as f:
        data = json.load(f)

    universe = data.get("universe", [])
    margin_tables = data.get("marginTables", [])

    # Build a dict of margin tables for quick lookup
    margin_table_dict = {int(table_id): table for table_id, table in margin_tables}

    # Collect listed symbols and their info
    listed = []
    used_margin_table_ids = set()
    for coin in universe:
        if not coin.get("isDelisted", False):
            entry = {
                "symbol": coin.get("name"),
                "szDecimals": coin.get("szDecimals"),
                "maxLeverage": coin.get("maxLeverage"),
                "marginTableId": coin.get("marginTableId")
            }
            listed.append(entry)
            if coin.get("marginTableId") is not None:
                used_margin_table_ids.add(int(coin["marginTableId"]))

    # Collect only the margin tables that are actually used
    used_margin_tables = {
        table_id: margin_table_dict[table_id]
        for table_id in used_margin_table_ids if table_id in margin_table_dict
    }

    # Save to file
    output = {
        "symbols": listed,
        "margin_tables": used_margin_tables
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved listed symbols and used margin tables to {output_path}")

@retry_on_exception()
# --- Hyperliquid base symbol discovery ---
async def async_get_hyperliquid_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all *active* Hyperliquid base symbols (exclude delisted ones)
    """
    wait = hyperliquid_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not hyperliquid_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[HYPERLIQUID] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            # API call symbol_discovery_Hyperliquid_meta consume 1 if it worked!!!
            # If rate limited! Try again!!! And again consume 1, 
            # also if fail consume 1!!!
            meta = info.meta()
            os.makedirs(os.path.dirname(HYPERLIQUID_META_DATA), exist_ok=True)
            with open(HYPERLIQUID_META_DATA, "w") as f:
                json.dump(meta, f, indent=2, default=str)
            extract_hyperliquid_symbol_and_margin_info(file_path=HYPERLIQUID_META_DATA, output_path=HYPERLIQUID_META_DATA_SAVED)
            logger.info(f"Hyperliquid full meta saved! {HYPERLIQUID_META_DATA}")
            success = True
            record_api_call('hyperliquid', '/meta', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[HYPERLIQUID] Success fetching load_markets in symbol_discovery")
            logger.debug(f'[HYPERLIQUID] MARKETS: {meta}')

            # Extract only active markets (not delisted)
            active = [
                coin['name'][1:] if isinstance(coin['name'], str) and coin['name'].startswith('k') else coin['name']
                for coin in meta.get('universe', [])
                if not coin.get('isDelisted', False)  # Only include if not delisted
            ]

            delisted = [
                coin['name']
                for coin in meta.get('universe', [])
                if coin.get('isDelisted', False)
            ]

            logger.debug(f"ACTIVE: {sorted(active)}")
            logger.debug(f"DELISTED: {sorted(delisted)}")

            return pd.DataFrame({'symbol': sorted(active)})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('hyperliquid', '/meta', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[HYPERLIQUID] Error fetching meta in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

# ============================================================================
# COINBASE SYMBOLS (All Markets)
# ============================================================================

def extract_coinbase_spot_markets_info(file_path=COINBASE_MARKET_LOADS, output_path=COINBASE_MARKET_LOADS_SAVED) -> None:
    os.makedirs(os.path.dirname(COINBASE_MARKET_LOADS_SAVED), exist_ok=True)
    # Load the JSON data
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Collect spot markets and their info
    spot_markets = []
    for symbol, info in data.items():
        # Only process spot markets that are USDC-based and active
        if (info.get('spot') == True and 
            info.get('quote') == 'USDC' and 
            info.get('active') == True):
            
            info_dict = info.get('info', {})
            entry = {
                "id": info.get('id'),
                "precision_amount": info.get('precision', {}).get('amount'),
                "precision_price": info.get('precision', {}).get('price'),
                "quote_min_size": info_dict.get('quote_min_size'),
                "quote_max_size": info_dict.get('quote_max_size'),
                "base_increment": info_dict.get('base_increment'),
                "quote_increment": info_dict.get('quote_increment')
            }
            spot_markets.append(entry)
    
    # Save to file (same structure as others)
    output = {
        "symbols": spot_markets
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved {len(spot_markets)} active USDC-based spot markets to {output_path}")    

@retry_on_exception()
# --- Coinbase spot symbol discovery ---
def get_coinbase_spot_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all tradable Coinbase spot symbols in BASE-QUOTE format (e.g., BTC-USDC, ETH-USDC, etc.), matching legacy bot usage.
    """
    wait = hyperliquid_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not hyperliquid_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[COINBASE] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.coinbaseadvanced()
            # API call symbol_discovery_Coinbase_markets consume 1 if it worked!!!
            # If rate limited! Try again!!! And again consume 1, 
            # also if fail consume 1!!!
            markets = exchange.load_markets()
            os.makedirs(os.path.dirname(COINBASE_MARKET_LOADS), exist_ok=True)
            with open(COINBASE_MARKET_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            extract_coinbase_spot_markets_info(file_path=COINBASE_MARKET_LOADS, output_path=COINBASE_MARKET_LOADS_SAVED)
            logger.info(f"Coinbase full markets saved! {COINBASE_MARKET_LOADS}")
            success = True
            record_api_call('coinbase', '/markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[COINBASE] Success fetching load_markets in symbol_discovery")
            logger.debug(f'[COINBASE] MARKETS: {markets}')
            spot_symbols = set()
            spot_delisted = set()
            for symbol in markets:
                market = markets[symbol]
                if market.get('spot') and market.get('active'):
                    base = market['base'].upper()
                    quote = market['quote'].upper()
                    if quote == 'USDC':
                        spot_symbols.add(f"{base}-{quote}")

                if market.get('spot') and market.get('active') == False:
                    base = market['base'].upper()
                    quote = market['quote'].upper()
                    if quote == 'USDC':
                        spot_delisted.add(f"{base}-{quote}")
            logger.debug(f'[COINBASE] SYMBOLS: {spot_symbols}')
            logger.debug(f'[COINBASE] DELISTED: {spot_delisted}')
            return pd.DataFrame({'symbol': sorted(spot_symbols)})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('coinbase', '/markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[COINBASE] Error fetching meta in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

def get_coinbase_base_symbols(retries: int = 3)  -> pd.DataFrame:
    """
    Return all tradable Coinbase spot symbols in BASE format (e.g., BTC, ETH, etc.).
    """
    if 'coinbase' not in enabled_exchanges:
        logger.info("[COINBASE] Exchange disabled in config, skipping")
        return pd.DataFrame()
    
    wait = hyperliquid_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not hyperliquid_symbol_discovery_bucket.consume():
        # Handle rate limit (retry/backoff/skip)
        logger.warning("[COINBASE] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            df = get_coinbase_spot_symbols()
            if df.empty or 'symbol' not in df.columns:
                return pd.DataFrame()
            # Each symbol is like 'BTC-USDC', so split by '-' and take the first part
            base_symbols = sorted(set(s.split('-')[0] for s in df['symbol']))
            logger.debug(base_symbols)
            return pd.DataFrame({'symbol': base_symbols})
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('coinbase', '/markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[COINBASE] Error fetching meta in symbol_discovery: {e}")
                return pd.DataFrame()
    # If all retries failed, return an empty DataFrame
    return pd.DataFrame()

# ============================================================================
# BINANCE SYMBOLS (All Markets)
# ============================================================================

def extract_binance_spot_info(file_path=BINANCE_MARKETS_LOADS, output_path=BINANCE_MARKETS_LOADS_SAVED) -> None:
    """Extract key parameters for Binance SPOT trading."""
    os.makedirs(os.path.dirname(BINANCE_MARKETS_LOADS_SAVED), exist_ok=True)
    with open(file_path, "r") as f:
        data = json.load(f)
    
    spot_markets = []
    for symbol, info in data.items():
        # Only process SPOT markets with USDC quote that are active
        if (info.get('spot') == True and 
            info.get('active') == True and
            info.get('quote') == 'USDC'):
            
            info_dict = info.get('info', {})
            
            market_info = {
                "symbol": info.get('symbol'),
                "base": info.get('base'),
                "quote": info.get('quote'),
                "precision_amount": info.get('precision', {}).get('amount'),
                "precision_price": info.get('precision', {}).get('price'),
                "price_precision": info_dict.get('quotePrecision'),
                "quantity_precision": info_dict.get('baseAssetPrecision'),
                "min_notional": info.get('limits', {}).get('cost', {}).get('min'),
                "min_amount": info.get('limits', {}).get('amount', {}).get('min'),
                "max_amount": info.get('limits', {}).get('amount', {}).get('max')
            }
            spot_markets.append(market_info)
    
    # Save to file (same structure as other exchanges)
    output = {
        "symbols": spot_markets
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved {len(spot_markets)} active SPOT markets (USDC pairs) to {output_path}")

# --- Binance USDT-M Futures Symbol Discovery ---
@retry_on_exception()
def get_binance_spot_symbols(retries: int = 3) -> pd.DataFrame:
    """
    Return all Binance SPOT symbols in BASE/QUOTE format (e.g., BTC/USDC, ETH/USDC).
    Saves full market data for inspection.
    """
    wait = binance_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not binance_symbol_discovery_bucket.consume():
        logger.warning("[BINANCE] Rate limit prevented API call, returning empty DataFrame")
        return pd.DataFrame()
    start = time.time()

    success = False
    for attempt in range(retries + 1):
        try:
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}  # SPOT trading
            }
            exchange = ccxt.binance(config)  # type: ignore
            
            # Fetch all markets
            markets = exchange.load_markets()
            logger.info(f"[BINANCE] Success fetching load_markets in symbol_discovery")
            logger.debug(f'[BINANCE] MARKETS: {markets}')
            
            # Save full market data for inspection
            os.makedirs(os.path.dirname(BINANCE_MARKETS_LOADS), exist_ok=True)
            with open(BINANCE_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            
            logger.info(f"Binance full markets saved! {BINANCE_MARKETS_LOADS}")
            logger.info(f"[BINANCE] Success fetching load_markets in symbol_discovery")
            success = True
            record_api_call('binance', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            
            # Extract SPOT symbols with USDC quote (like Coinbase)
            spot_symbols = set()
            spot_delisted = set()
            
            for symbol, market in markets.items():
                if market.get('spot') and market.get('active'):
                    base = market['base'].upper()
                    quote = market['quote'].upper()
                    if quote == 'USDC':
                        spot_symbols.add(f"{base}/{quote}")
                
                # Track delisted spot symbols
                if market.get('spot') and market.get('active') == False:
                    base = market['base'].upper()
                    quote = market['quote'].upper()
                    if quote == 'USDC':
                        spot_delisted.add(f"{base}/{quote}")
            
            logger.debug(f'[BINANCE] ACTIVE SPOT: {sorted(spot_symbols)}')
            logger.debug(f'[BINANCE] DELISTED SPOT: {sorted(spot_delisted)}')
            
            # Extract and save detailed info
            extract_binance_spot_info(file_path=BINANCE_MARKETS_LOADS, output_path=BINANCE_MARKETS_LOADS_SAVED)
            
            return pd.DataFrame({'symbol': sorted(spot_symbols)})
            
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('binance', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[BINANCE] Error fetching load_markets in symbol_discovery: {e}")
                return pd.DataFrame()
    
    return pd.DataFrame()

def get_binance_base_symbols() -> pd.DataFrame:
    """
    Return all normalized Binance base symbols (e.g., BTC, ETH, etc.) for SPOT trading.
    Returns DataFrame to match other exchange functions.
    """    
    if 'binance' not in enabled_exchanges:
        logger.info("[BINANCE] Exchange disabled in config, skipping")
        return pd.DataFrame({'symbol': []})
    
    try:
        df = get_binance_spot_symbols()
        if df.empty or 'symbol' not in df.columns:
            return pd.DataFrame({'symbol': []})
        
        # Extract base symbols from spot symbols (e.g., BTC/USDC -> BTC)
        # Same approach as Coinbase: split by separator and take base
        base_symbols = set()
        for s in df['symbol']:
            # Split by '/' to get base symbol (BTC/USDC -> BTC)
            base = s.split('/')[0].upper()
            # Strip ALL non-alphabetic characters (numbers, symbols, etc.) - SAME AS PHEMEX
            base = ''.join([c for c in base if c.isalpha()])
            if base:
                base_symbols.add(base)
        
        logger.debug(f'[BINANCE] Base symbols: {len(base_symbols)} unique')
        return pd.DataFrame({'symbol': sorted(base_symbols)})
    except Exception as e:
        logger.error(f"[BINANCE] Error extracting base symbols: {e}")
        return pd.DataFrame({'symbol': []})    

# ============================================================================
# KUCOIN SYMBOLS (All Markets)
# ============================================================================

@retry_on_exception()
def get_kucoin_symbols():
    """
    Fetch all active PERPETUAL SWAP symbols from KuCoin Futures.
    PERPS ONLY - NO SPOT, NO DATED FUTURES!
    """
    logger.info("Fetching KuCoin Futures perpetual swap symbols...")
    
    wait = kucoin_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not kucoin_symbol_discovery_bucket.consume():
        logger.warning("[KUCOIN] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    try:
        config = {'enableRateLimit': True}
        kucoin = ccxt.kucoinfutures(config)  # type: ignore - FUTURES EXCHANGE FOR PERPS
        
        markets = kucoin.load_markets()
        
        # Save raw markets data to file (like other exchanges)
        os.makedirs(os.path.dirname(KUCOIN_MARKETS_LOADS), exist_ok=True)
        with open(KUCOIN_MARKETS_LOADS, "w") as f:
            json.dump(markets, f, indent=2, default=str)
        
        logger.info(f"KuCoin full markets saved! {KUCOIN_MARKETS_LOADS}")
        success = True
        record_api_call('kucoin', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
        
        symbols = []
        for symbol, market in markets.items():
            # ONLY perpetual swaps - filter out dated futures
            if market.get('active') and market.get('swap') and market.get('type') == 'swap':
                symbols.append(symbol)
        
        extract_kucoin_markets_info(markets)
        
        logger.info(f"Found {len(symbols)} active KuCoin perpetual swap symbols")
        logger.debug(f"[KUCOIN] Sample symbols: {symbols[:10]}")
        return sorted(symbols)
        
    except Exception as e:
        success = False
        record_api_call('kucoin', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
        logger.error(f"[KUCOIN] Error fetching KuCoin Futures perpetual swaps: {e}")
        return []


def extract_kucoin_markets_info(markets):
    """
    Extract detailed market information from KuCoin Futures (PERPETUAL SWAPS ONLY).
    """
    os.makedirs(os.path.dirname(KUCOIN_MARKETS_LOADS_SAVED), exist_ok=True)
    
    major_quotes = ['USDT']  # KuCoin Futures uses USDT-margined contracts
    
    perp_swaps = []
    
    for symbol, info in markets.items():
        if not info.get('active'):
            continue
        
        # ONLY perpetual swaps
        if not (info.get('swap') and info.get('type') == 'swap'):
            continue
            
        quote = info.get('quote', '')
        if quote not in major_quotes:
            continue
        
        # Get max leverage from limits or info
        max_leverage = None
        leverage_limits = info.get('limits', {}).get('leverage', {})
        if leverage_limits:
            max_leverage = leverage_limits.get('max')
        
        # Fallback to info section if not in limits
        if max_leverage is None:
            info_dict = info.get('info', {})
            max_leverage = info_dict.get('maxLeverage')
        
        contract_info = {
            'symbol': symbol,
            'precision_amount': info.get('precision', {}).get('amount'),
            'precision_price': info.get('precision', {}).get('price'),
            'max_leverage': max_leverage,
        }
        perp_swaps.append(contract_info)
    
    output = {
        "symbols": perp_swaps
    }
    with open(KUCOIN_MARKETS_LOADS_SAVED, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved {len(perp_swaps)} KuCoin Futures perpetual swaps to {KUCOIN_MARKETS_LOADS_SAVED}")


def get_kucoin_base_symbols():
    """
    Extract base symbols from KuCoin Futures perpetual swaps.
    """
    if 'kucoin' not in enabled_exchanges:
        logger.info("[KUCOIN] Exchange disabled in config, skipping")
        return []
    
    symbols = get_kucoin_symbols()
    
    base_symbols = set()
    for s in symbols:
        # KuCoin format: BTC/USDT:USDT -> extract BTC
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    
    base_list = sorted(list(base_symbols))
    logger.info(f"Extracted {len(base_list)} unique KuCoin base symbols")
    return base_list


# --- NEW EXCHANGES: Bybit, OKX, Bitget, Gate.io, MEXC ---

@retry_on_exception()
def get_bybit_symbols(retries: int = 3):
    """
    Fetch all Bybit SWAP (perpetual) symbols using CCXT.
    Returns list of trading pairs like ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...]
    """
    if 'bybit' not in enabled_exchanges:
        logger.info("[BYBIT] Exchange disabled in config, skipping")
        return []
    
    wait = bybit_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not bybit_symbol_discovery_bucket.consume():
        logger.warning("[BYBIT] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.bybit({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}) # type: ignore
            markets = exchange.load_markets()
            
            # Save full market data
            os.makedirs(os.path.dirname(BYBIT_MARKETS_LOADS), exist_ok=True)
            with open(BYBIT_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            logger.info(f"[BYBIT] Markets saved to {BYBIT_MARKETS_LOADS}")
            
            swap_symbols = [s for s, m in markets.items() if m.get('type') == 'swap' and m.get('quote') == 'USDT' and m.get('active') == True]
            
            # Save processed symbols
            output = {"symbols": sorted(swap_symbols)}
            with open(BYBIT_MARKETS_LOADS_SAVED, 'w') as f:
                json.dump(output, f, indent=2)
            
            success = True
            record_api_call('bybit', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[BYBIT] Found {len(swap_symbols)} SWAP (perpetual) symbols")
            return sorted(swap_symbols)
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('bybit', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[BYBIT] Error fetching symbols: {e}")
                return []
    return []

def get_bybit_base_symbols():
    """
    Extract base symbols from Bybit SWAP perpetuals.
    BTC/USDT:USDT -> BTC
    """
    if 'bybit' not in enabled_exchanges:
        logger.info("[BYBIT] Exchange disabled in config, skipping")
        return []
    
    symbols = get_bybit_symbols()
    base_symbols = set()
    for s in symbols:
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    base_list = sorted(list(base_symbols))
    logger.info(f"[BYBIT] Extracted {len(base_list)} unique base symbols")
    return base_list

@retry_on_exception()
def get_okx_symbols(retries: int = 3):
    """
    Fetch all OKX SWAP (perpetual) symbols using CCXT.
    Returns list of trading pairs like ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...]
    """
    if 'okx' not in enabled_exchanges:
        logger.info("[OKX] Exchange disabled in config, skipping")
        return []
    
    wait = okx_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not okx_symbol_discovery_bucket.consume():
        logger.warning("[OKX] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.okx({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}) # type: ignore
            markets = exchange.load_markets()
            
            # Save full market data
            os.makedirs(os.path.dirname(OKX_MARKETS_LOADS), exist_ok=True)
            with open(OKX_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            logger.info(f"[OKX] Markets saved to {OKX_MARKETS_LOADS}")
            
            swap_symbols = [s for s, m in markets.items() if m.get('type') == 'swap' and m.get('quote') == 'USDT' and m.get('active') == True]
            
            # Save processed symbols
            output = {"symbols": sorted(swap_symbols)}
            with open(OKX_MARKETS_LOADS_SAVED, 'w') as f:
                json.dump(output, f, indent=2)
            
            success = True
            record_api_call('okx', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[OKX] Found {len(swap_symbols)} SWAP (perpetual) symbols")
            return sorted(swap_symbols)
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('okx', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[OKX] Error fetching symbols: {e}")
                return []
    return []

def get_okx_base_symbols():
    """
    Extract base symbols from OKX SWAP perpetuals.
    BTC/USDT:USDT -> BTC
    """
    if 'okx' not in enabled_exchanges:
        logger.info("[OKX] Exchange disabled in config, skipping")
        return []
    
    symbols = get_okx_symbols()
    base_symbols = set()
    for s in symbols:
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    base_list = sorted(list(base_symbols))
    logger.info(f"[OKX] Extracted {len(base_list)} unique base symbols")
    return base_list

@retry_on_exception()
def get_bitget_symbols(retries: int = 3):
    """
    Fetch all Bitget SWAP (perpetual) symbols using CCXT.
    Returns list of trading pairs like ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...]
    """
    if 'bitget' not in enabled_exchanges:
        logger.info("[BITGET] Exchange disabled in config, skipping")
        return []
    
    wait = bitget_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not bitget_symbol_discovery_bucket.consume():
        logger.warning("[BITGET] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.bitget({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}) # type: ignore
            markets = exchange.load_markets()
            
            # Save full market data
            os.makedirs(os.path.dirname(BITGET_MARKETS_LOADS), exist_ok=True)
            with open(BITGET_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            logger.info(f"[BITGET] Markets saved to {BITGET_MARKETS_LOADS}")
            
            swap_symbols = [s for s, m in markets.items() if m.get('type') == 'swap' and m.get('quote') == 'USDT' and m.get('active') == True]
            
            # Save processed symbols
            output = {"symbols": sorted(swap_symbols)}
            with open(BITGET_MARKETS_LOADS_SAVED, 'w') as f:
                json.dump(output, f, indent=2)
            
            success = True
            record_api_call('bitget', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[BITGET] Found {len(swap_symbols)} SWAP (perpetual) symbols")
            return sorted(swap_symbols)
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('bitget', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[BITGET] Error fetching symbols: {e}")
                return []
    return []

def get_bitget_base_symbols():
    """
    Extract base symbols from Bitget SWAP perpetuals.
    BTC/USDT:USDT -> BTC
    """
    if 'bitget' not in enabled_exchanges:
        logger.info("[BITGET] Exchange disabled in config, skipping")
        return []
    
    symbols = get_bitget_symbols()
    base_symbols = set()
    for s in symbols:
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    base_list = sorted(list(base_symbols))
    logger.info(f"[BITGET] Extracted {len(base_list)} unique base symbols")
    return base_list

@retry_on_exception()
def get_gateio_symbols(retries: int = 3):
    """
    Fetch all Gate.io SWAP (perpetual) symbols using CCXT.
    Returns list of trading pairs like ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...]
    """
    if 'gateio' not in enabled_exchanges:
        logger.info("[GATEIO] Exchange disabled in config, skipping")
        return []
    
    wait = gateio_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not gateio_symbol_discovery_bucket.consume():
        logger.warning("[GATEIO] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.gateio({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}) # type: ignore
            markets = exchange.load_markets()
            
            # Save full market data
            os.makedirs(os.path.dirname(GATEIO_MARKETS_LOADS), exist_ok=True)
            with open(GATEIO_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            logger.info(f"[GATEIO] Markets saved to {GATEIO_MARKETS_LOADS}")
            
            swap_symbols = [s for s, m in markets.items() if m.get('type') == 'swap' and m.get('quote') == 'USDT' and m.get('active') == True]
            
            # Save processed symbols
            output = {"symbols": sorted(swap_symbols)}
            with open(GATEIO_MARKETS_LOADS_SAVED, 'w') as f:
                json.dump(output, f, indent=2)
            
            success = True
            record_api_call('gateio', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[GATEIO] Found {len(swap_symbols)} SWAP (perpetual) symbols")
            return sorted(swap_symbols)
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('gateio', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[GATEIO] Error fetching symbols: {e}")
                return []
    return []

def get_gateio_base_symbols():
    """
    Extract base symbols from Gate.io SWAP perpetuals.
    BTC/USDT:USDT -> BTC
    """
    if 'gateio' not in enabled_exchanges:
        logger.info("[GATEIO] Exchange disabled in config, skipping")
        return []
    
    symbols = get_gateio_symbols()
    base_symbols = set()
    for s in symbols:
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    base_list = sorted(list(base_symbols))
    logger.info(f"[GATEIO] Extracted {len(base_list)} unique base symbols")
    return base_list

@retry_on_exception()
def get_mexc_symbols(retries: int = 3):
    """
    Fetch all MEXC SWAP (perpetual) symbols using CCXT.
    Returns list of trading pairs like ['BTC/USDT:USDT', 'ETH/USDT:USDT', ...]
    """
    if 'mexc' not in enabled_exchanges:
        logger.info("[MEXC] Exchange disabled in config, skipping")
        return []
    
    wait = mexc_symbol_discovery_bucket.wait_time()
    if wait > 0:
        time.sleep(wait)
    if not mexc_symbol_discovery_bucket.consume():
        logger.warning("[MEXC] Rate limit prevented API call, returning empty list")
        return []
    
    start = time.time()
    success = False
    
    for attempt in range(retries + 1):
        try:
            exchange = ccxt.mexc({'enableRateLimit': True, 'options': {'defaultType': 'swap'}}) # type: ignore
            markets = exchange.load_markets()
            
            # Save full market data
            os.makedirs(os.path.dirname(MEXC_MARKETS_LOADS), exist_ok=True)
            with open(MEXC_MARKETS_LOADS, "w") as f:
                json.dump(markets, f, indent=2, default=str)
            logger.info(f"[MEXC] Markets saved to {MEXC_MARKETS_LOADS}")
            
            swap_symbols = [s for s, m in markets.items() if m.get('type') == 'swap' and m.get('quote') == 'USDT' and m.get('active') == True]
            
            # Save processed symbols
            output = {"symbols": sorted(swap_symbols)}
            with open(MEXC_MARKETS_LOADS_SAVED, 'w') as f:
                json.dump(output, f, indent=2)
            
            success = True
            record_api_call('mexc', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
            logger.info(f"[MEXC] Found {len(swap_symbols)} SWAP (perpetual) symbols")
            return sorted(swap_symbols)
        except Exception as e:
            success = False
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            else:
                record_api_call('mexc', '/load_markets', method='GET', success=success, response_time=time.time()-start, tokens_consumed=1)
                logger.error(f"[MEXC] Error fetching symbols: {e}")
                return []
    return []

def get_mexc_base_symbols():
    """
    Extract base symbols from MEXC SWAP perpetuals.
    BTC/USDT:USDT -> BTC
    """
    if 'mexc' not in enabled_exchanges:
        logger.info("[MEXC] Exchange disabled in config, skipping")
        return []
    
    symbols = get_mexc_symbols()
    base_symbols = set()
    for s in symbols:
        if '/' in s:
            base = s.split('/')[0]
            base_symbols.add(base)
    base_list = sorted(list(base_symbols))
    logger.info(f"[MEXC] Extracted {len(base_list)} unique base symbols")
    return base_list


# No intersection logic here. Use symbol_intersection.py for that.
# Example usage:
if __name__ == "__main__":
    all_symbols_per_exchange = get_all_symbols_with_cache_per_exchange_format()
    all_symbols_base = get_all_symbols_with_cache_base_symbols()
    get_phemex_base_symbols()
    get_all_phemex_contract_symbols()  # This creates the file first
    extract_phemex_swap_contracts_info()  # Now this can read the file that was just created
    get_hyperliquid_symbols()
    extract_hyperliquid_symbol_and_margin_info()    
    get_coinbase_spot_symbols()
    extract_coinbase_spot_markets_info()
    get_kucoin_symbols()
    get_kucoin_base_symbols()
    
    # Test new exchanges
    print("\n" + "="*70)
    print("TESTING NEW EXCHANGES")
    print("="*70)
    
    print("\n[BYBIT]")
    bybit_symbols = get_bybit_symbols()
    bybit_base = get_bybit_base_symbols()
    print(f"  SWAP symbols: {len(bybit_symbols)} | First 10: {bybit_symbols[:10]}")
    print(f"  Base symbols: {len(bybit_base)} | First 20: {bybit_base[:20]}")
    
    print("\n[OKX]")
    okx_symbols = get_okx_symbols()
    okx_base = get_okx_base_symbols()
    print(f"  SWAP symbols: {len(okx_symbols)} | First 10: {okx_symbols[:10]}")
    print(f"  Base symbols: {len(okx_base)} | First 20: {okx_base[:20]}")
    
    print("\n[BITGET]")
    bitget_symbols = get_bitget_symbols()
    bitget_base = get_bitget_base_symbols()
    print(f"  SWAP symbols: {len(bitget_symbols)} | First 10: {bitget_symbols[:10]}")
    print(f"  Base symbols: {len(bitget_base)} | First 20: {bitget_base[:20]}")
    
    print("\n[GATEIO]")
    gateio_symbols = get_gateio_symbols()
    gateio_base = get_gateio_base_symbols()
    print(f"  SWAP symbols: {len(gateio_symbols)} | First 10: {gateio_symbols[:10]}")
    print(f"  Base symbols: {len(gateio_base)} | First 20: {gateio_base[:20]}")
    
    print("\n[MEXC]")
    mexc_symbols = get_mexc_symbols()
    mexc_base = get_mexc_base_symbols()
    print(f"  SWAP symbols: {len(mexc_symbols)} | First 10: {mexc_symbols[:10]}")
    print(f"  Base symbols: {len(mexc_base)} | First 20: {mexc_base[:20]}")
    
    print("\n" + "="*70)

# Example usage:
#if __name__ == "__main__":
    print(json.dumps(all_symbols_per_exchange, indent=2))
    print(json.dumps(all_symbols_base, indent=2))

# Example usage async:
#if __name__ == "__main__":
    asyncio.run(async_get_hyperliquid_symbols())

# Example usage for Binance
#if __name__ == "__main__":
    get_binance_spot_symbols()
