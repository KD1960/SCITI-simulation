# Learning effects in technology implementation — evidence and model

**Date:** 2026-09-19
**Purpose:** with implementation risk on, a second attempt had the same odds as the first, and a partner's success taught nothing. That looked too harsh, above all for the multi-party technologies (blockchain kept 2% of its value, control tower 13%). Kevin asked for evidence on learning, then a model.
**Sources:** 28 rows in `citations/citations.csv` (topic `learning`, C191–C218), each with how it was read. Many publisher sites blocked fetching; most rows are snippet or abstract only.

> **No study measures "odds of implementation failure on attempt N vs N+1" for enterprise or supply chain technology.** Everything here is by analogy (launch failures, bank failures, surgical outcomes, productivity learning curves, maturity surveys). Directions and structure are well supported; **every magnitude is judgment.**

## 1. What the evidence supports

**Learning from your own experience**
- Organisations do learn from failure, and failure lessons last longer than success lessons (Madsen & Desai 2010, orbital launches; Haunschild & Sullivan 2002, airlines). At the level of individuals it is weaker or even negative (KC, Staats & Gino 2013, cardiac surgeons), and repeat attempters split into improvers and non-improvers (Yin et al. 2019, *Nature*). So: a moderate average benefit from retrying, not a large one.
- Knowledge-work learning curves run about 12–20% improvement per doubling of experience (Boone, Ganeshan & Hicks 2008: progress ratio 0.88). Related experience transfers; unrelated experience barely does (Boh, Slaughter & Espinosa 2007).
- Across the full low-to-high maturity range, failure odds differ by about ×0.3 (Gartner 2025: 45% vs 20% of AI projects still running after 3 years). That bounds how far experience can push.

**Learning from others**
- It is strongly **local**. A one-SD rise in *in-state* peers' failure experience cut a bank's failure hazard to ×0.73; out-of-state peers contributed nothing (Kim & Miner 2007, full text).
- An actively **teaching hub** matters: the same suppliers cut defects 50% for Toyota and 26% for their largest US customer (Dyer & Hatch 2006). Hub *pressure* without support produces shallow, partial implementations (Iacovou et al. 1995; Walmart's RFID "slap-and-ship").
- Own and vicarious learning are complements: spillovers help only firms with related prior investment (Huang et al. 2022).

**No reliable global "the technology matures" trend.** Blockchain projects reaching production went 5% → 14% in a year, RFID pilots converted quickly after 2018, but AI pilots reaching production stayed at 53–54% over three years, and ERP cost and duration show no decline. Better to model learning through the network than as a time trend.

**Depreciation** ranges from ~2% a year where knowledge is codified and staff are stable to 40%+ a year in high-turnover production.

## 2. Recommended ranges (multipliers on the ODDS of failure)

| Item | LOW effect | **MID (used)** | HIGH effect | Confidence |
|---|---|---|---|---|
| Retry after failing at the same technology: 2nd attempt, 3rd+ | 0.90, 0.85 | **0.75, 0.60** | 0.55, 0.40 | Low: pure judgment on size |
| Per technology the firm already runs successfully | 0.95, floor 0.75 | **0.87, floor 0.50** | 0.80, floor 0.33 | Low–medium: floor loosely tied to maturity surveys |
| Per direct partner already running this technology successfully | 0.95, floor 0.80 | **0.88, floor 0.60** | 0.78, floor 0.45 | Low–medium: locality is solid, size is judgment |
| Depreciation of experience | 5%/yr | 15%/yr | 35%/yr | Medium that it exists; low on the rate |

## 3. What was built

`learning_multiplier(s, node, tech, week)` in `sciti/engine/adoption.py` multiplies the odds of failure by three factors (MID values, all in `assumptions`, set to 1.0 to switch off):

1. **Retry:** ×0.75 after one failed attempt at this technology, ×0.60 after two or more (`retry_failure_odds`).
2. **Own experience:** ×0.87 per technology the firm already runs successfully, partial successes included, floor 0.50 (`own_success_failure_odds`, `own_success_floor`).
3. **Partners:** ×0.88 per direct partner already running this technology successfully, floor 0.60 (`partner_success_failure_odds`, `partner_success_floor`). Direct partners only, per Kim & Miner.

Failing projects and projects still in setup teach nothing. The probability that failure gives up is shared between partial and full success in their original proportion, so learning also raises full success. Suppliers keep their ×1.75 small-firm odds. Agents' briefs show odds that include their own learning. Draws are still keyed, so replay is exact.

Worked example (in the tests): routing at a DC, p_fail 0.15. One earlier failure, two live technologies, one live partner: 0.75 × 0.87² × 0.88 = 0.50 → p_fail 0.081.

## 4. Left out, on purpose

- **Depreciation.** The horizon is three years; at 15% a year it would trim the effects modestly.
- **Hub teaching.** A supporting hub (×~0.70) vs a merely coercive one: the model has no notion of support.
- **Related vs unrelated experience.** Every live technology counts the same.
- **Complementarity** of own and partner learning: the two multiply independently.
- **Heterogeneous learners** (some firms never improve).
- **Learning that deepens partial success** (a higher benefit fraction), beyond the shift from partial to full.
- **A global maturity trend.**
- Counter-evidence to the small-firm penalty: McKinsey (2018) reports small firms 2.7× likelier to report transformation success (self-reported; smaller scopes). `small_firm_failure_odds` stays 1.75 but is flagged.
