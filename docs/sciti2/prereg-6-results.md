# Guesses page 6 — results: bigger projects fail more often

**Date:** 2026-09-25. **Engine:** tag `v1.4` (`assumptions.group_size_odds_per_doubling` 1.4; project odds shown in briefs by group size and on invitations; the payback rule discounts invitations by the project's expected benefit). **Page:** `prereg-6-group-size-odds.md` (signed before the run; arithmetic correction noted there: 48 firms is ×4.7, 61% nothing for control tower). **Numbers:** `experiments/*_current.csv` on v1.4 (v1.3 kept as `*_v1.3.csv`); new `hybrid_benchmark_results_current.csv`. Free, seeds 1–30; nothing changed after the results.

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 control tower, all 48 forced, +$10–25M | inside | +41 → **+21** (CI 4–38) | **Right** |
| G2 control tower, one tier (12 firms), +$2–8M | inside | +8 → **+6** | **Right** |
| G3 blockchain, all 34 forced, ≤ +$15M | ≤ 15 | +49 → **+10** (ns) | **Right** |
| G4 rule agents: control tower adoptions 5–15, groups 2–4, gain within ±$15M of +278 | all three | adoptions **14.1** ✓; groups **1.53** ✗; gain **+261** (−17) ✗ | **Wrong** (2 of 3 lines) |
| G5 random disruptions: forced control tower +$150–250M; risk intel and APS unchanged ±$10M; hybrid share 34–40% | all | **+216**; 383 / 214 unchanged; **34%** | **Right** (share at the edge) |
| G6 solo technologies unchanged within ±$3M | all | identical to v1.3 | **Right** |

## What the runs show

1. **Whole-network projects are now a bad bet, as the evidence says.** The forced 48-firm control tower gets nothing in about 61% of seeds; its calm value halves (+41 → +21) and its disruption value falls +387 → +216. Blockchain on all 34 eligible firms drops to +$10M (ns). Small groups are untouched (one tier +8 → +6).
2. **Rule agents shrink their groups but do not stop.** With project odds on every invitation, E4's default point forms 1.5 groups per calm run (was 4.8 with cheap seats, 0.13 before that) and adopts control tower 14 times (was 27). The gain is $17M lower (+261 vs +278): in calm the chains they no longer form were roughly break-even anyway.
3. **Following suppliers lose value again:** rule + followers at rate 0.2 falls +482 → +328, because followers now join fewer and smaller towers. The hybrid's edge stays (+812, 34% of the loss; +501 vs +268 in the CM_3 hit).
4. **Solo technologies did not move by a dollar**, as the design intends: the multiplier touches only group project draws.

## Reading

v1.4 closes the page 5 problem (48-firm projects at pair odds) with one judgment parameter that is gentler than Standish's span. The obvious next paid test is whether LLM agents, now shown project odds by group size, stop proposing whole-network towers (page 5 had them doing so in nearly every run) and what that does to their edge. That is a page 7 decision for Kevin; nothing else is pending from pages 1–6.
