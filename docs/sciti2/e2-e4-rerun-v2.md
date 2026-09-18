# E2–E4 rerun on the corrected engine and catalog v2

**Date:** 2026-09-18
**Engine and catalog:** `main` at `588473e` (audit fixes, freight in prices, ML sigma fix, inventory-adjusted profit, catalog v2)
**Commands:** `stress_test.py`, `who_with_whom.py`, `decision_rules.py` in `docs/sciti2/experiments/` (each `OUT_DIR`)
**Full numbers:** `experiments/stress_test_results_v2.csv`, `who_with_whom_results_v2.csv`, `decision_rules_main_effects_v2.csv`
**Replaces:** `stress-test-e2.md`, `who-with-whom-e3.md`, `decision-rules-e4.md` (2026-09-15, old engine, catalog v1)

All profit figures are `network_profit_with_inventory`, $M over 3 years, 30 paired seeds, versus a same-seed, same-scenario no-tech run. (ns) = 95% range includes zero. Designs are unchanged from the 2026-09-15 runs.

> Catalog v2 uses the MID values of `evidence-table.md`. Blockchain, APS, and risk intelligence still rest on weak evidence (`assumption: true`); costs are still placeholders.

## E2 Stress test

**What disruptions cost with no technology** (growth ×1, vs calm): CM_3 12 weeks −$2,022M and −3.25 pt fill; CM_4 12 weeks −$1,723M and −2.72 pt; DC_Shanghai 12 weeks −$440M and −0.70 pt; every 4-week hit under $105M and 0.2 pt. Four-week hits still sit inside the buffer.

**What each technology adds** (growth ×1):

| Scenario | Risk intel | APS | Control tower | Payback-rule agents |
|---|---|---|---|---|
| Calm | −8 | +20 (ns) | +63 | +430 |
| CM_3, 4 weeks | +19 | +43 | +60 | +415 |
| CM_3, 12 weeks | **+591** | **+366** | +103 | +436 |
| CM_4, 4 weeks | +4 (ns) | +25 | +61 | +423 |
| CM_4, 12 weeks | **+582** | **+442** | +96 | +415 |
| DC_Shanghai, 4 weeks | +37 | +23 | +63 | +425 |
| DC_Shanghai, 12 weeks | +71 | +19 (ns) | +60 | +430 |

Fill-rate gain in the CM_3 12-week hit: risk intel +0.96 pt, APS +0.70, control tower +0.24, payback-rule agents +0.08.

1. **Risk intelligence is still insurance, at about a third of its old size.** It recovers ~29% of a 12-week CM loss (+$591M of $2,022M); under catalog v1 it recovered most of it (+$1.2–1.5B). Two weeks saved on a 12-week outage and a 40% chance of warning are much weaker than "40% shorter, always warned". It costs $8M in calm.
2. **APS is now free insurance.** With stock counted, it no longer loses money in calm (+$20M, ns; it was −$30–60M on cash profit) and recovers +$366–442M in long CM hits.
3. **Control tower is steady:** +$57–63M in calm and short hits, ~+$100M in long CM hits, at every growth level (+$87–126M at growth ×1.5). The old "about zero at high growth" result is gone; it was a cash-profit artifact.
4. **Payback-rule agents gain +$415–436M everywhere and do not react to disruptions.** Their gain more than doubled (from ~+$190M) because the freight fix lets shippers see routing's savings, so they now adopt it. They still never buy risk intelligence, APS, or robotics.
5. Growth: at ×0.5 and ×1.5 every pattern above holds; APS grows with demand (+$89M calm at ×1.5), as capacity binds more often.

## E3 Who with whom (6 adopters, different structures)

| Arm | Firms | Calm | CM_3 12 weeks | Tech cost | CM bullwhip (calm) |
|---|---|---|---|---|---|
| Control tower, scattered | 6 | −5 | −5 | 5 | 0 |
| Control tower, 3 DC–store pairs | 6 | +10 | +11 (ns) | 7 | −13 |
| Control tower, downstream chain | 6 | +13 | **+81** | 7 | −19 |
| Control tower, upstream chain | 6 | +13 | +50 | 10 | −36 |
| Control tower, all firms | 48 | +63 | +103 | 35 | −71 |
| Blockchain, scattered | 6 | −2 | −2 | 2 | 0 |
| Blockchain, 3 supplier–CM pairs | 6 | +14 | +13 | 3 | 0 |
| Blockchain, CM_1 hub | 6 | +30 | +29 | 2 | 0 |
| Blockchain, CM_3 hub | 6 | **+105** | +103 | 2 | 0 |
| Blockchain, all eligible | 34 | +321 | +314 | 11 | 0 |

1. **Scattered adopters still get nothing** (pure cost), for both technologies.
2. **Control tower: the chain matters most in a disruption.** A six-firm downstream chain earns +$81M in the CM_3 hit, 79% of what all 48 firms earn, for a fifth of the cost. In calm, upstream and downstream chains now tie (+$13M); the upstream chain still cuts bullwhip twice as much.
3. **Blockchain value still follows volume covered, not shape**, at a little under half the v1 level (CM_3 hub +$105M vs +$224M): about $1.9M per part-per-product covered instead of $4M, in line with the smaller defect cut.

## E4 Decision rules (payback-rule agents, 2^5 factorial)

Network gain ranges from +$365M to +$576M in calm (defaults +$430M) and +$384M to +$603M in the CM_3 hit (defaults +$436M). Worst: short horizon, one adoption per quarter, 80% acceptance. Best: long horizon, two per quarter, by-size split, larger budget.

| Factor (low → high) | Calm | CM_3 12 weeks | Adoptions |
|---|---|---|---|
| Payback horizon 13–52 → 52–156 weeks | **+97** | **+95** | +23 |
| New adoptions per quarter 1 → 2 | **+84** | **+100** | +10 |
| Cost split equal → by size | +9 | +11 | +2 |
| Chain acceptance 40% → 80% | −3 (ns) | −9 | −9 |
| Budget share low → high | 0 | 0 | 0 |

Adoptions per run (defaults, calm): RFID 18.0, control tower 14.8, ML forecasting 13.3, blockchain 9.7, routing 6.5, **APS 0, robotics 0, risk intelligence 0**; 62 adoptions and 4.7 groups.

1. **The same two levers matter, and horizon now leads:** patience (+$97M) and pace (+$84M). Budget still never binds.
2. **Agents now adopt routing** (6.5 of 10 eligible), because the shipper pays freight and so sees the saving. This split-incentive artifact from the 2026-09-17 audit is fixed.
3. **Agents still never buy the insurance technologies or robotics**, in any of the 33 settings, even with a 12-week disruption in the run. The payback rule looks at last quarter's own costs: risk intelligence and APS pay off only in events that have not happened yet, and robotics' main benefit (faster dispatch, fewer stockouts) lands at the stores, not the DC that pays. This is the clearest difference from the LLM agents, who bought all three in the 2026-09-16 pilots.
4. Agents adopt ML forecasting 13 times a run although it is worth nothing to the network under v2; they see their own holding cost fall.

## Still open

- E5 (LLM agents) has not been rerun on the corrected engine and catalog v2. It is a paid run (about $2 a run with suppliers on rules); needs Kevin's approval.
- Disruption scenarios are still single scheduled events. The evidence table's base rates (a ≥1-month disruption about every 3.7 years per firm) could drive a random-disruption experiment, which is where risk intelligence and APS would get an expected value.
