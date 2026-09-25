# Guesses page 8 — results: Kevin's four rules (v1.5)

**Date:** 2026-09-25. **Engine:** tag `v1.5` (R1 tier-adjacent groups, `decision.allow_network_groups` default off; R2 protection hazard `protection_hazard_floor` 0.05 / `protection_half_life_weeks` 26, briefs carry `shocks`; R3 `network_experience` in briefs, rule agents scale savings by `network_sentiment` 0.5; R4 `max_attempts` 2). 251 tests; no-tech and tech goldens unchanged (forced adoptions are untouched). **Page:** `prereg-8-kevin-rules.md` (signed before the run). **Numbers:** `experiments/*_current.csv` on v1.5; v1.4 kept as `*_v1.4.csv`. Free, seeds 1–30, nothing changed after the results. G2, G5, G6 were measured with a 30-seed E4-default rerun that kept events (share of attempts by outcome, firm-technology pairs reaching two failures, largest group), on v1.5 and, for comparison, on v1.4 in a scratch worktree.

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 forced-arm screen unchanged ±$3M | all eight | identical to v1.4 | **Right** |
| G2 rule agents: 1–3 groups per calm run; control tower adoptions 8–16; largest group ≤ 12 | all three | **7.1** groups (5.4 dyads, 1.2 chains); **17.6** adoptions; largest group mean 4.3, max 6 ✓ | **Wrong** (2 of 3): tier-adjacent groups are smaller and cheaper, so rule agents form *more* of them |
| G3 hybrid − follow at rate 0.2 falls to +$150–350M | inside | +484 → **+211** (hybrid +612, follow +401) | **Right** |
| G4 hybrid − follow in the single CM_3 hit ≤ +$80M | ≤ 80 | +233 → **−14** | **Right**: the habit now waits for a shock, so protection arrives after the hit |
| G5 cancelled + failed share of rule-agent attempts falls ≥ 3 points | ≥ 3 | 33.8% → **27.1%** (−6.7) | **Right** |
| G6 ≤ 5% of firm-technology pairs reach two failures | ≤ 5% | **4.1%** (would have been 6.5% on v1.4) | **Right** |

## What the runs show

1. **Groups got small and many.** With chains limited to a tier and its neighbours, the biggest group in a 30-seed E4 run has 6 members (was 12) and most groups are pairs. Rule agents form 7 groups per run (was 1.5) because small projects carry pair-level odds and cost little to lose. Network profit is unchanged (+273 vs +261 calm).
2. **Protection now follows shocks.** In random disruptions the hybrid still beats the follower rule by +$211M (was +484): it buys after the first shock instead of in quarter 1, so early shocks are uncovered. In the single CM_3 hit the habit is worthless (−$14M): nothing has happened before week 30, so the hazard sits at 5% per quarter and protection arrives too late. **This is the intended behaviour of Kevin's rule, and it makes "buy protection first" a scenario-dependent result rather than a universal one.**
3. **Followers gain** (+328 → +401 at rate 0.2): small tier-adjacent towers are cheap and rarely cancelled.
4. **Learning from the network and the two-attempt cap both bite modestly:** the wasted-attempt share falls 6.7 points; 4% of firm-technology pairs hit the cap.
5. Solo forced arms did not move by a dollar.

## For the paper

v1.5 is the model. The headline calm table is unchanged from v1.4; the decision-policy results (E4, hybrid, followers) are the v1.5 numbers above. The paper's LLM run (page 7) now runs on v1.5.
