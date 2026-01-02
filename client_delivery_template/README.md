# 📦 Client Delivery Template System

**For Warshawski's Fiverr Orders**

This folder contains **reusable templates** for delivering custom trading strategies to Fiverr clients. Use this for EVERY order to save 80% of your time.

---

## 📁 Files in This Folder

| File | Purpose | Customize? |
|------|---------|-----------|
| `strategy_template.py` | Base strategy class with entry/exit logic | ✏️ YES - Core customization |
| `config_template.json` | Configuration file for client settings | ✏️ YES - Fill in brackets |
| `README_CLIENT.md` | Client-facing documentation | ✏️ YES - Add results |
| `requirements.txt` | Python dependencies | ❌ NO - Copy as-is |
| `DELIVERY_CHECKLIST.md` | Step-by-step delivery process | 📖 READ - Follow each time |
| `QUICK_START_EXAMPLES.py` | Common strategy patterns | 📖 READ - Copy examples |

---

## 🚀 Quick Start (When Order Arrives)

### 1. Create Client Folder
```bash
cd C:\Users\Warshawski\nexus_bt_system
mkdir -p client_deliveries/[CLIENT_NAME]_[DATE]
cd client_deliveries/[CLIENT_NAME]_[DATE]
```

### 2. Copy Template Files
```bash
cp ../../client_delivery_template/strategy_template.py ./strategy.py
cp ../../client_delivery_template/config_template.json ./config.json
cp ../../client_delivery_template/README_CLIENT.md ./README.md
cp ../../client_delivery_template/requirements.txt ./requirements.txt
```

### 3. Customize Strategy (15-30 minutes)
Open `strategy.py` and:
- Replace `[CLIENT_STRATEGY_NAME]` with actual name (e.g., `RSI_MACD_Strategy`)
- Add indicators in `calculate_indicators()` method
- Write entry/exit logic in `generate_signals()` method
- Set default parameters

**See `QUICK_START_EXAMPLES.py` for common patterns!**

### 4. Configure Settings
Open `config.json` and fill in:
- Client name and order ID
- Exchange (binance/coinbase/kucoin/hyperliquid/phemex)
- Trading pairs and timeframe
- Strategy parameters
- Risk management settings

### 5. Run Backtest
```bash
# Fetch data (use your existing system)
python ../../src/data/[exchange]_ohlcv_source.py --symbol [SYMBOL] --timeframe [TF]

# Run strategy backtest
python strategy.py
```

### 6. Document Results
Open `README.md` and update:
- Backtest performance metrics
- Entry/exit conditions
- Risk management details
- Usage examples

### 7. Package for Delivery
```powershell
# Clean up
Remove-Item -Recurse -Force __pycache__

# Create ZIP
Compress-Archive -Path * -DestinationPath ../[CLIENT_NAME]_delivery.zip
```

### 8. Deliver on Fiverr
- Upload ZIP file
- Send delivery message (see `DELIVERY_CHECKLIST.md`)
- Wait for review

---

## ⏱️ Time Estimates

**Basic Package:** 1.5-2 hours  
**Standard Package:** 4-5 hours  
**Premium Package:** 6-9 hours

**With this template system, you spend:**
- 20% time customizing
- 30% time backtesting
- 20% time documenting
- 30% time optimizing (if ordered)

---

## 🎯 Strategy Patterns (Copy These!)

### Pattern 1: RSI + MACD Momentum
```python
# Indicators
df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
df['macd'] = MACD(close=df['close']).macd()
df['macd_signal'] = MACD(close=df['close']).macd_signal()

# Entry: RSI oversold + MACD bullish cross
buy = (df['rsi'] < 30) & (df['macd'] > df['macd_signal'])

# Exit: RSI overbought OR MACD bearish cross
sell = (df['rsi'] > 70) | (df['macd'] < df['macd_signal'])
```

