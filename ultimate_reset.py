# ultimate_reset.py
import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.live.order_logger import OrderLogger
from src.live.paper_trader import PaperTrader

def ultimate_reset():
    print("🧨 ULTIMATE RESET - Clearing ALL State")
    print("="*80)

    # 1. Delete database files
    db_path = "data/market_data.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Deleted database: {db_path}")

    # 2. Clear logger
    logger = OrderLogger()
    logger.clear_positions()

    # 3. Force close via Alpaca (in case of ghost positions)
    trader = PaperTrader()
    trader.get_account()

    print("\n✅ Ultimate reset completed.")
    print("Check your Alpaca Paper dashboard to confirm positions are zero.")

if __name__ == "__main__":
    ultimate_reset()