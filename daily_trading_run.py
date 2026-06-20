# daily_trading_run.py - Robust Version with Retry
import pandas as pd
from datetime import datetime
import sys
import os
import time
import traceback
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from config import SYMBOLS
from src.strategies.signal_generator import SignalGenerator
from src.live.paper_trader import PaperTrader
from src.live.order_logger import OrderLogger

def daily_run():
    print(f"\n{'='*80}")
    print(f"🚀 DAILY TRADING RUN STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    try:
        # 1. Generate Latest Signals
        print("📡 Generating Latest Signals...")
        sg = SignalGenerator()
        signals = sg.get_all_signals()

        print("\n=== CURRENT SIGNALS ===")
        active_signals = 0
        for symbol, sig in signals.items():
            print(f"{symbol}: {sig['signal'].upper()} | Price ${sig.get('latest_price',0):.2f} | Size {sig.get('suggested_size',0)}")
            print(f"   → {sig.get('reason','No reason')}")
            if sig['signal'] != "hold":
                active_signals += 1

        # 2. Execute Paper Trades with Retry
        print("\n💼 Executing Safe Paper Orders...")
        trader = PaperTrader()
        logger = OrderLogger()
        
        # Retry logic for Alpaca connection
        max_retries = 3
        for attempt in range(max_retries):
            try:
                trader.get_account()
                print("✅ Connected to Alpaca Paper Trading")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Connection attempt {attempt+1} failed. Retrying in 5s...")
                    time.sleep(5)
                else:
                    print(f"❌ Failed to connect to Alpaca after {max_retries} attempts")
                    raise

        current_positions = logger.get_current_positions()
        print(f"Current Positions: {current_positions}")

        executed = 0
        for symbol, sig in signals.items():
            if sig['signal'] in ["buy", "sell"] and sig.get('suggested_size', 0) > 0:
                try:
                    trader.submit_safe_order(
                        symbol, 
                        sig['signal'], 
                        sig.get('suggested_size', 0), 
                        logger=logger
                    )
                    executed += 1
                    print(f"✅ Submitted {sig['signal'].upper()} order for {symbol}")
                except Exception as e:
                    print(f"❌ Failed to submit order for {symbol}: {e}")

        print(f"\n✅ Daily Run Completed - {executed} orders submitted")

    except Exception as e:
        print(f"\n❌ ERROR during daily run: {e}")
        traceback.print_exc()
        with open("daily_run_errors.log", "a") as f:
            f.write(f"\n{datetime.now()} - ERROR: {e}\n")
            traceback.print_exc(file=f)

if __name__ == "__main__":
    daily_run()