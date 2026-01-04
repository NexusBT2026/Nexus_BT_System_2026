# Professional Tear Sheet Guide
## Understanding Your Strategy Performance Report

**Version 1.0** | Last Updated: January 4, 2026

---

## 📖 What Is This Document?

This guide explains **every metric, chart, and visualization** in your professional tear sheet report. Use it as a reference to understand what each number means and how to interpret your strategy's performance.

**Your tear sheet contains 40+ metrics and 15+ visualizations** - this guide will help you understand all of them.

---

## 🎯 Quick Start: What To Look At First

If you're in a hurry, check these **5 key metrics** first:

1. **Cumulative Return** - Did the strategy make money?
2. **Sharpe Ratio** - Is it better than random luck?
3. **Max Drawdown** - What's the worst loss period?
4. **Win Rate** - How often does it win?
5. **Profit Factor** - How much do wins outweigh losses?

If these 5 look good, the strategy is likely solid. Read on for details.

---

## 📊 Section 1: Return Metrics

### Cumulative Return
**What it is:** Total gain/loss over the entire backtest period.

**Example:** `54.00%` means your $10,000 grew to $15,400

**What's good:**
- ✅ Positive = Strategy made money
- ⚠️ Negative = Strategy lost money
- 🎯 Target: >20% annually for crypto strategies

**What to watch:**
- Compare to benchmark (BTC buy-and-hold)
- Higher isn't always better if risk is too high

---

### CAGR (Compound Annual Growth Rate)
**What it is:** Annualized return rate, accounting for compounding.

**Example:** `13.95%` CAGR means if you kept this strategy running for years, you'd average 13.95% growth per year

**What's good:**
- ✅ 10-20% = Excellent for most strategies
- ✅ 20-50% = Exceptional (hedge fund level)
- ⚠️ >100% = Too good to be true? Check for overfitting

**Why it matters:** CAGR lets you compare strategies of different lengths fairly.

---

### MTD, 3M, 6M, YTD, 1Y (Period Returns)
**What it is:** Returns for specific time periods.

- **MTD** = Month-to-date
- **3M** = Last 3 months
- **6M** = Last 6 months
- **YTD** = Year-to-date
- **1Y** = Last 12 months

**What to watch:**
- Are recent returns (3M, 6M) similar to long-term (1Y, 3Y)?
- ⚠️ If recent returns are much worse, strategy might be degrading

---

### Best Day / Worst Day
**What it is:** Biggest single-day gain and loss.

**Example:**
- Best Day: `23.29%` = One day made 23.29% profit
- Worst Day: `-10.23%` = One day lost 10.23%

**What's good:**
- Best Day should be 2-3x larger than Worst Day
- ⚠️ If Worst Day is huge (-30%+), strategy is too risky

---

### Best Month / Worst Month
**What it is:** Best and worst monthly performance.

**What to watch:**
- ⚠️ Worst Month shows maximum pain tolerance needed
- ✅ If you can't emotionally handle Worst Month, don't trade this strategy

---

## 📊 Section 2: Risk-Adjusted Returns

**Key Concept:** Returns alone don't tell the whole story. These metrics measure **return per unit of risk**.

### Sharpe Ratio
**What it is:** Measures return adjusted for volatility (total risk).

**Formula:** `(Return - Risk-Free Rate) / Volatility`

**Interpretation:**
- ⚠️ <0.5 = Poor risk/reward
- ✅ 0.5-1.0 = Acceptable
- ✅ 1.0-2.0 = Good
- 🎯 >2.0 = Excellent (institutional quality)

**Example:** Sharpe of `0.73` means you get 0.73% return for every 1% of volatility you take.

**What to watch:**
- Compare to benchmark Sharpe
- Sharpe alone can be misleading (see Sortino)

---

### Sortino Ratio
**What it is:** Like Sharpe, but only penalizes **downside** volatility (losses).

**Why it's better than Sharpe:** Upside volatility is good! Sortino ignores it.

