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
