# Multi-party technologies under implementation risk — diagnosis, evidence, and a proposed fix

**Date:** 2026-09-19
**Status:** proposal for Kevin's ruling. **Nothing in the engine or catalog has been changed.**
**Sources:** 27 rows in `citations/citations.csv` (topics `combination shape` and `deepening`, C219–C245), each with how it was read. Four were read in full; most publisher pages blocked fetching.

## 1. What is actually happening in the model (and a correction)

With implementation risk on, blockchain kept 2% of its value and control tower 13%. I first said this was mainly about the *depth* of partial successes compounding along chains. A split test (free; 30 seeds; calm; every eligible firm attempts in week 1) shows that was only half right:

| Technology | Everything works | Failure only (no partials) | Depth only (nobody fails) | Both |
|---|---|---|---|---|
| Routing (solo) | +444 | +399 | +332 | +299 |
| Control tower | +63 | +29 | +36 | +8 (ns) |
| Blockchain | +321 | **+16** | +180 | +5 (ns) |

Profit with inventory, $M. Noise ±10–35.

- **Blockchain collapses because of failure, not depth.** A pair pays only when the supplier *and* its CM are live. A CM succeeds 35% of the time and a supplier 24%, drawn independently, so both succeed about 8% of the time, and one failed CM strips the benefit from all 7–8 of its suppliers. Depth alone would leave +$180M.
- **Control tower loses about half to each**, and the two multiply.
- What the code does today: a control tower's weight is `0.6 × (share of downstream partners live) × (own fraction)`; partners' fractions do not enter. A blockchain supplier's defect cut is `18% × (own fraction)` if any partner CM is live, else nothing; the CM's fraction does not enter. So depth is **linear in the firm's own fraction**, and partners matter only as live or not.

This points at three separate questions: (A) is the *unit of failure* right for multi-party projects, (B) how should depth translate into benefit, and (C) do shallow implementations deepen?

## 2. What the evidence says

### A. Unit of failure: the measured rates are per project, not per member

The blockchain failure evidence counts **projects** (Gartner: 5–14% of enterprise blockchain *projects* reach production; Capgemini: 3% of *deployments* at scale; Vadgama & Tasca: 271 *projects*). The model applies that rate to every member of a pair independently, so a two-firm project faces the risk twice, and a supplier faces it at ×1.75 odds on top. The consortium cases (TradeLens, we.trade, Marco Polo) failed as **platforms**, taking every member down together: correlated, not independent. The FDA/IFT pilots show the member-level risk is different in kind: a trace breaks where a recipient is simply *not participating* (Bhatt et al. 2013), and per-partner join rates run about 50–70% a year (conflict-minerals response rates, `implementation-failure-evidence.md` §3.3).

### B. How depth and partners combine

**Visibility / control towers: concave in depth, additive in partners. No source supports a multiplicative or weakest-link rule.**
- Gavirneni, Kapuscinski & Tayur (1999): going from no information to *partial* information saves 10–90% of supplier cost (average ~50%); going on to *full* information adds only 1–35%. Cachon & Fisher (2000) and Chen (1998): the deep-sharing increment is worth ~2% of cost. (Numbers read in full in Sahin & Robinson 2002.) So a partial implementation captures roughly 60–80% of full value, not 40%.
- Partial-collaboration simulations (Dominguez, Cannella et al. 2018, 2022): benefit rises with the number of sharing partners, roughly linearly in the share live, with no collapse when one echelon abstains; an echelon's own result depends most on *downstream* collaboration, which is what the model's share rule already uses.
- A data-quality floor exists: shared data is worthless once its error variance reaches the demand variance (Kwak & Gavirneni 2015; Cannella et al. 2018).

**Traceability: two tiers.**
- *Lot-precise, end-to-end tracing is weakest-link.* HHS OIG (2009, read in full): only 5 of 40 products (12.5%) could be traced through every stage when ~41% of facilities kept adequate records, which is what a product rule predicts.
- *But there is a coarse fallback tier.* In the same study 78% of products still got "likely facilities". And delivered quality across a pair is not purely multiplicative: supplier prevention and buyer appraisal are partial substitutes (Baiman, Fischer & Rajan 2000).

