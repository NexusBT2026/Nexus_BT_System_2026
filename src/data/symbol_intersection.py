"""
symbol_intersection.py: Utility functions for intersecting, filtering, and normalizing symbol lists from multiple exchanges.
Imports symbol discovery logic from symbol_discovery.py and exposes intersection/filtering utilities for use by schedulers, strategies, etc.
"""
import os
import sys
import asyncio
import pandas as pd

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.data.symbol_discovery import (load_cache_base_symbols, load_cache_per_exchange_format,
                                       get_all_symbols_with_cache_per_exchange_format, get_all_symbols_with_cache_base_symbols,
                                       get_all_phemex_contract_symbols, get_phemex_base_symbols, 
                                       get_hyperliquid_symbols,
                                       get_coinbase_spot_symbols, get_coinbase_base_symbols,
                                       get_binance_spot_symbols, get_binance_base_symbols,
                                       get_kucoin_symbols, get_kucoin_base_symbols )

from src.exchange.logging_utils import setup_logger
#from src.exchange.retry import retry_on_exception

logger = setup_logger('symbol_intersection_source', json_logs=True)

def get_coinbase_base() -> list[str]:
    """
    Helper function to get Coinbase base symbols as a list.
    Extracts base symbols from get_coinbase_base_symbols() DataFrame.
    """
    cb_df = get_coinbase_base_symbols()
    if hasattr(cb_df, 'symbol'):
        return cb_df['symbol'].tolist()
    return [str(x) for x in cb_df]

def get_phemex_base() -> list[str]:
    """
    Helper function to get Phemex base symbols as a list.
    Extracts base symbols from get_phemex_base_symbols() DataFrame.
    """
    pm_df = get_phemex_base_symbols()
    if hasattr(pm_df, 'symbol'):
        return pm_df['symbol'].tolist()
    return [str(x) for x in pm_df]

def get_binance_base() -> list[str]:
    """
    Helper function to get Binance base symbols as a list.
    Extracts base symbols from get_binance_base_symbols() DataFrame.
    """
    bn_df = get_binance_base_symbols()
    if hasattr(bn_df, 'symbol'):
        return bn_df['symbol'].tolist()
    return [str(x) for x in bn_df]

def get_kucoin_base() -> list[str]:
    """
    Helper function to get KuCoin base symbols as a list.
    get_kucoin_base_symbols() already returns a list, not a DataFrame.
    """
    kc_list = get_kucoin_base_symbols()
    # Already returns a list, just return it
    return kc_list

def get_common_base_symbols() -> list[str]:
    """
    Return the intersection of base symbols between ALL 5 exchanges: Coinbase, Phemex, Hyperliquid, Binance, and KuCoin (normalized, deduplicated).
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "coinbase" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [COINBASE], [PHEMEX], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        coinbase_bases = set(get_coinbase_base())
        phemex_bases = set(get_phemex_base())
        
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        # Extract the 'symbol' column as a list of strings
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
        logger.debug(f'[COINBASE]: {len(coinbase_bases)} & [PHEMEX]: {len(phemex_bases)} & [HYPERLIQUID]: {len(hyperliquid_bases)} & [BINANCE]: {len(binance_bases)} & [KUCOIN]: {len(kucoin_bases)}')
    # --- CACHE CHECK END ---
    
    common = coinbase_bases & phemex_bases & hyperliquid_bases & binance_bases & kucoin_bases
    logger.debug(f'[ALL 5 EXCHANGES] Common symbols: {sorted(common)}')
    return sorted(common)

async def async_get_common_base_symbols() -> list[str]:
    """
    Return the intersection of base symbols between ALL 5 exchanges: Coinbase, Phemex, Hyperliquid, Binance, and KuCoin (normalized, deduplicated).
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "coinbase" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [COINBASE], [PHEMEX], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        coinbase_bases = set(get_coinbase_base())
        phemex_bases = set(get_phemex_base())
        
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        # Extract the 'symbol' column as a list of strings
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
        logger.debug(f'[COINBASE]: {len(coinbase_bases)} & [PHEMEX]: {len(phemex_bases)} & [HYPERLIQUID]: {len(hyperliquid_bases)} & [BINANCE]: {len(binance_bases)} & [KUCOIN]: {len(kucoin_bases)}')
    # --- CACHE CHECK END ---
    
    common = coinbase_bases & phemex_bases & hyperliquid_bases & binance_bases & kucoin_bases
    logger.debug(f'[ALL 5 EXCHANGES] Common symbols: {sorted(common)}')
    return sorted(common)

