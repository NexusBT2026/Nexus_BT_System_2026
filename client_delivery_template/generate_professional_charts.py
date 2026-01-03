"""
Generate Professional Client Charts
Creates beautiful interactive visualizations for client deliveries
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json


def create_professional_charts(results: dict, symbol: str, strategy_name: str, output_file: str = "performance_report.html"):
    """
    Generate professional interactive charts for client delivery
    
    Args:
        results: Backtest results dictionary
        symbol: Trading pair (e.g., "BTC/USDT")
        strategy_name: Name of the strategy
        output_file: Output HTML filename
    """
    
    if results['total_trades'] == 0:
        print("⚠️  No trades to visualize")
        return
    
    # Create figure with subplots - CLEAN 2x3 LAYOUT
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            '📈 Equity Curve', '📊 Trade Distribution', '💰 Cumulative P&L',
            '🎯 Win/Loss Ratio', '📉 Drawdown Analysis', '🔢 Performance Metrics'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'bar'}, {'type': 'scatter'}],
            [{'type': 'pie'}, {'type': 'scatter'}, {'type': 'table'}]
        ],
        vertical_spacing=0.30,
        horizontal_spacing=0.15
    )
    
    trades = results['trades']
    trades_df = pd.DataFrame(trades)
    
    # 1. Equity Curve - FIXED: Properly calculate capital growth
    initial_capital = results.get('initial_capital', 10000)
    equity = [initial_capital]
    
    for trade in trades:
        # Add P&L scaled by capital (assuming position size)
        pnl_amount = trade['pnl'] * 1000  # Scale P&L to dollar amount
        equity.append(equity[-1] + pnl_amount)
    
    fig.add_trace(
        go.Scatter(
            x=list(range(len(equity))),
            y=equity,
            mode='lines',
            name='Equity',
            line=dict(color='#00D4FF', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.1)'
        ),
        row=1, col=1
    )
    
    # 2. Trade Distribution (Win/Loss)
    wins = len([t for t in trades if t['pnl'] > 0])
    losses = len([t for t in trades if t['pnl'] <= 0])
    
    fig.add_trace(
        go.Bar(
            x=['Win', 'Loss'],
            y=[wins, losses],
            marker_color=['#00FF88', '#FF4444'],
            text=[wins, losses],
            textposition='auto',
            name='Trades',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Cumulative P&L
    cumulative_pnl = []
    total = 0
    for t in trades:
        total += t['pnl']
        cumulative_pnl.append(total)
    
    fig.add_trace(
        go.Scatter(
            x=list(range(len(cumulative_pnl))),
            y=cumulative_pnl,
            mode='lines+markers',
            name='Cumulative P&L',
            line=dict(color='#FFD700', width=2),
            marker=dict(size=4),
            showlegend=False
        ),
        row=1, col=3
    )
    
    # 4. Win/Loss Pie Chart
    fig.add_trace(
        go.Pie(
            labels=['Win', 'Loss'],
            values=[wins, losses],
            marker_colors=['#00FF88', '#FF4444'],
            hole=0.4,
            textinfo='percent',
            textfont_size=11,
            showlegend=True
        ),
        row=2, col=1
    )
    
    # 5. Drawdown Analysis - Now spans 2 columns for better visibility
    peak = equity[0]
    drawdowns = []
    for e in equity:
        if e > peak:
            peak = e
        dd = ((peak - e) / peak) * 100
        drawdowns.append(-dd)
    
    fig.add_trace(
        go.Scatter(
            x=list(range(len(drawdowns))),
            y=drawdowns,
            mode='lines',
            name='Drawdown %',
            line=dict(color='#FF6B6B', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)',
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Returns Distribution - REMOVED (not useful for clients)
    
    # 6. Performance Metrics Table - COMPACT
    metrics_table = [
        ['Return', f"{results['total_return_pct']:.2f}%"],
        ['Win Rate', f"{results['win_rate']:.2f}%"],
        ['Trades', str(results['total_trades'])],
        ['Sharpe', f"{results['sharpe_ratio']:.2f}"],
        ['Max DD', f"{results['max_drawdown']:.2f}%"],
        ['P.Factor', f"{results['profit_factor']:.2f}"]
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='#00D4FF',
                align='left',
                font=dict(color='white', size=13)
            ),
            cells=dict(
                values=[[m[0] for m in metrics_table], [m[1] for m in metrics_table]],
                fill_color=['#F0F0F0', 'white'],
                align='left',
                font=dict(size=12),
                height=28
            )
        ),
        row=2, col=3
    )
    
    # Update layout - CLEAN, NO UGLY BOXES
    fig.update_layout(
        title=dict(
            text=f"<b style='font-size:28px'>{strategy_name}</b><br><span style='font-size:20px'>{symbol}</span>",
            font=dict(size=22, color='#1a1a1a'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        height=950,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=12, color='#333333'),
        margin=dict(t=100, b=50, l=60, r=60),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    # Simple grid lines only - NO BOXES
    fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8', zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor='#E8E8E8', zeroline=False)
    
    # Save to HTML
    fig.write_html(
        output_file,
        config={'displayModeBar': True, 'displaylogo': False},
        include_plotlyjs='cdn'
    )
    
    print(f"✅ Professional report saved: {output_file}")
    print(f"   Open in browser to view interactive charts!")
    
    return fig


def create_candlestick_chart(results: dict, symbol: str, strategy_name: str, ohlcv_data: pd.DataFrame, output_file: str = "candlestick_chart.html"):
    """
    Generate standalone candlestick chart with trade entry/exit markers
    
    Args:
        results: Backtest results dictionary
        symbol: Trading pair
        strategy_name: Name of the strategy
        ohlcv_data: DataFrame with columns: timestamp, open, high, low, close, volume
        output_file: Output HTML filename
    """
    
    if ohlcv_data is None or ohlcv_data.empty:
        print("⚠️  No OHLCV data")
        return
    
    trades = results['trades']
    
    # Create figure
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=ohlcv_data['timestamp'],
            open=ohlcv_data['open'],
            high=ohlcv_data['high'],
            low=ohlcv_data['low'],
            close=ohlcv_data['close'],
            name='Price',
            increasing_line_color='#00FF88',
            decreasing_line_color='#FF4444'
        )
    )
    
    # Entry markers
    entry_times = []
    entry_prices = []
    for trade in trades:
        if 'entry_idx' in trade and trade['entry_idx'] < len(ohlcv_data):
            entry_times.append(ohlcv_data.iloc[trade['entry_idx']]['timestamp'])
            entry_prices.append(trade['entry'])
    
    if entry_times:
        fig.add_trace(
            go.Scatter(
                x=entry_times,
                y=entry_prices,
                mode='markers+text',
                name='Entry',
                marker=dict(symbol='triangle-up', size=15, color='#00FF88', line=dict(color='white', width=2)),
                text=['▲' for _ in entry_times],
                textposition='bottom center',
                textfont=dict(size=16, color='#00FF88', family='Arial Black')
            )
        )
    
    # Exit markers
    exit_times = []
    exit_prices = []
    for trade in trades:
        if 'exit_idx' in trade and trade['exit_idx'] < len(ohlcv_data):
            exit_times.append(ohlcv_data.iloc[trade['exit_idx']]['timestamp'])
            exit_prices.append(trade['exit'])
    
    if exit_times:
        fig.add_trace(
            go.Scatter(
                x=exit_times,
                y=exit_prices,
                mode='markers+text',
                name='Exit',
                marker=dict(symbol='triangle-down', size=15, color='#FF6B6B', line=dict(color='white', width=2)),
                text=['▼' for _ in exit_times],
                textposition='top center',
                textfont=dict(size=16, color='#FF6B6B', family='Arial Black')
            )
        )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f"<b style='font-size:32px'>{strategy_name}</b><br><span style='font-size:24px'>{symbol} - Price Action & Trade Signals</span>",
            font=dict(size=26, color='#1a1a1a'),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis=dict(rangeslider=dict(visible=False), showgrid=True, gridcolor='#E8E8E8'),
        yaxis=dict(showgrid=True, gridcolor='#E8E8E8'),
        height=800,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=13, color='#333333'),
        margin=dict(t=120, b=60, l=80, r=80),
        plot_bgcolor='white',
        paper_bgcolor='#FAFAFA'
    )
    
    fig.write_html(output_file, config={'displayModeBar': True, 'displaylogo': False}, include_plotlyjs='cdn')
    print(f"✅ Candlestick chart saved: {output_file}")
    
    return fig


if __name__ == "__main__":
    print("Professional Chart Generator")
    print("This tool creates beautiful interactive reports for clients")
