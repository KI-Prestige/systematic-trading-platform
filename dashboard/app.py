import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtester.backtester import SimpleBacktester

st.title("Systematic Trading Platform Dashboard")
st.markdown("### Portfolio Overview & Backtest Results")

# Run backtest
if st.button("Run Backtest on All Symbols"):
    bt = SimpleBacktester()
    results = bt.run_on_all_symbols()
    
    for symbol, res in results.items():
        st.subheader(symbol)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Return", f"{res['total_return']:.2%}")
        col2.metric("Sharpe Ratio", f"{res['sharpe_ratio']:.2f}")
        col3.metric("Max Drawdown", f"{res['max_drawdown_pct']:.2f}%")
    
    st.success("Backtest completed!")

st.info("Next steps: Add live paper-trading, more strategies, and risk alerts.")