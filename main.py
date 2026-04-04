print("Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.data.data_fetcher import DataFetcher

print("Config loaded with symbols:", SYMBOLS)

# Test data pipeline
fetcher = DataFetcher(db_path="data/market_data.db")
df = fetcher.fetch_and_cache()
print(f"\nData fetched successfully! Shape: {df.shape}")
print("Latest data sample:")
print(df.tail(5)[['date', 'symbol', 'Close']])

fetcher.close()
print("Data pipeline test completed.")