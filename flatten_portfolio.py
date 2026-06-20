# flatten_portfolio.py - Safe Portfolio Flattener
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.live.paper_trader import PaperTrader
from src.live.order_logger import OrderLogger

def flatten_portfolio():
    print(f"\n{'='*80}")
    print(f"🛡️  SAFE PORTFOLIO FLATTENER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    trader = PaperTrader()
    logger = OrderLogger()

    # Get current account and positions
    try:
        equity, cash = trader.get_account()
        positions = logger.get_current_positions()
        
        print(f"📊 Account Summary:")
        print(f"   Total Equity : ${equity:,.2f}")
        print(f"   Cash Balance : ${cash:,.2f}\n")
        
        if not positions:
            print("✅ No open positions. Portfolio is already flat.")
            return
        
        print("📍 Current Open Positions:")
        total_exposure = 0
        for symbol, qty in positions.items():
            print(f"   {symbol}: {qty} shares")
            total_exposure += abs(qty)
        
        print(f"\nTotal Positions: {len(positions)} symbols | Total Shares: {total_exposure}")
        
        # Confirmation
        confirm = input("\n⚠️  Do you want to CLOSE ALL positions? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Operation cancelled by user.")
            return
        
        print("\n🔄 Closing all positions...")
        closed = 0
        
        for symbol, qty in positions.items():
            if qty == 0:
                continue
                
            action = "sell" if qty > 0 else "buy"
            size = abs(qty)
            
            try:
                print(f"   Closing {symbol} ({action} {size} shares)...")
                trader.submit_safe_order(symbol, action, size, logger=logger)
                closed += 1
            except Exception as e:
                print(f"   ❌ Failed to close {symbol}: {e}")
        
        print(f"\n✅ Portfolio flattening completed! Closed {closed} positions.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    flatten_portfolio()