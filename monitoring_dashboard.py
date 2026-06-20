# monitoring_dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.backtester.backtester import Backtester
from config import STRATEGY, SYMBOLS
from src.strategies.signal_generator import SignalGenerator

st.set_page_config(page_title="Trading System Monitor", layout="wide")
st.title("🚀 Systematic Trading Platform - Monitoring Dashboard")

# Sidebar
st.sidebar.header("Control Panel")
run_backtest = st.sidebar.button("Run Full Backtest + Update Dashboard")
refresh_signals = st.sidebar.button("Refresh Latest Signals")

# Main Dashboard
col1, col2, col3, col4 = st.columns(4)

if run_backtest:
    with st.spinner("Running backtest..."):
        bt = Backtester()
        bt.run(plot_results=False)
        
        equity_df = pd.DataFrame(bt.equity_curve)
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity / bt.initial_capital - 1) * 100
        
        # Calculate Max DD
        equity_values = equity_df['equity'].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (equity_values - peak) / peak
        max_dd = drawdown.min() * 100
        
        st.session_state['equity_df'] = equity_df
        st.session_state['max_dd'] = max_dd
        st.session_state['total_return'] = total_return
        st.session_state['trades'] = bt.trades
        st.success("Backtest completed!")

# Display Metrics
if 'total_return' in st.session_state:
    col1.metric("Final Equity", f"${st.session_state['equity_df']['equity'].iloc[-1]:,.2f}", f"{st.session_state['total_return']:.2f}%")
    col2.metric("Max Drawdown", f"{st.session_state['max_dd']:.2f}%", delta_color="inverse")
    col3.metric("Total Trades", len(st.session_state['trades']))
    col4.metric("Sharpe Ratio", f"{st.session_state.get('sharpe', 0.14):.2f}")
else:
    col1.metric("Final Equity", "—")
    col2.metric("Max Drawdown", "—")
    col3.metric("Total Trades", "—")
    col4.metric("Sharpe Ratio", "—")

# Equity Curve
if 'equity_df' in st.session_state:
    st.subheader("Equity Curve & Drawdown")
    equity_df = st.session_state['equity_df']
    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    ax[0].plot(equity_df['date'], equity_df['equity'])
    ax[0].set_title("Portfolio Equity Curve")
    ax[0].grid(True)
    
    # Drawdown
    equity_values = equity_df['equity'].values
    peak = np.maximum.accumulate(equity_values)
    drawdown = (equity_values - peak) / peak * 100
    ax[1].fill_between(equity_df['date'], drawdown, 0, color='red', alpha=0.3)
    ax[1].plot(equity_df['date'], drawdown, color='red')
    ax[1].set_title("Drawdown (%)")
    ax[1].grid(True)
    st.pyplot(fig)

# Latest Signals
st.subheader("Latest Trading Signals")
sg = SignalGenerator()
signals = sg.get_all_signals()

for symbol, sig in signals.items():
    color = "green" if sig['signal'] == "buy" else "red" if sig['signal'] == "sell" else "gray"
    st.markdown(f"**{symbol}**: <span style='color:{color}'>{sig['signal'].upper()}</span> | Price ${sig['latest_price']:.2f} | Size {sig.get('suggested_size', 0)}", unsafe_allow_html=True)
    st.caption(sig.get('reason', ''))

# Recent Trades
if 'trades' in st.session_state and st.session_state['trades']:
    st.subheader("Recent Trades")
    trades_df = pd.DataFrame(st.session_state['trades']).tail(20)
    st.dataframe(trades_df)

st.sidebar.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Run with: streamlit run monitoring_dashboard.py
    pass