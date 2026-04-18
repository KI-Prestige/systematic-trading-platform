import pandas as pd
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.data.data_fetcher import DataFetcher

def backfill_order_prices():
    """Backfill missing prices in paper_orders.csv using historical data"""
    csv_path = "backtests/paper_orders.csv"
    
    if not os.path.exists(csv_path):
        print("❌ paper_orders.csv not found!")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} orders. Backfilling prices...")
    
    fetcher = DataFetcher()
    updated = 0
    
    for i, row in df.iterrows():
        if pd.isna(row['price']) or row['price'] == '' or row['price'] is None:
            symbol = row['symbol']
            timestamp = pd.to_datetime(row['timestamp'])
            
            print(f"Fetching price for {symbol} at {timestamp.date()}...")
            
            try:
                # Get price on or before the order date
                hist = fetcher.fetch_and_cache([symbol])
                hist = hist[hist['symbol'] == symbol]
                hist.set_index('date', inplace=True)
                
                # Find closest price before or at timestamp
                available = hist[hist.index <= timestamp]
                if not available.empty:
                    price = float(available['Close'].iloc[-1])
                    df.at[i, 'price'] = price
                    updated += 1
                    print(f"   → Set {symbol} price to ${price:.2f}")
                else:
                    print(f"   → No historical data for {symbol}")
            except Exception as e:
                print(f"   → Error for {symbol}: {e}")
    
    if updated > 0:
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Backfill complete! Updated {updated} orders.")
        print("Newest orders:")
        print(df.tail(10)[['timestamp', 'symbol', 'action', 'qty', 'price']])
    else:
        print("\nNo missing prices found or nothing to update.")

if __name__ == "__main__":
    backfill_order_prices()