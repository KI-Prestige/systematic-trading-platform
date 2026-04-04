import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime
from typing import List, Optional

from ...config import SYMBOLS, START_DATE, END_DATE, TIMEFRAME

class DataFetcher:
    """Production-ready data fetcher with SQLite caching and table auto-creation."""
    
    def __init__(self, db_path: str = "data/market_data.db"):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        self.conn = None
        self._create_table_if_not_exists()
    
    def _get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Optional: easier row access
        return self.conn
    
    def _create_table_if_not_exists(self):
        """Create the price_data table with proper schema if it doesn't exist."""
        conn = self._get_connection()
        create_sql = """
        CREATE TABLE IF NOT EXISTS price_data (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER,
            PRIMARY KEY (date, symbol)
        );
        """
        conn.execute(create_sql)
        conn.commit()
        print(f"Database ready at {self.db_path} (table price_data ensured)")
    
    def fetch_and_cache(self, symbols: Optional[List[str]] = None, 
                       start: str = START_DATE, 
                       end: str = END_DATE) -> pd.DataFrame:
        """Fetch data with cache check. Auto-creates table on first run."""
        if symbols is None:
            symbols = SYMBOLS
        
        all_data = []
        conn = self._get_connection()
        
        for symbol in symbols:
            # Try to load from cache first
            query = """
                SELECT * FROM price_data 
                WHERE symbol = ? 
                AND date >= ? 
                AND date <= ?
            """
            try:
                cached = pd.read_sql_query(query, conn, params=(symbol, start, end))
                if not cached.empty:
                    print(f"✅ Loaded {symbol} from cache ({len(cached)} rows)")
                    all_data.append(cached)
                    continue
            except Exception as e:
                print(f"Cache read issue for {symbol}: {e}. Proceeding to download.")
            
            # Fetch fresh data from yfinance
            print(f"📥 Downloading fresh data for {symbol}...")
            data = yf.download(symbol, start=start, end=end, interval=TIMEFRAME, progress=False)
            
            if data.empty:
                print(f"⚠️ Warning: No data returned for {symbol}")
                continue
            
            # Clean and prepare data
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            data['symbol'] = symbol
            data.index.name = 'date'
            data.reset_index(inplace=True)
            data['date'] = data['date'].dt.strftime('%Y-%m-%d')  # Store as string for SQLite
            
            # Save to cache
            data.to_sql('price_data', conn, if_exists='append', index=False)
            print(f"💾 Cached {len(data)} rows for {symbol}")
            
            all_data.append(data)
        
        if not all_data:
            print("❌ No data fetched for any symbol.")
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined.sort_values(['symbol', 'date']).reset_index(drop=True)
        
        return combined
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


# Test when running the file directly
if __name__ == "__main__":
    fetcher = DataFetcher()
    df = fetcher.fetch_and_cache()
    print(f"\n✅ Data pipeline successful! Total rows: {len(df)}")
    print("Latest sample:")
    print(df.tail(5)[['date', 'symbol', 'Close']])
    fetcher.close()