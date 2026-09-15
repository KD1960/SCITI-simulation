# E2 Stress Test — Results

**Date:** 2026-09-15
**Engine:** `main` at `810a39a`
**Command:** `.venv/bin/python docs/sciti2/experiments/stress_test.py OUT_DIR` (3,150 runs, about 19 minutes)
**Full numbers:** `docs/sciti2/experiments/stress_test_results.csv`

> **Illustrative only.** Technology costs and effects, and the disruption sizes, are placeholders. These results show how the model behaves, not real-world impact.

## What we ran

**21 scenarios:**
- **Demand growth:** each product's yearly growth trend × 0.5, × 1 (normal), or × 1.5.
- **Disruption:** none, or one site hit from week 30 for **4 weeks** or **12 weeks**:
  - **CM_3** (Mexico): elastomers and plastics, 110 of the 160 parts in each product.
  - **CM_4** (Germany): glass, on the longest sea lane.
  - **DC_Shanghai**: the DC serving four Asia-Pacific stores.
- A hit cuts the site's output to 20% and adds 14 days to its shipments. DCs have no output limit in the model, so for DC_Shanghai only the delay applies.

**5 arms in every scenario, 30 seeds each:**
- No technology (the comparison point)
- Risk intelligence on all 10 eligible firms
- Control tower on all 48 firms
- APS (planning) on all 6 eligible firms
- Agents choosing for themselves with the payback rule

Forced group adoptions get the +25% group bonus. Every number below is an average paired difference over 30 seeds.

## Bottom line

1. **Short disruptions barely matter; long ones hurt a lot.** Four weeks at a component maker stays inside the stock buffer (profit −$17M at most; −$81M at DC Shanghai). Twelve weeks at a component maker cuts fill by about 3 points and profit by $1.4–1.6B.
2. **Risk intelligence is true insurance.** It costs $8M when nothing happens. In a 12-week component-maker disruption it wins back **$1.2–1.5B** and **most of the 2.7–3.3 lost fill points** (about 2.5–2.8 points). In a 4-week one it does almost nothing, because there is little to recover.
3. **APS is partial insurance.** It loses $30–60M in calm conditions but gains **$250–330M** in long component-maker disruptions. It raises fill in every scenario (+0.1 to +1.0 pt).
4. **Control tower is not insurance.** It earns about $100M in most scenarios, disrupted or not. Its profit gain **disappears when demand grows fast** (× 1.5), though it still raises fill and satisfaction there.
5. **The payback-rule agents miss the insurance technologies entirely.** They adopt about 52 technologies in every scenario, and never risk intelligence, APS, or warehouse robotics. So they gain $170–200M in every scenario at normal or slow growth (about $100M at fast growth) but get none of the disruption protection.
6. **Faster or slower demand growth is not much of a stress.** It changes profit mostly because there is more or less to sell (× 1.5: +$4.5B; × 0.5: −$2.8B). Fill moves by less than 0.3 points without a disruption.

## How much each scenario hurts (no technology, vs. calm with normal growth)

| Scenario (normal growth) | Profit | Fill rate | Stockout cost | Store on-time |
|---|---|---|---|---|
| CM_3 Mexico, 4 weeks | −$17M | −0.08 pt | +$14M | 0 |
| CM_3 Mexico, 12 weeks | **−$1,610M** | **−3.25 pt** | +$533M | 0 |
| CM_4 Germany, 4 weeks | −$6M (not significant) | −0.03 pt | +$4M | 0 |
| CM_4 Germany, 12 weeks | **−$1,373M** | **−2.72 pt** | +$446M | 0 |
| DC Shanghai, 4 weeks | −$81M | −0.17 pt | +$28M | −0.9 pt |
| DC Shanghai, 12 weeks | −$350M | −0.70 pt | +$115M | **−2.8 pt** |

With growth × 1.5, the 12-week component-maker hits cut fill a little more (−2.9 to −3.4 pt).

## What each technology is worth, by scenario (normal growth)

Profit change vs. no technology in the same scenario, $M over 3 years. * = the 95% range excludes zero.

| Scenario | Risk intelligence | APS | Control tower | Payback-rule agents |
|---|---|---|---|---|
| Calm | −8* | −32* | +99* | +190* |
| CM_3 Mexico, 4 weeks | +8 | −15 | +92* | +184* |
| CM_3 Mexico, 12 weeks | **+1,364*** | **+246*** | +120* | +180* |
| CM_4 Germany, 4 weeks | −2 | −28* | +95* | +182* |
| CM_4 Germany, 12 weeks | **+1,272*** | **+304*** | +119* | +173* |
| DC Shanghai, 4 weeks | +27* | −30* | +99* | +193* |
| DC Shanghai, 12 weeks | +195* | −33* | +96* | +190* |

**Fill rate change (points), same scenarios:**

| Scenario | Risk intelligence | APS | Control tower | Payback-rule agents |
|---|---|---|---|---|
| Calm | 0.00 | +0.16* | +0.08* | 0.00 |
| CM_3 Mexico, 12 weeks | **+2.72*** | +0.70* | +0.23* | 0.00 |
| CM_4 Germany, 12 weeks | **+2.51*** | +0.82* | +0.19* | −0.01 |
| DC Shanghai, 12 weeks | +0.41* | +0.16* | +0.09* | +0.01 |

At DC Shanghai, risk intelligence also restores 1.4 of the 2.8 lost on-time points.

**Growth changes the picture for two technologies (profit, $M, calm):**

| Growth | APS | Control tower | Payback-rule agents |
|---|---|---|---|
| × 0.5 | −15 (not significant) | +116* | +202* |
| × 1 | −32* | +99* | +190* |
| × 1.5 | −63* | −4 (not significant) | +119* |

## What the agents adopt

Average adoptions per run under the payback rule (normal growth):

| Scenario | RFID | Control tower | ML forecasting | Blockchain | Routing | Risk intel, APS, robotics |
|---|---|---|---|---|---|---|
| Calm | 17.6 | 13.7 | 11.9 | 6.7 | 2.8 | 0 |
| CM_3 Mexico, 12 weeks | 17.5 | 13.2 | 12.0 | 6.7 | 2.5 | 0 |

The payback rule looks back at last quarter's costs and doesn't see what is coming, so a disruption doesn't change its choices. Also, blockchain and routing were the two biggest earners in E1, yet agents adopt them least.

## What this means

- **For teaching:** "insurance vs. everyday savings" is now a clear, data-backed story. Risk intelligence is worthless until a long disruption, then worth about 170 times its cost.
- **For E3 (who with whom):** use a 12-week component-maker disruption as the stress condition. It moves fill rate by about 3 points; the only other large service change is on-time delivery in the 12-week DC Shanghai delay.
- **For E4 / E5 (how agents decide):** the payback rule ignores insurance and under-adopts the biggest earners. That is a good baseline to beat, and a clear question for the LLM agents: do they buy insurance?
- **To check:**
  - Why control tower's profit gain vanishes at high growth. The echelon forecast may lag a rising trend.
  - Why APS loses more money as demand grows.
- **Caveats:**
  - Disruption sizes (20% output, +14 days), the 40% recovery speed-up, and the group bonus are all placeholders.
  - At DC Shanghai only the delay applies.

## Settings

- Seeds 1–30; 156 weeks; disruptions start in week 30.
- Risk intelligence members: 4 CMs, 2 factories, 4 DCs. APS members: 4 CMs, 2 factories.
- 95% ranges use t = 2.045 for 30 paired seeds.
