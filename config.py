from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA"]
TIMEFRAME = "1d"
START_DATE = "2015-01-01"
END_DATE = "2026-04-01"

# Strategy Configuration - Mild Enhancement (Volatility Sizing + Min Hold)
STRATEGY = {
    "short_window": 25,
    "long_window": 50,
    "min_data_required": 300,
    "target_volatility": 0.01,      # Target daily volatility per position
    "max_position_size": 5.0,
    "min_position_size": 0.5,
    
    # Filters
    "adx_threshold": 20,
    "volume_multiplier": 1.1,
    "max_volatility": 0.035,
    "adx_window": 14,
    
    # New Mild Enhancements
    "regime_window": 200,                  # Keep for future
    "min_hold_bars": 5,                    # Ignore opposite signals for 5 days
    "risk_per_trade": 0.01,                # Risk 1% of capital per trade (mild)
    "momentum_confirmation": True,         # Require short-term momentum alignment
    "risk_per_trade": 0.01,                # Risk 1% of capital per trade (mild)
    "dynamic_adx": True,                   # Enable dynamic ADX threshold
    
    # Risk Management
    "stop_loss_pct": 0.08,
    "take_profit_pct": 0.15,
    "trailing_stop_pct": 0.05
}

# For future use
TRADING_MODE = "paper"   # Change to "live" later