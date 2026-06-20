import pandas as pd
import os
from datetime import datetime
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class OrderLogger:
    """Improved Order Logger with correct position tracking"""
    
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
    
    def log_order(self, symbol: str, action: str, qty: float, price: float = None, order_id: str = None):
        """Log order and update positions correctly"""
        if price is None:
            try:
                from src.data.data_fetcher import DataFetcher
                df = DataFetcher().fetch_and_cache([symbol])
                price = float(df['Close'].iloc[-1])
            except:
                price = None

        new_order = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'action': action.upper(),
            'qty': float(qty),
            'price': price,
            'order_id': order_id
        }
        
        self.orders = pd.concat([self.orders, pd.DataFrame([new_order])], ignore_index=True)
        self.orders = self.orders.sort_values('timestamp').reset_index(drop=True)
        self.orders.to_csv(self.log_file, index=False)
        
        print(f"📝 Logged: {action.upper()} {qty} {symbol} @ ${price:.2f if price else 'N/A'}")
    
    def get_current_positions(self):
        """Correct net position calculation"""
        if self.orders.empty:
            return {}
        
        positions = {}
        for symbol in self.orders['symbol'].unique():
            symbol_orders = self.orders[self.orders['symbol'] == symbol]
            buys = symbol_orders[symbol_orders['action'] == 'BUY']['qty'].sum()
            sells = symbol_orders[symbol_orders['action'] == 'SELL']['qty'].sum()
            net = buys - sells
            if abs(net) > 0.001:  # Tolerance for floating point
                positions[symbol] = net
        return positions
    
    def clear_positions(self):
        """Fully clear logger"""
        self.orders = pd.DataFrame(columns=self.orders.columns)
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        print("🧹 Fully cleared OrderLogger and log file.")
    
    def get_trade_history(self):
        return self.orders.sort_values('timestamp', ascending=False) if not self.orders.empty else pd.DataFrame()

# Test
if __name__ == "__main__":
    logger = OrderLogger()
    print("Current positions:", logger.get_current_positions())