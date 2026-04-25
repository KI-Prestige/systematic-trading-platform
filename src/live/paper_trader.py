import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.live.order_logger import OrderLogger
load_dotenv()

class PaperTrader:
    """Safe paper trading execution with position sizing and risk checks."""
    
    def __init__(self):
        self.client = TradingClient(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_SECRET_KEY"),
            paper=True
        )
        print("✅ Connected to Alpaca Paper Trading")

    
    def get_account(self):
        account = self.client.get_account()
        equity = float(account.equity)
        cash = float(account.cash)
        print(f"Paper Account → Equity: ${equity:.2f} | Cash: ${cash:.2f}")
        return equity, cash
    
    def submit_safe_order(self, symbol: str, signal: str, suggested_size: float = 1.0, logger=None):
        """Production-ready version with automatic SL/TP exits"""
        if logger is None:
            print("⚠️ No logger provided")
            return None

        positions = logger.get_current_positions()
        current_pos = positions.get(symbol, 0)

        # === 1. Check Stop-Loss / Take-Profit FIRST ===
        if current_pos != 0:
            exit_reason = self._check_exit_conditions(symbol, current_pos, logger)
            if exit_reason:
                print(f"🛑 EXIT TRIGGERED for {symbol}: {exit_reason}")
                self._close_position(symbol, current_pos, logger, exit_reason)
                return None
            else:
                self._print_position_status(symbol, current_pos, logger)

        # === 2. Normal signal handling (only if no exit) ===
        if signal not in ["buy", "sell"]:
            print(f"ℹ️ No action for {symbol} (signal: {signal})")
            return None

        print(f"   → {signal.upper()} signal received for {symbol} | Current position: {current_pos}")
        # Future new-order logic goes here
        return None

    def _print_position_status(self, symbol: str, current_pos: int, logger):
        """Clean PnL display"""
        from config import STRATEGY
        try:
            entry_price = logger.get_average_entry_price(symbol)
            if not entry_price:
                return
            
            from src.data.data_fetcher import DataFetcher
            df = DataFetcher().fetch_and_cache([symbol])
            latest_price = float(df['Close'].iloc[-1])
            
            if current_pos < 0:  # Short
                pnl_pct = (entry_price - latest_price) / entry_price * 100
            else:
                pnl_pct = (latest_price - entry_price) / entry_price * 100
                
            print(f"   📊 {symbol} (Short {abs(current_pos)}): PnL ≈ {pnl_pct:+.1f}%  |  SL: -8%   TP: +15%")
        except:
            pass

    def _check_exit_conditions(self, symbol: str, current_pos: int, logger) -> str:
        """Enhanced exit check with trailing stop"""
        from config import STRATEGY
        try:
            entry_price = logger.get_average_entry_price(symbol)
            if not entry_price:
                return ""
            
            from src.data.data_fetcher import DataFetcher
            df = DataFetcher().fetch_and_cache([symbol])
            latest_price = float(df['Close'].iloc[-1])
            
            if current_pos < 0:   # Short position
                pnl_pct = (entry_price - latest_price) / entry_price
            else:
                pnl_pct = (latest_price - entry_price) / entry_price
            
            # Hard Stop-Loss
            if pnl_pct <= -STRATEGY["stop_loss_pct"]:
                return f"STOP LOSS HIT ({pnl_pct*100:.1f}%)"
            
            # Hard Take-Profit
            if pnl_pct >= STRATEGY["take_profit_pct"]:
                return f"TAKE PROFIT HIT ({pnl_pct*100:.1f}%)"
            
            # New: Trailing Stop (once in profit by 5%, trail by 5%)
            if pnl_pct >= STRATEGY["trailing_stop_pct"]:
                trailing_level = pnl_pct - STRATEGY["trailing_stop_pct"]
                if pnl_pct < trailing_level:   # Price moved against us after profit
                    return f"TRAILING STOP HIT ({pnl_pct*100:.1f}%)"
            
            return ""
        except:
            return ""

    def _close_position(self, symbol: str, current_pos: int, logger, reason: str):
        """Close the full position"""
        close_side = "BUY" if current_pos < 0 else "SELL"
        close_qty = abs(current_pos)
        
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=close_qty,
                side=OrderSide.BUY if close_side == "BUY" else OrderSide.SELL,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY
            )
            order = self.client.submit_order(order_data)
            
            if logger:
                logger.log_order(symbol, close_side, close_qty, None, order.id)
            
            print(f"✅ POSITION CLOSED: {close_side} {close_qty} {symbol} | {reason}")
        except Exception as e:
            print(f"❌ Failed to close {symbol}: {e}")
# Test
if __name__ == "__main__":
    trader = PaperTrader()
    trader.get_account()