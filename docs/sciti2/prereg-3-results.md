# Guesses page 3 — results

**Date:** 2026-09-24. **Engine:** branch `page3-failure-split` → `main`, tag `v1.2`. **Page:** `prereg-3-two-kinds-of-failure.md` (signed before the run: pilot cost share 0.4, yes on G1–G5). **Numbers:** `experiments/tech_screen_results_current.csv`, `random_disruptions_results_current.csv`, `decision_rules_main_effects_current.csv` (the v1.1 tables are kept as `*_v1.1.csv`). Free; seeds 1–30; nothing changed after the results were seen.

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 blockchain rises to +$60–90M | inside range | +$47M → **+$49M** | **Wrong.** The cancelled-pilot saving is small: the forced all-eligible arm is one project, and its one-time cost ($4.2M for 34 firms) is a sliver of the ±$50M swing in what blockchain delivers when it works |
| G2 solo techs move ≤ $15M | all seven | largest move +$5M (ML forecasting, from the store-skill change) | **Right** |
| G3 rule agents form no more groups | ±0.2 per run | 0.13 calm / 0.30 hit (was ~0.2) | **Right** |
| G4 hybrid recovers 30–37% of the loss | inside band | 889 / 2,420 = **37%** (was 34%) | **Right**, at the edge |
| G5 ML forecasting stays in the noise; stores-only tier ≈ tech cost | −15..+5 and ≤ −3 | all firms +$1M (was −4); one-tier arm −$6M (was −10) | **Right** |

## What moved that no guess covered

- **Rule agents with following suppliers: +$385M → +$476M** at disruption rate 0.2 (calm E4 default +$279M, was +$274M). Suppliers now lose only 40% of their share when a group pilot is cancelled, and the rule counts its costs, so the same invitations are cheaper to accept and cheaper when they fail. The hybrid rose the same way (+818 → +889).
- Everything else is within $2M of the v1.1 table. The failure split changes **cost**, not benefit, and one-time costs are small next to the effects; the headline ranking is untouched.

## Reading

The two kinds of failure are the right model of the evidence (Kevin's reading of Capgemini, Gartner and Vadgama & Tasca), but they matter little for these results, because the catalog's one-time costs are placeholders and small. If real deployment costs are larger (the cost evidence for control tower, APS and ML is still the open data question in STATUS §0), the split will matter more.
