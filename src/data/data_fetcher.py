import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime
from typing import List, Optional

from ...config import SYMBOLS, START_DATE, END_DATE, TIMEFRAME

class DataFetcher:
    """Production-ready data fetcher with SQLite caching."""
    
    def __init__(self, db_path: str = "data/market_data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = None
    
    def _get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def fetch_and_cache(self, symbols: Optional[List[str]] = None, 
                       start: str = START_DATE, 
                       end: str = END_DATE) -> pd.DataFrame:
        """Fetch data from yfinance and cache in SQLite. Load from cache if possible."""
        if symbols is None:
            symbols = SYMBOLS
        
        all_data = []
        conn = self._get_connection()
        
        for symbol in symbols:
            # Check if data exists in cache
            query = f"SELECT * FROM price_data WHERE symbol = ? AND date >= ? AND date <= ?"
            cached = pd.read_sql_query(query, conn, params=(symbol, start, end))
            
            if not cached.empty:
                print(f"Loaded {symbol} from cache ({len(cached)} rows)")
                all_data.append(cached)
                continue
            
            # Fetch fresh data
            print(f"Downloading fresh data for {symbol}...")
            data = yf.download(symbol, start=start, end=end, interval=TIMEFRAME)
            
            if data.empty:
                print(f"Warning: No data for {symbol}")
                continue
            
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            data['symbol'] = symbol
            data.index.name = 'date'
            data.reset_index(inplace=True)
            
            # Save to cache
            data.to_sql('price_data', conn, if_exists='append', index=False)
            print(f"Cached {len(data)} rows for {symbol}")
            
            all_data.append(data)
        
        if not all_data:
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined.sort_values(['symbol', 'date']).reset_index(drop=True)
        
        return combined
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

# Simple test function
if __name__ == "__main__":
    fetcher = DataFetcher()
    df = fetcher.fetch_and_cache()
    print(df.tail())
    fetcher.close()