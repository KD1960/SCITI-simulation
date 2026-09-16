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

## Settings

- Seed 1; 156 weeks; 12 decision rounds; 48 agents; `visibility: partners`; prompt version v1.
- Caps: 1,500 calls, $20. The call cap was reached; the spend cap was not.
- Prices used: $2 / $10 per million tokens (Sonnet 5 list, 2026-09-16).
