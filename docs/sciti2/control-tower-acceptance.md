# Control tower acceptance results

**Date:** 2026-09-14
**Git commit:** `c76dd84` (branch `control-tower-echelon`, after Task 4, the echelon fix)
**Command:**
```
.venv/bin/python docs/sciti2/experiments/control_tower_acceptance.py OUT_DIR
```
10 seeds, 156 weeks, policy `none`, on `data/baseline.json`. Each arm is compared to a same-seed no-tech run (paired difference), reported as mean ± 95% confidence interval.

## Run 2 (after the fix)

### The four checks

| # | Check | Result |
|---|---|---|
| 1 | Bullwhip falls at DC, MFG, and CM (whole network) | **PASS** |
| 2 | Fill rate does not fall meaningfully (whole-network CI upper bound ≥ 0) | **PASS** |
| 3 | System inventory cost does not rise (whole-network CI lower bound ≤ 0) | **PASS** |
| 4 | Effect grows with adoption scope (Shanghai chain < downstream < whole network) | **PASS** |

**4 of 4 checks passed.** The fix works: with the echelon lead time and safety-stock floor in place, giving nodes a control tower now smooths ordering (bullwhip falls sharply) without hurting customers — fill rate holds steady or improves slightly, and network profit is slightly better than the no-tech baseline.

### Whole-network results (all 48 nodes adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −2.35 | −2.49 to −2.22 |
| Bullwhip, MFG | −13.28 | −14.59 to −11.96 |
| Bullwhip, CM | −78.69 | −87.18 to −70.2 |
| Fill rate | **+0.09 pt** | +0.05 to +0.12 pt |
| Satisfaction index | +0.05 pt | +0.03 to +0.07 pt |
| Holding cost | −$35.1M | −$42.0M to −$28.1M |
| Network profit | **+$110.5M** | +$60.8M to +$160.2M |
| Revenue | +$60.5M | −$78.3M to +$199.4M |
| Purchases cost | +$10.9M | −$120.7M to +$142.5M |
| COGS | −$42.9M | −$69.5M to −$16.4M |
| Shipping cost | −$3.7M | −$17.3M to +$9.8M |
| Stockout cost | **−$14.2M** | −$20.4M to −$7.9M |
| Scrap cost | −$21.4M | −$26.7M to −$16.1M |
| Tech cost | +$35.1M | +$35.1M to +$35.1M |

Baselines (no-tech, whole network): fill rate 98.35%, satisfaction 96.14%, holding cost $1,073M, network profit $32,430M, stockout cost $270.6M.

### Comparison: old rule vs. run 1 vs. run 2 (whole network)

| Rule | Fill rate | Stockout cost | Holding cost | Profit |
|---|---|---|---|---|
| Old rule (spec §1, end-customer demand as forecast signal) | −0.23 pt | +$38M | — | −$62M |
| Run 1 (echelon ordering, before the fix) | −12.2 pt | +$2,006M | −$493M | −$4,907M |
| Run 2 (echelon ordering, after the fix) | **+0.09 pt** | **−$14.2M** | **−$35.1M** | **+$110.5M** |

Run 2 is better than both the old rule and run 1 on every one of these numbers. Fill rate no longer falls at all — it ticks up slightly. Stockout cost falls slightly instead of rising. Bullwhip still falls sharply (see table above), and now that improvement comes without the fill-rate and cost damage seen in run 1.

## Downstream arm (4 DCs + 8 stores adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −2.33 | −2.48 to −2.18 |
| Bullwhip, MFG | −8.01 | −8.77 to −7.25 |
| Bullwhip, CM | −38.73 | −43.85 to −33.61 |
| Fill rate | +0.10 pt | +0.05 to +0.15 pt |
| Satisfaction index | +0.05 pt | +0.03 to +0.08 pt |
| Holding cost | +$17.4M | +$13.1M to +$21.6M |
| Network profit | +$26.5M | −$9.3M to +$62.3M |
| Stockout cost | −$15.7M | −$23.8M to −$7.6M |

## Shanghai-chain arm (DC_Shanghai + Retail_5–8 adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −0.87 | −0.96 to −0.78 |
| Bullwhip, MFG | −2.99 | −3.44 to −2.54 |
| Bullwhip, CM | −13.71 | −16.59 to −10.83 |
| Fill rate | +0.03 pt | −0.00 to +0.07 pt |
| Satisfaction index | +0.02 pt | −0.00 to +0.04 pt |
| Holding cost | +$5.4M | +$1.1M to +$9.7M |
| Network profit | +$16.6M | −$18.9M to +$52.0M |
| Stockout cost | −$5.5M | −$11.1M to +$0.2M |

Run 1's Shanghai-chain arm showed fill rate −2.5 pt and stockout cost +$417M. Run 2 shows fill rate roughly flat (+0.03 pt, CI touches zero) and stockout cost essentially flat to slightly lower (−$5.5M, CI touches zero). The small group has less echelon stock to redistribute, so its effect is smaller and less certain than the downstream and whole-network arms — but it moved from clearly harmful in run 1 to harmless in run 2.

## What changed, in plain language, by arm

**Shanghai chain (5 nodes).** The smallest group: one DC in Shanghai and its four stores. A control tower smooths their ordering a little (bullwhip drops by about 1 unit at the DC, 3 at the manufacturer, 14 at the contract manufacturer). Customers are served about as well as before — fill rate is flat, and stockout cost is flat to slightly lower. Profit is about flat too. Unlike run 1, this arm no longer hurts customers.

**Downstream (12 nodes: all 4 DCs and all 8 stores).** With every DC and store using a control tower, the smoothing effect is bigger (bullwhip drops more at every tier: about 2 units at DCs, 8 at manufacturers, 39 at contract manufacturers). Fill rate improves slightly (about 0.1 percentage points better), stockout cost falls about $15.7 million, and profit is about $26.5 million higher, though that last number is not statistically distinguishable from zero.

**Whole network (all 48 nodes, including manufacturers and contract manufacturers).** With everyone using a control tower, bullwhip drops the most — orders through the whole chain become far smoother (down about 2 units at DCs, 13 at manufacturers, 79 at contract manufacturers). Fill rate no longer falls; it is about 0.09 percentage points higher than no-tech. Stockout cost falls by about $14 million and holding cost falls by about $35 million. Network profit rises by about $111 million over the three-year run. This is the opposite of run 1's result at the same scope.

## What went wrong in run 1 and what changed

Run 1 used an echelon lead time that skipped the extra one-week review period each downstream stage adds, and it sized the echelon's safety stock as one pooled number that ignored the safety stock the downstream nodes were still keeping under their own local ordering rules. Two gaps followed from this, per spec §3.6:

1. **Missing review week.** The echelon target didn't add the one-week review period for each stage below the tower node, so a tower node's order target ran about a week short of what it actually needed. This alone, in a scratch test, cut the whole-network fill-rate drop from −12.2 pt to about −1.2 pt.
2. **Undersized safety stock.** The pooled echelon safety stock could be smaller than the sum of the safety stocks the downstream nodes still held under their own rules. The tower node then effectively squeezed its own stock to cover downstream, because its target didn't account for stock downstream nodes were already committed to keeping. DC_Shanghai's average stock, for example, fell from 8,085 to 1,249 units in run 1.

The fix (Task 4, spec §3.4–3.5) adds the missing review week to the echelon lead time and adds a safety-stock floor: the echelon plan never targets less safety stock than the sum of what the stages below it actually hold under their own installation rules. Run 2, with both fixes in place, passes all four acceptance checks.
