import yfinance as yf
import pandas as pd
import sqlite3
import os
from typing import List, Optional
import sys

# Safe import for config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import SYMBOLS, START_DATE, END_DATE, TIMEFRAME

class DataFetcher:
    """Clean production data fetcher with SQLite caching."""
    
    def __init__(self, db_path: str = "data/market_data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.conn = None
        self._create_table()
    
    def _get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn
    
    def _create_table(self):
        """Create table with consistent column names."""
        conn = self._get_connection()
        create_sql = """
        CREATE TABLE IF NOT EXISTS price_data (
            date TEXT PRIMARY KEY,
            symbol TEXT,
            Open REAL,
            High REAL,
            Low REAL,
            Close REAL,
            Volume INTEGER
        );
        """
        conn.execute(create_sql)
        conn.commit()
        print(f"✅ Database initialized at {self.db_path}")
    
    def fetch_and_cache(self, symbols: Optional[List[str]] = None, 
                       start: str = START_DATE, 
                       end: str = END_DATE) -> pd.DataFrame:
        if symbols is None:
            symbols = SYMBOLS
        
        all_data = []
        conn = self._get_connection()
        
        for symbol in symbols:
            # Try cache
            query = "SELECT * FROM price_data WHERE symbol = ? AND date >= ? AND date <= ?"
            try:
                cached = pd.read_sql_query(query, conn, params=(symbol, start, end))
                if not cached.empty:
                    print(f"✅ Loaded {symbol} from cache ({len(cached)} rows)")
                    all_data.append(cached)
                    continue
            except:
                pass
            
            # Download
            print(f"📥 Downloading {symbol} ...")
            df = yf.download(symbol, start=start, end=end, interval=TIMEFRAME, progress=False)
            
            if df.empty:
                print(f"⚠️ No data for {symbol}")
                continue
            
            # Standardize columns (handle 'Date' vs 'date')
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df.reset_index(inplace=True)
            df.rename(columns={'Date': 'date'}, inplace=True)   # Fix capital 'Date'
            df['symbol'] = symbol
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            
            # Flatten MultiIndex columns if they exist
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)



            # Safe insert with duplicate handling
            if not df.empty:
                df = df.drop_duplicates(subset=['date'])
                try:
                    df.to_sql('price_data', self.conn, if_exists='append', index=False)
                except Exception as e:
                    # Ignore duplicate errors
                    if "UNIQUE constraint failed" in str(e):
                        print(f"⚠️ Some duplicate dates ignored for {symbol}")
                    else:
                        print(f"Warning saving {symbol}: {e}")
                
                print(f"💾 Cached {len(df)} rows for {symbol}")
            
            all_data.append(df)
        
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data, ignore_index=True)
        result['date'] = pd.to_datetime(result['date'])
        result = result.sort_values(['symbol', 'date']).reset_index(drop=True)
        return result
    
    def close(self):
        if self.conn:
            self.conn.close()

# Test
if __name__ == "__main__":
    fetcher = DataFetcher()
    df = fetcher.fetch_and_cache()
    print(f"\nTotal rows: {len(df)}")
    if not df.empty:
        print(df.tail(5)[['date', 'symbol', 'Close']])
    fetcher.close()