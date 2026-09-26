# Guesses page 7 — results: LLM agents on the frozen model v1.5 (paper criterion A4)

**Date:** 2026-09-26 (Kevin started the runs 2026-09-25). **Engine:** `v1.5`, frozen. **Page:** `prereg-7-llm-on-v1.5.md` (guesses signed 2026-09-25, written for v1.4, kept as signed). **Runs:** `runs/prereg7_llm_calm/llm_s1..5`, `runs/prereg7_llm_cm3hit/llm_s1..5` (git-ignored). **Numbers:** `experiments/prereg7_llm_results.csv` (with the same-seed v1.5 free arms, `prereg7_free_arms_v1.5.csv`, and page 5's v1.3 LLM gains).

Ten runs, **$34.30** ($3.08–3.67 each), **0 fallbacks, all ten replay exactly.** This is the LLM run the paper quotes.

## Scorecard

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 no whole-network towers: biggest group 6–20, ≤ 30 distinct control tower adopters | both, ≥ 4 of 5 calm seeds | biggest group **13** in every run ✓; but **40–46 distinct adopters** (several tier-adjacent groups cover the chain) ✗; 0 network proposals were even attempted | **Wrong** on the second line; right in spirit (no 48-firm project) |
| G2 control tower attempts 10–40 per calm run | mean inside | **50.6** (page 5: 47–147) | **Wrong**, just above |
| G3 risk intel in weeks 1–14 in ≥ 4 of 5 hit seeds | ≥ 4 | **4 of 5** (week 1 in four, week 27 in one) | **Right** |
| G4 calm LLM − rule within ±$50M; hit LLM − rule > 0 in ≥ 3 of 5 and on average | both | calm **+$103M** ✗; hit **+$107M**, **5 of 5** seeds ✓ | **Wrong** on calm: the LLM arm beats the rule in *both* scenarios |
| G5 hybrid ≥ LLM in the hit on average | ≥ | hybrid +203 vs LLM **+315** | **Wrong** |
| G6 $2.5–4.5, replay exact, ≤ 2 fallbacks | all | $3.08–3.67, exact, 0 | **Right** |

## What the runs show (the paper's LLM results)

Profit with inventory vs same-seed no-tech, $M, five seeds:

| | Calm: LLM / rule+followers / hybrid | CM_3 hit: LLM / rule+followers / hybrid |
|---|---|---|
| mean | **+315 / +212 / +221** | **+315 / +208 / +203** |
| seeds where LLM > rule | 4 of 5 | 5 of 5 |
| fill rate, LLM vs no-tech | +0.02 to +0.28 pt | +0.05 to +0.30 pt |

1. **On v1.5 the LLM agents beat both free benchmarks by about $100M in both scenarios.** On v1.3 (page 5) the calm edge was zero. What changed is the rule side: Kevin's R2 makes rule and hybrid agents wait for a shock before buying protection, and R3 makes them shy after others' cancellations, while LLM agents (shown the same `shocks` and `network_experience`) still buy risk intelligence in week 1 in 8 of 10 runs and keep adopting through cancellations. Whether that is wisdom or over-confidence is the paper's discussion point: on these seeds it paid, including in calm, where the LLM arm's higher adoption of RFID, routing and adjacent-tier towers earned more than its extra tech spend.
2. **No more 48-firm projects.** No LLM firm proposed a network group (R1 refuses them; none tried). The biggest group is 13 in every run, a tier-adjacent chain. Yet 40–46 firms end up with control tower through several overlapping adjacent groups, and 44–65 attempts per run include cancellations and retries.
3. **Outcomes:** 14–28% of LLM-firm attempts are cancelled pilots and 0–9% deployed failures, close to the catalog odds; the two-attempt cap and the network's visible record did not stop them.
4. **Health:** the cheapest and cleanest paid runs so far.

## For the paper

Quote this table with the seed-by-seed rows in the CSV, and the v1.0 and v1.3 LLM runs (pages 1 and 5) only as the history of the model. Criterion A4 is met.
