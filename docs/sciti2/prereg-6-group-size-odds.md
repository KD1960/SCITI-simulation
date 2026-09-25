# Guesses page 6: bigger projects fail more often

**Status:** SIGNED by Kevin 2026-09-25 ("1.4 is fine, yes on all 6, build"). Built the same day on branch `page6-group-size` (243 tests). **Arithmetic correction found while building, rule unchanged:** ×1.4 per doubling gives ×4.7 at 48 members (log2(24) = 4.6 doublings), not ×3.9; so control tower at 48 firms is 61% nothing, not 57%, and blockchain 90%. Guesses left as signed.

## 0. Why

Page 5: with $25k supplier seats, LLM firms turn control tower into a **48-firm project**, and the model gives that project the same cancel/fail odds as a two-firm pair (one draw per group at catalog odds). Every seat then cancels together and all 48 retry next quarter (up to 147 attempts per run). The evidence says the opposite of "same odds": project failure rises with size. Standish CHAOS (logged, `implementation-failure-evidence.md` §Firm size): outright failure **7% for small projects to 43% for grand ones**; the consortium cases (TradeLens, we.trade, Marco Polo) died with dozens of members each. No source gives odds *per member*; the shape is judgment, flagged as such.

## 1. Proposed change

One new assumption, `group_size_odds_per_doubling` (draft **1.4**): a group project's odds of getting nothing (cancel + fail, at the catalog's cancel/fail split) are multiplied by `1.4 ^ log2(members / 2)`. A pair is unchanged; 4 members ×1.4; 8 ×2.0; 16 ×2.7; 48 ×3.9. Applied to the project draw only; members' depth draws and the small-firm multiplier stay as they are. `1.0` switches it off.

What it implies (nothing odds → probability): control tower 0.25 → pair 0.25, 8-firm chain 0.40, 48 firms **0.57**; blockchain 0.65 → 4 firms 0.72, 48 firms 0.88. Standish's small→grand span (7% → 43%, odds ×10) is wider than the 48-firm multiplier (×3.9), so 1.4 is on the gentle side.

Briefs show the group's odds on a `propose_group` option and on invitations (today they show solo odds only), so agents can see that a whole-chain proposal is riskier than a pair. The payback rule discounts by the same expected benefit.

## 2. Design (free; the LLM rerun is a later page)

Rerun on seeds 1–30: calm screen, random disruptions (rate 0.2), E4 default point, hybrid benchmark. **Note before running:** the screen's "all eligible firms" arm for control tower (48 firms) and blockchain (34) is *one* forced project, so under this change it gets nothing in ~57% / ~88% of seeds. That arm will collapse; the "one tier" arms (4–8 firms) are the fair read. The docs will say so.

## 3. Guesses

**G1.** Control tower, all 48 firms forced, calm: +$41M → **+$10–25M** (works in ~43% of seeds). Counts as yes: inside range.
**G2.** Control tower, one tier (DCs + stores, 12 firms, odds ×2.5): +$8M → +$2–8M. Counts as yes: inside range.
**G3.** Blockchain, all eligible (34 firms): +$49M → **≤ +$15M**. Counts as yes.
**G4.** Rule agents at the E4 default stop proposing whole-network towers: control tower adoptions per calm run 27 → 5–15, groups 4.8 → 2–4, and network gain within ±$15M of +$278M. Counts as yes: all three.
**G5.** Random disruptions at 0.2: the control tower arm (all 48 forced, one project) falls from +$387M to +$150–250M; risk intel (solo) and APS (solo) unchanged within ±$10M; hybrid share 34–40%. Counts as yes: all.
**G6.** Solo technologies unchanged within ±$3M. Counts as yes.

## 4. Not allowed

No tuning of 1.4 after the results; if Kevin wants another value it is a new page. The forced all-eligible arms are reported as they come.

Kevin's view on the shape/value: ______ · Guesses: ______ · Signed (Kevin), date: ______

## 5. Scored 2026-09-25

`prereg-6-results.md`: G1, G2, G3, G5, G6 right; G4 wrong. Tag `v1.4`.
