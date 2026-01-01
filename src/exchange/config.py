"""
config.py: Configuration loading and validation for Hyperliquid, Phemex, Coinbase, Binance and Kucoin integration.
"""
from typing import Dict, Any
import json
import os

def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    """
    Load and validate config from a JSON file.

    Args:
        config_path (str): Path to the configuration JSON file.

    Returns:
        Dict[str, Any]: Loaded configuration dictionary.

    Raises:
        FileNotFoundError: If the config file does not exist.
        KeyError: If 'secret_key' is missing in the config.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with open(config_path, 'r') as f:
        config = json.load(f)
    if 'secret_key' not in config:
        raise KeyError("Missing 'secret_key' in config.")
    return config

def get_secret_key(config_path: str = 'config.json') -> str:
    """
    Load the secret key from environment variable or config file.
    Environment variable HYPERLIQUID_SECRET_KEY takes precedence.
    """
    secret_key = os.getenv('HYPERLIQUID_SECRET_KEY')
    if secret_key:
        return secret_key
    config = load_config(config_path)
    return config['secret_key']

def get_phemex_api_keys(config_path: str = 'config.json') -> tuple[str, str]:
    """
    Load the Phemex API key and secret from environment variables or config file.
    Environment variables PHEMEX_API_KEY and PHEMEX_API_SECRET take precedence.
    """
    api_key = os.getenv('PHEMEX_API_KEY')
    api_secret = os.getenv('PHEMEX_API_SECRET')
    if api_key and api_secret:
        return api_key, api_secret
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with open(config_path, 'r') as f:
        config = json.load(f)
    if 'phemex_api_key' in config and 'phemex_api_secret' in config:
        return config['phemex_api_key'], config['phemex_api_secret']
    raise KeyError("Missing Phemex API credentials in environment or config.")

def get_coinbase_api_keys(config_path: str = 'config.json') -> tuple[str, str, str]:
    """
    Load the Coinbase API key, secret, and passphrase from environment variables or config file.
    Environment variables COINBASE_API_KEY, COINBASE_API_SECRET, COINBASE_API_PASSPHRASE take precedence.
    Returns: (api_key, api_secret, passphrase)
    """
    api_key = os.getenv('COINBASE_API_KEY')
    api_secret = os.getenv('COINBASE_API_SECRET')
    passphrase = os.getenv('COINBASE_API_PASSPHRASE')
    if api_key and api_secret and passphrase:
        return api_key, api_secret, passphrase
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with open(config_path, 'r') as f:
        config = json.load(f)
    if 'coinbase_api_key' in config and 'coinbase_api_key_secret' in config and 'coinbase_api_passphrase' in config:
        return config['coinbase_api_key'], config['coinbase_api_key_secret'], config['coinbase_api_passphrase']
    raise KeyError("Missing Coinbase API credentials in environment or config.")

def get_binance_api_keys(config_path: str = 'config.json') -> tuple[str, str]:
    """
    Load the Binance API key and secret from environment variables or config file.
    Environment variables BINANCE_API_KEY and BINANCE_API_SECRET take precedence.
    """
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if api_key and api_secret:
        return api_key, api_secret
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with open(config_path, 'r') as f:
        config = json.load(f)
    if 'binance_api_key' in config and 'binance_api_secret' in config:
        return config['binance_api_key'], config['binance_api_secret']
    raise KeyError("Missing Binance API credentials in environment or config.")

def get_kucoin_api_keys(config_path: str = 'config.json') -> tuple[str, str, str]:
    """
    Load the KuCoin API key, secret, and passphrase from environment variables or config file.
    Environment variables KUCOIN_API_KEY, KUCOIN_API_SECRET, KUCOIN_API_PASSPHRASE take precedence.
    """
    api_key = os.getenv('KUCOIN_API_KEY')
    api_secret = os.getenv('KUCOIN_API_SECRET')
    api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE')
    if api_key and api_secret and api_passphrase:
        return api_key, api_secret, api_passphrase
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file not found: {config_path}')
    with open(config_path, 'r') as f:
        config = json.load(f)
    if 'kucoin_api_key' in config and 'kucoin_api_secret' in config and 'kucoin_api_passphrase' in config:
        return config['kucoin_api_key'], config['kucoin_api_secret'], config['kucoin_api_passphrase']
    raise KeyError("Missing KuCoin API credentials in environment or config.")