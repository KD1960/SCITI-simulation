# Results with implementation risk switched on

**Date:** 2026-09-19
**Engine and catalog:** branch `implementation-failure` at `19519a0` (catalog v2 + implementation risk)
**Commands:** `tech_screen.py` and `random_disruptions.py` in `docs/sciti2/experiments/`
**Full numbers:** `experiments/tech_screen_results_v2_risk.csv`, `experiments/random_disruptions_results_risk.csv`
**Compare with:** `catalog-v2-results.md` and `random-disruptions.md` (same engine with every adoption succeeding)
**Evidence for the odds:** `implementation-failure-evidence.md`; sources in `citations/citations.csv`

> Only blockchain's failure odds are measured. The others are triangulated or borrowed from general IT-project evidence. Treat the sizes below as "what the model says if those odds are right".

## How it works (short)

Each adoption attempt gets one keyed random draw (so runs still replay exactly): **fail** (one-time cost spent, running cost paid until the project is abandoned after `fail_after_weeks`, never switches on, the firm may try again), **partial** (switches on at `partial_fraction` of the catalog effect), or **full**. Suppliers, the small firms, have failure odds ×1.75. Group members draw separately; a failed member counts as not adopting, so it weakens its partners' chain and pair effects. Agents see the odds in their briefs, never the outcome; the payback rule multiplies expected savings by the expected benefit share. `assumptions.implementation_risk: false` turns it all off.

Realised outcomes in the runs match the catalog (hybrid arm, rate 0.2): blockchain 75% fail / 17% partial / 8% full (suppliers pull the failure share above 65%); control tower 33 / 46 / 21; ML forecasting 47 / 34 / 19; risk intelligence 27 / 51 / 22; RFID 23 / 39 / 38; routing 20 / 44 / 36; APS 14 / 47 / 39.

## E1, calm conditions (every eligible firm attempts in week 1; profit with inventory, $M, 30 seeds)

| Technology | Every adoption works | With implementation risk | 95% range | Share kept |
|---|---|---|---|---|
| Routing | +444 | **+299** | 265 to 332 | 67% |
| Warehouse robotics | +124 | **+63** | 41 to 86 | 51% |
| RFID | +83 | **+49** | 33 to 66 | 59% |
| APS | +20 (ns) | +10 (ns) | −6 to 27 | — |
| Control tower | +63 | **+8 (ns)** | −5 to 21 | 13% |
| Blockchain | +321 | **+5 (ns)** | 0 to 11 | 2% |
| ML forecasting | −7 (ns) | −4 (ns) | −13 to 5 | — |
| Risk intelligence | −8 | −7 | | — |

## Random disruptions (rate 0.2 = realistic, 0.4 = stress)

| Arm | Works always, 0.2 | **With risk, 0.2** | 95% range | With risk, 0.4 | With risk, calm |
|---|---|---|---|---|---|
| Risk intelligence, all eligible | +564 | **+259** | 138 to 380 | +466 | −7 |
| APS, all eligible | +307 | **+210** | 147 to 272 | +333 | +10 (ns) |
| Control tower, all 48 | +465 | **+210** | 102 to 317 | +544 | +8 (ns) |
| Payback rule, suppliers follow | +890 | **+358** | 256 to 460 | +490 | +233 |
| Hybrid (insurance habit) | +1,444 | **+611** | 406 to 816 | +1,111 | +227 |
| Hybrid + robotics | +1,495 | **+676** | 469 to 883 | +1,144 | +248 |

Fill-rate gains at rate 0.2 with risk: hybrid +0.81 pt (was +1.53), risk intelligence +0.46, control tower +0.43, APS +0.41.

## Findings

