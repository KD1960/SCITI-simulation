# E5 — LLM agents on the corrected engine and catalog v2

**Date:** 2026-09-18
**Engine and catalog:** `main` at `9b99ed9` (all 2026-09-17/18 fixes, catalog v2)
**Config:** `configs/mvp_llm.yaml` with Sonnet 5 prices set ($2 in / $10 out per MTok), `rules_roles: [Supplier]`, seed 1, 156 weeks, calm
**Run folder:** `runs/mvp_llm_s1_20260918T192217Z` (git-ignored). An earlier folder, `runs/mvp_llm_s1_20260918T191706Z`, is a 2-second run where the API rejected the key and every decision fell back to rules; ignore it.
**Approved by Kevin:** yes (estimate $2.81 expected, $8.64 maximum)

> One seed. Catalog v2 effect sizes are evidence-based MID values, but blockchain, APS, and risk intelligence still rest on weak evidence, and costs are placeholders. Read this as a behaviour check, not an estimate.

## Run health

| | |
|---|---|
| Replay | **exact** (`sciti replay`) |
| Invariant checks | passed |
| LLM calls | 459 (18 downstream firms; the 30 suppliers made 660 rule decisions and no calls) |
| Cost | **$7.14** (estimate said $2.81) |
| Time | 62 minutes |
| Malformed replies | 27 of 459 (6%): 22 were cut off at `max_tokens` 2000 |
| Fallbacks to rules | 5 |

**Why it cost 2.5× the estimate:** each call used 3,965 tokens in and 762 out (the estimate assumed 3,000 and 400), and each LLM agent made 2.1 calls per quarter (assumed 1.3) because agents answered many group proposals. `sciti estimate` now uses the measured figures; on this config it says $7.26.

## Result (seed 1, vs the same-seed no-tech run)

| | LLM agents (suppliers on rules) | Payback rule, all 48 agents |
|---|---|---|
| Profit with inventory | **+$326M** | **+$363M** |
| Cash profit | +$317M | +$388M |
| Fill rate | +0.02 pt | +0.06 pt |
| Satisfaction index | +0.0006 | +0.0003 |
| Retail on-time | +0.19 pt | −0.03 pt |
| Adoptions | 30 | 59 |
| Groups formed | 2 (both blockchain pairs) | 5 (4 blockchain pairs, 1 control tower chain) |
| Technology spend | $21M | $47M |
| Shipping cost | −$305M | −$281M |
| Purchases / scrap | −$46M / −$49M | −$291M / −$146M |
| CM bullwhip | −14 | −55 |
| CO2 | −2.4% | −2.4% |

What the LLM agents bought: RFID 10, risk intelligence 6, routing 5, blockchain 4, ML forecasting 3, APS 1, warehouse robotics 1, **control tower 0**.
What the rule bought: RFID 18, control tower 14, ML forecasting 13, blockchain 8, routing 6; never risk intelligence, APS, or robotics.

## Findings

1. **Putting suppliers on the payback rule blocks chain coalitions.** LLM agents proposed control tower groups all run long: 171 control tower proposals failed for lack of acceptances, and not one formed. A chain proposal invites every connected firm, 30 of them suppliers, and it needs 60% to accept. The rule-driven suppliers accepted 133 of 4,440 control tower invitations (3%); LLM agents accepted 268 of 1,643 (16%). In the 2026-09-16 all-LLM pilot, 47 firms adopted control tower in 5 chains. So `rules_roles: [Supplier]` is not neutral: it saves about 60% of the calls but removes the LLM agents' main coordinated move. Most of the profit gap to the old pilot (+$475M then) is this, plus catalog v2's smaller effects.
2. **LLM agents still buy insurance, and the rule still never does.** Six firms bought risk intelligence (CM_2, CM_3, CM_4 in week 1; DC_Sofia, MFG_US, CM_1 later), one bought APS, one bought robotics, in a calm run where none of these pays back. This matches both 2026-09-16 pilots and E4 (0 of 33 rule settings).
3. **With control tower blocked, the LLM agents did a little worse than the rule on this seed** (+$326M vs +$363M): fewer adoptions, less blockchain (4 vs 8), so less scrap saved, partly offset by lower tech spend. They captured slightly more of routing's saving (−$305M vs −$281M shipping).
4. **Agents turn down duplicate invitations sensibly.** Typical reason: "Already accepting the cheaper DC_Shanghai control tower proposal; avoid duplicate adoption." Many overlapping chain proposals per quarter split the acceptances, which also keeps each below the 60% bar.
5. Replies still hit the 2,000-token limit 22 times; each costs a retry.

## Update 2026-09-18: Kevin chose option (c)