**Interpretation:**
- ⚠️ <0.5 = Poor
- ✅ 1.0-2.0 = Good
- 🎯 >2.0 = Excellent

**Example:** Sortino of `1.28` means your downside risk is well-controlled.

**What to watch:**
- If Sortino is much higher than Sharpe, strategy has good upside with controlled downside (ideal!)

---

### Calmar Ratio
**What it is:** Return divided by maximum drawdown.

**Formula:** `CAGR / Max Drawdown`

**Interpretation:**
- ⚠️ <1.0 = Return doesn't justify drawdown pain
- ✅ 1.0-3.0 = Acceptable
- 🎯 >3.0 = Excellent risk/reward

**Example:** Calmar of `0.65` means you get 0.65% CAGR for every 1% of maximum drawdown.

---

### Omega Ratio
**What it is:** Ratio of gains to losses, probability-weighted.

**Interpretation:**
- ⚠️ <1.0 = Losing strategy
- ✅ 1.0-1.5 = Decent
- 🎯 >1.5 = Strong performance

**Why it matters:** Captures the full distribution of returns (not just average).

---

## 📊 Section 3: Drawdown Analysis

**Key Concept:** Drawdowns measure **pain** - how much you'd lose from peak to trough.

### Max Drawdown
**What it is:** Largest peak-to-trough decline.

**Example:** `-21.62%` means at worst, you'd be down 21.62% from your highest point

