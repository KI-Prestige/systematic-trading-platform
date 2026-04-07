import pandas as pd
import os
from datetime import datetime
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class OrderLogger:
    """Improved logger with better timestamp handling and reloading."""
    
    def __init__(self, log_file: str = "backtests/paper_orders.csv"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.orders = self.load_existing()
    
    def load_existing(self):
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
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
        print(f"📝 Logged: {action.upper()} {qty} {symbol} at {new_order['timestamp']}")
    
    def get_current_positions(self):
        if self.orders.empty:
            return {}
        positions = {}
        for symbol in self.orders['symbol'].unique():
            buys = self.orders[(self.orders['symbol'] == symbol) & (self.orders['action'] == 'BUY')]['qty'].sum()
            sells = self.orders[(self.orders['symbol'] == symbol) & (self.orders['action'] == 'SELL')]['qty'].sum()
            net = buys - sells
            if net != 0:
                positions[symbol] = net
        return positions
    
    def get_trade_history(self):
        return self.orders.sort_values('timestamp', ascending=False) if not self.orders.empty else pd.DataFrame()

# Test
if __name__ == "__main__":
    logger = OrderLogger()
    print("Current positions:", logger.get_current_positions())
    print("Total trades:", len(logger.orders))