A `rules_roles` agent now also accepts a group invitation when its first-year cost (one-time share + 52 weeks of running cost) is at most `decision.follow_revenue_share` of its yearly revenue (first set to 1%) and the share fits its budget. Free check (payback rule for everyone, suppliers as followers, seed 1): suppliers accepted all 570 invitations (545 as "small cost; going along with partners"), 2 control tower chains and 4 blockchain chains formed, all 30 suppliers joined both, and the network gain rose from +$363M to +$632M. Kevin then lowered the default to 0.5%; the free check gives the identical result, because supplier invitations cost only 0.05–0.35% of yearly revenue (median 0.14%). Suppliers start declining only below about 0.1–0.3%. Not yet tried with LLM agents (a paid run).

## Second run, 2026-09-18: suppliers follow partners (`follow_revenue_share` 0.5%)

**Run folder:** `runs/mvp_llm_s1_20260918T204012Z` (git-ignored), engine `b61b965`, same seed, config, and model; the only change is the follower rule. Approved by Kevin (estimate $7.26).

| Run health | |
|---|---|
| Replay | **exact** |
| Invariant checks | passed |
| LLM calls | 319 |
| Cost | **$3.07** (2,611 tokens in, 439 out per call; 30 minutes) |
| Malformed replies | 9 of 319 (3 truncated); 1 fallback |

It cost less than half the first run because chains formed early: once firms hold control tower, there are far fewer proposals to answer each quarter (the first run's agents re-proposed failed chains all run long). The estimate ($7.26) was calibrated on that first run, so it is now on the high side; budget between the two.

### Five arms, seed 1, vs the same-seed no-tech run

| | Payback rule | Rule + suppliers follow | LLM, suppliers on plain rules | **LLM + suppliers follow** |
|---|---|---|---|---|
| Profit with inventory | +$363M | +$632M | +$326M | **+$354M** |
| Fill rate | +0.06 pt | +0.06 pt | +0.02 pt | **+0.14 pt** |
| Satisfaction | +0.0003 | +0.0011 | +0.0006 | **+0.0016** |
| Retail on-time | −0.03 pt | −0.03 pt | +0.19 pt | **+0.27 pt** |
| Adoptions | 59 | 116 | 30 | 109 |
| Groups | 5 | 8 | 2 | **12** |
| Control tower adopters | 14 | 44 | 0 | **47** |
| CM bullwhip | −55 | −63 | −14 | −60 |
| Technology spend | $47M | $67M | $21M | $82M |
| Scrap saved | $146M | $547M | $49M | $119M |
| Stockout cost | −$12M | −$12M | −$3M | **−$28M** |

LLM firms' adoptions (18 downstream firms): RFID 17, control tower 17, ML forecasting 13, routing 9, risk intelligence 7, APS 6, blockchain 4, robotics 2. Suppliers (following): control tower 30, blockchain 4.

### Findings

1. **The fix works: control tower chains form again.** A 28-firm chain formed in week 14 and a 17-firm chain in week 27; 47 firms hold control tower, the same count as the 2026-09-16 all-LLM pilot, at 40% of the calls. CM bullwhip falls by 60 (it fell 14 without the fix).
2. **LLM agents give the best service of the five arms:** fill +0.14 pt, on-time +0.27 pt, satisfaction +0.0016, stockout cost −$28M. They buy what protects service (risk intelligence 7, APS 6, robotics 2), which the rule never buys.
3. **But they leave the biggest prize on the table: blockchain.** The rule with following suppliers earns +$632M, mostly from $547M of scrap saved by four blockchain chains covering all 30 suppliers. The LLM CMs formed only four blockchain pairs ($119M scrap saved). Their blockchain proposals mostly failed as "no eligible partners" (51) or on the one-new-technology-per-quarter quota (21): they spent their quarterly slot on other technologies, and proposed to partners who already held it or were not eligible. This is the gap to study next, not a verdict on LLM agents: the brief shows each technology's effect but not the money it would save this firm.
4. **Insurance buying is now seen in all four paid runs** (2026-09-16 ×2, 2026-09-18 ×2): CM_2, CM_3, and CM_4 bought risk intelligence in week 1 in both of today's runs.
5. LLM agents spend the most on technology ($82M) for a gain similar to the plain rule's (+$354M vs +$363M): in calm conditions the insurance technologies are a cost. The disruption arm is where that spend should pay; it has not been rerun on catalog v2.

## What to decide next

- **Chain coalitions with suppliers on rules.** Options: (a) suppliers on rules only for their own proposals, LLM for responses (about +30 × response calls); (b) count the 60% acceptance bar over LLM-role invitees only; (c) a supplier accepts a group invitation when its cost share is below a threshold; (d) leave it and treat control tower as out of reach in cheap runs. Needs Kevin's ruling.
- Whether to raise `max_tokens` again or ask for shorter reasons in the prompt.
- More seeds and a disruption arm before any claim about LLM vs rule profit (about $3–7 per run).
- Why LLM CMs under-use blockchain: consider adding each technology's expected saving for this firm to the brief (the rule already computes it), or raising the one-per-quarter quota.
