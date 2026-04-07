import streamlit as st
import sys
import os
import pandas as pd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.backtester.backtester import SimpleBacktester
from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader
from src.live.order_logger import OrderLogger

st.set_page_config(page_title="Quant Trading Platform", layout="wide")
st.title("🚀 Systematic Trading Platform Dashboard")
st.markdown("**Junior Quant Developer Portfolio** – Data → Signals → Risk → Paper Execution")

tab1, tab2, tab3 = st.tabs(["Backtest", "Live Signals", "Paper Portfolio"])

with tab1:
    if st.button("Run Full Backtest"):
        with st.spinner("Running backtest..."):
            bt = SimpleBacktester()
            results = bt.run_on_all_symbols()
            for symbol, res in results.items():
                st.subheader(symbol)
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Return", f"{res['total_return']:.2%}")
                col2.metric("Sharpe", f"{res['sharpe_ratio']:.2f}")
                col3.metric("Max DD", f"{res['max_drawdown_pct']:.2f}%")

with tab2:
    if st.button("Generate Latest Signals"):
        with st.spinner("Generating signals..."):
            sg = SignalGenerator()
            signals = sg.get_all_signals()
            for symbol, sig in signals.items():
                st.subheader(symbol)
                st.write(f"**Signal:** {sig['signal'].upper()}")
                st.write(f"Price: ${sig['latest_price']:.2f} | Suggested Size: {sig['suggested_position_size']}")
                st.write(f"Reason: {sig['reason']}")

with tab3:
    if st.button("🔄 Refresh Paper Portfolio"):
        with st.spinner("Loading latest paper account and orders..."):
            trader = PaperTrader()
            logger = OrderLogger()
            
            equity, cash = trader.get_account()
            
            st.subheader("Paper Account")
            col1, col2 = st.columns(2)
            col1.metric("Equity", f"${equity:.2f}")
            col2.metric("Cash", f"${cash:.2f}")
            
            st.subheader("Current Positions")
            positions = logger.get_current_positions()
            if positions:
                pos_df = pd.DataFrame(list(positions.items()), columns=["Symbol", "Net Shares"])
                st.dataframe(pos_df)
            else:
                st.info("No open positions yet.")
            
            st.subheader("Recent Orders (Latest First)")
            history = logger.get_trade_history()
            if not history.empty:
                st.dataframe(history.head(15))
            else:
                st.info("No orders logged yet. Run main.py to generate signals and orders.")

st.caption("Built as part of a systematic trading platform for job portfolio | Paper trading only")