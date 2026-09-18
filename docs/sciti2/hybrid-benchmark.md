# Hybrid benchmark — payback rule plus an insurance habit

**Date:** 2026-09-18
**Engine and catalog:** branch `insurance-habit` (corrected engine, catalog v2)
**Command:** `.venv/bin/python docs/sciti2/experiments/hybrid_benchmark.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/hybrid_benchmark_results.csv`

> Catalog v2 effect sizes are evidence-based MID values; blockchain, APS, and risk intelligence still rest on weak evidence, and costs are placeholders.

## Why

In all four paid LLM runs, LLM agents bought risk intelligence, APS, and robotics; the payback rule never does (E4: 0 of 33 settings). In the 2026-09-18 disruption run, one such purchase (CM_3, risk intelligence, week 1) was worth about $800M. This benchmark asks whether that edge is a habit that can be written down.

## The habit (`decision.insurance_techs`)

A rules agent also buys a listed solo technology, with no payback needed, when its first-year cost (one-time + 52 weeks of running cost) is at most `insurance_revenue_share` (0.5%) of yearly revenue and the one-time cost fits its budget. Payback picks come first and share the quarterly limit; listed technologies are bought in the order listed. It is off by default.

## Design

Four arms, every agent on the payback rule: plain rule; suppliers follow partners; hybrid (follow + habit for risk intelligence, then APS); hybrid + robotics. Calm, and CM_3 at 20% for 12 weeks from week 30. 30 paired seeds, 3 years, vs a same-seed, same-scenario no-tech run. Profit is `network_profit_with_inventory`, $M; every profit figure below is clear of zero at 95%.

## Results

| Arm | Calm profit | Calm fill | Hit profit | Hit fill | Hit stockout cost | Tech spend | Adoptions |
|---|---|---|---|---|---|---|---|
| Payback rule | +430 | +0.05 pt | +429 | +0.07 pt | −13 | 48 | 62 |
| Rule + suppliers follow | +626 | +0.04 pt | +638 | +0.08 pt | −16 | 68 | 118 |
| **Hybrid** (risk intel, APS) | +632 | +0.09 pt | **+1,221** | **+1.06 pt** | −204 | 86 | 134 |
| Hybrid + robotics | **+674** | +0.19 pt | **+1,272** | +1.17 pt | −225 | 103 | 138 |

95% ranges for hit profit: follow 608–669; hybrid 1,171–1,272; hybrid + robotics 1,227–1,318.

## Findings

1. **The habit is free in calm and worth about +$580M in a long disruption.** Hybrid vs follow: +$6M in calm (inside the noise; $18M more tech spend is paid back by $10M less stockout cost and APS), +$583M in the CM_3 hit. It nearly doubles what the rule recovers and lifts fill by a full point.
2. **It reproduces the LLM agents' edge.** Seed 1, CM_3 hit: LLM agents +$1,175M, fill +1.40 pt; hybrid on the same seed is in the same range, and its 30-seed mean is +$1,221M. With the habit, CM_3 buys risk intelligence in week 1 in all 30 seeds, as the LLM CM_3 did in every paid run.
3. **Order matters.** A first version filled the single week-1 slot alphabetically (APS before risk intelligence) and let payback picks take every later slot; CM_3 got risk intelligence in week 66, after the disruption, and the hybrid recovered only +$963M. Buying in listed order (risk intelligence first) added +$258M. Protection has to be bought before the payback queue, which is what the LLM agents did.
4. **Forecast luck barely matters.** The habit's gain over follow is +$591M on the 13 seeds where the disruption could be seen coming and +$576M on the 17 where it could not. Nearly all the value is the two weeks of outage saved at the hit site, not the early warning. The seed-1 luck flag on the paid run is therefore minor.
5. **Robotics adds about +$45M in both scenarios** and the only on-time gain (+1 pt): it pays for itself through the stores' stockouts, which the DC's own payback never sees.

## What this means

- The LLM agents' advantage in these runs is one describable habit, not broad superiority: "buy cheap protection first, without waiting for a payback." A rule with that habit matches them at no API cost, and still harvests blockchain better.
- What is left for LLM agents to show: reacting to events (none seen so far; the brief has no event feed), choosing *which* protection fits *which* site, and coalition building that a rule does not already do.
- The habit's value depends on catalog v2's risk intelligence effect (2 weeks saved, low-confidence evidence) and on a disruption happening. Expected value needs disruption base rates: at one ≥1-month disruption per 3.7 years per firm (MGI), a CM faces roughly an 80% chance of one in the 3-year horizon, against a cost of $8M network-wide for risk intelligence.
