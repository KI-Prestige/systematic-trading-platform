# reset_positions.py - Full Reset
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.live.order_logger import OrderLogger
from src.live.paper_trader import PaperTrader

def full_reset():
    print(f"🧹 FULL PORTFOLIO RESET - {datetime.now()}")
    print("="*70)

    # 1. Reset Logger
    logger = OrderLogger()
    logger.clear_positions()   # In-memory

    # 2. Force close any remaining positions via Alpaca
    trader = PaperTrader()
    trader.get_account()
    
    positions = logger.get_current_positions()
    print(f"Current tracked positions before force close: {positions}")

    if positions:
        print("Force-closing remaining positions directly...")
        for symbol, qty in list(positions.items()):
            if qty != 0:
                action = "sell" if qty > 0 else "buy"
                size = abs(qty)
                try:
                    print(f"   Closing {symbol} ({action} {size})...")
                    trader.submit_safe_order(symbol, action, size, logger=logger)
                except Exception as e:
                    print(f"   Failed to close {symbol}: {e}")
    
    # 3. Final Check
    final_positions = logger.get_current_positions()
    print(f"\n✅ Final positions after reset: {final_positions}")
    print("Portfolio should now be flat.")

if __name__ == "__main__":
    full_reset()