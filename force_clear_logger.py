# force_clear_logger.py
import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.live.order_logger import OrderLogger
from src.live.paper_trader import PaperTrader

def force_clear_logger():
    print("🧨 FORCING CLEAR OF ORDER LOGGER...")
    print("="*70)

    # 1. Clear database completely
    try:
        conn = sqlite3.connect('data/market_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM positions")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM price_data")  # Optional
        conn.commit()
        conn.close()
        print("✅ Database cleared")
    except:
        print("No database or tables found")

    # 2. Clear in-memory logger
    logger = OrderLogger()
    if hasattr(logger, 'positions'):
        logger.positions = {}
    if hasattr(logger, 'clear_positions'):
        logger.clear_positions()

    print("✅ OrderLogger cleared")

    # 3. Final check via Alpaca
    trader = PaperTrader()
    trader.get_account()
    
    final = logger.get_current_positions()
    print(f"Final tracked positions: {final}")
    print("\n✅ Reset complete. Check Alpaca dashboard.")

if __name__ == "__main__":
    force_clear_logger()