### Pattern 2: Bollinger Bands Mean Reversion
```python
# Indicators
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
df['bb_upper'] = bb.bollinger_hband()
df['bb_lower'] = bb.bollinger_lband()

# Entry: Price touches lower band
buy = df['close'] <= df['bb_lower']

# Exit: Price touches upper band
sell = df['close'] >= df['bb_upper']
```

### Pattern 3: EMA Crossover
```python
# Indicators
df['ema_fast'] = df['close'].ewm(span=12, adjust=False).mean()
df['ema_slow'] = df['close'].ewm(span=26, adjust=False).mean()

# Entry: Fast crosses above slow
buy = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1))

# Exit: Fast crosses below slow
sell = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1))
```

### Pattern 4: Breakout with Volume
```python
# Indicators
df['sma'] = df['close'].rolling(window=20).mean()
df['volume_sma'] = df['volume'].rolling(window=20).mean()

# Entry: Price breaks above SMA with high volume
buy = (df['close'] > df['sma']) & (df['volume'] > df['volume_sma'] * 1.5)

# Exit: Price falls below SMA
sell = df['close'] < df['sma']
```

**See `QUICK_START_EXAMPLES.py` for complete implementations!**

---

## 📋 Client Communication Templates

### Order Acknowledgment
```
Hi [CLIENT_NAME],

Thank you for your order! I've received your requirements and will start working on your custom [STRATEGY_TYPE] strategy.

Expected delivery: [DATE]

I'll update you with progress checkpoints.

Best regards,
Warshawski
```

### Mid-Project Update (Optional, for Premium)
```
Hi [CLIENT_NAME],

Quick update on your strategy:

✅ Indicators implemented
✅ Initial backtest complete (preliminary results look promising)
🔄 Currently optimizing parameters

On track for delivery by [DATE].

Best regards,
Warshawski
```

### Delivery Message
```
Hi [CLIENT_NAME],

Your custom [STRATEGY_TYPE] strategy is complete!

📊 BACKTEST RESULTS:
- Total Return: [X]%
- Win Rate: [X]%
- Total Trades: [X]
- Max Drawdown: [X]%

📦 INCLUDED:
- Strategy implementation
- Full source code
- Backtest results
- Setup instructions

See README.md for setup. Test on paper trading first!

Thank you!

Warshawski
```

---

## 🔒 Security Checklist

**NEVER include in deliveries:**
- Your main nexus_bt_system code
- Other clients' strategies
- Real API keys
- Internal tools
- Optimization scripts (unless ordered)

**ALWAYS include:**
- Only the specific strategy ordered
- Generic config template (no keys)
- Client-specific documentation
- Requirements.txt
- README with instructions

---

## 💡 Pro Tips

1. **Keep templates updated** - If you find a better way, update the template
2. **Reuse successful patterns** - Build a library of tested strategy patterns
3. **Document edge cases** - Note any tricky requirements for future reference
4. **Test before delivery** - Always run backtest on clean environment
5. **Archive client files** - Keep organized for reference/revisions

---

## 📊 Order Tracking (Optional)

Create a simple spreadsheet:

| Order ID | Client | Strategy Type | Package | Delivered | Review | Notes |
|----------|--------|---------------|---------|-----------|--------|-------|
| FO-001 | John | RSI+MACD | Basic | 2026-01-05 | ⭐⭐⭐⭐⭐ | Quick order |
| FO-002 | Sarah | BB Mean Rev | Standard | 2026-01-08 | ⭐⭐⭐⭐⭐ | Needed optimization |

---

## 🎓 Learning from Orders

After each delivery:
- **What went well?** → Add to templates
- **What took extra time?** → Simplify process
- **Common client requests?** → Pre-build modules
- **Repeated questions?** → Improve README

**This system gets FASTER with each order!**

---

## 🚀 You're Ready!

Everything you need is in this folder. When your first Fiverr order arrives:

1. Open `DELIVERY_CHECKLIST.md`
2. Follow step-by-step
3. Refer to `QUICK_START_EXAMPLES.py` for patterns
4. Deliver quality work in 1-5 hours

**You've got this!** 💪