**Interpretation:**
- ✅ <10% = Low risk
- ⚠️ 10-20% = Moderate risk
- 🔴 20-50% = High risk
- 💀 >50% = Extreme risk (most traders can't handle this)

**Critical question:** Can you emotionally handle losing this much?

---

### Max DD Duration (Longest DD Days)
**What it is:** How many days it took to recover from worst drawdown.

**Example:** `116 days` means you'd wait 4 months underwater before breaking even

**Why it matters:**
- Long drawdowns test patience
- Many traders quit during long drawdowns
- ⚠️ >6 months is psychologically challenging

---

### Avg Drawdown / Avg Drawdown Days
**What it is:** Typical drawdown depth and duration.

**Why it matters:**
- Max DD is rare (worst case)
- Avg DD shows what you'll experience regularly
- ✅ If Avg DD is much smaller than Max DD, strategy is generally stable

---

### Recovery Factor
**What it is:** Total return divided by max drawdown.

**Interpretation:**
- ⚠️ <1.0 = Return doesn't justify risk
- ✅ 1.0-3.0 = Acceptable
- 🎯 >3.0 = Excellent

**Example:** Recovery Factor of `2.61` means returns are 2.61x the worst drawdown.

---

### Ulcer Index
**What it is:** Measures depth and duration of drawdowns combined.

**Interpretation:**
- Lower is better
- Measures "pain" of holding through drawdowns
- ⚠️ High Ulcer Index = Long, deep drawdowns (painful to trade)

---

## 📊 Section 4: Volatility & Risk

### Volatility (Annualized)
**What it is:** Standard deviation of returns, annualized.

**Example:** `20.66%` means typical annual swings are ±20.66%

**Interpretation:**
- ✅ <15% = Low volatility (safer)
- ⚠️ 15-30% = Moderate volatility
- 🔴 >30% = High volatility (crypto is typically 50-80%)

**Why it matters:** Higher volatility = larger swings = more emotional stress.

---

### Value-at-Risk (VaR 95%)
**What it is:** Maximum loss expected on 95% of days.

**Example:** VaR of `-2.08%` means 95% of days you won't lose more than 2.08%

**Interpretation:**
- ✅ <2% = Low daily risk
- ⚠️ 2-5% = Moderate daily risk
- 🔴 >5% = High daily risk

**What to watch:**
- 1 in 20 days (5%) will be worse than VaR
- Plan for those bad days!

---

### Expected Shortfall (CVaR 95%)
**What it is:** **Average** loss on the worst 5% of days.

**Example:** CVaR of `-3.09%` means when bad days happen, average loss is 3.09%

**Why it's important:**
- VaR tells you the threshold
- CVaR tells you how bad it gets **beyond** that threshold
- ⚠️ If CVaR is much worse than VaR, you have extreme tail risk

---

### Skewness
**What it is:** Measures asymmetry of return distribution.

**Interpretation:**
- **Positive skew** (>0) = Occasional large wins, frequent small losses (lottery-like)
- **Negative skew** (<0) = Occasional large losses, frequent small wins (writing insurance)
- **Zero skew** = Symmetric (normal distribution)

**What's good:**
- ✅ Positive skew (5-10) = Strategy has beneficial asymmetry
- ⚠️ Very high skew (>20) = Rare huge wins (might be luck)

---

### Kurtosis
**What it is:** Measures "fat tails" - likelihood of extreme events.

**Interpretation:**
- **Low kurtosis** (0-3) = Normal distribution (rare extremes)
- **High kurtosis** (>3) = Fat tails (more extreme events than expected)
- **Very high** (>100) = Strategy has sparse trading (few large moves)

**What to watch:**
- ⚠️ High kurtosis (>50) = Expect occasional extreme moves
- This is **normal** for strategies with infrequent trades
- Don't panic! It's a mathematical artifact, not a problem

---

## 📊 Section 5: Win/Loss Statistics

### Win Rate
**What it is:** Percentage of winning trades.

**Example:** `54.55%` = 54.55% of trades were profitable

**Interpretation:**
- ⚠️ <40% = Low win rate (needs large avg wins)
- ✅ 40-60% = Typical for good strategies
- ✅ 60-70% = High win rate
- 🤔 >80% = Too high? Check for overfitting

**Common misconception:** High win rate doesn't guarantee profitability!

---

### Payoff Ratio (Avg Win / Avg Loss)
**What it is:** Average win size divided by average loss size.

**Example:** Payoff of `1.33` means wins are 1.33x bigger than losses

**Interpretation:**
- ⚠️ <1.0 = Wins smaller than losses (need high win rate)
- ✅ 1.0-2.0 = Balanced
- 🎯 >2.0 = Large winners (can have lower win rate)

**Golden rule:** `Win Rate × Payoff Ratio > 1.0` = Profitable

**Example:** 54% win rate × 1.33 payoff = 0.72 (marginal, but profitable with volume)

---

### Profit Factor
**What it is:** Total gains divided by total losses.

**Formula:** `Sum of All Wins / Sum of All Losses`

**Interpretation:**
- 🔴 <1.0 = Losing strategy (don't trade!)
- ⚠️ 1.0-1.5 = Marginally profitable
- ✅ 1.5-2.0 = Good
- 🎯 >2.0 = Excellent

**Example:** Profit Factor of `1.4` means wins are 1.4x larger than losses in total.

---

### Max Consecutive Wins / Losses
**What it is:** Longest winning/losing streak.

**Example:**
- Max Consecutive Wins: `9` = Best streak was 9 wins in a row
- Max Consecutive Losses: `8` = Worst streak was 8 losses in a row

**Why it matters:**
- Prepare emotionally for long losing streaks
- ⚠️ If max losing streak is >10, it's psychologically tough

---

### Common Sense Ratio
**What it is:** Measures if returns are consistent with risk taken.

**Interpretation:**
- ✅ >1.0 = Strategy makes sense
- ⚠️ <1.0 = Returns don't justify risk

---

### Tail Ratio
**What it is:** 95th percentile gain divided by 95th percentile loss.

**Interpretation:**
- ✅ >1.0 = Beneficial asymmetry (big wins > big losses)
- ⚠️ <1.0 = Dangerous asymmetry (big losses > big wins)

---

## 📊 Section 6: Position Sizing

### Kelly Criterion
**What it is:** Optimal position size to maximize long-term growth.

**Example:** `14.62%` means bet 14.62% of capital per trade (theoretically optimal)

**Interpretation:**
- ⚠️ **Never** use full Kelly! It's too aggressive
- ✅ Use 25-50% of Kelly (fractional Kelly)
- Example: 14.62% Kelly → Use 3.6% to 7.3% per trade

**Why it matters:** Prevents over-betting and blowing up account.

---

### Risk of Ruin
**What it is:** Probability of losing all capital.

**Interpretation:**
- ✅ 0% = Effectively zero chance (good!)
- ⚠️ <1% = Very low risk
- 🔴 >5% = Too risky (unacceptable for most traders)

---

## 📊 Section 7: Benchmark Comparison

Your tear sheet shows **two columns**: Strategy vs Benchmark (BTC/ETH buy-and-hold)

### What To Look For:

1. **Strategy Sharpe > Benchmark Sharpe** ✅
   - Your strategy is more risk-efficient

2. **Strategy Max DD < Benchmark Max DD** ✅
   - Your strategy is safer

3. **Strategy Return > Benchmark Return** 🎯
   - Your strategy beats buy-and-hold

**Ideal scenario:** Better returns with lower drawdowns = Alpha generation!

---

## 📊 Section 8: Understanding Charts

### 1. Cumulative Returns Chart
**What it shows:** Equity curve over time.

**How to read it:**
- **Upward slope** = Making money
- **Flat periods** = Not trading (strategy-only returns)
- **Downward slope** = Drawdown period

**What to look for:**
- ✅ Smooth upward trend
- ⚠️ Long flat periods = Strategy inactive
- 🔴 Sharp drops = Large losses

---

### 2. Drawdown Chart (Underwater Plot)
**What it shows:** How far below peak you are at any time.

**How to read it:**
- **Zero line** = At all-time high
- **Below zero** = Underwater (in drawdown)
- **Shaded area** = Depth and duration of pain

**What to look for:**
- ✅ Quick recoveries (back to zero fast)
- ⚠️ Long underwater periods = Hard to trade psychologically

---

### 3. Monthly Returns Heatmap
**What it shows:** Calendar view of monthly performance.

**How to read it:**
- **Green squares** = Positive months
- **Red squares** = Negative months
- **Intensity** = Magnitude of return

**What to look for:**
- ✅ More green than red
- ✅ Consistent performance across months
- ⚠️ All losses in specific months = Seasonal weakness

---

### 4. Rolling Sharpe Ratio
**What it shows:** How Sharpe ratio changes over time (6-month windows).

**What to look for:**
- ✅ Stable Sharpe = Consistent performance
- ⚠️ Declining Sharpe = Strategy degrading
- ⚠️ Volatile Sharpe = Inconsistent performance

---

### 5. Distribution of Returns
**What it shows:** Histogram of daily returns.

**What to look for:**
- **Bell curve shape** = Normal distribution (predictable)
- **Fat right tail** = Occasional big wins (good!)
- **Fat left tail** = Occasional big losses (bad!)
- ⚠️ If not bell-shaped, strategy has unusual risk profile

---

### 6. Worst Drawdowns Table
**What it shows:** Top 10 worst drawdown periods.

**Columns:**
- **Started** = When drawdown began
- **Recovered** = When equity returned to peak
- **Drawdown %** = Depth of loss
- **Days** = Duration underwater

**What to look for:**
- ✅ Short durations (<30 days)
- ⚠️ Multiple long drawdowns = Psychologically tough

---

## 📊 Section 9: Red Flags to Watch

### 🚩 Red Flag #1: Too Good To Be True
**Signs:**
- CAGR >100% with low drawdown
- Sharpe >3.0
- Win rate >80%

**What it means:** Likely overfit or using future data (look-ahead bias).

---

### 🚩 Red Flag #2: Recent Degradation
**Signs:**
- 3M and 6M returns much worse than 1Y and 3Y
- Recent Sharpe < Historical Sharpe

**What it means:** Strategy might be dying (market conditions changed).

---

### 🚩 Red Flag #3: Extreme Tail Risk
**Signs:**
- CVaR is 3x worse than VaR
- Worst Day is >20% loss
- Negative skew with high kurtosis

**What it means:** Strategy is a "picking up pennies in front of a steamroller" - small wins, catastrophic losses.

---

### 🚩 Red Flag #4: Inconsistent Performance
**Signs:**
- Rolling Sharpe is all over the place
- Long periods of zero returns
- All profits from one lucky period

**What it means:** Strategy is unreliable or lucky.

---

## 📊 Section 10: Making The Decision

### Step 1: Check The Fundamentals
- ✅ Positive CAGR
- ✅ Sharpe >0.5
- ✅ Max DD <30%
- ✅ Profit Factor >1.25

### Step 2: Compare To Benchmark
- ✅ Better Sharpe than buy-and-hold
- ✅ Lower drawdown than buy-and-hold
- ✅ Ideally higher returns too

### Step 3: Check Risk Profile
- ✅ Can you handle Max Drawdown emotionally?
- ✅ Can you wait through Longest DD period?
- ✅ Is VaR acceptable for your risk tolerance?

### Step 4: Look For Red Flags
- ⚠️ Any of the red flags above?
- ⚠️ Strategy degrading recently?
- ⚠️ Extreme tail risk?

### Step 5: Make Decision
**If all checks pass:**
- ✅ Strategy is worth paper trading
- ✅ Start with small position (25-50% of Kelly)
- ✅ Monitor performance monthly

**If checks fail:**
- 🔴 Don't trade yet
- 🔴 Ask for strategy improvements
- 🔴 Consider different parameters

---

## 📊 Appendix: Glossary

**Alpha** - Excess return above benchmark  
**Annualized** - Scaled to yearly basis  
**Asymmetry** - Unbalanced distribution (skew)  
**Backtest** - Historical simulation of strategy  
**Benchmark** - Comparison standard (e.g., BTC buy-and-hold)  
**Beta** - Correlation with market  
**CAGR** - Compound Annual Growth Rate  
**CVaR** - Conditional Value at Risk (tail risk)  
**Drawdown** - Peak-to-trough decline  
**Fat tails** - More extreme events than normal distribution  
**Kelly Criterion** - Optimal bet sizing formula  
**Kurtosis** - Measure of tail heaviness  
**Overfit** - Strategy works on past data but not future  
**Sharpe Ratio** - Risk-adjusted return metric  
**Skew** - Asymmetry of distribution  
**Sortino Ratio** - Downside-focused Sharpe  
**Tail risk** - Extreme event risk  
**Underwater** - Below previous peak (in drawdown)  
**VaR** - Value at Risk (loss threshold)  
**Volatility** - Standard deviation of returns  
**Win rate** - Percentage of winning trades

---

## 📊 FAQ

**Q: My Sharpe is only 0.6. Is that bad?**  
A: No! 0.5-1.0 is acceptable. Crypto is volatile, so Sharpe >1.0 is rare. Focus on Sortino too.

**Q: I have high kurtosis (300+). Is something wrong?**  
A: No! High kurtosis is **normal** for strategies with sparse trading. It's a math artifact, not a bug.

**Q: Should I look at Strategy column or Benchmark column?**  
A: Look at **both**! Strategy shows your strategy's performance. Benchmark shows if you beat buy-and-hold.

**Q: What if my strategy loses recently but was great historically?**  
A: ⚠️ Red flag. Markets change. Strategy might be degrading. Monitor closely.

**Q: Can I trust a backtest with only 20 trades?**  
A: ⚠️ Low sample size. Results could be lucky. Need 100+ trades for statistical confidence.

**Q: What's the most important metric?**  
A: No single metric! Look at: CAGR, Sharpe, Max DD, Profit Factor, and Win Rate together.

**Q: My tear sheet shows 13.9 skew and 308 kurtosis. Help!**  
A: That's **normal** for sparse trading strategies (few large trades with many zero-return days). Not a concern.

---

## 📞 Questions?

If anything is unclear or you need strategy adjustments, please reach out!

**Remember:** Past performance doesn't guarantee future results. Always start with paper trading before risking real capital.

---

**Document Version:** 1.0  
**Last Updated:** January 4, 2026  
**For:** Professional Strategy Tear Sheet Reports
