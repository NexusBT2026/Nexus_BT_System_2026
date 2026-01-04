# Visual Guide to Your Tear Sheet Report
## Understanding Every Chart & Graph

**Version 1.0** | Last Updated: January 4, 2026

---

## 📋 What You're Looking At

Your **486 KB HTML tear sheet** contains **18 interactive charts** plus a **metrics table**. This guide explains what each visualization shows and how to read it.

**File you received:** `BTC_6h_rsi_divergence_production.html` (or similar)

**How to use it:**
1. Open the HTML file in any web browser (Chrome, Firefox, Safari, Edge)
2. Scroll through the report from top to bottom
3. **Hover over charts** to see exact values
4. **Zoom** by clicking and dragging on any chart
5. **Toggle benchmark** by clicking the legend

---

## 🎯 Quick Navigation

Your tear sheet is organized into **3 main sections:**

### **Section 1: Performance Metrics Table** (Top)
- 40+ metrics in two columns (Strategy vs Benchmark)
- Covered in CLIENT_TEARSHEET_GUIDE.md

### **Section 2: Returns & Performance Charts** (Middle)
- Charts 1-9: Return visualizations
- Shows profitability and growth

### **Section 3: Risk & Analysis Charts** (Bottom)
- Charts 10-18: Risk and distribution analysis
- Shows safety and consistency

---

## 📊 CHART 1: Cumulative Returns
**Location:** First chart after metrics table

### What You're Looking At:
```
Y-axis: Total Return (%)
X-axis: Time (dates)
Lines:  - Blue = Your Strategy
        - Orange = Benchmark (BTC buy-and-hold)
```

### How to Read It:
- **Start:** Both lines begin at 0% (baseline)
- **Upward slope** = Making money
- **Flat line** = No trades (your strategy is waiting)
- **Downward slope** = Losing money
- **Gap between lines** = Outperformance or underperformance

### What Good Looks Like:
✅ **Blue line above orange** = You're beating buy-and-hold  
✅ **Smooth upward curve** = Consistent growth  
✅ **Steeper slope** = Faster returns  

### Red Flags:
🚩 **Blue below orange** = Buy-and-hold would be better  
🚩 **Jagged with big drops** = High volatility  
🚩 **Long flat periods** = Strategy inactive (might miss opportunities)

### Example Interpretation:
```
If chart shows:
- Blue line ends at +54%
- Orange line ends at +180%
→ Strategy made 54% but benchmark made 180%
→ Buy-and-hold was better in this period
```

---

## 📊 CHART 2: Drawdown (Underwater Plot)
**Location:** Second chart

### What You're Looking At:
```
Y-axis: Drawdown (%)
X-axis: Time (dates)
Area:   Shaded area = How far below peak you are
```

### How to Read It:
- **0% line (top)** = At all-time high equity
- **Below zero** = Underwater (in drawdown)
- **Shaded area depth** = How much you're losing from peak
- **Shaded area width** = How long you're underwater

### What Good Looks Like:
✅ **Shallow dips** (less than -10%) = Low drawdown  
✅ **Quick recovery** (narrow shaded areas) = Bounces back fast  
✅ **Lots of time at 0%** = Often at new highs  

### Red Flags:
🚩 **Deep dips** (more than -30%) = Painful losses  
🚩 **Wide shaded areas** = Long underwater periods (months)  
🚩 **Never reaches 0%** = Never hits new high (dying strategy)

### Example Interpretation:
```
If chart shows:
- Deepest dip: -21.62%
- Longest underwater period: 4 months
→ Worst case: You'd be down 21.62% from peak
→ You'd wait 4 months to break even
→ Can you handle this emotionally?
```

---

## 📊 CHART 3: Daily Returns
**Location:** Third chart

### What You're Looking At:
```
Y-axis: Daily Return (%)
X-axis: Time (dates)
Bars:   - Green = Positive days
        - Red = Negative days
        - Gray = No trades
```

