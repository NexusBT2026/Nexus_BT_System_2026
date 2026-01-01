import streamlit as st
import pandas as pd
import plotly.express as px
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

st.set_page_config(page_title="Strategy Performance Dashboard", layout="wide")

st.title("Strategy Performance Dashboard")

# Set your results directory here
RESULTS_DIR = os.path.join(project_root, 'results')

# Load data
abs_params_path = os.path.join(RESULTS_DIR, "absolute_params.csv")
all_qualified_path = os.path.join(RESULTS_DIR, "all_qualified_results.csv")

@st.cache_data
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

abs_params = load_data(abs_params_path)
all_qualified = load_data(all_qualified_path)

if abs_params is not None:
    st.subheader("Top Strategies (absolute_params.csv)")
    st.dataframe(abs_params.head(50))

    # Filters
    symbols = abs_params['symbol'].unique()
    strategies = abs_params['strategy_name'].unique() if 'strategy_name' in abs_params.columns else abs_params['strategy'].unique()
    symbol = st.selectbox("Filter by Symbol", [None] + list(symbols))
    strategy = st.selectbox("Filter by Strategy", [None] + list(strategies))
    filtered = abs_params.copy()
    if symbol:
        filtered = filtered[filtered['symbol'] == symbol]
    if strategy:
        col = 'strategy_name' if 'strategy_name' in filtered.columns else 'strategy'
        filtered = filtered[filtered[col] == strategy]

    st.write(f"Showing {len(filtered)} strategies")
    st.dataframe(filtered)

    # Show detailed stats for selected symbol and strategy
    if symbol and strategy:
        st.subheader(f"Detailed Results for {symbol} / {strategy}")
        # Try both possible strategy column names
        strat_col = 'strategy_name' if 'strategy_name' in filtered.columns else 'strategy'
        timeframe = None
        if not filtered.empty:
            timeframe = filtered.iloc[0]['timeframe'] if 'timeframe' in filtered.columns else None
        if timeframe:
            # Build path to JSON file
            json_path = os.path.join(RESULTS_DIR, symbol, str(timeframe), f"results_{strategy}_strategy.json")
            if os.path.exists(json_path):
                import json
                with open(json_path, 'r') as f:
                    result = json.load(f)
                # Show summary stats
                st.json(result)
                # Show pie chart for win/loss trades if available
                stats = result.get('stats', {})
                if stats and 'winning_trades' in stats and 'losing_trades' in stats:
                    win = int(stats['winning_trades'])
                    loss = int(stats['losing_trades'])
                    fig = px.pie(names=['Winning Trades', 'Losing Trades'], values=[win, loss], title='Winning vs Losing Trades')
                    st.plotly_chart(fig, use_container_width=True)
                # Show gauges for win rate, sharpe, return
                col1, col2, col3 = st.columns(3)
                with col1:
                    wr = result.get('win_rate') or stats.get('win_rate')
                    if wr is not None:
                        st.metric('Win Rate (%)', f"{float(wr)*100 if float(wr)<=1 else float(wr):.2f}")
                with col2:
                    sharpe = result.get('sharpe') or stats.get('sharpe')
                    if sharpe is not None:
                        st.metric('Sharpe Ratio', f"{float(sharpe):.2f}")
                with col3:
                    ret = result.get('return_pct')
                    if ret is not None:
                        st.metric('Return (%)', f"{float(ret):.2f}")
            else:
                st.info(f"No detailed result file found for {symbol} / {strategy} / {timeframe}")
        else:
            st.info("No timeframe found for this selection.")

    # Plots
    st.subheader("Performance Distributions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if 'win_rate' in filtered.columns:
            fig = px.histogram(filtered, x='win_rate', nbins=20, title='Win Rate Distribution')
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if 'sharpe' in filtered.columns:
            fig = px.histogram(filtered, x='sharpe', nbins=20, title='Sharpe Ratio Distribution')
            st.plotly_chart(fig, use_container_width=True)
    with col3:
        profit_col = 'net_profit' if 'net_profit' in filtered.columns else ('return_pct' if 'return_pct' in filtered.columns else None)
        if profit_col:
            fig = px.histogram(filtered, x=profit_col, nbins=20, title=f'{profit_col} Distribution')
            st.plotly_chart(fig, use_container_width=True)

    # Heatmap
    st.subheader("Win Rate Heatmap (Symbol vs Strategy)")
    strat_col = 'strategy_name' if 'strategy_name' in filtered.columns else 'strategy'
    if {'symbol', strat_col, 'win_rate'}.issubset(filtered.columns):
        pivot = filtered.pivot_table(index='symbol', columns=strat_col, values='win_rate', aggfunc='mean')
        st.dataframe(pivot)
        fig = px.imshow(pivot, aspect='auto', color_continuous_scale='viridis', title='Average Win Rate by Symbol and Strategy')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"Could not find {abs_params_path}. Please run the pipeline and ensure results are available.")

st.markdown("---")
st.caption("Built with Streamlit. Data source: absolute_params.csv and all_qualified_results.csv")
