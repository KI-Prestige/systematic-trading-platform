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
    "rf_probability_threshold": 0.65,   # Minimum confidence to take signal
    "rf_n_estimators": 100,
    "rf_max_depth": 6,
    
    "short_window": 25,
    "long_window": 50,
    "weekly_short": 5,               # ~1 month on weekly
    "weekly_long": 10,               # ~2 months on weekly
    "weekly_regime_window": 200,     # ~200-day for trend                            
    "min_data_required": 100,
    "target_volatility": 0.01,      # Target daily volatility per position
    "max_position_size": 5.0,
    "min_position_size": 0.5,
    
    # Filters
    "adx_threshold": 20,
    "volume_multiplier": 0.95,
    "max_volatility": 0.06,
    "adx_window": 15,
    
    # New Mild Enhancements
    "regime_window": 200,                  # Keep for future
    "min_hold_bars": 5,                    # Ignore opposite signals for 5 days
    "risk_per_trade":0.02,                # Risk 0.25% of capital per trade (mild)
    "momentum_confirmation": True,         # Require short-term momentum alignment
    "dynamic_adx": True,                   # Enable dynamic ADX threshold
    
    # Risk Management
    "pullback_threshold": 0.03,      # Enter if price pulls back up to 2.5% above short SMA
    "stop_loss_pct": 0.06,
    "take_profit_pct": 0.25,
    "trailing_stop_pct": 0.10,
    "MAX_PORTFOLIO_DD": 0.15          # Pause/reduce after 18% DD
}

# For future use
TRADING_MODE = "paper"   # Change to "live" later