1. **Solo technologies keep 50–70% of their value; multi-party technologies keep almost none.** Routing (67%), RFID (59%), and robotics (51%) land where simple arithmetic says (35% full + ~50% partial at 0.6 ≈ 65%). Blockchain keeps 2% and control tower 13%, far less than my arithmetic guess (a quarter to a third), because **failures compound across partners**: a blockchain pair needs the supplier *and* its CM to succeed (a CM fails 65% of the time and takes all its suppliers' benefit with it; suppliers fail 76%), and a control tower's strength is the *share* of its chain that is live, each link scaled by its own partial fraction. This is the model's version of the TradeLens and CPFR evidence: multi-party value needs critical mass, and independent failures destroy it.
2. **Routing is now alone at the top in calm conditions** (+$299M); nothing else exceeds +$65M.
3. **Protection still pays under realistic disruptions, at about 45% of the earlier size.** Risk intelligence +$259M for ~$7M (positive in 80% of seeds; median +$139M; worst −$33M); the insurance habit is worth +$252M over the rule without it (positive in 87% of seeds); the hybrid recovers 25% of the disruption loss (was 60%).
4. **APS holds up best** (68% kept at rate 0.2): solo, low failure odds (15%), and its partial successes still add capacity when it matters.
5. **Agents attempt much more** (about 153 adoption attempts per run vs 117): failed projects are retried. Retrying is free of learning in the model (the odds never improve), which is probably pessimistic.
6. **In calm conditions the payback rule's gain falls from +$626M to +$233M**: most of it had come from control tower and blockchain groups that now rarely work.

## Cautions and known simplifications

- **Partial risk intelligence is almost a failure in the model.** A partial subscriber saves 0.35 × 2 = 0.7 weeks, and outages are whole weeks, so it rounds to no saving (the extra safety stock during a known disruption still applies). "Subscribed but not embedded in decisions" is a fair reading of partial success, but the rounding is an artifact. Options: keep, or draw the saving probabilistically (0.7 weeks = 70% chance of one week).
- A failed project never delivers anything; in reality robotics fails late, after working for 2–4 years (Kroger). Not modelled.
- The whole one-time cost is sunk on failure (evidence: 30–50% for routing software, ~100% for blockchain pilots).
- Partners' failures are independent. Shared-platform death (TradeLens-style, all members at once) is not modelled; with pair and chain compounding already this severe, it would matter little for blockchain here.
- Forced-adoption arms attempt once, in week 1; they do not retry. Agents do.
- Group invitations do not yet show the odds, and the payback rule does not discount group responses.
- No learning: a firm's second attempt has the same odds as its first, and partners' successes do not raise a firm's odds.

## Update 2026-09-19: with learning switched on

Learning (`learning-evidence.md`; MID values) cuts the odds of failure on a retry, with each technology the firm already runs, and with each direct partner already running the same technology. The random-disruption experiment was rerun on the same schedules; numbers in `experiments/random_disruptions_results_risk_learning.csv`. Forced-adoption arms attempt once in week 1, before anyone has anything to learn from, so they do not change.

| Arm (profit with inventory, $M) | Every adoption works | Risk, no learning | **Risk + learning** | 95% range |
|---|---|---|---|---|
| Calm: payback rule, suppliers follow | +626 | +233 | **+247** | 213 to 280 |
| Calm: hybrid | +632 | +227 | **+244** | 207 to 281 |
| Rate 0.2: payback rule, suppliers follow | +890 | +358 | **+373** | 277 to 470 |
| Rate 0.2: hybrid (insurance habit) | +1,444 | +611 | **+625** | 425 to 825 |
| Rate 0.2: hybrid + robotics | +1,495 | +676 | **+693** | 497 to 889 |
| Rate 0.4: hybrid | +2,563 | +1,111 | **+1,202** | 981 to 1,423 |

Outcomes per attempt in the hybrid arm (rate 0.2), without → with learning: blockchain fail 75% → 69%; control tower 33% → 29%; ML forecasting 47% → 37%; risk intelligence 27% → 23%; routing 20% → 14%; RFID 23% → 21%; APS 14% → 11%. Working blockchain adopters per run 13.0 → 14.9; control tower 37.5 → 39.8.

**Findings**

1. **Learning at the MID values helps a little and changes no conclusion:** +$14–17M at rate 0.2 (about 4%), +$91M at rate 0.4. Failure shares fall by 3–10 points.
> **Correction (same day):** finding 2 below is only half right. A split test (`multi-party-combination-proposal.md` §1) shows blockchain's collapse is driven by *failure* (two independent risky parties must both succeed: +321 → +16 with failure alone, +180 with depth alone); control tower loses about half to each.

2. **The collapse of multi-party value is not mainly about failure, so learning cannot fix it.** Control tower has ~40 of 48 firms live, yet its value stays low, because most live firms are partial successes at 0.4 and a chain's strength is (share of partners live) × (own fraction), with each partner's own visibility scaled the same way. Blockchain needs both ends of a pair live, and both ends are usually partial. The value lost is mostly in the **depth** of implementation, which learning here does not touch (the evidence review suggested it should: Dyer & Hatch measure depth, and "slap-and-ship" is shallow compliance, not failure).
3. The insurance habit is still worth +$252M at rate 0.2 (positive in 77% of seeds).

**What this points to:** if the multi-party result looks too harsh, the lever to examine is how partial successes combine across partners (multiplying fractions along a chain is a strong assumption) and whether experience and hub support deepen partial implementations, not the failure odds.
