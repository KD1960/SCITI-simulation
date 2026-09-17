# E5 First LLM Pilot — Results

**Date:** 2026-09-16
**Engine:** `main` at `381eba0`
**Run:** `mvp_llm_s1_20260916T155215Z`, seed 1, 156 weeks, model `claude-sonnet-5`
**Approved by Kevin:** Sonnet 5, expected ~$7.49, cap $20
**Actual spend:** **$18.61** (1,500 calls — the call cap), wall time 2 h 27 m

> **Illustrative only.** One seed. Technology costs and effects are placeholders. Treat the comparison below as a first look, not a result.

## Headline

**LLM agents buy what the payback rule never buys — including insurance — and on this seed they earned four times as much.**

| Measure (vs. same-seed no-tech) | LLM agents | Payback rule |
|---|---|---|
| Network profit | **+$554M** | +$133M |
| Fill rate | **+0.24 pt** | +0.00 pt |
| Satisfaction | **+0.0023** | −0.0000 |
| Adoptions | 61 | 52 |
| Groups formed | 9 (8 pairs, 1 triad) | 4 |
| Spend on technology | $49.8M | $43.8M |

**What they adopted:** RFID 16, routing 9, blockchain 8, control tower 8, **risk intelligence 7**, **APS 6**, ML forecasting 6, **warehouse robotics 1**.

The payback rule adopted none of the last three in any of the 1,980 runs in E4. The LLM agents also spread their choices across all eight technologies, while the rule concentrates on three.

## Two problems with this run

**1. It cost 2.5× the estimate and hit the call cap.**
- Estimated: 749 calls, $7.49. Actual: 1,500 calls (the cap), $18.61.
- The cost **per call** was close to the estimate: $0.0124 actual against $0.010 assumed (`sciti estimate` uses 3,000 input and 400 output tokens).
- The miss was the **number of calls**: twice the expected count. The estimate allows 1.3 calls per agent per quarter; this run needed 2.6, because every cut-off reply was retried and then handed to the fallback.
- After the call cap, the last 39 decisions fell back to the payback rule.

**2. 38% of decisions were rule fallbacks, because replies were cut off.**
- 419 of 1,110 logged decisions used the fallback.
- Error mix: 122 "reply contains no JSON object", 26 malformed JSON (several "unterminated string" — the signature of a truncated reply).
- **Cause:** the policy sends `max_tokens: 600` (`decision.max_tokens`), and Sonnet 5 thinks by default. Thinking tokens come out of that same 600-token budget and are billed at the output rate. So the model often spent the budget before finishing its JSON. Each truncated reply cost money, was retried (another paid call), and often ended in a fallback.

Neither problem invalidates the run — every decision, error, and fallback is logged — but a cleaner run should be cheaper and use far fewer fallbacks.

## Replication

`sciti replay` reproduced the run **exactly** from the decision log, in 2 seconds with no API calls. This closes success criterion 3 in the design spec (a paid LLM run that replays exactly).

## Suggested fixes before the next paid run

1. **Give replies room:** raise `decision.max_tokens` from 600 to about 2,000, or turn thinking off for this call (Sonnet 5 accepts that). Expect fewer fallbacks and a lower cost per useful reply.
2. **Make the format machine-checked:** ask for the JSON through structured outputs, so a reply can't be malformed.
3. **Fix the estimate:** its token guess is fine; its call-count guess (1.3 per agent per quarter) is not. Either raise it, or report a range that assumes every reply may be retried once.
4. **Then rerun** one seed and compare against this one before spending on more seeds.

## What to ask next

- Do LLM agents recognise the split incentives from E4 (routing and blockchain benefits landing on partners), or is their broader spread just curiosity?
- Do they buy insurance *before* a disruption they can't see coming? This run had no disruption; the E2 stress scenario would test it.
- With fallbacks reduced, does the profit advantage over the rule hold across seeds?

---

## Rerun on the fixed settings (2026-09-16, engine `309f13c`)

Same seed, same model and prices, after the three fixes (reply budget 2,000 tokens; reply shape requested through the API; honest estimate).

