# Control tower acceptance results

**Date:** 2026-09-14
**Git commit:** `9c31f77` (branch `control-tower-echelon`, after Task 1 and Task 2)
**Command:**
```
.venv/bin/python docs/sciti2/experiments/control_tower_acceptance.py OUT_DIR
```
10 seeds, 156 weeks, policy `none`, on `data/baseline.json`. Each arm is compared to a same-seed no-tech run (paired difference), reported as mean ± 95% confidence interval.

## The four checks

| # | Check | Result |
|---|---|---|
| 1 | Bullwhip falls at DC, MFG, and CM (whole network) | **PASS** |
| 2 | Fill rate does not fall meaningfully (whole-network CI upper bound ≥ 0) | **FAIL** |
| 3 | System inventory cost does not rise (whole-network CI lower bound ≤ 0) | **PASS** |
| 4 | Effect grows with adoption scope (Shanghai chain < downstream < whole network) | **PASS** |

**3 of 4 checks passed.** Check 2 failed: the new echelon-ordering rule causes a bigger drop in fill rate than the old rule it replaced.

## Whole-network results (all 48 nodes adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −4.42 | −4.70 to −4.14 |
| Bullwhip, MFG | −17.68 | −19.20 to −16.16 |
| Bullwhip, CM | −95.12 | −104.9 to −85.3 |
| Fill rate | **−12.2 pt** | −12.5 to −12.0 pt |
| Satisfaction index | −6.1 pt | −6.2 to −6.0 pt |
| Holding cost | −$493M | −$502M to −$484M |
| Network profit | −$4,907M | −$5,063M to −$4,752M |
| Revenue | −$26,580M | −$27,170M to −$26,000M |
| Purchases cost | −$19,570M | −$20,010M to −$19,140M |
| COGS | −$2,970M | −$3,037M to −$2,904M |
| Shipping cost | −$680M | −$707M to −$653M |
| Stockout cost | **+$2,006M** | +$1,959M to +$2,052M |
| Scrap cost | −$548M | −$556M to −$540M |
| Tech cost | +$35M | +$35M to +$35M |

Baselines (no-tech, whole network): fill rate 98.35%, satisfaction 96.14%, holding cost $1,073M, network profit $32,430M, stockout cost $270.6M.

### Compared with the old rule (spec §1, before this redesign)

| Rule | Fill rate | Profit | Stockout cost |
|---|---|---|---|
| Old rule (end-customer demand as forecast signal) | −0.23 pt | −$62M | +$38M |
| New rule (echelon ordering, this experiment) | **−12.2 pt** | **−$4,907M** | **+$2,006M** |

The new rule is far worse on all three whole-network numbers than the rule it replaced. Bullwhip is much better under the new rule (see table above), but the fill-rate and cost damage is large enough to fail acceptance check 2.

## Downstream arm (4 DCs + 8 stores adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −4.18 | −4.38 to −3.97 |
| Bullwhip, MFG | −13.42 | −14.52 to −12.31 |
| Bullwhip, CM | −70.68 | −78.23 to −63.14 |
| Fill rate | −3.3 pt | −3.6 to −3.1 pt |
| Satisfaction index | −1.7 pt | −1.8 to −1.6 pt |
| Holding cost | −$169M | −$175M to −$163M |
| Network profit | −$1,249M | −$1,387M to −$1,111M |
| Stockout cost | +$548M | +$508M to +$588M |

## Shanghai-chain arm (DC_Shanghai + Retail_5–8 adopt)

| Measure | Change vs. no-tech | 95% CI |
|---|---|---|
| Bullwhip, DC | −1.98 | −2.18 to −1.78 |
| Bullwhip, MFG | −6.49 | −7.50 to −5.47 |
| Bullwhip, CM | −34.64 | −40.96 to −28.31 |
| Fill rate | −2.5 pt | −2.7 to −2.4 pt |
| Satisfaction index | −1.3 pt | −1.4 to −1.2 pt |
| Holding cost | −$53M | −$58M to −$48M |
| Network profit | −$1,114M | −$1,197M to −$1,032M |
| Stockout cost | +$417M | +$387M to +$448M |

A task reviewer flagged that in a single golden run (Shanghai chain, one seed) fill rate fell from 98.19% to 97.65% (−0.54 pt) and stockout cost rose about 30%. Averaged over all 10 seeds, the Shanghai-chain arm here shows a bigger drop: fill rate falls about 2.5 percentage points and stockout cost rises about 4.6 times (from a no-tech baseline of $270.6M, no-tech, up $417M). Both the single golden run and this 10-seed average point the same way: fill rate gets worse and stockout cost rises when the Shanghai chain adopts a control tower. The size differs because one is a single seed and the other is a 10-seed average, but the direction and rough scale agree.

## What changed, in plain language, by arm

**Shanghai chain (5 nodes).** This is the smallest group: one DC in Shanghai and its four stores. Giving them a control tower makes ordering smoother up the chain (bullwhip — how much orders swing compared to real demand — drops by about 2 units at the DC, 6 at the manufacturer, and 35 at the contract manufacturer). But customers are worse served: about 2.5 fewer orders out of 100 get filled on time, and the cost of running out of stock goes up by about $417 million over the three-year run. Company profit falls by about $1.1 billion, mostly because of lost sales and higher stockout cost, offset a little by lower purchase and holding costs.

**Downstream (12 nodes: all 4 DCs and all 8 stores).** With every DC and store using a control tower, the smoothing effect is bigger (bullwhip drops more at every tier) but so is the damage: about 3.3 fewer orders out of 100 get filled, stockout cost rises about $548 million, and profit falls by about $1.2 billion.

**Whole network (all 48 nodes, including manufacturers and contract manufacturers).** With everyone using a control tower, bullwhip drops the most — orders through the whole chain become far smoother. But the fill-rate problem gets much worse, not better: about 12 fewer orders out of 100 get filled on time. Stockout cost rises by about $2.0 billion (from a $271 million baseline to about $2.3 billion) and network profit falls by about $4.9 billion over the three-year run. Holding cost does fall, as intended, by about $493 million, but that saving is far smaller than the stockout and lost-sales damage.

## Stopped here

Acceptance check 2 (fill rate does not fall meaningfully) **FAILED**: at whole-network adoption, the paired fill-rate change is −12.2 percentage points, and the 95% confidence interval (−12.5 to −12.0 pt) is entirely negative, well below the "upper bound ≥ 0" bar in spec §2.

Per the spec's acceptance rule ("if a criterion fails, stop and report; don't tune to pass"), no engine code, parameters, or acceptance criteria were changed to make this check pass. Checks 1, 3, and 4 passed: bullwhip falls at all three tiers, system inventory cost (holding) does not rise, and the effect grows with adoption scope in the expected order. Check 2's failure means the echelon-ordering redesign, as specified, trades a large bullwhip reduction for a fill-rate and cost regression that is worse than the rule it replaced. This needs Kevin's review before further tuning or a wider rollout.
