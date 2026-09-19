# Random-disruption experiment

**Date:** 2026-09-19
**Engine and catalog:** `main` at `4f6ab09` (corrected engine, catalog v2, suppliers-follow rule, insurance habit)
**Command:** `.venv/bin/python docs/sciti2/experiments/random_disruptions.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/random_disruptions_results.csv`

> The disruption rates are a working rule assembled from BCI, MGI (2020), and Resilinc (evidence-table.md §3), not a single primary source. Catalog v2's risk intelligence effect (two weeks of outage saved, 40% chance of warning) and APS effect rest on weak evidence. Costs are placeholders.

## Why

E2 and the hybrid benchmark used one scheduled disruption. That shows what protection is worth *if* a long disruption hits, not what it is worth on average. Here every run gets a random schedule drawn from real-world base rates.

## Design

- Every supplier, CM, factory, and DC (40 sites) draws Poisson(rate × 3 years) disruptions. Rate = chance per site-year, run at **0.2** and **0.4** (the evidence gives 0.3–0.5 for "any disruption"; 0 is the calm reference).
- Length: 65% 1–3 weeks, 27% 4–12 weeks, 8% 13–26 weeks. Start week uniform. Severity as in E2 (capacity to 20%, +14 days on outgoing shipments; delay only at DCs).
- That gives about 23 disruptions per run at 0.2 and 48 at 0.4; about 1.6 and 4.3 of them are 4+ weeks at a CM, factory, or DC.
- Each seed has one schedule, shared by all arms. 30 paired seeds, 3 years; differences are against the same-seed no-tech run with the same schedule. Profit is `network_profit_with_inventory`, $M.

## What random disruptions cost with no technology

| Rate | Profit vs calm | Fill | Stockout cost |
|---|---|---|---|
| 0.2 | **−2,420** (−3,248 to −1,591) | −3.95 pt | +762 |
| 0.4 | **−5,921** (−6,960 to −4,882) | −9.61 pt | +1,851 |

**Calibration check:** MGI (2020) puts disruption losses at about 45% of one year's EBITDA per decade, i.e. 13.5% of a year's profit over three years. The model's network earns about $13.8B a year, so that benchmark is about −$1.9B over the horizon. Rate 0.2 (−$2.4B) is close to it; rate 0.4 (−$5.9B) is about three times too costly. **Treat 0.2 as the realistic case and 0.4 as a stress case.**

## What each arm recovers

| Arm | Calm | Rate 0.2 | Rate 0.4 | Fill gain at 0.2 | Tech spend |
|---|---|---|---|---|---|
| Risk intelligence, all eligible (10 firms) | −8 | **+724** | +1,839 | +1.23 pt | 8 |
| APS, all eligible (6 firms) | +20 (ns) | +307 | +601 | +0.61 pt | 14 |
| Control tower, all 48 | +63 | +465 | +981 | +0.85 pt | 35 |
| Payback rule, suppliers follow | +626 | +890 | +1,195 | +0.58 pt | 67 |
| **Hybrid** (+ habit: risk intel, APS) | +632 | **+1,556** | +2,952 | **+1.71 pt** | 85 |
| Hybrid + robotics | +674 | +1,631 | +3,005 | +1.85 pt | 103 |

All disrupted-rate figures are clear of zero at 95%. Ranges at rate 0.2: risk intelligence 497–952; hybrid 1,274–1,839; follow 754–1,027.

## Findings

1. **At realistic rates, risk intelligence is the best-value technology in the catalog.** Ten firms spend $8M and recover +$724M (30% of the disruption loss) and 1.2 pt of fill. It pays in 90% of seeds at rate 0.2 (worst seed −$35M, median +$732M) and in every seed at 0.4. Its calm-conditions result (−$8M) was never the right way to judge it.
2. **The insurance habit is worth +$666M on average at rate 0.2** (hybrid vs follow; positive in 93% of seeds, worst seed −$7M, best +$2.1B) and +$1,757M at 0.4, for $18M more technology spend. The hybrid recovers 64% of the disruption loss at rate 0.2.
3. **Control tower earns much more under disruptions than in calm** (+$465M vs +$63M): echelon ordering rebuilds stock in the right places after a hit. APS follows the same pattern (+$307M vs +$20M).
4. **The payback rule alone leaves most of this on the table.** Its gain rises only from +$626M to +$890M, because it buys nothing for protection; the rise comes from control tower and RFID working harder.
5. **Robotics adds ~+$50–75M everywhere**, independent of the disruption rate.
6. **Ranking under realistic disruptions differs from the calm ranking.** Calm (E1, catalog v2): routing +444, blockchain +321, robotics +124, RFID +83, control tower +63. With random disruptions at 0.2, risk intelligence (+724) and control tower (+465) move to the top among single technologies tested here. (Routing, blockchain, RFID, and robotics were not run as forced arms here; their savings do not depend on disruptions, so their calm figures carry over approximately.)

## Cautions

- **Risk intelligence carries a lot of weight on weak evidence.** Its value here is mostly "two weeks saved per outage at the subscriber's own site" (the hybrid benchmark showed early warning adds little). If the true saving is one week, expect roughly half the gain; the sensitivity screen at 0.5× showed +$260M vs +$575M for a single 12-week hit.
- All disruptions have the same severity (20% capacity). Real events vary; milder ones would lower every figure.
- Disruptions are independent across sites. Regional events that hit several sites at once are not modelled and would favour chain-wide protection.
- Suppliers are disrupted but cannot hold risk intelligence in the catalog (eligible roles: CM, MFG, DC).

## What this means for the project

- Judge protection technologies on the random-disruption scenario at rate 0.2, not in calm conditions.
- A decision policy that cannot value protection (the plain payback rule) misses the single largest source of value at realistic disruption rates. LLM agents and the hybrid rule both capture it.
- The next most valuable evidence to collect is the real effect of risk monitoring on outage length at the subscriber's site.
