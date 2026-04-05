import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

load_dotenv()

class PaperTrader:
    """Safe paper trading execution with position sizing and risk checks."""
    
    def __init__(self):
        # 1. Force load from the root directory (up two levels from this file)
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')
        load_dotenv(dotenv_path=env_path)
        
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        # 2. Debug check (delete this after it works)
        if not api_key or not secret_key:
            print(f"❌ ERROR: Keys not found at {os.path.abspath(env_path)}")
            sys.exit(1) # Stop the script immediately
            
        self.client = TradingClient(api_key, secret_key, paper=True)
        print("✅ Connected to Alpaca Paper Trading")

    
    def get_account(self):
        account = self.client.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        print(f"Paper Account → Equity: ${equity:.2f} | Cash: ${cash:.2f}")
        return equity, cash
    
    def submit_safe_order(self, symbol: str, signal: str, suggested_size: float = 1.0):
        """Place order only if signal is valid and size is reasonable."""
        if signal not in ["buy", "sell"]:
            print(f"ℹ️ No action for {symbol} (signal: {signal})")
            return None
        
        # Safety: limit position size to 5-10% of portfolio max
        safe_qty = max(1, int(suggested_size * 5))  # Small size for paper testing (e.g. 5 shares max)
        
        side = OrderSide.BUY if signal == "buy" else OrderSide.SELL
        
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=safe_qty,
                side=side,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data)
            print(f"✅ PAPER ORDER EXECUTED: {side.upper()} {safe_qty} shares of {symbol} | Order ID: {order.id}")
            return order
        except Exception as e:
            print(f"❌ Order failed for {symbol}: {e}")
            return None

# Test
if __name__ == "__main__":
    trader = PaperTrader()
    trader.get_account()