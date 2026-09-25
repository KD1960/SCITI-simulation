# Guesses page 5: LLM agents on v1.3 (cheap seats, two kinds of failure, real costs)

**Status:** SIGNED by Kevin 2026-09-24 ("yes on all 6, signed"). Engine `v1.3`, no code change.

## 0. Why

Every paid LLM run so far (pages 1 and 2) was on `v1.0`/`v1.1`. Since then: cancelled pilots cost 40% (page 3), stores' ML skill fell to 0.03 (page 3), and the four information technologies got evidence-based costs (page 4). Page 4 showed the supplier seat price alone brought control tower chains back for rule agents (0.13 → 4.8 groups per run). The question: **do LLM agents, who see odds and costs in their briefs, respond to the same change, and does it earn them anything?**

## 1. Design

Same as page 1, on `v1.3`, so every number is comparable seed by seed:

| | |
|---|---|
| Engine | `v1.3`; brief and prompt as on page 1 (odds shown, prompt `v2`, collaboration 0.5) |
| Scenarios | calm; CM_3 12-week hit |
| Paid arm | LLM agents, suppliers follow (`configs/prereg_llm_calm.yaml`, `configs/prereg_llm_cm3hit.yaml`, unchanged; Sonnet 5 $2 / $10 per MTok, cap $12 per run) |
| Free same-seed arms | no tech; payback rule with suppliers following at collaboration 0.5; hybrid at 0.5 — rerun on `v1.3` (`experiments/prereg_free_arms.py` with the two extra slider arms dropped) |
| Seeds | 1–5, both scenarios: 10 paid runs, about $25–30 (page 1 cost $26.65) |
| Comparison | page 1's `v1.0` LLM runs on the same seeds (`experiments/prereg_llm_results.csv`) |

## 2. Guesses

**G1. LLM agents form more groups on v1.3.** Page 1: 6–12 groups per run. Guess: 10–18 per run, mostly control tower chains. Counts as yes: the mean over 5 calm seeds is above page 1's mean (9.2) by at least 2.
**G2. Control tower adoptions rise.** Page 1: 17–31 per run among all 48 firms. Guess: 30–45. Counts as yes: mean ≥ 30 in calm.
**G3. The LLM arm still beats the rule with followers on average, in both scenarios.** Page 1: +$293M vs +$182M calm; +$291M vs +$178M hit. Guess: the LLM edge over the rule shrinks (the rule now joins chains too) but stays positive: +$30–100M in calm. Counts as yes: LLM mean − rule mean > 0 in both scenarios.
**G4. Protection is still bought late.** Page 1: no risk intel before week 40. Guess: the same, since the odds are still shown; cheaper subscriptions (risk intel one-time $50–100k, was $250–500k) do not move the timing. Counts as yes: no LLM firm attempts risk intel before week 30 in ≥ 4 of 5 hit seeds.
**G5. Cancelled pilots show up in the log.** Guess: 10–25% of LLM-firm adoption attempts end `cancel`, and 2–8% `fail`. Counts as yes: both inside range (mean over the 10 runs).
**G6. Run health.** $2–3.5 per run, replay exact, 0–2 fallbacks per run.

## 3. Not allowed

No change to the brief, prompt, catalog or rules for this test. If G1 fails (LLM agents do not respond to cheap seats), the follow-on (do they read costs at all?) is a new page.

## 4. Sign-off

- [x] Kevin's guesses: agrees with all six
- [x] Sonnet 5 $2 / $10 per MTok (2026-09-24); `sciti estimate` $7.26 per run; cap $12 per run

Signed (Kevin), date: 2026-09-24

## 5. Scored 2026-09-25

`prereg-5-results.md`: G2, G5 right; G1, G3, G4, G6 wrong. $37.28; all ten replay exactly.