### How to Read It:
- **Bar height** = Magnitude of daily return
- **Most bars near zero** = Normal for sparse trading strategies
- **Occasional tall bars** = Big winning or losing days
- **Pattern** = Frequency and size of moves

### What Good Looks Like:
✅ **More green than red** = More winning days  
✅ **Tall green bars** = Big wins  
✅ **Short red bars** = Small losses (controlled risk)  

### Red Flags:
🚩 **Very tall red bars** = Catastrophic loss days  
🚩 **More red than green** = More losing days than winners  
🚩 **All returns in one period** = Lucky spike, not consistent

### Example Interpretation:
```
If chart shows:
- 95% gray bars (near zero)
- Occasional green spikes (+5% to +23%)
- Few red bars (-3% to -10%)
→ Strategy trades rarely but captures big moves
→ This is NORMAL for algorithmic strategies
```

---

## 📊 CHART 4: Monthly Returns Heatmap
**Location:** Fourth chart (looks like a calendar)

### What You're Looking At:
```
Columns: Months (Jan-Dec)
Rows:    Years
Colors:  - Dark green = Big wins (+10%+)
         - Light green = Small wins (+1% to +10%)
         - Light red = Small losses (-1% to -10%)
         - Dark red = Big losses (-10%+)
         - White/Gray = Flat (0%)
```

### How to Read It:
- **Hover over squares** to see exact monthly return
- **Color intensity** = Magnitude of return
- **Pattern across months** = Seasonal tendencies

### What Good Looks Like:
✅ **More green than red** = Profitable months dominate  
✅ **Consistent across years** = Reliable performance  
✅ **No extreme red clusters** = Risk controlled  

### Red Flags:
🚩 **Dark red months** = Painful monthly losses  
🚩 **Red clusters** (e.g., all Q4 red) = Seasonal weakness  
🚩 **One green year, rest red** = Lucky period, not robust

### Example Interpretation:
```
If heatmap shows:
- 2024: Mix of light green and gray
- 2025: More intense green, few reds
→ Strategy improving over time (good)
→ Or market conditions more favorable
```

---

## 📊 CHART 5: Rolling Sharpe (6-Month)
**Location:** Fifth chart

### What You're Looking At:
```
Y-axis: Sharpe Ratio
X-axis: Time (dates)
Line:   Rolling 6-month Sharpe calculation
```

### How to Read It:
- **Line value** = Risk-adjusted return over past 6 months
- **Line slope** = Whether strategy is improving or degrading
- **Line stability** = Consistency of performance

### What Good Looks Like:
✅ **Line above 1.0** = Good risk-adjusted returns  
✅ **Stable line** = Consistent performance  
✅ **Upward trend** = Strategy improving over time  

### Red Flags:
🚩 **Line trending down** = Strategy degrading  
🚩 **Wild swings** = Inconsistent risk/reward  
🚩 **Mostly below 0** = Poor risk-adjusted returns

### Example Interpretation:
```
If chart shows:
- Sharpe fluctuates between 0.5 and 1.5
- Recent months: 0.7 to 0.9
- Slight downward trend
→ Performance is decent but may be weakening
→ Monitor closely for continued degradation
```

---

## 📊 CHART 6: Yearly Returns
**Location:** Sixth chart

### What You're Looking At:
```
Y-axis: Annual Return (%)
X-axis: Years
Bars:   - Green = Positive years
        - Red = Negative years
```

### How to Read It:
- **Bar height** = Total return for that year
- **Pattern** = Consistency across years
- **Comparison** = Strategy vs benchmark side-by-side

### What Good Looks Like:
✅ **All or mostly green bars** = Profitable years  
✅ **Similar bar heights** = Consistent annual returns  
✅ **Strategy bars taller than benchmark** = Outperformance  

### Red Flags:
🚩 **Red bars** = Losing years  
🚩 **One huge bar, rest flat** = One lucky year  
🚩 **Recent bars shrinking** = Declining performance