def get_hyperliquid_unmatched_symbols() -> list[str]:
    """
    Return Hyperliquid base symbols that are NOT present on Phemex, Coinbase, Binance, or KuCoin (normalized, deduplicated).
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "hyperliquid" in cache["symbols"] and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [HYPERLIQUID], [PHEMEX], [COINBASE], [BINANCE], and [KUCOIN]')
    else:
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(
        str(s) for s in (
            set(str(x) for x in hyperliquid_bases)
            - set(str(x) for x in phemex_bases)
            - set(str(x) for x in coinbase_bases)
            - set(str(x) for x in binance_bases)
            - set(str(x) for x in kucoin_bases)
        )
    )
    logger.debug(f"[HYPERLIQUID] - [PHEMEX] - [COINBASE] - [BINANCE] - [KUCOIN]: {unmatched}")
    return unmatched

async def async_get_hyperliquid_unmatched_symbols() -> list[str]:
    """
    Return Hyperliquid base symbols that are NOT present on Phemex, Coinbase, Binance, or KuCoin (normalized, deduplicated).
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "hyperliquid" in cache["symbols"] and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [HYPERLIQUID], [PHEMEX], [COINBASE], [BINANCE], and [KUCOIN]')
    else:
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(
        str(s) for s in (
            set(str(x) for x in hyperliquid_bases)
            - set(str(x) for x in phemex_bases)
            - set(str(x) for x in coinbase_bases)
            - set(str(x) for x in binance_bases)
            - set(str(x) for x in kucoin_bases)
        )
    )
    logger.debug(f"[HYPERLIQUID] - [PHEMEX] - [COINBASE] - [BINANCE] - [KUCOIN]: {unmatched}")
    return unmatched

