# Guesses page 4 — results

**Date:** 2026-09-24. **Engine:** tag `v1.3` (catalog v3 costs for control tower, APS, ML forecasting, risk intelligence). **Page:** `prereg-4-costs.md` (signed before the run; table unchanged; yes on G1–G6). **Numbers:** `experiments/tech_screen_results_current.csv`, `random_disruptions_results_current.csv`, `decision_rules_main_effects_current.csv`, stress arm `tech_screen_results_costs_x10.csv`; v1.2 tables kept as `*_v1.2.csv`. Free, seeds 1–30, nothing changed after the results.

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 calm ranking unchanged | same order | routing 299, robotics 65, RFID 50, blockchain 49, control tower 41, APS 15, ML 5, risk intel −4 | **Right** |
| G2 control tower +$40–55M | inside | +35 → **+41** | **Right** |
| G3 risk intel calm −$2 to −5M; rate 0.2 within ±$20M | both | −7 → **−4**; 380 → 383 | **Right** |
| G4 hybrid share 34–40% | inside | 915 / 2,420 = **38%** | **Right** |
| G5 at costs ×10: four information techs negative, four physical techs positive | all eight | control tower −190, ML −71, APS −59, risk intel −36 ✓; routing **+240** ✓; but RFID **−56**, robotics **−89**, blockchain −2 ns | **Wrong** on three: only routing survives a tenfold cost |
| G6 rule agents form 0.5–2 groups per run in calm | inside | 0.13 → **4.77** (control tower adoptions 0.5 → 26.6 per run) | **Wrong**, by direction right and size far larger |

## What the runs show

1. **The four cost changes move nothing that matters:** every calm value within $6M of v1.2; the disruption arms within $26M; the hybrid still recovers 38% of the loss. Costs at 0.01–0.1% of revenue cannot rank technologies. The "costs are placeholders" caveat now applies only to routing, RFID, robotics and blockchain, whose placeholders sit inside their evidence ranges.
2. **Cheap supplier seats bring control tower chains back for rule agents.** With a supplier seat at $25k + $300/week (was $150k + $1,500/week), the payback rule accepts chain invitations again: 4.8 groups and 27 control tower adoptions per calm run, from 0.1 and 0.5 on v1.2. Network gain is unchanged (+$278M vs +$279M): the chains cost about what they earn in calm. This reverses the v1.1 finding that "agents who know the odds stop forming groups"; that finding rested on the supplier seat price.
3. **Break-even is not where the sensitivity screen put it.** At ×10, only routing pays (+240); RFID and robotics turn negative at roughly 4–6× their cost, not the 4–200× the 2026-09-17 arithmetic said (that arithmetic predates implementation risk, which cut every gain 40–60%).

## Reading

Page 4 closes the cost caveat for the four technologies where it mattered, and what it changed was not a ranking but a behaviour: how readily rule agents join chains. The next pre-registered question should be whether LLM agents respond the same way (they were not rerun here).