| | First run | **Fixed run** |
|---|---|---|
| Cost | $18.61 | **$5.40** |
| Calls | 1,500 (hit the cap) | 706 |
| Wall time | 2 h 27 m | 50 m |
| Replies that failed | 38% fell back to the rule | **1%** (7 of 686) |
| Rule fallbacks | 419 | 2 |

The estimate said $7.49 clean, up to $14.98 with retries. The real figure came in below both.

**Results (seed 1, vs. the same seed with no technology):**

| Measure | LLM (fixed) | LLM (first run) | Payback rule |
|---|---|---|---|
| Network profit | **+$475M** | +$554M | +$133M |
| Satisfaction | **+0.0042** | +0.0023 | −0.0000 |
| Fill rate | +0.13 pt | +0.24 pt | +0.00 pt |
| Store on-time | **+1.14 pt** | — | — |
| Adoptions | 112 | 61 | 52 |
| Groups formed | 14 (5 chains, 8 pairs, 1 triad) | 9 (no chains) | 4 |
| Spent on technology | $92M | $50M | $44M |

**What changed with working replies:** the agents adopted nearly twice as much and, for the first time, formed **chains** — 47 control tower adoptions, against 8 in the first run. They also bought insurance again: risk intelligence 10, APS 6, warehouse robotics 3.

**Where the money came from:** purchases −$395M, scrap −$228M, shipping −$233M, COGS −$182M, holding −$57M, stockouts −$21M, minus $92M of technology cost. Bullwhip fell at every tier (component makers −77). CO2 fell 0.21 Mt (−7%).

**Compared with E3:** the agents built the chain structures that E3 found pay best, which the payback rule never does.

**Replication:** `sciti replay` reproduced this run exactly, again.

**Still open:** 7 replies were still cut off at 2,000 tokens; one seed only; no disruption tested. The natural next steps are a stress-scenario LLM run and a few more seeds.

---

## Under a disruption (2026-09-16, seed 1, engine `309f13c`)

Same seed and settings, plus the E2 stress condition: Mexico (CM_3) at 20% output with +14 days for 12 weeks from week 30. **$5.68, 754 calls, 54 minutes, 4 fallbacks. Replay exact.**

Compared with the same seed and scenario from E2:

| Measure (vs. no technology, same seed and disruption) | LLM agents | Payback rule |
|---|---|---|
| Network profit | **+$1,554M** | +$144M |
| Fill rate | **+2.46 pt** | +0.09 pt |
| Satisfaction | **+0.0163** | +0.0003 |
| Store on-time | **+1.28 pt** | −0.04 pt |
| Stockout cost | **−$402M** | −$15M |
| Adoptions / groups | 112 / 14 | 52 / 4 |
| Spent on technology | $95M | $42M |

For scale: the disruption itself costs about $1.6B and 3.3 fill points with no technology (E2). The LLM agents recover most of it; the payback rule recovers almost none.

### Did they buy insurance before the trouble?

Partly. Insurance adoptions (risk intelligence, APS, warehouse robotics) split 4 before week 30 and 14 after:

| Week | Who | What |
|---|---|---|
| 1 | **CM_3** (the plant that gets hit), CM_4, MFG_US | risk intelligence |
| 27 | DC_Shanghai | risk intelligence |
| 40 onward | CM_1, CM_2, both factories, all four DCs | risk intelligence, APS, robotics |

The agents cannot see the disruption coming, and nothing in the brief hints at it. The four early buys came from persona, not foresight — the reasons given were about caution and resilience:

> "Cautious persona favors low-cost, quick-setup solo tech that improves risk recovery and early warning" — CM_3, quarter 1

That one adoption matters most: CM_3 is the site that gets hit, and its risk intelligence shortens the shock. The rest bought in *after* the disruption started, which in this model still helps against the tail of it.

**The contrast with the payback rule is the finding.** The rule never buys these technologies at all, in any scenario or setting (E2, E4). LLM agents buy them from week 1 for reasons a spreadsheet payback can't express.

**Caveats:** one seed; the persona mix decides how many cautious firms exist; the recovery effect size is a placeholder.

## Settings

- Seed 1; 156 weeks; 12 decision rounds; 48 agents; `visibility: partners`; prompt version v1.
- Caps: 1,500 calls, $20. The call cap was reached; the spend cap was not.
- Prices used: $2 / $10 per million tokens (Sonnet 5 list, 2026-09-16).
