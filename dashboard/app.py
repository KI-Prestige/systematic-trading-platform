import streamlit as st
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtester.backtester import SimpleBacktester

st.set_page_config(page_title="Quant Trading Platform", layout="wide")
st.title("🚀 Systematic Trading Platform")
st.markdown("**Production-grade backtesting & risk dashboard** – Junior Quant Developer Portfolio Project")

st.sidebar.header("Controls")
if st.sidebar.button("Run Full Backtest"):
    with st.spinner("Running backtest on all symbols..."):
        bt = SimpleBacktester(transaction_cost=0.001)
        results = bt.run_on_all_symbols()
        
        for symbol, res in results.items():
            st.subheader(symbol)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Return", f"{res['total_return']:.2%}")
            col2.metric("Sharpe Ratio", f"{res['sharpe_ratio']:.2f}")
            col3.metric("Max Drawdown", f"{res['max_drawdown_pct']:.2f}%")
            col4.metric("Trades", res['num_trades'])
        
        st.success("Backtest completed successfully!")

st.info("✅ Data cached | ✅ Risk-managed SMA strategy | ✅ Walk-forward validation")
st.caption("Next: Paper-trading integration and cloud deployment")