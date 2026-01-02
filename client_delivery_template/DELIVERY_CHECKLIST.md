# WARSHAWSKI'S CLIENT DELIVERY CHECKLIST
# Use this for EVERY Fiverr order - stays consistent!

## 📋 WHEN ORDER ARRIVES

### 1. Gather Client Requirements (from Fiverr questions)
- [ ] Exchange: _______________
- [ ] Symbols: _______________
- [ ] Timeframe: _______________
- [ ] Strategy type: _______________
- [ ] Risk tolerance: _______________
- [ ] Special indicators: _______________
- [ ] Other requirements: _______________

### 2. Acknowledge Order (within 2 hours)
```
Hi [CLIENT_NAME],

Thank you for your order! I've received your requirements and will start working on your custom [STRATEGY_TYPE] strategy.

Expected delivery: [DATE]

I'll update you with progress checkpoints. All communication via messages as discussed.

Best regards,
Warshawski
```

---

## 🛠️ DEVELOPMENT PROCESS

### 3. Create Client Folder
```bash
cd C:\Users\Warshawski\nexus_bt_system
mkdir client_deliveries
cd client_deliveries
mkdir [CLIENT_NAME]_[DATE]
cd [CLIENT_NAME]_[DATE]
```

### 4. Copy Template Files
```bash
# Copy from client_delivery_template/
cp ../client_delivery_template/strategy_template.py ./strategy.py
cp ../client_delivery_template/config_template.json ./config.json
cp ../client_delivery_template/README_CLIENT.md ./README.md
```

### 5. Customize Files (15-30 minutes)

**strategy.py:**
- [ ] Replace [CLIENT_STRATEGY_NAME] with actual name
- [ ] Fill in strategy description
- [ ] Add client-specific indicators in calculate_indicators()
- [ ] Implement entry/exit logic in generate_signals()
- [ ] Set default parameters
- [ ] Test locally

**config.json:**
- [ ] Client name and order ID
- [ ] Exchange name
- [ ] Trading symbols
- [ ] Timeframe
- [ ] Strategy parameters
- [ ] Risk management settings

**README.md:**
- [ ] Client name and date
- [ ] Strategy description
- [ ] Entry/exit conditions
- [ ] Backtest results (after running)
- [ ] Performance metrics table
- [ ] Usage examples

### 6. Fetch Data & Run Backtest
```bash
# Use your existing data fetching
python C:\Users\Warshawski\nexus_bt_system\src\data\[EXCHANGE]_ohlcv_source.py --symbol [SYMBOL] --timeframe [TF]

# Run backtest
python strategy.py

# Or use main backtest engine
python C:\Users\Warshawski\nexus_bt_system\run_bt.py --strategy strategy --symbol [SYMBOL]
```

### 7. Optimize (if client ordered Standard/Premium)
```bash
# Run optimization
python C:\Users\Warshawski\nexus_bt_system\src\optimizers\optimizer.py --strategy strategy --trials 100
```

### 8. Document Results
- [ ] Copy backtest metrics to README.md
- [ ] Save performance summary
- [ ] Export trade history CSV
- [ ] Generate charts (if visualization ready)

---

## 📦 PACKAGE FOR DELIVERY

### 9. Create Requirements.txt
```txt
ccxt>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
ta>=0.11.0
python-dateutil>=2.8.0
```

### 10. Clean Up Files
- [ ] Remove any API keys from config.json
- [ ] Delete cache/temp files
- [ ] Remove __pycache__ folders
- [ ] Keep only essential files

### 11. Final File Structure
```
client_delivery/
├── strategy.py           ✓
├── config.json.example   ✓
├── requirements.txt      ✓
├── README.md            ✓
├── results/
│   ├── backtest_report.json
│   └── trades.csv
└── (charts if available)
```

### 12. Zip for Delivery
```powershell
Compress-Archive -Path * -DestinationPath ../[CLIENT_NAME]_delivery.zip
```

---

## 📤 DELIVER ON FIVERR

### 13. Upload Files
- [ ] Upload .zip file to Fiverr order
- [ ] Include README.md preview in message

### 14. Delivery Message Template
```
Hi [CLIENT_NAME],

Your custom [STRATEGY_TYPE] strategy is complete and ready!

📊 BACKTEST RESULTS:
- Total Return: [X]%
- Win Rate: [X]%
- Total Trades: [X]
- Max Drawdown: [X]%
- Sharpe Ratio: [X]

📦 WHAT'S INCLUDED:
- Custom strategy implementation
- Full source code with documentation
- Backtest results and trade history
- Configuration template
- Setup instructions in README.md

🚀 NEXT STEPS:
1. Extract the ZIP file
2. Follow README.md for setup
3. Test on paper trading before going live

⚠️ REMINDER:
Past backtest performance doesn't guarantee future results. Start with small positions and monitor closely.

Thank you for your order! If you have setup questions, let me know.

Best regards,
Warshawski
```

### 15. After Delivery
- [ ] Wait for client feedback (24-48 hours)
- [ ] Answer any setup questions
- [ ] Request review once client confirms it works
- [ ] Archive client files locally

---

## ⏱️ TIME ESTIMATES

**Basic Package (Simple Strategy):**
- Customization: 30 minutes
- Backtesting: 30 minutes
- Documentation: 30 minutes
- **Total: 1.5-2 hours**

**Standard Package (Custom Strategy + Optimization):**
- Customization: 1 hour
- Optimization: 2 hours
- Documentation: 1 hour
- **Total: 4-5 hours**

**Premium Package (Multiple Strategies):**
- Customization: 2-3 hours
- Optimization: 3-4 hours
- Documentation: 1-2 hours
- **Total: 6-9 hours**

---

## 💡 QUICK TIPS

**Reuse These:**
- File structure (always the same)
- README template (just fill in brackets)
- Config template (copy/paste)
- Message templates (personalize client name)

**Customize These:**
- Strategy logic (generate_signals method)
- Indicators (based on client request)
- Parameters (optimize for their symbols)
- Risk settings (match their tolerance)

**Never Share:**
- Your main nexus_bt_system code
- Other clients' strategies
- API keys or credentials
- Internal optimization tools

---

## ✅ QUALITY CHECKS BEFORE DELIVERY

- [ ] Strategy code runs without errors
- [ ] Backtest produces reasonable results (not 1000% returns!)
- [ ] README has all client-specific info filled in
- [ ] No placeholder [BRACKETS] left in files
- [ ] No API keys in config files
- [ ] Requirements.txt lists all dependencies
- [ ] Tested on clean Python environment
- [ ] Trade logic matches client requirements
- [ ] Risk management settings are sensible

---

**THIS TEMPLATE SAVES YOU 80% OF WORK**
Just fill in the blanks each time! 🚀
