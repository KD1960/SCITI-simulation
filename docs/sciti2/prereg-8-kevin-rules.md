# Guesses page 8: four rules from Kevin (unfreeze v1.4 → v1.5)

**Status:** SIGNED by Kevin 2026-09-25 ("design is fine, yes on all 6, build"). Built, run and scored the same day: `prereg-8-results.md`; tag `v1.5`.

## 0. Kevin's requests (2026-09-25, verbatim in spirit)

1. "Whole network control tower" should be a switch, default off. Co-adoption is one tier at a time: a firm at tier T can only be joined by firms at T−1 or T+1.
2. Everyone buying protection in week 1 is not desirable. Protection purchase probability should fall over time, jump after a shock, then fall again as the shock recedes.
3. Adoption failures by others in the network with technology Z should lower other firms' chance of adopting Z later, and successes raise it.
4. A firm gets two chances at any technology; after two failures it cannot try again.

## 1. Design of each change

**R1. Tier-adjacent groups; network groups off by default.** Tiers in order: Supplier, CM, MFG, DC, Retail. `group_members` keeps only firms whose tier is within one of the proposer's (so a CM's chain = its suppliers, itself, the factories). `partners: ["network"]` is refused with `coalition_failed` reason `network groups off` unless `decision.allow_network_groups: true` (default false; the switch Kevin asked for). The system prompt says so. Forced adoptions (experiments) are unaffected, so the screen's "all eligible" arms still run.

**R2. Protection hazard.** Every brief gets `weeks_since_last_disruption` (in the firm's upstream/downstream reach; `null` if none yet) and `recent_disruptions` (site, start week, weeks, still active). For rule and hybrid agents the insurance habit fires only when a keyed draw is below `h(w) = h_floor + (1 − h_floor) · 0.5^(w / half_life)`, with `assumptions.protection_hazard_floor` 0.05 per quarter and `protection_half_life_weeks` 26; before any shock `h = h_floor`. LLM agents are told the same facts and decide; whether they behave this way is a guess (G3), not a rule. (Kevin's choice 2026-09-25: brief, not an override.)

**R3. Learning from the network.** Every brief lists `network_experience[tech]` = counts of full / partial / cancelled / failed outcomes among all firms in the last 52 weeks (firms already learn from *partners'* live technologies through the failure odds; this adds what everyone can see). Rule agents scale a technology's expected saving by `1 + assumptions.network_sentiment × (good − bad) / (good + bad + 1)`, good = full + partial, bad = cancelled + failed, `network_sentiment` 0.5 (so an all-bad record halves the saving, an all-good one raises it by half). LLM agents see the counts.

**R4. Two attempts.** After two cancelled or failed attempts at a technology, the engine refuses a third (`rejected`, reason `two failures`), the technology leaves the firm's eligible list, and group invitations skip it. `assumptions.max_attempts` 2.

All four are switchable: `allow_network_groups`, `protection_hazard_floor` 1.0 (always fires), `network_sentiment` 0, `max_attempts` 0 (unlimited). Goldens: the no-tech golden must not change; the tech golden will (R1 changes forced-free group formation only via agents, so check).

## 2. Design of the test (free; seeds 1–30)

Calm screen (forced arms; expect no change except through R4 retries), random disruptions (rate 0.2), E4 default point, hybrid benchmark. Then the page-7 paid run on v1.5.

## 3. Guesses

**G1.** Forced-arm screen values unchanged within ±$3M (R1–R3 do not touch forced adoptions; R4 only stops third attempts, which forced arms never make). Counts as yes: all eight.
**G2.** Rule agents at the E4 default: groups per calm run 1.5 → 1–3 (chains are smaller but cheaper to fail), control tower adoptions 14 → 8–16, largest group ≤ 12 members. Counts as yes: all three.
**G3.** Hybrid at rate 0.2: the habit now fires late (after the first shock) instead of quarter 1, so its edge over the follower rule shrinks: hybrid − follow falls from +$484M to +$150–350M. Counts as yes: inside range.
**G4.** Hybrid in the single CM_3 hit (hybrid benchmark): the habit fires *after* week 30, so protection arrives too late for the hit: hybrid − follow falls from +$233M to ≤ +$80M. Counts as yes.
**G5.** R3 lowers control tower and blockchain attempts in E4 after early cancellations: cancelled + failed share of rule-agent attempts falls by ≥ 3 points versus v1.4. Counts as yes.
**G6.** R4 binds rarely: ≤ 5% of rule-agent firm-technology pairs reach two failures in a 156-week run. Counts as yes.

## 4. Not allowed

No change to the four parameters (0.05, 26, 0.5, 2) after the results; a different value is a new page.

Kevin's edits to §1: none · Guesses: agrees with all six · Signed (Kevin), date: 2026-09-25
