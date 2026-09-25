# Guesses page 7: LLM agents on the frozen model (v1.5) — paper criterion A4

**Status:** SIGNED by Kevin 2026-09-25 (with four model rules attached, built first as page 8 → `v1.5`). **Runs on `v1.5`**, the frozen paper model; the guesses below were written for v1.4 and are kept as signed, with one note: on v1.5 agents also see `shocks` and `network_experience`, groups are tier-adjacent, and network proposals are refused (R1), which bears on G1–G3 and is why the run is worth doing.

## 0. Why

`GOALS.md` A4: the paper's LLM-agent claims must rest on more than one seed at the frozen tag. Pages 1 and 5 ran on v1.0 and v1.3. Since v1.3, project odds grow with group size and agents see them on every proposal and invitation (page 6). Page 5 had LLM firms proposing 48-firm towers in nearly every run.

## 1. Design

Identical to pages 1 and 5 (same configs, seeds, scenarios), so all three LLM runs line up seed by seed:

| | |
|---|---|
| Engine | `v1.5`; odds shown; prompt `v2` (updated for R1–R4); collaboration 0.5 |
| Scenarios | calm; CM_3 12-week hit |
| Paid arm | `configs/prereg_llm_calm.yaml`, `configs/prereg_llm_cm3hit.yaml` (unchanged; Sonnet 5 $2 / $10 per MTok; cap $12 per run) |
| Free same-seed arms | no tech; rule + followers (0.5); hybrid (0.5), rerun on v1.5: `experiments/prereg7_free_arms_v1.5.csv` |
| Seeds | 1–5; 10 paid runs, about $35–45 (page 5 was $37.28) |
| Output | `runs/prereg7_llm_calm`, `runs/prereg7_llm_cm3hit` |

## 2. Guesses

**G1. LLM agents stop proposing whole-network towers.** Page 5: 47–48 distinct control tower adopters in 4 of 5 calm runs. Guess: the biggest group per run has 6–20 members; no run has more than 30 distinct control tower adopters. Counts as yes: both, in ≥ 4 of 5 calm seeds.
**G2. Fewer wasted attempts.** Page 5: 47–147 control tower attempts per run. Guess: 10–40. Counts as yes: mean over calm seeds inside range.
**G3. Protection still bought in week 1** (cheap, and the odds shown are solo odds, unchanged since page 5). Counts as yes: a risk-intel attempt in weeks 1–14 in ≥ 4 of 5 hit seeds.
**G4. The LLM arm matches the rule with followers in calm and beats it in the hit.** Guess: calm LLM − rule within ±$50M; hit LLM − rule > 0 in ≥ 3 of 5 seeds and on average. Counts as yes: both.
**G5. The hybrid rule is the stronger free benchmark:** hybrid ≥ LLM in the hit on average (page 5: hybrid +364 vs LLM +407, seed 2 aside). Counts as yes: hybrid mean ≥ LLM mean in the hit.
**G6. Health:** $2.5–4.5 per run, replay exact, ≤ 2 fallbacks per run.

## 3. What the paper will quote from this run

Adoptions by technology and by group size; groups formed and their sizes; the share of attempts cancelled / failed / partial / full; protection timing; profit-with-inventory and fill rate versus the three free arms, seed by seed, with the same-seed v1.0 and v1.3 LLM runs alongside as "what earlier model versions showed" (not as results).

## 4. Not allowed

No change to anything for this test. After it, the model stays frozen for the paper.

Kevin's guesses: as drafted (signed with his 2026-09-25 message) · Signed (Kevin), date: 2026-09-25