---

## 📊 CHART 7: Earnings (Dollar Growth)
**Location:** Seventh chart

### What You're Looking At:
```
Y-axis: Cumulative Profit ($)
X-axis: Time (dates)
Line:   Total dollar profit assuming $10,000 start
```

### How to Read It:
- **Similar to Chart 1** but in dollars instead of percentages
- **Final value** = What $10,000 grew to
- **Slope** = Rate of wealth accumulation

### What Good Looks Like:
✅ **Steady upward climb** = Consistent profit  
✅ **Accelerating slope** = Compounding effect  
✅ **Few pullbacks** = Capital preserved  

### Example Interpretation:
```
If chart shows:
- Starts at $10,000
- Ends at $15,400
→ $5,400 profit on $10,000 (54% return)
```

---

## 📊 CHART 8: Log Returns
**Location:** Eighth chart

### What You're Looking At:
```
Y-axis: Cumulative Return (log scale)
X-axis: Time (dates)
Lines:  Strategy vs Benchmark (logarithmic)
```

### How to Read It:
- **Logarithmic scale** makes long-term growth easier to see
- **Useful for strategies with >100% returns**
- **Straight line on log scale** = Exponential growth

### Why It Exists:
- Makes it easier to compare different magnitude returns
- Shows compounding visually
- Professional standard for long-term performance

---

## 📊 CHART 9: Rolling Volatility (6-Month)
**Location:** Ninth chart

### What You're Looking At:
```
Y-axis: Annualized Volatility (%)
X-axis: Time (dates)
Lines:  - Blue = Strategy volatility
        - Orange = Benchmark volatility
```

### How to Read It:
- **Higher line** = More volatile (riskier)
- **Line stability** = Consistent risk profile
- **Spikes** = Periods of high uncertainty

### What Good Looks Like:
✅ **Blue below orange** = Strategy is safer than buy-and-hold  
✅ **Stable line** = Predictable risk  
✅ **Low values** (<20%) = Low volatility  

### Red Flags:
🚩 **Increasing trend** = Risk growing over time  
🚩 **Frequent spikes** = Unpredictable risk  
🚩 **Very high** (>50%) = Extremely volatile

---

## 📊 CHART 10: Rolling Sortino (6-Month)
**Location:** Tenth chart

### What You're Looking At:
```
Y-axis: Sortino Ratio
X-axis: Time (dates)
Line:   Rolling 6-month downside risk-adjusted return
```

### How to Read It:
- **Similar to Chart 5** but focuses only on downside risk
- **Higher values** = Better downside protection
- **Trend** = Whether risk control is improving

### What Good Looks Like:
✅ **Stable above 1.0** = Good downside protection  
✅ **Above Sharpe ratio** = Better at protecting downside  

---

## 📊 CHART 11: Rolling Beta (6-Month)
**Location:** Eleventh chart

### What You're Looking At:
```
Y-axis: Beta (correlation to benchmark)
X-axis: Time (dates)
Line:   How much strategy moves with benchmark
```

### How to Read It:
- **Beta = 1.0** → Strategy moves exactly with benchmark
- **Beta > 1.0** → Strategy more volatile than benchmark
- **Beta < 1.0** → Strategy less volatile than benchmark
- **Beta near 0** → Strategy independent of benchmark

### What Good Looks Like:
✅ **Beta < 1.0** = Less risky than market  
✅ **Stable beta** = Consistent relationship  
✅ **Low beta** (<0.5) = True alpha generation (market-neutral)

---

## 📊 CHART 12: Distribution of Returns
**Location:** Twelfth chart (histogram)

### What You're Looking At:
```
X-axis: Return size (%)
Y-axis: Frequency (number of days)
Bars:   Height shows how often each return happens
Curve:  Red line = Normal distribution overlay
```