**Hub vs spoke.** The hub's benefit follows partner *coverage*, not partner depth: Walmart cut out-of-stocks ~16–26% from suppliers doing the shallowest possible tagging (Hardgrave et al., read in full); Chrysler's EDI savings scaled with the share of suppliers connected. A spoke's own benefit follows its *own* depth (Subramani 2004; Lee, Clark & Tam 1999; slap-and-ship gives the supplier nothing).

### C. Deepening

Performance dips at go-live, then improves over months (McAfee 2002); stabilisation takes 3–9 months and most gains arrive after it (Deloitte 1999; Ross & Vitale). Adoption does not imply routinisation (Zhu, Kraemer & Xu 2006, 1,857 firms), and a large share stay shallow (Panorama 2013: 27% got under a third of the benefit, 11% none). Hub support roughly doubles the rate of improvement, and the gain is hub-specific (Dyer & Hatch 2006). **No source gives a monthly deepening rate or the share that eventually deepens.**

## 3. Proposed fix (three parts, in order of evidence strength)

### Part 1 — One project draw per group (fixes the unit-of-failure mismatch). *Recommended.*

When firms adopt a multi-party technology **as a group** (a blockchain pair, a control tower chain), the group is one project:
- **One keyed draw for the project** decides fail / partial / full for the platform, at the catalog odds (blockchain 0.65 / 0.25 / 0.10). If the project fails, every member fails together (the TradeLens pattern).
- **Each member then draws its own onboarding**, at lower "joiner" odds: fail 0.25, partial 0.45, full 0.30 (the general IT-project priors, BCG 30/44/26; suppliers ×1.75 odds as now). A member's depth is the lesser of the project's and its own.
- A firm adopting alone, or joining partners who are already live, draws as now (with the partner-learning discount).
- Effect on blockchain, by arithmetic: a pair works with probability ~0.35 × 0.75 × 0.6 ≈ 16% instead of 8%, and, more importantly, outcomes are correlated inside a CM's hub, so a working project carries all its suppliers. Expect blockchain to recover from +$5M to somewhere around +$40–80M of its +$321M: still the most fragile technology, as the evidence says it should be.

Confidence: **medium-high on the structure** (the measured rates are per project; consortium failures are correlated), **low on the joiner odds** (borrowed priors).

### Part 2 — Concave depth for information technologies. *Recommended.*

