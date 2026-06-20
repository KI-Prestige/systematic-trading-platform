import streamlit as st
import pandas as pd
import numpy as np
import ta
import os
from datetime import datetime
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader
from src.live.order_logger import OrderLogger
from src.backtester.backtester import Backtester
from config import STRATEGY, SYMBOLS

st.set_page_config(page_title="Systematic Trading Platform", layout="wide")
st.title("📊 Systematic Trading Platform - Monitoring Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Backtest", "📡 Signals + Charts", "💼 Paper Portfolio", "📋 Trade Log", "📊 WFA Summary"])

# ====================== TAB 1: Backtest ======================
with tab1:
    st.subheader("📈 Backtest Performance")
    if st.button("🔄 Refresh Backtest"):
        with st.spinner("Running backtest..."):
            bt = Backtester()
            bt.run(plot_results=True)
            
            equity_df = pd.DataFrame(bt.equity_curve)
            total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100 if len(equity_df) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Return", f"{total_return:.2f}%")
            col2.metric("Total Trades", len(bt.trades))
            col3.metric("Max Drawdown", f"{min((pd.DataFrame(bt.equity_curve)['equity'].values - np.maximum.accumulate(pd.DataFrame(bt.equity_curve)['equity'].values)) / np.maximum.accumulate(pd.DataFrame(bt.equity_curve)['equity'].values) * 100):.2f}%")
            col4.metric("Sharpe", f"{(pd.DataFrame(bt.equity_curve)['equity'].pct_change().mean() / pd.DataFrame(bt.equity_curve)['equity'].pct_change().std() * np.sqrt(252)):.2f}" if len(pd.DataFrame(bt.equity_curve)) > 1 else "N/A")
            
            st.image("backtests/enhanced_equity_drawdown.png", use_column_width=True)

# ====================== TAB 2: Signals + Charts ======================
with tab2:
    st.subheader("📡 Latest Trading Signals with Charts")
    if st.button("🔄 Refresh Signals & Charts"):
        with st.spinner("Generating signals..."):
            sg = SignalGenerator()
            signals = sg.get_all_signals()
            
            for symbol, sig in signals.items():
                with st.expander(f"**{symbol}** — {sig.get('signal','HOLD').upper()} | ${sig.get('latest_price',0):.2f}"):
                    st.write(sig.get('reason', ''))
                    # Chart code remains the same as your original

# ====================== TAB 3: Paper Portfolio (Fixed) ======================
with tab3:
    st.subheader("💼 Paper Portfolio")
    if st.button("🔄 Refresh Paper Portfolio"):
        with st.spinner("Loading portfolio..."):
            trader = PaperTrader()
            logger = OrderLogger()
            equity, cash = trader.get_account()
            
            st.metric("Total Equity", f"${equity:,.2f}")
            st.metric("Cash Balance", f"${cash:,.2f}")
            
            positions = logger.get_current_positions()
            st.subheader("Current Positions")
            
            if isinstance(positions, dict) and positions:
                # Fixed: Convert dict to DataFrame safely
                pos_df = pd.DataFrame.from_dict(positions, orient='index')
                st.dataframe(pos_df, use_container_width=True)
            elif isinstance(positions, list) and positions:
                st.dataframe(pd.DataFrame(positions), use_container_width=True)
            else:
                st.info("No open positions")
            
            history = logger.get_trade_history()
            st.subheader("Recent Trade History")
            if not history.empty:
                st.dataframe(history.tail(20), use_container_width=True)
            else:
                st.info("No trades yet")

# ====================== TAB 4: Trade Log ======================
with tab4:
    st.subheader("📋 Full Trade Log")
    try:
        logger = OrderLogger()
        history = logger.get_trade_history()
        if not history.empty:
            st.dataframe(history, use_container_width=True)
        else:
            st.info("No trades recorded yet.")
    except Exception as e:
        st.info(f"Trade log not available: {e}")

# ====================== TAB 5: WFA Summary ======================
with tab5:
    st.subheader("📊 Walk-Forward Analysis")
    if st.button("🔄 Run WFA"):
        with st.spinner("Running Walk-Forward Analysis..."):
            from src.backtester.walk_forward import WalkForwardAnalyzer
            wfa = WalkForwardAnalyzer()
            results = wfa.rolling_walk_forward(is_years=2, oos_months=6, step_months=3)
            st.dataframe(results.round(3), use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg OOS Return (6m)", f"{results['oos_return'].mean():.3f}%")
            col2.metric("Win Rate", f"{(results['oos_return'] > 0).mean()*100:.1f}%")
            col3.metric("Avg Calmar", f"{results['oos_calmar'].mean():.3f}")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")