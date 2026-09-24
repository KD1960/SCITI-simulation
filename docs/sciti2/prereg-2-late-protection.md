# Guesses page 2: why protection moved late, and where the LLM edge comes from

**Status:** SIGNED by Kevin on 2026-09-23 ("yes on all 4 and build/run"). Switches built the same day (231 tests pass, goldens unchanged); the commit holding this page is tagged `v1.1`.
**Rule carried over from page 1:** no change to any parameter, brief, prompt, or rule except the two diagnostic switches listed in §1, which default to the `v1.0` behaviour.

## 0. The two facts to explain

- **F1.** In the three 2026-09-18 runs (engine before implementation risk, prompt v1), CM_3 bought risk intelligence in week 1, citing its cautious persona. In all ten `v1.0` runs, no firm bought risk intelligence before week 40; CM_3 first tried at week 40–79. CM_3's seed-1 persona is unchanged (the persona draw did not move), so the persona is not the reason.
- **F2.** In the CM_3 hit, the LLM arm beats the payback rule by +$113M on average with nobody holding risk intelligence when the outage starts. Its stockout cost is only $14–39M below the rule's in 4 seeds (and $23M above in seed 1), so the edge is not mainly disruption relief.

## 1. What changes (diagnostic switches only)

| Switch | Default (= v1.0) | Test value |
|---|---|---|
| `decision.prompt_version` | `v2` | `v1` (no collaboration sentence; everything else identical) |
| `decision.show_implementation_odds` | `true` | `false` (the brief omits `implementation_odds`; the odds still apply) |

Both must leave every existing golden and replay unchanged at the default. Built and tested before signing; tag `v1.1` on the signed page.

## 2. Design

**Q1 (paid): which change moved protection late?** CM_3 12-week hit scenario (where early protection matters), seeds 1 and 2, suppliers following, collaboration 0.5:
- A: `v1.0` as run (already have; no new spend).
- B: prompt `v1`, odds shown.
- C: prompt `v2`, odds hidden.
Four new runs, about $11 (cap $12 each). "Early" = any LLM firm attempts risk intelligence or APS before week 30.

**Q2 (free): where does the hit edge come from?** Decompose LLM minus rule (same seed, `follow_c0.5`) in the ten existing runs by cost line: stockout, purchases (incl. scrap), shipping, holding, handling, tech, and inventory change. No new runs.

## 3. Guesses

**G1. Hiding the odds brings the early purchase back; the prompt line does not.**
- Draft guess: C buys protection before week 30 in both seeds; B does not.
- Counts as "odds are the cause": C early in 2 of 2 seeds and B late in 2 of 2. "Prompt is the cause": the reverse. Anything else: "unclear" (both or neither; then the cause may be the agents' new habit of spending the one-per-quarter slot on routing/RFID first).
- Kevin's guess (2026-09-23): agrees with the draft guess and the line.

**G2. The early-buying arm gains more in the hit.**
- Draft guess: whichever arm buys before week 30 gains at least +$100M more than arm A on the same seed, if the purchase does not fail.
- Counts as yes: both early runs (if any) beat A by +$100M.
- Kevin's guess (2026-09-23): agrees with the draft guess and the line.

**G3. The hit edge is a calm-type edge.**
- Draft guess: purchases + shipping (RFID, routing, control tower chains) explain more of LLM − rule than stockout does, in at least 4 of 5 hit seeds.
- Counts as yes: |Δ purchases + Δ shipping| > |Δ stockout| in ≥ 4 of 5 seeds.
- Kevin's guess (2026-09-23): agrees with the draft guess and the line.

**G4. The rule's weak spot is under-adoption, not protection.**
- Draft guess: the LLM arm's tech cost is higher in every seed (it is: +$9–30M), and its gain per adoption is lower than the rule's; the edge comes from volume.
- Counts as yes: LLM adoptions among the 18 LLM firms ≥ 1.5 × the rule's adoptions among the same 18 firms in ≥ 4 of 5 seeds.
- Kevin's guess (2026-09-23): agrees with the draft guess and the line.

## 4. Not allowed after seeing results

No tuning of the odds display, the prompt, or the rule for a nicer number. If the answer to G1 is "odds", the follow-on question (should agents see odds? real managers do) is a design decision for Kevin, made on a new page.

## 5. Sign-off

- [x] Switches built, 231 tests pass, goldens unchanged, tag `v1.1`.
- [x] Kevin's guesses filled in (agrees with all four).
- [x] Sonnet 5 $2 / $10 per MTok (2026-09-23); estimate $7.26 per run; cap $12 per run; 4 runs. Configs `configs/prereg2_B_prompt_v1.yaml`, `configs/prereg2_C_odds_hidden.yaml`.

Signed (Kevin), date: 2026-09-23

## 6. Notes added after signing (facts only)

- **2026-09-23, Q2 free decomposition done** (`experiments/prereg2_decomposition.csv`; rule arm `follow_c0.5` rerun on seeds 1–5 to read its cost lines). LLM minus rule, $M, CM_3 hit, seeds 1–5: stockout +23 / −28 / −14 / −39 / −32; purchases −16 / +227 / +180 / +537 / +325; shipping −91 / −128 / −35 / −53 / −230; tech +30 / +26 / +21 / +27 / +9. **G3: line met 5 of 5** (|Δpurchases + Δshipping| > |Δstockout| in every seed), but not in the way the draft guess pictured: purchases *rise* with the LLM agents (more volume moves through the chain), and shipping falls (routing); scrap savings are not the story. Revenue was not in the table and should be read next. **G4: wrong 5 of 5**: the LLM firms adopt only 1.04–1.30× as often as the rule's same 18 firms (80–93 vs 65–83), not 1.5×; the edge is not volume of adoptions.
- Q1 (paid arms B and C) waiting for Kevin to start.
- **2026-09-23, Q1 paid arms done** (Kevin started them; `runs/prereg2_B/llm_s1..2`, `runs/prereg2_C/llm_s1..2`, git-ignored; $10.55 for four runs; 0 fallbacks; all four replay exactly). CM_3 hit, gain vs same-seed no-tech, $M, seeds 1 / 2: **A** (v1.0) +270 / +285; **B** (prompt v1, odds shown) +301 / +382; **C** (prompt v2, odds hidden) **+529 / +822**. First protection purchase: A week 66 / 79; B week 53 / **27** (CM_1 risk intel, MFG_US APS); C **week 1 in both seeds** (3–4 firms, CM_3 itself in seed 2; CM_3 week 14 in seed 1).
  - **G1: "unclear" by the line** (C early 2 of 2, but B early in 1 of 2, by three weeks). The pattern is one-sided all the same: hiding the odds returns the week-1 habit in both seeds; the prompt line only nudges timing.
  - **G2: right for C** (+$259M and +$537M over A, both above +$100M), **not for B seed 2** (+$97M, just under the line). 2 of 3 early runs met it.
  - So: **showing agents the fail/partial odds is what stopped them buying protection early**, and buying it early is worth $260–540M in this scenario. Whether agents *should* see the odds is Kevin's design decision (page 4 rule); real managers see something like them. Nothing changed.
- **Kevin's ruling (2026-09-23): show them.** Default unchanged (`show_implementation_odds: true`); the hidden-odds arm stays available for comparison only.
