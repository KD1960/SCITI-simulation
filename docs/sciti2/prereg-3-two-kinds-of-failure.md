# Guesses page 3: two kinds of failure, and ML forecast skill at stores

**Status:** SIGNED by Kevin 2026-09-24 ("40% is fine, yes on all 5, build"). Built, run and scored the same day: `prereg-3-results.md`; tag `v1.2`.

## 0. Why (Kevin's reading of the blockchain sources, 2026-09-24)

Kevin read Capgemini 2018, Gartner/Litan 2021 and Vadgama & Tasca 2021 in full. The 65% "failure" rate mostly counts projects that **never left development or pilot** (87% proof of concept at Capgemini; 86% not in production at Gartner). Only about **10%** are projects that were **fully deployed and then failed** (Vadgama & Tasca: 9.6% identified as failed; the TradeLens / we.trade / Marco Polo deaths). Today the catalog treats every failure as the second kind: full one-time cost sunk, running cost paid until `fail_after_weeks`. That overstates the cost of the common case: a cancelled pilot spends only part of the deployment budget.

Kevin also read Jain, Girotra & Netessine 2022, Norrman & Jansson 2004 and Banker 2016 and **agrees with the risk-intelligence effect as modelled** (min(2 weeks, 25% of the outage); 30% warning). No change there.

## 1. Proposed change (catalog fields; engine reads them)

Split `p_fail` into two draws with different costs:

| Field | Meaning | Cost to the firm | Blockchain draft | Others |
|---|---|---|---|---|
| `p_cancel` | stuck in development/pilot, then cancelled | `pilot_cost_share` × one-time cost (draft 0.4), no running cost, retry allowed after `cancel_after_weeks` (draft 26) | **0.55** | ML forecasting 0.35 (pilots that never reach production), others: most of today's `p_fail` |
| `p_fail` | deployed, then failed | as today: full one-time cost, running cost until `fail_after_weeks` | **0.10** | the deployed-then-failed share of today's value; where no source splits it, `p_fail` = 0.25 × today's, `p_cancel` = 0.75 × today's (judgment, flagged) |

`p_partial`, `partial_fraction`, learning, the group project draw and the small-firm multiplier all stay as they are. A cancelled group project cancels for every member (one draw, as now). Total probability of getting nothing is unchanged (`p_cancel + p_fail` = today's `p_fail`), so this changes **cost**, not **benefit**.

Evidence needed before signing: a per-technology split for at least ML forecasting and APS; otherwise the 25/75 rule is used and marked `assumption: true` in the catalog. Every source goes in the citation log.

## 1b. Second change (Kevin's ruling on M5, 2026-09-24)

Makridakis, Spiliotis & Assimakopoulos (2022), p. 1351: the top methods beat exponential smoothing by ~40% at the total level, ~23% at the middle levels, and only ~3% at product, product-state and product-store level (level 12, "the vast majority of the series"). The catalog's `forecast_skill` 0.3 at DCs and factories is supported; **0.1 at stores is three times the evidence and drops to 0.03.** Catalog `by_role` Retail: 0.1 → 0.03; evidence note updated; nothing else in the ML entry changes.

## 2. Design

Free. Rerun the calm technology screen and the random-disruption arms (rate 0.2) on seeds 1–30 and compare with `*_current.csv`; the LLM arm is not rerun (its briefs would show two odds; that is a page-4 question).

## 3. Guesses

**G1.** Blockchain's calm value for all eligible firms rises from +$47M to between +$60M and +$90M (cheaper cancellations; benefit unchanged). Counts as yes: inside that range.
**G2.** No solo technology moves by more than $15M (their cancelled share is small and their one-time costs are small relative to gains). Counts as yes: all seven within ±$15M of `_current`.
**G3.** The rule agents, who discount by `expected_benefit`, form no more groups than before (0.2 per run, plain rule), because the odds of getting nothing are unchanged. Counts as yes: groups per run within ±0.2.
**G4.** The hybrid's share of the random-disruption loss recovered stays 30–37%. Counts as yes: inside that band.
**G5.** ML forecasting for all eligible firms stays within the noise: calm value between −$15M and +$5M (was −4 ns), and the stores-only tier falls to about the tech cost (≤ −$3M). Counts as yes: both.

## 4. Not allowed

No change to `p_partial`, the effect sizes (including the new 0.03), or the pilot cost share after seeing results.

Kevin's guesses: agrees with all five · Signed (Kevin), date: 2026-09-24
