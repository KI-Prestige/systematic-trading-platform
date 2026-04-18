import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys
import ta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader
from src.live.order_logger import OrderLogger
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Systematic Trading Platform", layout="wide")
st.title("📊 Systematic Trading Platform")

tab1, tab2, tab3 = st.tabs(["📈 Backtest Results", "📡 Latest Signals + Charts", "💼 Paper Portfolio"])

# ====================== TAB 2: Latest Signals + Charts ======================
with tab2:
    st.subheader("📡 Latest Trading Signals with Charts")
    
    if st.button("🔄 Refresh Signals & Charts"):
        with st.spinner("Generating latest signals and charts..."):
            sg = SignalGenerator()
            signals = sg.get_all_signals()
            
            for symbol, sig in signals.items():
                with st.expander(f"**{symbol}** — {sig['signal'].upper()} | Price ${sig['latest_price']} | Size {sig['suggested_size']}", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.metric("Signal", sig['signal'].upper(), delta=None)
                        st.write("**Reason:**")
                        st.info(sig['reason'])
                        st.write(f"**ADX:** {sig.get('adx', 'N/A')}")
                        st.write(f"**Volatility:** {sig.get('volatility', 'N/A')}")
                    
                    with col2:
                        # Generate interactive chart
                        df = sg.fetcher.fetch_and_cache([symbol])
                        data = df[df['symbol'] == symbol].copy()
                        data.set_index('date', inplace=True)
                        data = data.sort_index().tail(120)  # Last 120 days for clarity
                        
                        # Calculate indicators for chart
                        data['short_sma'] = data['Close'].rolling(20).mean()
                        data['long_sma'] = data['Close'].rolling(50).mean()
                        data['adx'] = ta.trend.ADXIndicator(high=data['High'], low=data['Low'], close=data['Close'], window=14).adx()
                        
                        # Create subplot
                        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                          row_heights=[0.5, 0.2, 0.3], vertical_spacing=0.05)
                        
                        # Price + SMAs
                        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name="Close Price", line=dict(color="blue")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['short_sma'], name="Short SMA (20)", line=dict(color="orange")), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['long_sma'], name="Long SMA (50)", line=dict(color="red")), row=1, col=1)
                        
                        # ADX
                        fig.add_trace(go.Scatter(x=data.index, y=data['adx'], name="ADX", line=dict(color="purple")), row=2, col=1)
                        fig.add_hline(y=25, line_dash="dash", line_color="gray", row=2, col=1)
                        
                        # Volume
                        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name="Volume", marker_color="lightblue"), row=3, col=1)
                        
                        fig.update_layout(height=700, title_text=f"{symbol} - Golden Cross Strategy Analysis (Last 120 days)")
                        fig.update_yaxes(title_text="Price", row=1, col=1)
                        fig.update_yaxes(title_text="ADX", row=2, col=1)
                        fig.update_yaxes(title_text="Volume", row=3, col=1)
                        
                        st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Run `python main.py` daily to generate new signals and potential paper orders.")

# ====================== Other Tabs (kept minimal) ======================
with tab1:
    st.info("Backtest results coming in future phases...")

with tab3:
    st.subheader("💼 Paper Portfolio")
    if st.button("🔄 Refresh Paper Portfolio"):
        try:
            logger = OrderLogger()
            trader = PaperTrader()
            equity, cash = trader.get_account()
            
            st.metric("Equity", f"${equity:,.2f}")
            st.metric("Cash", f"${cash:,.2f}")
            
            history = logger.get_trade_history()
            if not history.empty:
                st.dataframe(history.head(15), use_container_width=True)
            else:
                st.info("No orders yet.")
        except Exception as e:
            st.error(f"Error: {e}")