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

st.set_page_config(page_title="Systematic Trading Platform", layout="wide")
st.title("📊 Systematic Trading Platform - Full View")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Backtest Results", "📡 Latest Signals + Charts", "💼 Paper Portfolio", "📋 Trade Log"])

# ====================== TAB 1: Backtest Results ======================
with tab1:
    st.subheader("📈 Backtest Performance")
    if st.button("🔄 Refresh Backtest Results"):
        with st.spinner("Running backtest..."):
            from src.backtester.backtester import Backtester
            bt = Backtester()
            bt.run(start_date="2024-01-01")
            
            st.success("Backtest completed!")
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            equity_df = pd.DataFrame(bt.equity_curve)
            total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100 if len(equity_df) > 0 else 0
            
            col1.metric("Total Return", f"{total_return:.2f}%")
            col2.metric("Total Trades", len(bt.trades))
            col3.metric("Max Drawdown", f"{min((pd.DataFrame(bt.equity_curve)['equity'].values - np.maximum.accumulate(pd.DataFrame(bt.equity_curve)['equity'].values)) / np.maximum.accumulate(pd.DataFrame(bt.equity_curve)['equity'].values) * 100):.2f}%")
            col4.metric("Sharpe Ratio", f"{(pd.DataFrame(bt.equity_curve)['equity'].pct_change().mean() / pd.DataFrame(bt.equity_curve)['equity'].pct_change().std() * np.sqrt(252)):.2f}" if len(pd.DataFrame(bt.equity_curve)) > 1 else "N/A")
            
            # Show equity curve
            st.image("backtests/enhanced_equity_drawdown.png", use_column_width=True)
            
            # Monthly returns
            if len(equity_df) > 0:
                equity_df.index = pd.to_datetime(equity_df['date'])
                monthly = equity_df['equity'].resample('ME').last().pct_change() * 100
                st.subheader("Monthly Returns (%)")
                st.dataframe(monthly.round(2), use_container_width=True)

# ====================== TAB 2: Latest Signals + Charts ======================
with tab2:
    st.subheader("📡 Latest Trading Signals with Charts")
    if st.button("🔄 Refresh Signals & Charts"):
        with st.spinner("Generating signals..."):
            sg = SignalGenerator()
            signals = sg.get_all_signals()
            
            for symbol, sig in signals.items():
                with st.expander(f"**{symbol}** — {sig['signal'].upper()} | Price ${sig.get('latest_price', 'N/A')} | Size {sig.get('suggested_size', 'N/A')}", expanded=False):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Signal", sig['signal'].upper())
                        st.info(sig['reason'])
                    with col2:
                        df = sg.fetcher.fetch_and_cache([symbol])
                        data = df[df['symbol'] == symbol].copy()
                        data.set_index('date', inplace=True)
                        data = data.tail(120)
                        data['short_sma'] = data['Close'].rolling(20).mean()
                        data['long_sma'] = data['Close'].rolling(50).mean()
                        data['adx'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close'], 14).adx()
                        
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots
                        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.2, 0.3])
                        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close", line=dict(color="blue")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['short_sma'], name="Short SMA", line=dict(color="orange")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['long_sma'], name="Long SMA", line=dict(color="red")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['adx'], name="ADX", line=dict(color="purple")), row=2, col=1)
                        fig.add_hline(y=20, line_dash="dash", line_color="gray", row=2, col=1)
                        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name="Volume", marker_color="lightblue"), row=3, col=1)
                        fig.update_layout(height=700, title=f"{symbol} Analysis")
                        st.plotly_chart(fig, use_container_width=True)

# ====================== TAB 3: Paper Portfolio ======================
with tab3:
    st.subheader("💼 Paper Portfolio")
    if st.button("🔄 Refresh Paper Portfolio"):
        try:
            logger = OrderLogger()
            trader = PaperTrader()
            equity, cash = trader.get_account()
            
            col1, col2 = st.columns(2)
            col1.metric("Equity", f"${equity:,.2f}")
            col2.metric("Cash", f"${cash:,.2f}")
            
            history = logger.get_trade_history()
            if not history.empty:
                st.dataframe(history.head(15), use_container_width=True)
            else:
                st.info("No orders yet.")
        except Exception as e:
            st.error(f"Error: {e}")

# ====================== TAB 4: Trade Log ======================
with tab4:
    st.subheader("📋 Full Trade Log")
    if st.button("🔄 Load Trade Log"):
        try:
            log_path = "backtests/trade_log.csv"
            if os.path.exists(log_path):
                trade_log = pd.read_csv(log_path)
                st.dataframe(trade_log, use_container_width=True)
            else:
                st.info("No trade log found. Run backtester first.")
        except Exception as e:
            st.error(f"Error loading trade log: {e}")

st.caption("Run `python main.py` daily | Backtester: `python src/backtester/backtester.py`")

