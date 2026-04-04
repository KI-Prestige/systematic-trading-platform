print("🚀 Systematic Trading Platform - Starting up...")

from config import SYMBOLS
from src.data.data_fetcher import DataFetcher

print(f"Config loaded with {len(SYMBOLS)} symbols.")

# Test data pipeline
fetcher = DataFetcher()
df = fetcher.fetch_and_cache()

if not df.empty:
    print(f"\n✅ Data pipeline successful! Shape: {df.shape}")
    print("Latest sample:")
    print(df.tail(5)[['date', 'symbol', 'Close']])
else:
    print("❌ No data returned.")

fetcher.close()
print("✅ Step 2 data pipeline test completed.")