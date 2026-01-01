import logging
import numpy as np
import pandas as pd

def summarize_trading_performance(trades: pd.DataFrame, starting_balance: float) -> dict:
    """
    Generate Freqtrade-style summary metrics for a trading run.
    Args:
        trades: DataFrame with columns ['open_date', 'close_date', 'profit_abs', 'profit_pct', 'side']
        starting_balance: Initial account balance
    Returns:
        Dictionary of summary metrics
    """
    logger = logging.getLogger(__name__)
    if trades.empty:
        logger.warning("No trades to summarize.")
        return {}
    final_balance = starting_balance + trades['profit_abs'].sum()
    total_profit = final_balance - starting_balance
    total_profit_pct = (total_profit / starting_balance) * 100
    trade_count = len(trades)
    win_trades = trades[trades['profit_abs'] > 0]
    loss_trades = trades[trades['profit_abs'] < 0]
    win_rate = len(win_trades) / trade_count if trade_count else 0
    avg_profit = trades['profit_abs'].mean()
    max_drawdown = (trades['profit_abs'].cumsum().cummax() - trades['profit_abs'].cumsum()).max()
    sharpe = (
        trades['profit_abs'].mean() / trades['profit_abs'].std() * np.sqrt(trade_count)
        if trades['profit_abs'].std() > 0 else 0
    )
    summary = {
        'Starting balance': starting_balance,
        'Final balance': final_balance,
        'Total profit': total_profit,
        'Total profit %': total_profit_pct,
        'Trade count': trade_count,
        'Win rate': win_rate,
        'Avg profit': avg_profit,
        'Max drawdown': max_drawdown,
        'Sharpe ratio': sharpe,
    }
    logger.info("\n===== SUMMARY METRICS =====\n" + "\n".join(f"{k}: {v}" for k, v in summary.items()))
    return summary
