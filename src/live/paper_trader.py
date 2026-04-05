import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import SYMBOLS
from dotenv import load_dotenv

load_dotenv()

class PaperTrader:
    """Simple paper trading client using Alpaca."""
    
    def __init__(self):
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca keys not found in .env")
        
        self.client = TradingClient(self.api_key, self.secret_key, paper=True)
        print("✅ Connected to Alpaca Paper Trading")
    
    def get_account(self):
        account = self.client.get_account()
        print(f"Cash: ${float(account.cash):.2f} | Portfolio Value: ${float(account.portfolio_value):.2f}")
        return account
    
    def place_market_order(self, symbol: str, qty: float, side: str = "buy"):
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        order = self.client.submit_order(order_data)
        print(f"✅ Paper order placed: {side.upper()} {qty} {symbol}")
        return order
    
    def get_positions(self):
        positions = self.client.get_all_positions()
        if positions:
            for p in positions:
                print(f"{p.symbol}: {p.qty} shares @ ${float(p.current_price):.2f}")
        else:
            print("No open positions")
        return positions

# Test
if __name__ == "__main__":
    trader = PaperTrader()
    trader.get_account()
    # trader.place_market_order("AAPL", 1, "buy")  # Uncomment only when ready
    trader.get_positions()