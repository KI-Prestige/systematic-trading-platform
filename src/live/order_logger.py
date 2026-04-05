import pandas as pd
import os
from datetime import datetime
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class OrderLogger:
    """Simple logger to track all paper orders and build portfolio history."""
    
    def __init__(self, log_file: str = "backtests/paper_orders.csv"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.orders = self.load_existing()
    
    def load_existing(self):
        if os.path.exists(self.log_file):
            return pd.read_csv(self.log_file)
        return pd.DataFrame(columns=['timestamp', 'symbol', 'action', 'qty', 'price', 'order_id'])
    
    def log_order(self, symbol: str, action: str, qty: int, price: float = None, order_id: str = None):
        new_order = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'action': action.upper(),
            'qty': qty,
            'price': price,
            'order_id': order_id
        }
        self.orders = pd.concat([self.orders, pd.DataFrame([new_order])], ignore_index=True)
        self.orders.to_csv(self.log_file, index=False)
        print(f"📝 Logged: {action.upper()} {qty} {symbol} | Order ID: {order_id}")
    
    def get_current_positions(self):
        if self.orders.empty:
            return {}
        # Simple net position calculation
        positions = {}
        for symbol in self.orders['symbol'].unique():
            buys = self.orders[(self.orders['symbol'] == symbol) & (self.orders['action'] == 'BUY')]['qty'].sum()
            sells = self.orders[(self.orders['symbol'] == symbol) & (self.orders['action'] == 'SELL')]['qty'].sum()
            positions[symbol] = buys - sells
        return positions

# Test
if __name__ == "__main__":
    logger = OrderLogger()
    logger.log_order("AAPL", "sell", 5, 253.79, "test123")
    print("Current positions:", logger.get_current_positions())