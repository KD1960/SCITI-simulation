# Held-out seeds 31–60: confirmation of the headline table

**Date:** 2026-09-23. **Engine:** `v1.1` (`sciti/` identical to `v1.0` except the two diagnostic switches at their defaults). **Line, written before the run** (guesses page 1 §5): confirmed = same sign and same ranking, and each number inside the 95% interval of the seeds 1–30 result or within ±25% of it. **Numbers:** `experiments/tech_screen_results_holdout31-60.csv`, `experiments/random_disruptions_results_holdout31-60.csv` (scripts unchanged; `SEEDS = 31..60`; rate 0.2 only). Free; run folders deleted as they went.

## Calm technology screen (all eligible firms, profit with inventory, $M)

| Tech | Seeds 1–30 | 95% CI | Seeds 31–60 | Inside CI |
|---|---|---|---|---|
| routing | +299 | 265–332 | **+301** | yes |
| warehouse robotics | +63 | 41–86 | +57 | yes |
| RFID | +49 | 33–66 | +39 | yes |
| blockchain | +47 | 19–74 | +35 | yes |
| control tower | +33 | 17–50 | +39 | yes |
| APS | +10 ns | −6–27 | +10 | yes |
| ML forecasting | −4 ns | −13–5 | −6 | yes |
| risk intelligence | −7 | — | −7 | yes |

**Confirmed.** Every number inside its interval; every sign the same; the ranking holds except that RFID, blockchain and control tower (all +35 to +49) trade places inside their overlapping intervals.

## Random disruptions, rate 0.2 ($M vs same-seed no-tech)

| Arm | Seeds 1–30 | 95% CI | Seeds 31–60 | Inside CI | As a share of the no-tech loss |
|---|---|---|---|---|---|
| no-tech loss vs calm | −2,420 | −3,248 to −1,591 | **−3,678** | no | — |
| hybrid + robotics | +905 | 673–1,137 | +1,157 | no | 37% → 31% |
| hybrid | +818 | 596–1,040 | +1,094 | no | 34% → 30% |
| rule + suppliers follow | +385 | 253–516 | +474 | yes | 16% → 13% |
| control tower | +380 | 229–531 | +539 | no | 16% → 15% |
| risk intelligence | +379 | 256–502 | +419 | yes | 16% → 11% |
| APS | +210 | 147–272 | +315 | no | 9% → 9% |

**Partly confirmed.** Seeds 31–60 drew a harsher disruption schedule (no-tech loss 52% larger, itself outside the seeds 1–30 interval), and every protective arm's gain grew with it, so four of six arms fall outside their intervals in dollars. Signs all hold. The ranking holds at the top and bottom (hybrid arms first, APS last); the middle three (follow, control tower, risk intelligence: +379–385 on seeds 1–30) reorder to control tower > follow > risk intelligence. As a share of the loss recovered, every arm is within 5 points of its seeds 1–30 value.

## What to say from now on

- Calm-condition technology values: confirmed on unseen seeds; quote the seeds 1–30 numbers with their intervals.
- Disruption arms: quote as a share of the no-tech loss (hybrid recovers about a third, single protective technologies 10–16%, APS about 9%), not as dollars, because the dollar figure follows the severity of the disruption draw. The dollar intervals from 30 seeds understate seed-to-seed variation in the disruption schedule itself.
- Nothing was re-tuned. Seeds 31–60 are now used; the next confirmation needs seeds 61+.
