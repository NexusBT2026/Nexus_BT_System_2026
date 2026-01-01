"""
Nexus Backtesting System - Display Icons
Provides icons (emojis or ASCII) based on terminal encoding support.
"""

import sys

def get_icons():
    """Get display icons based on terminal encoding support."""
    is_utf8 = sys.stdout.encoding and 'utf' in sys.stdout.encoding.lower()
    if is_utf8:
        return {
            'python': '🐍',
            'package': '📦',
            'config': '⚙️',
            'folder': '📁',
            'wrench': '🔧',
            'target': '🎯',
            'chart': '📊',
            'party': '🎉',
            'check': '✅',
            'cross': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'gear': '⚙️',
            'rocket': '🚀',
            'cpu': '🖥️',
            'memory': '💾',
            'disk': '💿',
            'strategy': '🎯',
            'data': '📊',
            'health': '❤️',
            'results': '📈',
            'note': '📝',
            'search': '🔍',
            'hospital': '🏥',
            'book': '📖',
            'recycle': '🔄',
            'zap': '⚡',
            'game': '🎮',
            'phone': '📞',
            'bug': '🐛',
            'pray': '🙏'
        }
    else:
        return {
            'python': '[PYTHON]',
            'package': '[PKG]',
            'config': '[CFG]',
            'folder': '[DIR]',
            'wrench': '[TOOL]',
            'target': '[AIM]',
            'chart': '[STATS]',
            'party': '[DONE]',
            'check': '[OK]',
            'cross': '[FAIL]',
            'warning': '[WARN]',
            'info': '[INFO]',
            'gear': '[CFG]',
            'rocket': '[START]',
            'cpu': '[CPU]',
            'memory': '[MEM]',
            'disk': '[DISK]',
            'strategy': '[STRAT]',
            'data': '[DATA]',
            'health': '[HEALTH]',
            'results': '[RESULTS]',
            'note': '[NOTE]',
            'search': '[SEARCH]',
            'hospital': '[HEALTH]',
            'book': '[DOC]',
            'recycle': '[LOOP]',
            'zap': '[FAST]',
            'game': '[GAME]',
            'phone': '[CALL]',
            'bug': '[BUG]',
            'pray': '[THANKS]'
        }

icons = get_icons()