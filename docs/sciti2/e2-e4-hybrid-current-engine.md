# E2–E4 and the hybrid benchmark on the current engine

**Date:** 2026-09-19
**Engine and catalog:** `main` at `c9821fa`: catalog v2 with implementation risk, learning, group project draws, and concave depth for information technologies all on.
**Commands:** `stress_test.py`, `who_with_whom.py`, `decision_rules.py`, `hybrid_benchmark.py` in `docs/sciti2/experiments/`
**Full numbers:** `experiments/*_current.csv`
**Compare with:** `e2-e4-rerun-v2.md` and `hybrid-benchmark.md` (same catalog effect sizes, every adoption succeeding)

All profit figures are `network_profit_with_inventory`, $M over 3 years, 30 paired seeds, vs a same-seed, same-scenario no-tech run. "Works" = the earlier runs where every adoption succeeds; "Risk" = now. (ns) = 95% range includes zero.

> Only blockchain's failure odds are measured; the rest are triangulated or borrowed (`implementation-failure-evidence.md`). Learning and depth magnitudes are judgment.

## E2 Stress test (growth ×1)

| Scenario | Risk intel: works → risk | APS | Control tower | Payback-rule agents |
|---|---|---|---|---|
| Calm | −8 → −7 | +20 ns → +10 ns | +63 → +33 | +430 → **+234** |
| CM_3, 4 weeks | +19 → +8 ns | +43 → +23 | +60 → +35 | +415 → +229 |
| CM_3, 12 weeks | +591 → **+217** | +366 → **+217** | +103 → +86 | +436 → +223 |
| CM_4, 12 weeks | +582 → +250 | +442 → +261 | +96 → +65 | +415 → +227 |
| DC_Shanghai, 12 weeks | +71 → +18 | +19 ns → +9 ns | +60 → +31 | +430 → +231 |

1. **Protection keeps about 40–60% of its value in a long CM hit.** Risk intelligence falls the most (37% kept in the CM_3 hit): one forced attempt per firm, a 30% chance the hit site's own subscription fails, and a partial subscription saves one week instead of two. **APS now ties it** (+$217M each), because APS fails only 15% of the time.
2. **Control tower holds up best in a long hit** (83% kept in CM_3): concave depth means a shallow chain still re-places stock well.
3. **The payback rule's gain roughly halves everywhere** (+$430M → +$234M calm) and still does not react to disruptions.
4. At growth ×1.5 everything scales up (calm: APS +$67M, control tower +$55M, rule +$297M); at ×0.5 APS is worth nothing in calm (+$1M ns).

## E3 Who with whom (6 adopters; all-firms reference)

| Arm | Calm: works → risk | CM_3 12 weeks: works → risk |
|---|---|---|
| Control tower, scattered | −5 → −5 | −5 → −5 |
| Control tower, 3 DC–store pairs | +10 → +2 ns | +11 ns → 0 ns |
| Control tower, downstream chain | +13 → +6 ns | +81 → **+60** |
| Control tower, upstream chain | +13 → +3 ns | +50 → +36 |
| Control tower, all 48 | +63 → +33 | +103 → +86 |
| Blockchain, scattered | −2 → −1 | −2 → −1 |
| Blockchain, 3 supplier–CM pairs | +14 → 0 ns | +13 → 0 ns |
| Blockchain, CM_1 hub | +30 → +4 | +29 → +3 |
| Blockchain, CM_3 hub | +105 → **+16** | +103 → +16 |
| Blockchain, all eligible | +321 → +47 | +314 → +48 |

1. **The structural findings stand:** scattered adopters get nothing; a six-firm downstream control tower chain earns most of what all 48 firms earn in a disruption (+$60M of +$86M); blockchain value follows volume covered (CM_3 hub > CM_1 hub > pairs).
2. **Small groups are now barely worth it in calm conditions.** A pair or a small chain is one project: a 25–65% chance of getting nothing at all. Six-firm control tower groups are not distinguishable from zero in calm; three blockchain pairs are worth nothing.
3. Blockchain keeps ~15% at every scale, as in E1.

## E4 Decision rules (payback-rule agents, 2^5 factorial)

Network gain now ranges from +$234M to +$271M in calm (was +$365M to +$576M) and +$223M to +$296M in the CM_3 hit (was +$384M to +$603M). The default setting is now the *worst* of the 33 in both conditions.

| Factor (low → high) | Calm: works → risk | CM_3 12 weeks: works → risk | Adoptions (risk) |
|---|---|---|---|
| Payback horizon 13–52 → 52–156 weeks | +97 → **+3 (ns)** | +95 → +10 (ns) | +26 |
| New adoptions per quarter 1 → 2 | +84 → +23 (ns) | +100 → **+45** | +12 |
| Cost split equal → by size | +9 → +2 (ns) | +11 → 0 (ns) | +4 |
| Chain acceptance 40% → 80% | −3 (ns) → −5 (ns) | −9 → −11 | −13 |
| Budget share low → high | 0 → 0 | 0 → 0 | 0 |

Adoptions per run (defaults, calm): RFID 22.1, ML forecasting 13.6, routing 5.0, **blockchain 1.8 (was 9.7), control tower 0.5 (was 14.8)**, APS 0, robotics 0, risk intelligence 0; 43 attempts and **0.2 groups per run (was 4.7)**.

1. **Knowing the odds, rule-based agents all but stop forming groups.** The payback rule now multiplies expected savings by the expected benefit share (blockchain ~0.2, control tower ~0.45), so group technologies rarely clear the payback bar. Group formation falls from 4.7 to 0.2 per run. This is rational at the firm level and is the model's version of the adoption stall seen for blockchain consortia.
2. **Patience no longer pays.** A longer payback horizon still produces 26 more adoption attempts, but they add nothing (+$3M, ns): the marginal projects it lets in are the risky ones. Only pace (two per quarter) still helps, and only in the disruption case.
3. Agents still never buy APS, robotics, or risk intelligence in any setting.

## Hybrid benchmark

| Arm | Calm: works → risk | CM_3 12 weeks: works → risk | Fill in the hit (risk) |
|---|---|---|---|
| Payback rule | +430 → +234 | +429 → +211 | +0.01 pt (ns) |
| Rule + suppliers follow | +626 → +274 | +638 → +265 | +0.06 pt |
| Hybrid (habit: risk intel, APS) | +632 → +269 | +1,221 → **+481** | +0.47 pt |
| Hybrid + robotics | +674 → +297 | +1,272 → **+515** | +0.54 pt |

1. **The insurance habit still pays: +$216M in the CM_3 hit** (hybrid vs follow), free in calm (−$5M, inside the noise). It is 37% of its earlier size, for the same reasons as risk intelligence in E2.
2. **Suppliers following is worth much less** (+$40M calm, was +$196M): it mattered because it let control tower and blockchain chains form, and those now rarely get proposed and often fail.
3. Robotics adds ~+$30M in both conditions (was ~+$45M).

## What holds and what changed

**Holds:** the ranking of technologies; protection is worth buying and the payback rule never buys it; scattered adopters get nothing; chains matter most in disruptions; blockchain follows volume; budget never binds.

**Changed:** every gain is roughly 40–60% of its everything-works size, except group technologies, which agents now mostly avoid; policy levers that worked by admitting more adoptions (patience, following suppliers) lose most of their value, because the marginal adoption is a risky one.

**Open question this raises:** LLM agents proposed and joined groups freely in the 2026-09-18 runs. With failure odds in their briefs, do they still, and are they right to? That is the paid run to do next.
