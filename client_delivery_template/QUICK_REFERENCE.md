# ⚡ QUICK REFERENCE CARD
# Print this or keep it open - use for EVERY order!

## 🎯 WHEN ORDER ARRIVES (5 minutes)

```bash
# 1. Create folder
mkdir client_deliveries/[CLIENT]_[DATE]
cd client_deliveries/[CLIENT]_[DATE]

# 2. Copy templates
cp ../../client_delivery_template/* .

# 3. Send acknowledgment (see MESSAGE_TEMPLATES.md)
```

---

## ✏️ CUSTOMIZATION WORKFLOW (15-30 minutes)

### Files to Edit:
1. **strategy.py** (core work)
2. **config.json** (settings)
3. **README.md** (results)

### Strategy.py Changes:
```python
# 1. Class name
class [ClientStrategyName]:

# 2. __init__ parameters
def __init__(self, param1, param2, param3):

# 3. Indicators
def calculate_indicators(self, df):
    # Add: RSI, MACD, BB, EMA, ATR, etc.

# 4. Entry/exit logic
def generate_signals(self, df):
    buy = (condition1) & (condition2)
    sell = (condition3) | (condition4)
```

---

## 📊 COMMON INDICATOR IMPORTS

```python
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice
```

---

## 🎯 STRATEGY PATTERNS (COPY THESE!)

### RSI Oversold/Overbought
```python
rsi = RSIIndicator(close=df['close'], window=14).rsi()
buy = rsi < 30
sell = rsi > 70
```

### MACD Crossover
```python
macd = MACD(close=df['close'])
macd_line = macd.macd()
signal = macd.macd_signal()
buy = (macd_line > signal) & (macd_line.shift(1) <= signal.shift(1))
sell = (macd_line < signal) & (macd_line.shift(1) >= signal.shift(1))
```

### Bollinger Bands
```python
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
buy = df['close'] <= bb.bollinger_lband()
sell = df['close'] >= bb.bollinger_hband()
```

### EMA Crossover
```python
ema_fast = df['close'].ewm(span=12, adjust=False).mean()
ema_slow = df['close'].ewm(span=26, adjust=False).mean()
buy = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
sell = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1))
```

---

## 🏃 TESTING & DELIVERY (30-60 minutes)

```bash
# 1. Run backtest
python strategy.py

# 2. Check results look reasonable (not 1000% gains!)

# 3. Update README.md with metrics

# 4. Clean & package
Remove-Item -Recurse __pycache__
Compress-Archive -Path * -DestinationPath ../[CLIENT]_delivery.zip

# 5. Upload to Fiverr + send delivery message
```

---

## 📋 PRE-DELIVERY CHECKLIST

- [ ] Strategy runs without errors
- [ ] Results are realistic
- [ ] All [BRACKETS] replaced
- [ ] No API keys in files
- [ ] README has client results
- [ ] requirements.txt included
- [ ] Tested in clean environment

---

## 💬 MESSAGE QUICK TEMPLATES

**Acknowledgment:**
"Thank you for your order! Starting on your [TYPE] strategy. Delivery: [DATE]."

**Delivery:**
"Your strategy is complete! Results: [X]% return, [Y]% win rate, [Z] trades. See README.md."

**Support:**
"To install: pip install -r requirements.txt. Follow README.md steps. Let me know if issues!"

---

## ⏱️ TIME BUDGET

**Basic (Simple Strategy):**
- Setup: 10 min
- Coding: 30 min
- Testing: 30 min
- Docs: 20 min
- **Total: 1.5 hours** → $150 = $100/hour

**Standard (Custom + Optimization):**
- Setup: 10 min
- Coding: 1 hour
- Optimization: 2 hours
- Testing: 30 min
- Docs: 30 min
- **Total: 4 hours** → $400 = $100/hour

**Premium (Multiple Strategies):**
- Setup: 15 min
- Coding: 3 hours
- Optimization: 3 hours
- Testing: 1 hour
- Docs: 1 hour
- **Total: 8 hours** → $800 = $100/hour

---

## 🎓 STRATEGY TYPE DECODER

| Client Says | Use These Indicators | Pattern |
|-------------|---------------------|---------|
| "Momentum" | RSI + MACD | Oversold buy, overbought sell |
| "Mean reversion" | Bollinger Bands + RSI | Buy at lower band, sell at upper |
| "Trend following" | EMA crossover | Fast crosses slow |
| "Breakout" | SMA + Volume | Price breaks above SMA with volume |
| "Scalping" | Short EMA + small targets | Quick entries/exits |

---

## 🚨 RED FLAGS (Pause & Clarify)

- Client wants "guaranteed profits"
- Requests live trading with their API keys
- Wants you to manage their money
- Asks for financial advice
- Unrealistic expectations (1000% returns)

**Response:** "I provide technical development only, not financial advice or guarantees."

---

## 📞 SUPPORT SCOPE

**INCLUDED (Free):**
- Setup instructions
- Explaining backtest results
- Fixing bugs in delivered code
- Basic parameter adjustments (within revisions)

**NOT INCLUDED (New Order):**
- Adding new features
- Live trading setup (unless ordered)
- Ongoing optimization
- Strategy redesign
- Training/consultation

---

## 🎯 SUCCESS CHECKLIST

After each delivery:
- [ ] Delivered on time
- [ ] Code works correctly
- [ ] Client messages answered < 24 hours
- [ ] README is complete
- [ ] Results are documented

**Good delivery = 5-star review = More orders!**

---

## 📱 KEEP THESE OPEN

1. **DELIVERY_CHECKLIST.md** - Step-by-step process
2. **QUICK_START_EXAMPLES.py** - Copy/paste patterns
3. **MESSAGE_TEMPLATES.md** - Communication
4. **This file** - Quick reference

---

**YOU'VE GOT THIS! 🚀**

Every order makes you faster and better!