### How to Read It:
- **Shape** = Risk profile of strategy
- **Center peak** = Most common return
- **Width** = Volatility
- **Tails** = Extreme events

### What Good Looks Like:
✅ **Bell curve shape** = Normal, predictable returns  
✅ **Right tail longer** = Occasional big wins (positive skew)  
✅ **Tall center, short tails** = Consistent returns  

### Red Flags:
🚩 **Left tail longer** = Occasional catastrophic losses  
🚩 **Two peaks** = Bimodal (inconsistent strategy)  
🚩 **Very fat tails** = Frequent extreme events  

### Example Interpretation:
```
If histogram shows:
- Tall spike at 0% (most days)
- Few bars spread between -10% and +23%
→ NORMAL for sparse trading strategies
→ Most days inactive, occasional big trades
→ NOT a red flag!
```

---

## 📊 CHART 13: QQ Plot (Quantile-Quantile)
**Location:** Thirteenth chart (scatter plot)

### What You're Looking At:
```
Axes:   Theoretical vs Sample Quantiles
Line:   Red diagonal = Perfect normal distribution
Dots:   Your actual returns
```

### How to Read It:
- **Dots on red line** = Returns follow normal distribution
- **Dots above line** = More positive extremes than normal
- **Dots below line** = More negative extremes than normal

### What Good Looks Like:
✅ **Dots mostly on line** = Predictable, normal behavior  
✅ **Upper dots above line** = Beneficial fat right tail  

### Red Flags:
🚩 **Lower dots far below line** = Dangerous fat left tail  
🚩 **S-curve pattern** = Non-normal distribution (unpredictable)

---

## 📊 CHART 14: EOY Returns (Table)
**Location:** Fourteenth visualization

### What You're Looking At:
```
Rows:    Years
Columns: Strategy vs Benchmark annual returns
```

### How to Read It:
- **Each row** = One year's performance
- **Compare columns** = Strategy vs benchmark
- **Pattern** = Consistency across years

### What to Look For:
✅ Strategy column consistently positive  
✅ Strategy beats benchmark most years  
⚠️ If benchmark consistently better → just buy BTC!

---

## 📊 CHART 15: Daily Returns by Month (Box Plot)
**Location:** Fifteenth chart

### What You're Looking At:
```
X-axis: Months (Jan-Dec)
Y-axis: Daily return range
Boxes:  - Box = 25th to 75th percentile
        - Line in box = Median
        - Whiskers = Min/max (excluding outliers)
        - Dots = Outlier days
```

### How to Read It:
- **Box height** = Typical return range for that month
- **Box position** = Whether month is profitable
- **Whiskers** = Extreme moves in that month

### What Good Looks Like:
✅ **Boxes mostly above zero** = Profitable months  
✅ **Consistent box sizes** = Stable behavior year-round  
✅ **Outliers on upside** = Big wins possible  

### Red Flags:
🚩 **Certain months always red** = Seasonal weakness  
🚩 **Huge boxes** = Very inconsistent monthly behavior

---

## 📊 CHART 16: Daily Returns by Weekday (Box Plot)
**Location:** Sixteenth chart

### What You're Looking At:
```
X-axis: Days (Mon-Fri)
Y-axis: Daily return range
Boxes:  Same as Chart 15
```

### How to Read It:
- Shows if certain days perform better
- **Not relevant for crypto** (24/7 markets)
- **More useful for stock strategies**

---

## 📊 CHART 17: Monthly Returns Scatter
**Location:** Seventeenth chart

### What You're Looking At:
```
X-axis: Benchmark monthly returns
Y-axis: Strategy monthly returns
Dots:   Each dot = One month
Line:   Diagonal = Perfect correlation
```

### How to Read It:
- **Dots above diagonal** = Strategy outperforming
- **Dots below diagonal** = Strategy underperforming
- **Tight cluster** = High correlation
- **Scattered** = Low correlation (independent)

