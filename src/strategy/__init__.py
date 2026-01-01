"""
Strategy package for trading algorithms and signal generation modules.
"""

import os
import sys
import importlib
import inspect

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Dynamically import all strategy classes
strategies = {}
strategy_dir = os.path.dirname(__file__)

for file in os.listdir(strategy_dir):
    if file.endswith('.py') and not file.startswith('__') and 'EXAMPLE' not in file:
        module_name = file[:-3]
        try:
            module = importlib.import_module(f'src.strategy.{module_name}')
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and 'Strategy' in name:
                    strategies[module_name] = obj
                    break  # Assume one class per module
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
            pass  # Skip if import fails

# For testing, manually import the key strategies if not loaded
try:
    from .rsi_divergence_EXAMPLE import RSIDivergenceStrategy
    strategies['rsi_divergence'] = RSIDivergenceStrategy
except ImportError:
    pass

try:
    from .rsi_divergence_with_hold_EXAMPLE import RSIDivergenceStrategy as RSIDivergenceWithHoldStrategy
    strategies['rsi_divergence_with_hold'] = RSIDivergenceWithHoldStrategy
except ImportError:
    pass

try:
    from .macd_ema_atr_strategy_EXAMPLE import MACDEMAATRStrategy
    strategies['macd_ema_atr_strategy'] = MACDEMAATRStrategy
except ImportError:
    pass

try:
    from .macd_ema_atr_strategy_with_hold_EXAMPLE import MACDEMAATRStrategy as MACDEMAATRWithHoldStrategy
    strategies['macd_ema_atr_strategy_with_hold'] = MACDEMAATRWithHoldStrategy
except ImportError:
    pass