def get_unmatched_coinbase_symbols() -> list[str]:
    """
    Return Coinbase base symbols that are NOT present on Phemex, Hyperliquid, Binance, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "coinbase" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [COINBASE], [PHEMEX], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        coinbase_bases = set(get_coinbase_base())
        phemex_bases = set(get_phemex_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in coinbase_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[COINBASE] - [PHEMEX] - [HYPERLIQUID] - [BINANCE] - [KUCOIN]: {unmatched}')
    return unmatched

async def async_get_unmatched_coinbase_symbols() -> list[str]:
    """
    Return Coinbase base symbols that are NOT present on Phemex, Hyperliquid, Binance, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "coinbase" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [COINBASE], [PHEMEX], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        coinbase_bases = set(get_coinbase_base())
        phemex_bases = set(get_phemex_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in coinbase_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[COINBASE] - [PHEMEX] - [HYPERLIQUID] - [BINANCE] - [KUCOIN]: {unmatched}')
    return unmatched

def get_unmatched_binance_symbols() -> list[str]:
    """
    Return Binance base symbols that are NOT present on Phemex, Hyperliquid, Coinbase, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "binance" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "coinbase" in cache["symbols"] and "kucoin" in cache["symbols"]:
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [BINANCE], [PHEMEX], [HYPERLIQUID], [COINBASE], and [KUCOIN]')
    else:
        binance_bases = set(get_binance_base())
        phemex_bases = set(get_phemex_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        coinbase_bases = set(get_coinbase_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in binance_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[BINANCE] - [PHEMEX] - [HYPERLIQUID] - [COINBASE] - [KUCOIN]: {unmatched}')
    return unmatched

async def async_get_unmatched_binance_symbols() -> list[str]:
    """
    Return Binance base symbols that are NOT present on Phemex, Hyperliquid, Coinbase, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "binance" in cache["symbols"] and "phemex_base" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "coinbase" in cache["symbols"] and "kucoin" in cache["symbols"]:
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [BINANCE], [PHEMEX], [HYPERLIQUID], [COINBASE], and [KUCOIN]')
    else:
        binance_bases = set(get_binance_base())
        phemex_bases = set(get_phemex_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        coinbase_bases = set(get_coinbase_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in binance_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[BINANCE] - [PHEMEX] - [HYPERLIQUID] - [COINBASE] - [KUCOIN]: {unmatched}')
    return unmatched

def get_unmatched_phemex_symbols() -> list[str]:
    """
    Return Phemex base symbols that are NOT present on Coinbase, Hyperliquid, Binance, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [PHEMEX], [COINBASE], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in phemex_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[PHEMEX] - [COINBASE] - [HYPERLIQUID] - [BINANCE] - [KUCOIN]: {unmatched}')
    return unmatched

async def async_get_unmatched_phemex_symbols() -> list[str]:
    """
    Return Phemex base symbols that are NOT present on Coinbase, Hyperliquid, Binance, or KuCoin.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"] and "kucoin" in cache["symbols"]:
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [PHEMEX], [COINBASE], [HYPERLIQUID], [BINANCE], and [KUCOIN]')
    else:
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        kucoin_bases = set(get_kucoin_base())
        
    unmatched = sorted(set(str(s) for s in phemex_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases) - set(str(s) for s in kucoin_bases))
    logger.debug(f'[PHEMEX] - [COINBASE] - [HYPERLIQUID] - [BINANCE] - [KUCOIN]: {unmatched}')
    return unmatched

def get_unmatched_kucoin_symbols() -> list[str]:
    """
    Return KuCoin base symbols that are NOT present on Phemex, Coinbase, Hyperliquid, or Binance.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "kucoin" in cache["symbols"] and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"]:
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [KUCOIN], [PHEMEX], [COINBASE], [HYPERLIQUID], and [BINANCE]')
    else:
        kucoin_bases = set(get_kucoin_base())
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        
    unmatched = sorted(set(str(s) for s in kucoin_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases))
    logger.debug(f'[KUCOIN] - [PHEMEX] - [COINBASE] - [HYPERLIQUID] - [BINANCE]: {unmatched}')
    return unmatched

async def async_get_unmatched_kucoin_symbols() -> list[str]:
    """
    Return KuCoin base symbols that are NOT present on Phemex, Coinbase, Hyperliquid, or Binance.
    """
    # --- CACHE CHECK START ---
    cache = load_cache_base_symbols()
    if cache and "symbols" in cache and "kucoin" in cache["symbols"] and "phemex_base" in cache["symbols"] and "coinbase" in cache["symbols"] and "hyperliquid" in cache["symbols"] and "binance" in cache["symbols"]:
        kucoin_bases = cache["symbols"]["kucoin"]
        if isinstance(kucoin_bases, dict) and "symbol" in kucoin_bases:
            kucoin_bases = kucoin_bases["symbol"]
        kucoin_bases = set(str(s).replace('USDT', '') for s in kucoin_bases if isinstance(s, str))
        
        phemex_bases = cache["symbols"]["phemex_base"]
        if isinstance(phemex_bases, dict) and "symbol" in phemex_bases:
            phemex_bases = phemex_bases["symbol"]
        phemex_bases = set(str(s).replace('USDT', '') for s in phemex_bases if isinstance(s, str))
        
        coinbase_symbols = cache["symbols"]["coinbase"]
        if isinstance(coinbase_symbols, dict) and "symbol" in coinbase_symbols:
            coinbase_symbols = coinbase_symbols["symbol"]
        coinbase_bases = set(s.split('-')[0] for s in coinbase_symbols if isinstance(s, str))
        
        hyperliquid_bases = cache["symbols"]["hyperliquid"]
        if isinstance(hyperliquid_bases, dict) and "symbol" in hyperliquid_bases:
            hyperliquid_bases = hyperliquid_bases["symbol"]
        hyperliquid_bases = set(str(s) for s in hyperliquid_bases if isinstance(s, str))
        
        binance_bases = cache["symbols"]["binance"]
        if isinstance(binance_bases, dict) and "symbol" in binance_bases:
            binance_bases = binance_bases["symbol"]
        binance_bases = set(str(s).replace('USDT', '') for s in binance_bases if isinstance(s, str))
        
        logger.debug('[CACHE] Using cached base symbols for [KUCOIN], [PHEMEX], [COINBASE], [HYPERLIQUID], and [BINANCE]')
    else:
        kucoin_bases = set(get_kucoin_base())
        phemex_bases = set(get_phemex_base())
        coinbase_bases = set(get_coinbase_base())
        hyperliquid_bases_raw = get_hyperliquid_symbols()
        if hasattr(hyperliquid_bases_raw, 'symbol'):
            hyperliquid_bases = set(hyperliquid_bases_raw['symbol'].tolist())
        else:
            hyperliquid_bases = set(hyperliquid_bases_raw)
        binance_bases = set(get_binance_base())
        
    unmatched = sorted(set(str(s) for s in kucoin_bases) - set(str(s) for s in phemex_bases) - set(str(s) for s in coinbase_bases) - set(str(s) for s in hyperliquid_bases) - set(str(s) for s in binance_bases))
    logger.debug(f'[KUCOIN] - [PHEMEX] - [COINBASE] - [HYPERLIQUID] - [BINANCE]: {unmatched}')
    return unmatched

# --- NEW EXCHANGES: Bybit, OKX, Bitget, Gate.io, MEXC ---

def get_bybit_base() -> list[str]:
    """
    Helper function to get Bybit base symbols as a list.
    Extracts base symbols from get_bybit_base_symbols().
    """
    from src.data.symbol_discovery import get_bybit_base_symbols
    return get_bybit_base_symbols()

def get_okx_base() -> list[str]:
    """
    Helper function to get OKX base symbols as a list.
    Extracts base symbols from get_okx_base_symbols().
    """
    from src.data.symbol_discovery import get_okx_base_symbols
    return get_okx_base_symbols()

def get_bitget_base() -> list[str]:
    """
    Helper function to get Bitget base symbols as a list.
    Extracts base symbols from get_bitget_base_symbols().
    """
    from src.data.symbol_discovery import get_bitget_base_symbols
    return get_bitget_base_symbols()

def get_gateio_base() -> list[str]:
    """
    Helper function to get Gate.io base symbols as a list.
    Extracts base symbols from get_gateio_base_symbols().
    """
    from src.data.symbol_discovery import get_gateio_base_symbols
    return get_gateio_base_symbols()

def get_mexc_base() -> list[str]:
    """
    Helper function to get MEXC base symbols as a list.
    Extracts base symbols from get_mexc_base_symbols().
    """
    from src.data.symbol_discovery import get_mexc_base_symbols
    return get_mexc_base_symbols()

def get_unmatched_bybit_symbols() -> list[str]:
    """
    Return symbols that are on Bybit but NOT on any of the original 5 exchanges
    (Phemex, Hyperliquid, Coinbase, Binance, KuCoin).
    """
    bybit_bases: set[str] = set(get_bybit_base())
    phemex_bases: set[str] = set(get_phemex_base())
    coinbase_bases: set[str] = set(get_coinbase_base())
    hyperliquid_bases_raw = get_hyperliquid_symbols()
    if hasattr(hyperliquid_bases_raw, 'symbol'):
        hyperliquid_bases: set[str] = set(hyperliquid_bases_raw['symbol'].tolist())
    else:
        hyperliquid_bases = set(str(x) for x in hyperliquid_bases_raw)
    binance_bases: set[str] = set(get_binance_base())
    kucoin_bases: set[str] = set(get_kucoin_base())
    
    unmatched = sorted(bybit_bases - phemex_bases - coinbase_bases - hyperliquid_bases - binance_bases - kucoin_bases)
    logger.info(f'[BYBIT] Unique symbols not on other exchanges: {len(unmatched)}')
    return unmatched

async def async_get_unmatched_bybit_symbols() -> list[str]:
    """Async version of get_unmatched_bybit_symbols"""
    return await asyncio.to_thread(get_unmatched_bybit_symbols)

def get_unmatched_okx_symbols() -> list[str]:
    """
    Return symbols that are on OKX but NOT on any of the original 5 exchanges.
    """
    okx_bases: set[str] = set(get_okx_base())
    phemex_bases: set[str] = set(get_phemex_base())
    coinbase_bases: set[str] = set(get_coinbase_base())
    hyperliquid_bases_raw = get_hyperliquid_symbols()
    if hasattr(hyperliquid_bases_raw, 'symbol'):
        hyperliquid_bases: set[str] = set(hyperliquid_bases_raw['symbol'].tolist())
    else:
        hyperliquid_bases = set(str(x) for x in hyperliquid_bases_raw)
    binance_bases: set[str] = set(get_binance_base())
    kucoin_bases: set[str] = set(get_kucoin_base())
    
    unmatched = sorted(okx_bases - phemex_bases - coinbase_bases - hyperliquid_bases - binance_bases - kucoin_bases)
    logger.info(f'[OKX] Unique symbols not on other exchanges: {len(unmatched)}')
    return unmatched

async def async_get_unmatched_okx_symbols() -> list[str]:
    """Async version of get_unmatched_okx_symbols"""
    return await asyncio.to_thread(get_unmatched_okx_symbols)

def get_unmatched_bitget_symbols() -> list[str]:
    """
    Return symbols that are on Bitget but NOT on any of the original 5 exchanges.
    """
    bitget_bases: set[str] = set(get_bitget_base())
    phemex_bases: set[str] = set(get_phemex_base())
    coinbase_bases: set[str] = set(get_coinbase_base())
    hyperliquid_bases_raw = get_hyperliquid_symbols()
    if hasattr(hyperliquid_bases_raw, 'symbol'):
        hyperliquid_bases: set[str] = set(hyperliquid_bases_raw['symbol'].tolist())
    else:
        hyperliquid_bases = set(str(x) for x in hyperliquid_bases_raw)
    binance_bases: set[str] = set(get_binance_base())
    kucoin_bases: set[str] = set(get_kucoin_base())
    
    unmatched = sorted(bitget_bases - phemex_bases - coinbase_bases - hyperliquid_bases - binance_bases - kucoin_bases)
    logger.info(f'[BITGET] Unique symbols not on other exchanges: {len(unmatched)}')
    return unmatched

async def async_get_unmatched_bitget_symbols() -> list[str]:
    """Async version of get_unmatched_bitget_symbols"""
    return await asyncio.to_thread(get_unmatched_bitget_symbols)

def get_unmatched_gateio_symbols() -> list[str]:
    """
    Return symbols that are on Gate.io but NOT on any of the original 5 exchanges.
    """
    gateio_bases: set[str] = set(get_gateio_base())
    phemex_bases: set[str] = set(get_phemex_base())
    coinbase_bases: set[str] = set(get_coinbase_base())
    hyperliquid_bases_raw = get_hyperliquid_symbols()
    if hasattr(hyperliquid_bases_raw, 'symbol'):
        hyperliquid_bases: set[str] = set(hyperliquid_bases_raw['symbol'].tolist())
    else:
        hyperliquid_bases = set(str(x) for x in hyperliquid_bases_raw)
    binance_bases: set[str] = set(get_binance_base())
    kucoin_bases: set[str] = set(get_kucoin_base())
    
    unmatched = sorted(gateio_bases - phemex_bases - coinbase_bases - hyperliquid_bases - binance_bases - kucoin_bases)
    logger.info(f'[GATEIO] Unique symbols not on other exchanges: {len(unmatched)}')
    return unmatched

async def async_get_unmatched_gateio_symbols() -> list[str]:
    """Async version of get_unmatched_gateio_symbols"""
    return await asyncio.to_thread(get_unmatched_gateio_symbols)

def get_unmatched_mexc_symbols() -> list[str]:
    """
    Return symbols that are on MEXC but NOT on any of the original 5 exchanges.
    """
    mexc_bases: set[str] = set(get_mexc_base())
    phemex_bases: set[str] = set(get_phemex_base())
    coinbase_bases: set[str] = set(get_coinbase_base())
    hyperliquid_bases_raw = get_hyperliquid_symbols()
    if hasattr(hyperliquid_bases_raw, 'symbol'):
        hyperliquid_bases: set[str] = set(hyperliquid_bases_raw['symbol'].tolist())
    else:
        hyperliquid_bases = set(str(x) for x in hyperliquid_bases_raw)
    binance_bases: set[str] = set(get_binance_base())
    kucoin_bases: set[str] = set(get_kucoin_base())
    
    unmatched = sorted(mexc_bases - phemex_bases - coinbase_bases - hyperliquid_bases - binance_bases - kucoin_bases)
    logger.info(f'[MEXC] Unique symbols not on other exchanges: {len(unmatched)}')
    return unmatched

async def async_get_unmatched_mexc_symbols() -> list[str]:
    """Async version of get_unmatched_mexc_symbols"""
    return await asyncio.to_thread(get_unmatched_mexc_symbols)

# Add more filtering/normalization utilities as needed

# Example usage:
if __name__ == "__main__":
    print("=== Testing Symbol Intersection Functions ===\n")
    
    print("1. Common symbols (all 5 exchanges):")
    common = get_common_base_symbols()
    print(f"   Found {len(common)} common symbols: {common[:5]}...\n")
    
    print("2. Hyperliquid unmatched:")
    hl_unmatched = get_hyperliquid_unmatched_symbols()
    print(f"   Found {len(hl_unmatched)} HL-only symbols: {hl_unmatched[:5]}...\n")
    
    print("3. Coinbase unmatched:")
    cb_unmatched = get_unmatched_coinbase_symbols()
    print(f"   Found {len(cb_unmatched)} CB-only symbols: {cb_unmatched[:5]}...\n")
    
    print("4. Binance unmatched:")
    bn_unmatched = get_unmatched_binance_symbols()
    print(f"   Found {len(bn_unmatched)} BN-only symbols: {bn_unmatched[:5]}...\n")
    
    print("5. Phemex unmatched:")
    pm_unmatched = get_unmatched_phemex_symbols()
    print(f"   Found {len(pm_unmatched)} PM-only symbols: {pm_unmatched[:5]}...\n")
    
    print("6. KuCoin unmatched:")
    kc_unmatched = get_unmatched_kucoin_symbols()
    print(f"   Found {len(kc_unmatched)} KC-only symbols: {kc_unmatched[:5]}...\n")
    
    print("\n" + "="*70)
    print("TESTING NEW EXCHANGES - UNIQUE SYMBOLS")
    print("="*70 + "\n")
    
    print("7. Bybit unmatched (not on original 5 exchanges):")
    bybit_unmatched = get_unmatched_bybit_symbols()
    print(f"   Found {len(bybit_unmatched)} Bybit-only symbols")
    print(f"   First 20: {bybit_unmatched[:20]}\n")
    
    print("8. OKX unmatched (not on original 5 exchanges):")
    okx_unmatched = get_unmatched_okx_symbols()
    print(f"   Found {len(okx_unmatched)} OKX-only symbols")
    print(f"   First 20: {okx_unmatched[:20]}\n")
    
    print("9. Bitget unmatched (not on original 5 exchanges):")
    bitget_unmatched = get_unmatched_bitget_symbols()
    print(f"   Found {len(bitget_unmatched)} Bitget-only symbols")
    print(f"   First 20: {bitget_unmatched[:20]}\n")
    
    print("10. Gate.io unmatched (not on original 5 exchanges):")
    gateio_unmatched = get_unmatched_gateio_symbols()
    print(f"   Found {len(gateio_unmatched)} Gate.io-only symbols")
    print(f"   First 20: {gateio_unmatched[:20]}\n")
    
    print("11. MEXC unmatched (not on original 5 exchanges):")
    mexc_unmatched = get_unmatched_mexc_symbols()
    print(f"   Found {len(mexc_unmatched)} MEXC-only symbols")
    print(f"   First 20: {mexc_unmatched[:20]}\n")
    
    print("="*70)
    print("TOTAL NEW UNIQUE SYMBOLS FROM 5 NEW EXCHANGES")
    print("="*70)
    all_new_unique = set(bybit_unmatched + okx_unmatched + bitget_unmatched + gateio_unmatched + mexc_unmatched)
    print(f"Combined unique symbols: {len(all_new_unique)}")
    print(f"This adds {len(all_new_unique)} NEW symbols to your existing 1600+!")
    print("="*70 + "\n")
    
    print("\n=== Testing Async Functions ===\n")
    asyncio.run(async_get_common_base_symbols())
    asyncio.run(async_get_hyperliquid_unmatched_symbols())
    asyncio.run(async_get_unmatched_coinbase_symbols())
    asyncio.run(async_get_unmatched_binance_symbols())
    asyncio.run(async_get_unmatched_phemex_symbols())
    asyncio.run(async_get_unmatched_kucoin_symbols())
    
