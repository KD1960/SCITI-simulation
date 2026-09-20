# Catalog v2 — E1 and sensitivity screen rerun

> **Status (2026-09-20):** this is the "every adoption works" case. With implementation risk, learning, and group project draws on (the default since 2026-09-19), see `multi-party-combination-proposal.md` §6.

**Date:** 2026-09-18
**Engine and catalog:** branch `catalog-v2` at `4a4d1b3` (catalog v2: MID values from `evidence-table.md`, ML skill by role, risk intelligence as weeks saved plus warning probability)
**Commands:** `tech_screen.py OUT_DIR` and `sensitivity_screen.py OUT_DIR` (both in `docs/sciti2/experiments/`)
**Full numbers:** `experiments/tech_screen_results_v2.csv`, `experiments/sensitivity_screen_results_v2.csv`
**Compare with:** `tech-screen-e1-2026-09-17.md` (catalog v1, same engine apart from the v2 changes)

All profit figures are `network_profit_with_inventory`, $M over 3 years, 30 paired seeds, every eligible firm adopting in week 1 (so the +25% group bonus applies). (ns) = 95% range includes zero.

## E1: v1 vs v2, calm conditions

| Technology | v1 profit | v2 profit | What changed in the catalog | Other v2 effects |
|---|---|---|---|---|
| Routing | +444 | **+444** | CO2 cut 10% → 6% | CO2 −222 kt (was −370) |
| Blockchain | +706 | **+321** | Defect cut 40% → 18% | Satisfaction +0.0010 |
| Warehouse robotics | +198 | **+124** | Dispatch −1.0 → −0.6 day | Satisfaction +0.0067, fill +0.24 pt |
| Item-level RFID | +185 | **+83** | Shrink cut 50% → 20% | — |
| Control tower | +65 | **+63** | Visibility 1.0 → 0.6 (0.75 in a group) | CM bullwhip −71 (was −78); fill +0.10 pt |
| APS | +20 (ns) | +20 (ns) | none | fill +0.16 pt |
| ML forecasting | −35 | **−7 (ns)** | Stores 0.3 → 0.1 | CM bullwhip −58; fill +0.04 pt |
| Risk intelligence | −8 | −8 | new shape | no disruptions, so pure cost |

One-tier arms (v2): RFID at stores +29; control tower at DCs + stores +18; APS at factories +22; ML forecasting at stores −15; routing at DCs 0; risk intelligence at CMs −3.

## What this says

1. **Routing is now the top technology, not blockchain.** Blockchain's gain more than halves, in proportion to its effect size, and it rests on the weakest evidence in the table.
2. **Control tower barely moves.** Cutting visibility from 1.0 to 0.6 costs $2M of $65M and a tenth of the bullwhip cut. Most of the benefit arrives by the time the echelon signal has a little over half the weight. This makes the control tower result robust to its most uncertain parameter.
3. **RFID's v1 gain was mostly shrink.** With the shrink cut at 20% the gain falls from +185 to +83. The model's shrink baseline (0.2%/week, about 6× retail shrink) is now the number to check: RFID's value scales with it.
4. **Robotics' dispatch speed is worth about $74M.** Moving from −1.0 to −0.6 day cuts the gain by more than a third, so the customer-service side of robotics matters as much as handling cost.
5. **ML forecasting is now neutral (−7, ns) instead of a loss.** Lower skill at stores removes the store-tier loss; it still cuts CM bullwhip by more than half.

## Sensitivity screen on v2 (effect sizes at 0.5×, 1×, 1.5× of the v2 values)

| Technology | Calm 0.5× | Calm 1× | Calm 1.5× | CM_3 hit 0.5× | CM_3 hit 1× | CM_3 hit 1.5× | Break-even cost (1×, calm / hit) |
|---|---|---|---|---|---|---|---|
| Routing | +219 | +444 | +670 | +211 | +430 | +649 | 63× / 61× |
| Blockchain | +157 | +321 | +481 | +155 | +314 | +470 | 31× / 30× |
| Warehouse robotics | +49 | +124 | +182 | +46 | +119 | +177 | 7× / 7× |
| RFID | +43 | +83 | +117 | +17 | +51 | +90 | 7× / 5× |
| Control tower | +29 | +63 | +65 | +79 | +91 | +89 | 3× / 4× |
| APS | +8 | +20 | +24 | +226 | +387 | +503 | 2× / 29× |
| ML forecasting | −5 | −7 | −15 | +32 | +49 | +37 | 0.6× / 4× |
| Risk intelligence | −8 | −8 | −8 | +260 | +575 | +887 | never / 71× |

- **The ranking is stable inside the evidence ranges** except between neighbours: blockchain at 1.5× (+481) passes routing at 1× (+444); robotics and RFID can swap.
- **Costs still do not decide anything** for routing, blockchain, robotics, or RFID. They now matter for control tower (3×), APS in calm (2×), and ML forecasting (below 1× in calm): these are the three where cost evidence is worth collecting.
- **Risk intelligence's gain in a 12-week CM hit is +$575M, about a third of v1's.** Two weeks saved on a 12-week outage is a 17% cut (v1 assumed 40%), and only ~40% of seeds get advance warning. It is still the most valuable technology in a long disruption, followed by APS (+$387M).
- **ML forecasting helps in a disruption** (+$49M) even though it is neutral in calm.
- Control tower at 1.5× equals 1×: 0.6 × 1.5 × 1.25 (group bonus) is above the cap of 1.

## Still open

- Shrink baseline (0.2%/week) and RFID running cost at high-volume sites (evidence-table §4.3).
- Cost evidence for control tower, APS, and ML forecasting.
- E2–E5 still predate the engine fixes and catalog v2.
