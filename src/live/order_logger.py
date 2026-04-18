import pandas as pd
import os
from datetime import datetime
import sys
from src.data.data_fetcher import DataFetcher
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

class OrderLogger:
    """Improved logger with better timestamp handling and reloading."""
    
    def __init__(self, log_file: str = "backtests/paper_orders.csv"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.orders = self.load_existing()
        self.fetcher = DataFetcher()
    
    def load_existing(self):
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame(columns=['timestamp', 'symbol', 'action', 'qty', 'price', 'order_id'])
    
    def log_order(self, symbol: str, action: str, qty: int, price: float = None, order_id: str = None):
        """Log order with price capture"""
        if price is None:
            # Try to get current price as fallback
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
            'qty': qty,
            'price': price,
            'order_id': order_id
        }
        
        self.orders = pd.concat([self.orders, pd.DataFrame([new_order])], ignore_index=True)
        self.orders = self.orders.sort_values('timestamp', ascending=False).reset_index(drop=True)
        self.orders.to_csv(self.log_file, index=False)
        print(f"📝 Logged: {action.upper()} {qty} {symbol} @ ${price:.2f if price else 'N/A'}")
    
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
    
    def get_average_entry_price(self, symbol: str) -> float or None:
        """Get best available entry price with fallback"""
        if self.orders.empty:
            return None
        
        symbol_orders = self.orders[self.orders['symbol'] == symbol].copy()
        if symbol_orders.empty:
            return None
        
        valid_prices = symbol_orders['price'].dropna()
        if not valid_prices.empty:
            return float(valid_prices.iloc[-1])  # Most recent price
        
        # Fallback: use current market price
        try:
            from src.data.data_fetcher import DataFetcher
            df = DataFetcher().fetch_and_cache([symbol])
            return float(df['Close'].iloc[-1])
        except:
            return None
    
    def get_position_summary(self, symbol: str) -> dict:
        """Return current position info including average entry price."""
        if self.orders.empty:
            return {"position": 0, "avg_entry": None, "last_price": None}
        
        symbol_orders = self.orders[self.orders['symbol'] == symbol].copy()
        if symbol_orders.empty:
            return {"position": 0, "avg_entry": None, "last_price": None}
        
        buys = symbol_orders[symbol_orders['action'] == 'BUY']
        sells = symbol_orders[symbol_orders['action'] == 'SELL']
        
        total_buy_qty = buys['qty'].sum() if not buys.empty else 0
        total_sell_qty = sells['qty'].sum() if not sells.empty else 0
        net_position = total_buy_qty - total_sell_qty
        
        # Use the most recent order's price as approximation for now
        latest_order_price = symbol_orders['price'].dropna().iloc[-1] if not symbol_orders['price'].dropna().empty else None
        
        return {
            "position": net_position,
            "avg_entry": latest_order_price,
            "last_order_price": latest_order_price
        }
    
    def get_latest_entry_price(self, symbol: str) -> float | None:
        """Get the most recent order price for a symbol as reference."""
        if self.orders.empty:
            return None
        symbol_orders = self.orders[self.orders['symbol'] == symbol]
        if symbol_orders.empty:
            return None
        # Get the last non-null price
        prices = symbol_orders['price'].dropna()
        return float(prices.iloc[-1]) if not prices.empty else None

# Test
if __name__ == "__main__":
    logger = OrderLogger()
    print("Current positions:", logger.get_current_positions())
    print("Total trades:", len(logger.orders))