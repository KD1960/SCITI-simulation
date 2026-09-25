# Guesses page 5 — results: LLM agents on v1.3

**Date:** 2026-09-25 (Kevin started the runs 2026-09-24). **Engine:** `v1.3`, unchanged. **Page:** `prereg-5-llm-on-v1.3.md` (signed before the runs; yes on G1–G6). **Runs:** `runs/prereg5_llm_calm/llm_s1..5`, `runs/prereg5_llm_cm3hit/llm_s1..5` (git-ignored). **Numbers:** `experiments/prereg5_llm_results.csv` (with the same-seed v1.3 free arms from `prereg5_free_arms_v1.3.csv` and page 1's v1.0 LLM gains).

Ten runs, **$37.28** ($3.44–4.40 each), ~300–330 calls per run, **0 fallbacks, all ten replay exactly.**

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 more groups (10–18 per calm run) | mean ≥ 9.2 + 2 | 5–11, mean **8.0** (page 1: 9.2) | **Wrong.** Not more groups; bigger ones (see 1 below) |
| G2 control tower adoptions ≥ 30 per calm run | mean ≥ 30 | 47–147, mean 100, **all 48 firms** in 4 of 5 seeds | **Right**, far beyond the guess; two thirds are retries after a cancelled network-wide project |
| G3 LLM beats the rule on average in both scenarios | both > 0 | calm **−$8M** (LLM +240 vs rule +248); hit **+$166M** (+407 vs +240, but +$636M of that gap is seed 2) | **Wrong** in calm |
| G4 protection still bought late | no risk intel before week 30 in ≥ 4 of 5 hit seeds | risk intel bought **in week 1** in 4 of 5 hit seeds and 4 of 5 calm seeds (CM_1, CM_2, CM_4, MFG_US, sometimes CM_3) | **Wrong** |
| G5 cancels 10–25%, fails 2–8% of LLM-firm attempts | both | **16.2%** and **4.8%** | **Right** |
| G6 $2–3.5 per run, replay exact, ≤ 2 fallbacks | all | $3.44–4.40 (6 of 10 above $3.5); exact; 0 | **Wrong** on cost only |

## What the runs show

1. **Cheap seats turned control tower into a network-wide project.** With a supplier seat at $25k, LLM firms propose the whole chain, all 30 following suppliers accept, and every one of the 48 firms adopts (47–48 distinct firms in every run). Because a group is one project draw, a cancelled proposal cancels for all 48 at once, and they try again next quarter: seed 1 calm shows 144 attempts (96 cancelled, 35 partial, 13 full). Group *count* fell (8 vs 9) because one network group replaces several chains.
2. **Cheap protection is bought in week 1 again.** On page 2 the odds display pushed the first risk-intel purchase to week 40+. On v1.3 the one-time cost fell from $250–500k to $50–100k, and with the odds still shown, CM_1/CM_2/CM_4 and MFG_US buy it in week 1 in 8 of 10 runs. So the page 2 finding was about price *and* odds: agents who see a 30% failure chance skip a $500k purchase but not a $50k one. Nobody is re-tuning anything; this is the behaviour of informed agents at evidence-based prices.
3. **The LLM edge over the rule is gone in calm and seed-driven in the hit.** Calm: LLM +$240M vs rule +$248M (v1.0: +293 vs +182). Hit: +$407M vs +$240M, but seed 2 alone is +876 vs +240 (its risk-intel draw succeeded; the hybrid got +855 on that seed); the other four seeds average +289 vs +240. The rule with followers on v1.3 joins chains and (as hybrid) buys protection; what the LLM agents did "for free" on v1.0, the rule now does too.
4. **All-or-nothing network projects are costly:** 93–99 cancelled seats per run at 40% of a seat's cost, plus the quarter lost each time. This is the model's group-project-draw assumption (one draw per group) at its extreme: a 48-firm consortium is treated like a 2-firm pair.

## Reading

Two model features now interact in a way nobody guessed: cheap supplier seats plus one-draw-per-group make whole-network control tower projects both irresistible and fragile. Whether a 48-member project should have the same cancellation odds as a pair is the open design question (real consortia fail *more* often with more members, per the TradeLens cases). That is the next page, not a tweak.

## What we did not do

No parameter, brief, prompt or rule changed after seeing these results.
