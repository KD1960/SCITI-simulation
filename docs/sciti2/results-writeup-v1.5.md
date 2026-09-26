# SCITI results write-up on the frozen model v1.5 (paper criterion A5)

**Date:** 2026-09-26. **Model:** tag `v1.5` (commit `17078bc`). Every table below was made with `sciti/` identical to v1.5 (the CSVs are stamped `8601d4a`, `45bb09a`, `17078bc` or `dbbc8e2`; `git diff <stamp> v1.5 -- sciti` is empty for each). Numbers are profit with inventory, $M over 156 weeks, paired against the same-seed no-technology run, 30 seeds (seeds 1–30) unless stated; 95% intervals are t-based. Held-out confirmation: seeds 91–120 (`holdout-seeds-91-120.md`), 15 of 15 headline numbers inside their intervals.

## 1. What the model is (one paragraph for the paper)

A 48-firm agent-based simulation of the Ridge Line supply chain (30 suppliers, 4 component makers, 2 factories, 4 distribution centres, 8 stores), built from the case workbook, run weekly for three years with stochastic demand, lanes and defects. Each quarter every firm may adopt one of eight technologies alone or with partners in a group. Effect sizes are the MID values of a 245-source evidence table; costs for the four technologies where cost matters are evidence-based; the rest are placeholders inside their ranges. Adoptions can be cancelled in pilot (40% of the one-time cost), fail after deployment (full cost), or deliver partly; group projects draw once for all members and their odds of getting nothing rise ×1.4 per doubling of members; groups span a tier and its neighbours; a firm gets two attempts per technology; firms learn from their own retries, their technologies, their partners and the network's visible record; protection habits of rule agents follow shocks. Three decision policies are compared on identical draws: LLM agents (Claude Sonnet 5, one call per firm-quarter, every reply logged and replayed exactly), a transparent payback rule (with suppliers following their partners into groups), and the hybrid rule (payback plus an insurance habit that fires after shocks).

## 2. Calm conditions: each technology forced on every eligible firm (`tech_screen_results_current.csv`)

| Technology | Firms | Profit $M (95% CI) | Fill rate pt | Satisfaction | CM bullwhip | CO2 t |
|---|---|---|---|---|---|---|
| Routing / TMS | 10 | **+299** (265–333) | 0.00 | 0.0000 | 0 | **−148,000** |
| Warehouse robotics | 4 | **+65** (43–87) | **+0.14** | **+0.0038** | 0 | +4,000 |
| Item-level RFID | 18 | **+50** (34–67) | −0.02 | −0.0001 | −1 | −5,600 |
| Control tower (48 firms, one project) | 48 | +21 (4–38) | +0.05 | +0.0003 | **−28** | +1,500 |
| APS | 6 | +15 (−1–31) | +0.10 | +0.0005 | −7 | +5,700 |
| Blockchain (34 firms, one project) | 34 | +10 (−4–25) | 0.00 | 0.0000 | 0 | 0 |
| ML forecasting | 14 | +5 (−3–14) | +0.04 | +0.0002 | **−27** | +2,100 |
| Risk intelligence | 10 | −4 (−4 to −3) | 0.00 | 0.0000 | 0 | 0 |

Reading: routing is the one large calm-conditions gain; robotics is the only service gain; the information technologies cut upstream bullwhip by a quarter but earn little in calm; risk intelligence is pure cost until something goes wrong. The two whole-network arms are single projects that get nothing ~60–90% of the time (v1.4 rule), so their calm values are averages over mostly-failed seeds; one-tier arms (`scope = tier`) are the fairer read for group technologies.

## 3. Random disruptions at a realistic rate (`random_disruptions_results_current.csv`, rate 0.2 per site-year, 30 schedules shared by all arms)

| Arm | Profit $M | Share of the no-tech loss recovered | Fill pt |
|---|---|---|---|
| No-tech loss vs calm | **−2,420** | — | −3.95 |
| Hybrid rule + robotics habit | +614 | 25% | +0.70 |
| Hybrid rule (payback + insurance after shocks) | **+612** | 25% | +0.68 |
| Payback rule, suppliers follow | +401 | 17% | +0.29 |
| Risk intelligence on all 10 eligible firms ($8M) | +383 | 16% | +0.65 |
| Control tower, all 48 forced | +216 | 9% | +0.40 |
| APS, all 6 forced | +214 | 9% | +0.41 |

Reading: protection technologies are worth buying once disruptions are realistic; the hybrid rule recovers a quarter of the loss. Quote disruption results as shares of the loss (the dollar figure follows the severity of the draw; `holdout-seeds-31-60.md`).

## 4. Decision rules: what moves a payback rule's outcome (`decision_rules_main_effects_current.csv`, 2^5 factorial, 30 seeds)

