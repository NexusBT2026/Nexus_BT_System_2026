"""
QUICK START EXAMPLE
Copy this when client orders arrive - customize in 15 minutes!
"""

# EXAMPLE 1: Client wants RSI + MACD momentum strategy for BTC on Binance

# 1. COPY TEMPLATE
# cp strategy_template.py strategy_rsi_macd.py

# 2. REPLACE IN strategy_rsi_macd.py:
"""
class RSI_MACD_Strategy:  # <-- Replace [CLIENT_STRATEGY_NAME]
    
    def __init__(self, 
                 rsi_period: int = 14,           # <-- param1
                 rsi_oversold: int = 30,         # <-- param2
                 rsi_overbought: int = 70,       # <-- param3
                 stop_loss_pct: float = 2.0,
                 take_profit_pct: float = 4.0):
        
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        # ... rest stays same
    
    def calculate_indicators(self, df):
        df = df.copy()
        
        # RSI
        from ta.momentum import RSIIndicator
        rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
        df['rsi'] = rsi.rsi()
        
        # MACD
        from ta.trend import MACD
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        return df
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # BUY: RSI oversold AND MACD crosses above signal
        buy_condition = (
            (df['rsi'] < self.rsi_oversold) &
            (df['macd'] > df['macd_signal']) &
            (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        )
        
        # SELL: RSI overbought OR MACD crosses below signal
        sell_condition = (
            (df['rsi'] > self.rsi_overbought) |
            ((df['macd'] < df['macd_signal']) &
             (df['macd'].shift(1) >= df['macd_signal'].shift(1)))
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        return df
"""

# 3. UPDATE config.json:
"""
{
  "client_info": {
    "name": "JohnDoe",
    "order_id": "FO-12345",
    "delivery_date": "2026-01-05"
  },
  "exchange": {
    "name": "binance",
    "testnet": false
  },
  "trading": {
    "symbols": ["BTC/USDT"],
    "timeframe": "5m",
    "initial_capital": 10000
  },
  "strategy": {
    "name": "RSI_MACD_Strategy",
    "type": "momentum",
    "parameters": {
      "rsi_period": 14,
      "rsi_oversold": 30,
      "rsi_overbought": 70
    },
    "risk_management": {
      "stop_loss_pct": 2.0,
      "take_profit_pct": 4.0,
      "position_size_pct": 10.0
    }
  }
}
"""

# 4. UPDATE README.md:
"""
### Strategy Name
**RSI + MACD Momentum Strategy**

### Description
Combines RSI oversold/overbought levels with MACD crossovers to identify high-probability momentum trades. Enters when RSI is oversold and MACD crosses bullish, exits when RSI is overbought or MACD crosses bearish.

### Entry Conditions
- RSI below 30 (oversold)
- MACD crosses above signal line
- Previous candle had MACD below signal

### Exit Conditions
- RSI above 70 (overbought), OR
- MACD crosses below signal line

### Risk Management
- Stop Loss: 2%
- Take Profit: 4%
- Position Size: 10% per trade
"""

# 5. RUN BACKTEST
"""
python strategy_rsi_macd.py
"""

# DONE! Takes 15 minutes once you know the pattern.


# ============================================================================
# EXAMPLE 2: Client wants Bollinger Bands mean reversion for ETH on Coinbase
# ============================================================================

"""
class BollingerBands_MeanReversion:
    
    def __init__(self,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 rsi_period: int = 14,
                 stop_loss_pct: float = 3.0,
                 take_profit_pct: float = 3.0):
        # Store params...
    
    def calculate_indicators(self, df):
        from ta.volatility import BollingerBands
        from ta.momentum import RSIIndicator
        
        bb = BollingerBands(close=df['close'], window=self.bb_period, window_dev=self.bb_std)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_middle'] = bb.bollinger_mavg()
        
        rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
        df['rsi'] = rsi.rsi()
        
        return df
    
    def generate_signals(self, df):
        df['signal'] = 0
        
        # BUY: Price touches lower band + RSI oversold
        buy_condition = (
            (df['close'] <= df['bb_lower']) &
            (df['rsi'] < 30)
        )
        
        # SELL: Price touches upper band + RSI overbought
        sell_condition = (
            (df['close'] >= df['bb_upper']) &
            (df['rsi'] > 70)
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        return df
"""

# ============================================================================
# EXAMPLE 3: Client wants EMA crossover for multiple pairs on KuCoin
# ============================================================================

"""
class EMA_Crossover:
    
    def __init__(self,
                 ema_fast: int = 12,
                 ema_slow: int = 26,
                 stop_loss_pct: float = 2.5,
                 take_profit_pct: float = 5.0):
        # Store params...
    
    def calculate_indicators(self, df):
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        return df
    
    def generate_signals(self, df):
        df['signal'] = 0
        
        # BUY: Fast EMA crosses above slow EMA
        buy_condition = (
            (df['ema_fast'] > df['ema_slow']) &
            (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1))
        )
        
        # SELL: Fast EMA crosses below slow EMA
        sell_condition = (
            (df['ema_fast'] < df['ema_slow']) &
            (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1))
        )
        
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        return df
"""

# ============================================================================
# PATTERN TO FOLLOW FOR ANY ORDER:
# ============================================================================
"""
1. Identify strategy type from client request
2. Pick relevant indicators (RSI, MACD, BB, EMA, ATR, etc.)
3. Copy template → rename class
4. Add indicators in calculate_indicators()
5. Write entry/exit logic in generate_signals()
6. Update config.json with params
7. Update README.md with description
8. Run backtest
9. Package and deliver

TAKES 15-30 MINUTES PER ORDER ONCE YOU KNOW THE PATTERN!
"""
