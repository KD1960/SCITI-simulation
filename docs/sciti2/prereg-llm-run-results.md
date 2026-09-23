# Pre-registered paid LLM run with implementation risk — results

**Date:** 2026-09-23 (runs started by Kevin 2026-09-22). **Engine:** tag `v1.0` (runs made at `3866ef2`, which changes nothing under `sciti/` since `v1.0`). **Guesses page:** `prereg-llm-run-implementation-risk.md` (signed before the runs). **Runs:** `runs/prereg_llm_calm/llm_s1..5`, `runs/prereg_llm_cm3hit/llm_s1..5` (git-ignored). **Numbers:** `experiments/prereg_llm_results.csv` (one row per paid run, with the same-seed free arms from `prereg_free_arms.csv`).

Sonnet 5 at $2 / $10 per MTok. Ten runs, **$26.65** in all ($2.37–3.05 each; estimate said $7.26 each). About 300 calls per run, **0 fallbacks**, 4–11 malformed replies per ~750 decisions (≤1.5%). **All ten replay exactly.**

## Scorecard (every guess, as promised)

| Guess | Line | Result | Verdict |
|---|---|---|---|
| G1 protection | ≥3 LLM firms attempt risk intel or APS, calm | 7–9 firms in every calm seed (8–9 risk-intel and 6–7 APS attempts per run) | **Right** on the line; the "fewer than before" part was wrong: more firms than in any 2026-09-18 run |
| G2 CM_3 early | CM_3 attempts risk intel before week 30, hit scenario | First CM_3 attempt at week 66 / 79 / 79 / 40 / 53. **Nobody** in any of the ten runs bought risk intel before week 40 (first purchases week 40–66) | **Wrong** 5 of 5 |
| G3 groups | ≥1 group forms, calm; read against the rule band | 6–12 groups per calm run (5–13 in the hit), every run with ≥2 control tower chains; rule with followers 8–14 at every slider level | **Right**; LLM agents sit inside or just below the rule band, so "neither more nor less collaborative than the rule" |
| G4 beats rule | LLM − rule > +$75M in ≥4 of 5 seeds | Calm: +71, +188, +86, +8, +205 (3 of 5). Hit: −55, +192, +39, +89, +302 (3 of 5). Means: calm +293 vs +182; hit +291 vs +178 | **Not met** by the line, but the draft guess ("about the same in calm; ahead in the hit only via G2") was wrong too: LLM agents are ahead on average in both scenarios without an early CM_3 purchase |
| G5 hybrid matches | LLM − hybrid < +$100M, hit | +115, −481, +83, +134, +145: 4 of 5 above +100 | **Wrong.** The free hybrid no longer reproduces the LLM agents (except seed 2, where the hybrid's own risk-intel draw made +$766M) |
| G6 right to? | judgment | Protection: 7–10 firms spend on it; LLM arm still beats the rule in the hit on average. Groups: they form control tower chains like the rule does and blockchain pairs almost never (0 in ten runs) | Buying protection and avoiding blockchain look right; see caveat below |
| G7 health | $3–7, <6% malformed, <10 fallbacks, replay exact | $2.4–3.1, ≤1.5%, 0, exact | **Right** (cheaper than guessed) |

## What the runs show

1. **LLM agents adopt much more than before:** 80–93 adoptions among the 18 LLM firms per run (2026-09-18: 30 in the whole run), across every technology: RFID ~20, control tower 17–31, ML forecasting 12–22, routing 9–12, risk intel 6–12, APS 5–7, robotics 3–4 per run. Between 7% and 57% of adoption attempts fail (mostly group projects, all-or-nothing per chain); the agents retry.
2. **Protection is bought late, not early.** Every risk-intel purchase in ten runs came at week 40 or later; the modal first purchase is week 53–66. In the three 2026-09-18 runs CM_3 bought it in week 1. The two things that changed between those runs and these are the failure odds in the brief and the collaboration line in system prompt v2. This is the main open question; not tuned, not diagnosed.
3. **The hit-scenario edge is no longer one purchase.** Nobody had risk intel when the CM_3 outage began (week 30), yet the LLM arm still gains +$291M on average versus +$178M for the rule and fill +0.08 to +0.25 pt. Where the gain comes from is not yet decomposed.
4. **Seed matters more than arm.** The rule's gain runs from +$52M to +$325M across seeds; the LLM arm from +$185M to +$368M; the hybrid from +$69M to +$766M. Five seeds is enough to see the LLM arm ahead on average, not enough for a tight estimate.
5. **Cost estimate is still 2.5× high** ($7.26 vs $2.4–3.1); chains form early so fewer response calls happen.

Caveats: single engine version; five seeds; the free hybrid arm's value depends on one risk-intel draw per seed; costs are placeholders; the collaboration slider was untested with LLM agents at any level but 0.5.

## What we did not do

No parameter, brief, prompt, or rule was changed after the results were seen. The next idea (why protection moved from week 1 to week 53+, and where the hit edge comes from) gets a new guesses page and a new tag.
