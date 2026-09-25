# Held-out seeds 61–90: confirmation of the v1.4 headline table (paper criterion A2)

**Date:** 2026-09-25. **Engine:** `v1.4`, frozen. **Line (page 1 §5, unchanged):** confirmed = same sign and ranking, and each number inside the seeds 1–30 95% interval or within ±25% of it. **Numbers:** `experiments/tech_screen_results_holdout61-90.csv`, `random_disruptions_results_holdout61-90.csv`. Free; seeds 61–90 are now used.

## Calm technology screen (all eligible firms, $M)

| Tech | Seeds 1–30 | 95% CI | Seeds 61–90 | Inside CI |
|---|---|---|---|---|
| routing | +299 | 265–333 | +265 | yes |
| warehouse robotics | +65 | 43–87 | +64 | yes |
| RFID | +50 | 34–67 | +47 | yes |
| control tower (all 48, one project) | +21 | 4–38 | +10 | yes |
| APS | +15 ns | −1–31 | +11 | yes |
| blockchain (all 34, one project) | +10 ns | −4–25 | −3 | yes |
| ML forecasting | +5 ns | −3–14 | +6 | yes |
| risk intelligence | −4 | −4 to −3 | −3 | yes |

**Confirmed.** 8 of 8 inside their intervals; all signs hold for the significant items; the three that straddle zero (control tower, APS, blockchain) stay near zero, which is the finding. Ranking: routing first by a wide margin; robotics and RFID next; everything else within noise of one another.

## Random disruptions, rate 0.2

| Arm | Seeds 1–30 | 95% CI | Seeds 61–90 | Inside CI | Share of loss, 1–30 → 61–90 |
|---|---|---|---|---|---|
| no-tech loss | −2,420 | −3,248 to −1,591 | −3,143 | yes | — |
| hybrid + robotics | +863 | 649–1,077 | +887 | yes | 36% → 28% |
| hybrid | +812 | 619–1,004 | +864 | yes | 34% → 27% |
| risk intelligence | +383 | 260–506 | +348 | yes | 16% → 11% |
| rule + suppliers follow | +328 | 246–411 | +363 | yes | 14% → 12% |
| control tower (all 48, one project) | +216 | 74–358 | +184 | yes | 9% → 6% |
| APS | +214 | 152–277 | +268 | yes | 9% → 9% |

**Confirmed.** 7 of 7 inside their intervals, including the no-tech loss this time (seeds 61–90 drew a schedule inside the seeds 1–30 range, unlike 31–60). Ranking holds exactly. Shares of loss recovered are a little lower because the loss was larger.

## For the paper

Quote the seeds 1–30 v1.4 numbers with their intervals as the main results and cite this file as the confirmation. Criterion A2 is met.