For control tower (and risk intelligence's partial case, which now rounds to nothing), translate depth into effect with **g(d) = d^0.5**: a 0.4-deep implementation delivers 63% of the effect instead of 40%. Partner combination stays additive in the share live, as now. Optionally, treat depth below 0.2 as worthless (data-quality floor); no catalog value is that low today, so it would not bind.
- Effect, by arithmetic: control tower's depth-only case rises from +$36M toward ~+$48M of +$63M; with failure on, from +$8M toward ~+$15–20M.
- Leave routing, RFID, robotics, and APS linear: their effects are physical (cost per unit, capacity), and nothing in the evidence says half an implementation gives more than half.

Confidence: **high on concavity** (Gavirneni et al., Cachon & Fisher, Chen: full-text numbers), **judgment on the exponent 0.5**.

### Part 3 — A degraded tier for traceability. *Optional; smaller effect.*

Let a blockchain adopter keep a share of the defect cut when its partner is *not* live: effect = ω × (pair term) + (1 − ω) × (own-depth term), ω ≈ 0.5–0.6. The pair term is today's rule; the own term is internal process and coarse tracing. Supported by the OIG study's 78% fallback and by Baiman et al.; ω is judgment. With Part 1 in place this matters less, and it weakens the "pair" idea that defines the technology in the model, so I would hold it back.

### Not proposed now — deepening over time

The direction is supported (dip, then improvement; hub support doubles the rate; a quarter to 40% never deepen), but every number would be judgment (2% a month after month 6, 4% with a live hub partner). It also interacts with Part 2. Better to add it only if Parts 1–2 still leave partial successes looking too weak.

## 4. How I would test it

1. Build Parts 1 and 2 behind `assumptions` switches, tests first (hand-computed group-draw and g(d) cases).
2. Rerun the split test above and the random-disruption experiment; report each part's contribution separately.
3. Sensitivity: joiner odds at LOW / MID / HIGH; exponent 0.5 vs 0.7 vs 1.0.
4. Expect: routing still first in calm; blockchain partly recovered but fragile; control tower modestly positive in calm and clearly positive under disruptions; risk intelligence unchanged except for its partial case.

## 5. Results after building Parts 1 and 2 (2026-09-19, branch `group-project-draw`, not merged)

Built as proposed: `assumptions.group_project_draw` (+ `joiner_p_fail` 0.25, `joiner_p_partial` 0.45) and catalog `depth_exponent` (0.5 for control tower and risk intelligence). 221 tests pass. (The stacked version's numbers were not kept; the table below records them.) Profit with inventory, $M, 30 seeds.

| Arm | Every adoption works | Risk + learning (before) | **With Parts 1 and 2** | 95% range |
|---|---|---|---|---|
| Calm: blockchain, all eligible | +321 | +5 (ns) | **+15 (ns)** | 0 to 30 |
| Calm: control tower, all 48 | +63 | +8 (ns) | **+6 (ns)** | −7 to 19 |
| Calm: payback rule, suppliers follow | +626 | +247 | +246 | 210 to 282 |
| Rate 0.2: risk intelligence | +564 | +259 | **+379** | 256 to 502 |
| Rate 0.2: control tower | +465 | +210 | +212 | 94 to 330 |
| Rate 0.2: payback rule, suppliers follow | +890 | +373 | +341 | 228 to 454 |
| Rate 0.2: hybrid (insurance habit) | +1,444 | +625 | **+763** | 553 to 973 |
| Rate 0.2: hybrid + robotics | +1,495 | +693 | **+855** | 640 to 1,069 |

**What happened, honestly**

1. **Part 2 worked as expected.** Risk intelligence recovers +$379M (was +$259M; fill +0.65 pt), because a partial subscriber now saves one week instead of rounding to none. The insurance habit is worth +$422M (was +$252M; positive in 87% of seeds), and the hybrid recovers 32% of the disruption loss (was 26%).
2. **Part 1 did not deliver the recovery I predicted** (I said blockchain would come back to +$40–80M; it came back to +$15M, not distinguishable from zero, and control tower did not move). The reason is in my own design: the joiner draw is stacked *on top of* the project draw, so a group member's chance of failing went **up**, not down: control tower 1 − 0.75 × 0.75 = 44% (was 25–29%; realised 49%); blockchain 1 − 0.35 × 0.75 = 74% (was 69–75%). What Part 1 adds is correlation (a working platform carries its members), and that is worth less than the extra failure costs. A check with a perfect platform shows the joiner layer alone takes blockchain from +$321M to +$79M, since a pair still needs two joiners to succeed and suppliers fail 37% of the time.
3. For control tower the two parts roughly cancel: concave depth helps, stacked failure hurts.

**Options for Part 1 (Kevin's ruling)**

- **(a) Keep it as built.** Defensible reading of the evidence (a platform can fail, and members separately fail to onboard: 30–50% of invited partners do not join in a year), and multi-party technologies stay nearly worthless under implementation risk. That may simply be the honest answer: it is what happened to most real blockchain consortia.
- **(b) Keep the structure, make joining safer:** e.g. joiner odds 0.10 fail / 0.35 partial. Pure judgment; I have no source for a number, and choosing one because it gives a nicer result would be tuning.
- **(c) Switch Part 1 off by default** (`group_project_draw: false`), keep Part 2, and leave the flag for sensitivity runs. Simplest; returns to per-member catalog odds.
- **(d) Replace stacking with substitution:** in a group, the *project* draw replaces the members' failure draws entirely (members only draw depth). Then a control tower member fails 25% of the time, as the catalog says, but all together. This is the cleanest reading of "the measured rates are per project" and removes the double count.

My recommendation is **(d)**: it keeps the evidence-based idea (one project, correlated outcome), removes my double-counting mistake, and needs no invented joiner odds. Members would keep a depth draw (partial vs full) so onboarding quality still varies.

## 6. Option (d) built and run (2026-09-19, Kevin's ruling)

In a group adopting a pair or chain technology, **one project draw at the catalog odds decides fail / partial / full for everyone, and it replaces the members' own failure draws.** Members only draw the depth of their onboarding: shallow with the catalog's odds of partial among survivors (blockchain 0.25/0.35 = 0.71; control tower 0.50/0.75 = 0.67), scaled by the same learning and small-firm multipliers, and a member's depth is the lesser of the project's and its own. The invented joiner odds are gone. Part 2 (concave depth, exponent 0.5, for control tower and risk intelligence) is unchanged. 221 tests pass; tech golden regenerated. Numbers: `experiments/tech_screen_results_current.csv`, `experiments/random_disruptions_results_current.csv`.

Profit with inventory, $M, 30 seeds; every figure in bold is clear of zero at 95%.

| Arm | Every adoption works | Independent draws + learning | Stacked (rejected) | **Option (d)** | 95% range |
|---|---|---|---|---|---|
| Calm: blockchain, all eligible | +321 | +5 (ns) | +15 (ns) | **+47** | 19 to 74 |
| Calm: control tower, all 48 | +63 | +8 (ns) | +6 (ns) | **+33** | 17 to 50 |
| Calm: payback rule, suppliers follow | +626 | +247 | +246 | **+274** | 238 to 311 |
| Rate 0.2: risk intelligence | +564 | +259 | +379 | **+379** | 256 to 502 |
| Rate 0.2: control tower | +465 | +210 | +212 | **+380** | 229 to 531 |
| Rate 0.2: APS | +307 | +210 | +210 | **+210** | 147 to 272 |
| Rate 0.2: payback rule, suppliers follow | +890 | +373 | +341 | **+385** | 253 to 516 |
| Rate 0.2: hybrid (insurance habit) | +1,444 | +625 | +763 | **+818** | 596 to 1,040 |
| Rate 0.2: hybrid + robotics | +1,495 | +693 | +855 | **+905** | 673 to 1,137 |
| Rate 0.4: hybrid | +2,563 | +1,202 | — | **+1,577** | 1,341 to 1,814 |

Solo technologies are untouched (calm: routing +299, robotics +63, RFID +49, APS +10 ns).

**Findings**

1. **Multi-party technologies are now fragile but not worthless.** Blockchain keeps 15% of its everything-works value (+$47M) and control tower 52% in calm (+$33M). Both are now distinguishable from zero.
2. **Control tower is worth as much as risk intelligence under realistic disruptions:** +$380M (82% of its everything-works value; positive in 80% of seeds, median +$275M; fill +0.71 pt), against +$379M for risk intelligence. It costs more ($35M vs $8M), so risk intelligence is still the better value per dollar. Because a control tower is one project, it is also all-or-nothing: a quarter of seeds get nothing from it.
3. **The hybrid recovers 34% of the realistic disruption loss** (+$818M of $2.4B; was 26%); the insurance habit is worth +$433M (positive in 90% of seeds).
4. **What agents experience** (hybrid arm, rate 0.2): blockchain attempts fail 62% of the time (was 75%) and 21 of ~56 attempts per run end up working; control tower 29% fail, ~40 of 55 working, nearly all partial (66%) because a shallow project caps every member.
5. The ranking in calm conditions is unchanged: routing, then robotics, RFID, blockchain, control tower.

**Remaining judgment calls in this design:** the depth exponent 0.5; members' shallow-onboarding odds borrowed from the catalog's partial share; the project draw ignores learning and the small-firm penalty; one forced "all eligible" adoption is treated as a single project (34 firms on one blockchain platform, 48 on one control tower), which is the platform reading of the evidence but makes those arms all-or-nothing per seed.
