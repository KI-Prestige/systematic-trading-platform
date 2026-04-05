import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.live.order_logger import OrderLogger
load_dotenv()

class PaperTrader:
    """Safe paper trading execution with position sizing and risk checks."""
    
    def __init__(self):
        self.client = TradingClient(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            paper=True
        )
        print("✅ Connected to Alpaca Paper Trading")

    
    def get_account(self):
        account = self.client.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        print(f"Paper Account → Equity: ${equity:.2f} | Cash: ${cash:.2f}")
        return equity, cash
    
    def submit_safe_order(self, symbol: str, signal: str, suggested_size: float = 1.0, logger=None):
        if signal not in ["buy", "sell"]:
            print(f"ℹ️ No action for {symbol}")
            return None
        
        safe_qty = max(1, int(suggested_size * 5))
        side = "BUY" if signal == "buy" else "SELL"
        
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=safe_qty,
                side=OrderSide.BUY if signal == "buy" else OrderSide.SELL,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data)
            
            # Log the order
            if logger:
                logger.log_order(symbol, side, safe_qty, None, order.id)
            else:
                print(f"✅ PAPER ORDER: {side} {safe_qty} {symbol}")
            
            return order
        except Exception as e:
            print(f"❌ Order failed: {e}")
            return None

# Test
if __name__ == "__main__":
    trader = PaperTrader()
    trader.get_account()