### What Good Looks Like:
✅ **Most dots above diagonal** = Consistent outperformance  
✅ **Scattered dots** = Not just following benchmark  
✅ **Upper right quadrant** = Both profitable together  

### Red Flags:
🚩 **Dots in lower left** = Both losing together  
🚩 **All dots on diagonal** = Just copying benchmark

---

## 📊 CHART 18: Snapshot (4-in-1 Summary)
**Location:** Last chart (four panels)

### What You're Looking At:
**Top Left:** Cumulative returns (Chart 1)  
**Top Right:** Drawdown underwater (Chart 2)  
**Bottom Left:** Daily returns bars (Chart 3)  
**Bottom Right:** Monthly heatmap (Chart 4)

### Purpose:
- **Quick overview** of all key visuals
- **Side-by-side comparison** at a glance
- **Print-friendly** summary page

---

## 🎨 Understanding Colors & Styles

### Color Coding:
- **Blue** = Your strategy
- **Orange** = Benchmark (BTC/ETH)
- **Green** = Positive/profit
- **Red** = Negative/loss
- **Gray** = Neutral/no trade

### Interactive Features:
1. **Hover** = See exact values
2. **Click legend** = Toggle lines on/off
3. **Click and drag** = Zoom into time period
4. **Double click** = Reset zoom
5. **Scroll** = Move through report

---

## 📱 Viewing Tips

### Best Practices:
✅ **Use Chrome or Firefox** for best compatibility  
✅ **Fullscreen mode** for easier viewing (F11)  
✅ **Zoom in on charts** to see detail  
✅ **Save the HTML file** - works offline forever  

### Troubleshooting:
⚠️ **Charts not interactive?** → Enable JavaScript  
⚠️ **Colors look wrong?** → Try different browser  
⚠️ **File won't open?** → Right-click → Open With → Browser

---

## 🎯 Quick Visual Assessment Checklist

### ✅ Green Flags (Good Strategy):
1. **Chart 1:** Blue line trending up, smooth growth
2. **Chart 2:** Shallow dips, quick recoveries
3. **Chart 4:** More green than red squares
4. **Chart 5:** Rolling Sharpe stable above 1.0
5. **Chart 9:** Blue line below orange (less volatile)
6. **Chart 12:** Bell curve or positive skew
7. **Chart 17:** Dots above diagonal

### 🚩 Red Flags (Problematic Strategy):
1. **Chart 1:** Blue below orange (underperforming benchmark)
2. **Chart 2:** Deep dips (>30%) or never reaches zero
3. **Chart 4:** Clusters of dark red months
4. **Chart 5:** Rolling Sharpe declining over time
5. **Chart 9:** Blue line increasing (risk growing)
6. **Chart 12:** Fat left tail (catastrophic loss risk)
7. **Chart 17:** Dots below diagonal (underperforming)

---

## 📊 Common Visual Patterns Explained

### Pattern 1: "The Staircase"
**Seen in:** Chart 1 (Cumulative Returns)
```
What it looks like: Flat → Jump → Flat → Jump
What it means: Strategy trades rarely but captures big moves
Is it good? YES - Normal for algorithmic trading
```

### Pattern 2: "The Spike Forest"
**Seen in:** Chart 3 (Daily Returns)
```
What it looks like: Mostly gray/zero with occasional tall spikes
What it means: Sparse trading with discrete entries/exits
Is it good? YES - Not continuously exposed to market
```

### Pattern 3: "The Sawtooth"
**Seen in:** Chart 1 (Cumulative Returns)
```
What it looks like: Up → Down → Up → Down (jagged)
What it means: High volatility, frequent reversals
Is it good? MAYBE - Depends on if trend is net positive
```

### Pattern 4: "The Plateau"
**Seen in:** Chart 1 (Cumulative Returns)
```
What it looks like: Long flat period with no growth
What it means: Strategy stopped trading or stopped working
Is it good? NO - Dead money, could invest elsewhere
```