Network gain at the default point: **+$277M calm, +$284M in the CM_3 hit**; 63 adoptions and 6.5 groups per run. Main effects on profit ($M, calm / hit): two adoptions per quarter instead of one **+25 / +43**; a long horizon (104 vs 26 weeks) **+15 / +19**; a stricter 80% chain-acceptance bar −5 / −6; budget share and cost split ≈ 0. Rule agents never adopt risk intelligence, APS or robotics in any setting (the payback rule cannot see their value).

## 5. Hybrid benchmark, single 12-week CM_3 hit (`hybrid_benchmark_results_current.csv`)

| Arm | Calm | CM_3 hit |
|---|---|---|
| Payback rule, all 48 | +273 | +256 |
| Rule + suppliers follow | +293 | +280 |
| Hybrid (risk intel, APS habit after shocks) | +281 | +266 |
| Hybrid + robotics | +281 | +274 |

Reading: with protection habits that wait for a shock (v1.5 R2), the hybrid has no edge in a single mid-horizon hit; its value is in repeated disruptions (§3).

## 6. LLM agents versus the free benchmarks (`prereg7_llm_results.csv`, `prereg7_free_arms_v1.5.csv`; 5 seeds; pre-registered, `prereg-7-llm-on-v1.5.md`)

| Arm | Calm (5 seeds) | CM_3 hit (5 seeds) |
|---|---|---|
| **LLM agents** (18 downstream firms on Sonnet 5, suppliers following) | **+315** (150–409) | **+315** (164–424) |
| Payback rule, suppliers follow | +212 (58–306) | +208 (85–345) |
| Hybrid | +221 (84–310) | +203 (84–303) |
| LLM ahead of the rule | 4 of 5 seeds | 5 of 5 seeds |
| LLM fill rate vs no-tech | +0.02 to +0.28 pt | +0.05 to +0.30 pt |

What the LLM agents did: 76–102 adoptions among the 18 LLM firms per run across every technology; risk intelligence bought in week 1 in 8 of 10 runs (10–14 attempts per run) while rule agents waited for a shock; 10–17 groups per run, the biggest 13 members (a tier-adjacent chain), no whole-network proposals; 14–28% of attempts cancelled in pilot and 0–9% failed after deployment; the two-attempt cap and the network's visible record did not deter them. Cost $34.30 for ten runs; every run replays exactly from its decision log.

Earlier model versions (for the history section only, not results): on v1.0 (page 1) the LLM arm was ahead in calm and behind in the hit on average; on v1.3 (page 5) it matched the rule in calm; the differences trace to the rule side (supplier seat prices, protection hazards) rather than to the agents.

## 7. Structure and stress on v1.5 (`who_with_whom_results_current.csv`, `stress_test_results_current.csv`, 30 seeds)

**Who adopts with whom (E3).** Same technology, six adopters in different structures ($M, calm / CM_3 12-week hit): control tower scattered across tiers **−4 / −4**; three DC–store pairs +3 / +1; upstream chain (suppliers–CM–factory) +3 / **+27**; downstream chain (factory–DCs–stores) +5 / **+47**; all 48 as one project +21 / +46. Blockchain: scattered −1 / −1; three supplier–CM pairs +1 / +1; CM_1 hub +2 / +2; CM_3 hub (the hit site) **+9 / +9**; all 34 +10 / +12. Reading: scattered adopters get nothing; connected chains earn most, and almost all of it in disruptions; a six-firm downstream chain recovers as much as all 48 firms; blockchain value follows the volume covered.

**Stress (E2).** 21 scenarios (demand growth ×0.5 / 1 / 1.5 × no hit, or a 4- or 12-week hit at CM_3, CM_4 or DC_Shanghai) × 4 arms. No-tech cost of a 12-week CM hit at baseline growth: **−$1.7 to −2.0B** (a 4-week hit sits inside the buffers: −$8 to −25M). Risk intelligence on its 10 firms recovers **+$221–254M** of a 12-week CM hit and costs $4M in calm; APS recovers +$221–266M and is worth +$15M in calm at baseline growth, +$72M at ×1.5 growth (capacity binds); control tower (48 firms, one project) +$37–46M in CM hits; payback-rule agents +$260–270M in every scenario at baseline growth (they never buy protection, so the hit does not change what they earn). Reading: risk intelligence is insurance, APS is partial insurance that also pays when demand grows, and the rule's gain is scenario-blind.
## 8. Provenance

Every CSV above carries `git_commit` and `run_date`; run folders were deleted after reading. The eight pre-registered pages (`prereg-*.md`) hold the guesses signed before each run and the scorecards after. Citation log: `citations/citations.csv` (245 rows; the ten headline sources read in full by Kevin, 2026-09-24). Paid LLM spend for the whole project: $135 across 2026-09-18..26.
