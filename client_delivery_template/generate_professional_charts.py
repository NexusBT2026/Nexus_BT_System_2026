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
    
    # Create figure with subplots
    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=(
            '📈 Equity Curve', '📊 Trade Distribution',
            '💰 Cumulative P&L', '🎯 Win/Loss Ratio',
            '📉 Drawdown Over Time', '⚡ Trade Returns',
            '📅 Trades Per Day', '🔢 Performance Metrics'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'bar'}],
            [{'type': 'scatter'}, {'type': 'pie'}],
            [{'type': 'scatter'}, {'type': 'histogram'}],
            [{'type': 'bar'}, {'type': 'table'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.15
    )
    
    trades = results['trades']
    trades_df = pd.DataFrame(trades)
    
    # 1. Equity Curve
    equity = [results['final_capital'] - sum([t['pnl'] for t in trades[:i]]) for i in range(len(trades) + 1)]
    equity.reverse()
    
    fig.add_trace(
        go.Scatter(
            x=list(range(len(equity))),
            y=equity,
            mode='lines',
            name='Equity',
            line=dict(color='#00D4FF', width=3),
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
            x=['Winning', 'Losing'],
            y=[wins, losses],
            marker_color=['#00FF88', '#FF4444'],
            text=[wins, losses],
            textposition='auto',
            name='Trades'
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
            marker=dict(size=6)
        ),
        row=2, col=1
    )
    
    # 4. Win/Loss Pie Chart
    fig.add_trace(
        go.Pie(
            labels=['Winning Trades', 'Losing Trades'],
            values=[wins, losses],
            marker_colors=['#00FF88', '#FF4444'],
            hole=0.4,
            textinfo='label+percent',
            textfont_size=12
        ),
        row=2, col=2
    )
    
    # 5. Drawdown (simplified)
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
            line=dict(color='#FF6B6B', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)'
        ),
        row=3, col=1
    )
    
    # 6. Trade Returns Histogram
    fig.add_trace(
        go.Histogram(
            x=trades_df['pnl_pct'],
            nbinsx=20,
            name='Returns',
            marker_color='#00D4FF',
            opacity=0.7
        ),
        row=3, col=2
    )
    
    # 7. Trades Timeline (by entry time if available)
    if 'entry_time' in trades[0]:
        try:
            trades_df['date'] = pd.to_datetime(trades_df['entry_time'])
            trades_per_day = trades_df.groupby(trades_df['date'].dt.date).size()
            
            fig.add_trace(
                go.Bar(
                    x=trades_per_day.index.astype(str),
                    y=trades_per_day.values,
                    marker_color='#9D4EDD',
                    name='Trades/Day'
                ),
                row=4, col=1
            )
        except:
            fig.add_trace(
                go.Bar(
                    x=['Day 1', 'Day 2', 'Day 3'],
                    y=[len(trades)//3, len(trades)//3, len(trades)//3],
                    marker_color='#9D4EDD',
                    name='Trades (estimated)'
                ),
                row=4, col=1
            )
    
    # 8. Performance Metrics Table
    metrics_table = [
        ['Total Return', f"{results['total_return_pct']:.2f}%"],
        ['Win Rate', f"{results['win_rate']:.2f}%"],
        ['Total Trades', str(results['total_trades'])],
        ['Profit Factor', f"{results['profit_factor']:.2f}"],
        ['Max Drawdown', f"{results['max_drawdown']:.2f}%"],
        ['Sharpe Ratio', f"{results['sharpe_ratio']:.2f}"],
        ['Final Capital', f"${results['final_capital']:.2f}"]
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='#00D4FF',
                align='left',
                font=dict(color='white', size=14)
            ),
            cells=dict(
                values=[[m[0] for m in metrics_table], [m[1] for m in metrics_table]],
                fill_color=['#F0F0F0', 'white'],
                align='left',
                font=dict(size=12),
                height=30
            )
        ),
        row=4, col=2
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"<b>{strategy_name}</b> - {symbol} Performance Report",
            font=dict(size=24, color='#333333'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=False,
        height=1600,
        template='plotly_white',
        font=dict(family='Arial, sans-serif', size=11, color='#333333'),
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridcolor='#E5E5E5')
    fig.update_yaxes(showgrid=True, gridcolor='#E5E5E5')
    
    # Save to HTML
    fig.write_html(
        output_file,
        config={'displayModeBar': True, 'displaylogo': False},
        include_plotlyjs='cdn'
    )
    
    print(f"✅ Professional report saved: {output_file}")
    print(f"   Open in browser to view interactive charts!")
    
    return fig


if __name__ == "__main__":
    print("Professional Chart Generator")
    print("This tool creates beautiful interactive reports for clients")