### Pattern 5: "The Cliff"
**Seen in:** Chart 2 (Drawdown)
```
What it looks like: Sudden deep drop
What it means: Major losing trade or sequence
Is it good? NO - Risk not controlled
```

---

## 🔍 Advanced: Comparing Multiple Strategies

When you have tear sheets for multiple strategies:

### Compare Chart 1 (Returns):
- Which has steeper slope? (faster growth)
- Which is smoother? (less volatility)
- Which ends higher? (total return)

### Compare Chart 2 (Drawdown):
- Which has shallower dips? (safer)
- Which recovers faster? (resilience)
- Which spends more time at 0%? (frequently at highs)

### Compare Chart 5 (Rolling Sharpe):
- Which is more stable? (consistent)
- Which is higher on average? (better risk/reward)
- Which is trending up? (improving)

### Decision Rule:
**Best strategy = Highest Chart 1 with shallowest Chart 2**

---

## 💡 Expert Tips

### Tip 1: Context Matters
- **Time period shown** = Are you looking at bull market only?
- **Number of trades** = Few trades = results could be lucky
- **Market conditions** = 2024-2025 was mostly bull; will it work in bear?

### Tip 2: Trust Your Eyes
- **If charts look scary** = Strategy probably is scary
- **If charts look smooth** = Strategy probably is stable
- **Visual intuition is powerful** - don't ignore it!

### Tip 3: Compare to Simple Buy-and-Hold
- **Is orange line simpler?** → Maybe just hold BTC
- **Is blue line better enough?** → Justify the complexity?
- **Risk-adjusted comparison** → Not just absolute returns

### Tip 4: Print the Snapshot (Chart 18)
- **One-page overview** for quick reference
- **Share with friends/team** without full report
- **Track strategy evolution** over time

---

## ❓ Visual FAQs

**Q: Why are most bars in Chart 3 gray/zero?**  
A: Your strategy doesn't trade every day. Gray = no position = no return. This is NORMAL and GOOD (not exposed to risk when not trading).

**Q: Chart 12 looks weird - one tall spike and nothing else?**  
A: Normal for sparse trading. Most days have 0% return (tall spike at zero), occasional trades create other bars.

**Q: My Chart 1 is flat for 6 months. Is strategy broken?**  
A: Strategy probably didn't find good setups. Not broken, just waiting for right conditions. Check if market was choppy/sideways.

**Q: Orange line is always above blue in Chart 1. Should I give up?**  
A: Not necessarily! Check Chart 2 - if your drawdown is much smaller, you're taking less risk. Risk-adjusted returns matter more than absolute returns.

**Q: Chart 5 (Rolling Sharpe) is negative sometimes. Bad?**  
A: Short-term negative Sharpe is normal. What matters is average over full period. One bad month doesn't kill a strategy.

---

## 📞 Next Steps

After reviewing all 18 charts:

### ✅ If most green flags → **Proceed with confidence**
1. Start with paper trading (simulated)
2. Use conservative position sizing (25-50% of Kelly)
3. Monitor performance monthly

### ⚠️ If mixed signals → **Investigate further**
1. Review CLIENT_TEARSHEET_GUIDE.md for metric details
2. Compare to other strategies
3. Ask for parameter optimization

### 🚩 If most red flags → **Don't trade yet**
1. Request strategy improvements
2. Try different symbols/timeframes
3. Consider different strategy entirely

---

## 📚 Related Documents

- **CLIENT_TEARSHEET_GUIDE.md** - Explains all 50+ metrics
- **README.md** - System overview and capabilities
- Contact for strategy consulting or custom analysis

---

**Remember:** These visualizations are based on historical data. Past performance doesn't guarantee future results. Always start with paper trading and small positions.

**Document Version:** 1.0  
**Last Updated:** January 4, 2026  
**Report Type:** Professional QuantStats HTML Tear Sheet (486 KB)
