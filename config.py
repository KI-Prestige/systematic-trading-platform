from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA"]
TIMEFRAME = "1d"
START_DATE = "2015-01-01"
END_DATE = "2026-04-01"

# Strategy Configuration
STRATEGY = {
    "short_window": 20,
    "long_window": 50,
    "min_data_required": 300,
    "target_volatility": 0.01,
    "max_position_size": 5.0,
    "min_position_size": 0.5,
    
    # Tuned Filters (Conservative but slightly more responsive)
    "adx_threshold": 22,           # Lowered from 25 → slightly easier to trade
    "volume_multiplier": 1.1,      # Softened from 1.2
    "max_volatility": 0.035,       # Increased a bit (3.5%)
    "adx_window": 14,
    
    # New: Stop Loss & Take Profit
    "stop_loss_pct": 0.08,         # 8% stop loss
    "take_profit_pct": 0.15        # 15% take profit
}

# For future use
TRADING_MODE = "paper"   # Change to "live" later