# Guesses page: paid LLM run with implementation risk

**Status:** DRAFT for Kevin to edit. Nothing here is fixed until Kevin signs the last line.
**Drafted:** 2026-09-20, after the independent engineering review (STATUS §7, last note).
**Why this page exists:** the model changed shape about ten times in six days, each time after a result was seen. Writing the guesses, the measures, and the pass/fail lines down *before* the run is what lets the result count as a test. The page is committed before the run starts, so git shows it came first.

## 1. What is frozen

| Item | Value |
|---|---|
| Engine | tag `v1.0` (to be made on the commit that holds this signed page) |
| Catalog | `sciti/tech/catalog.yaml` (v2), unchanged |
| Switches | all defaults: implementation risk, learning, group project draw, concave depth on |
| LLM config | a priced copy of `configs/mvp_llm.yaml`: `claude-sonnet-5`, `rules_roles: [Supplier]`, `follow_revenue_share` 0.005, `max_tokens` 2000, `visibility: partners` |
| Brief | as built (shows `implementation_odds`; no event feed; no per-firm expected saving) |

No engine, catalog, brief, or config change between signing and the end of the analysis. If a bug stops the run, fix it, note it here with the commit, and start again from the top; do not look at partial results first.

## 2. Design

| | |
|---|---|
| Scenarios | calm; CM_3 12-week hit (the E2/E5 scenario) |
| Paid arm | LLM agents, suppliers follow |
| Free same-seed arms | no tech; payback rule with suppliers following; hybrid (payback + insurance habit: risk intelligence, APS) |
| Seeds | **Kevin to choose:** seed 1 only (about $6–14 total, comparable with the 2026-09-18 runs, but still one seed), or seeds 1–5 (about $30–70; the reviewer's minimum before any LLM claim) |
| Main measure | `network_profit_with_inventory` vs the same-seed no-tech run |
| Other measures | fill rate; groups formed; adoptions by technology; week of first risk-intelligence purchase at CM_3; share of adoption attempts that fail; malformed replies and fallbacks; cost |

With one seed, every answer below is "seen / not seen on seed 1", not an estimate. With five seeds, report the mean and the number of seeds that agree.

## 3. The guesses

For each: the question, a draft guess (the assistant's, from results so far), the line that counts as "yes", and a space for Kevin's own guess. **Kevin: change any guess or line you disagree with. Your guess is the one that counts.**

**G1. Do LLM agents still buy protection when they can see the odds of failure?**
Background: they bought risk intelligence in all three paid runs (6, 7, 7 firms). Its brief now shows about a 30% chance of failure and 45% of partial success.
- Draft guess: yes, but fewer: 3–6 firms buy risk intelligence in each scenario.
- Counts as yes: at least 3 firms attempt risk intelligence or APS in the calm run.
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G2. Does CM_3 still buy risk intelligence early in the hit scenario?**
Background: that one week-1 purchase made almost all of the LLM edge on 2026-09-18 (+$798M alone).
- Draft guess: yes, CM_3 attempts it before week 30 (persona-driven, as before). Whether it *works* is a coin toss the agent does not control (about 30% fail).
- Counts as yes: a CM_3 risk-intelligence attempt before the hit starts.
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G3. Do LLM agents still form groups?**
Background: rule agents who know the odds almost stop (0.2 groups per run, was 4.7). LLM agents formed 2 control tower chains and 4 blockchain pairs on 2026-09-18 (suppliers following).
- Draft guess: fewer groups, but not zero: at least one control tower chain forms; blockchain pairs 0–2.
- Counts as yes: at least 1 group of any kind forms in the calm run. Counts as "like the rule": 0 groups.
- **Open before signing (Kevin, 2026-09-21):** "there should be a slider to adjust baseline level of collaboration." Not yet designed; it is a model change, so it must be built (or set aside for a later page) before the freeze.
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G4. Do LLM agents beat the payback rule?**
Background, current engine, 30 seeds: rule with followers +$274M calm / +$265M hit; hybrid +$269M calm / +$481M hit (`e2-e4-hybrid-current-engine.md`).
- Draft guess: calm, about the same as the rule (within ±$75M). Hit: LLM beats the rule **only if** G2 happens and that project does not fail; otherwise about the same.
- Counts as "beats": LLM minus rule is more than +$75M on the main measure (on five seeds: in at least 4 of 5).
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G5. Does the free hybrid rule still match the LLM agents?**
Background: on the everything-works engine the hybrid reproduced the LLM edge for free.
- Draft guess: yes. Hybrid is within ±$100M of the LLM arm in the hit scenario, or ahead.
- Counts as yes: LLM minus hybrid is below +$100M in the hit scenario.
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G6. Are they right to?** (the judgment question from STATUS §0)
- For protection: compare the LLM firms' risk-intelligence and APS spend with what those purchases returned on this seed, and with the 30-seed random-disruption result (risk intelligence +$379M for $8M, positive in most seeds). Draft guess: buying it is right on average; on a single calm seed it will look like a small loss (about −$7M).
- For groups: draft guess: avoiding blockchain pairs is right (+$47M for all firms, most fragile); avoiding control tower chains is wrong once disruptions are realistic (+$380M at rate 0.2).
- Kevin's guess (2026-09-21): agrees with the draft guess and the pass/fail line.

**G7. Run health.**
- Draft guess: cost $3–7 per run; malformed replies under 6%; fallbacks under 10; replay exact.
- If replay is not exact, stop and treat it as a bug before reading any result.
- Kevin (2026-09-21): agrees.

## 4. What we will not do after seeing the results

- Change a parameter, the brief, or a rule and rerun *this* test. A new idea gets a new page and a new tag.
- Drop a seed, a scenario, or a measure.
- Report only the measures that came out well. The write-up lists every guess above with "right / wrong / unclear".

## 5. Held-out seeds

Every free experiment so far used seeds 1–30. Seeds **31–60** have never been run. After the freeze, rerun the headline table (STATUS §0) once on seeds 31–60 with the same scripts. Draft line for "confirmed": same sign and same ranking, and each headline number inside the 95% interval of the seeds 1–30 result or within ±25% of it. Anything that fails is reported as not confirmed, not re-tuned.

## 6. Sign-off

- [ ] Kevin has edited the guesses and the pass/fail lines.
- [ ] Seeds chosen: ______
- [ ] Sonnet 5 prices confirmed on the day: $____ in / $____ out per MTok; `sciti estimate` says $____; approved cap $____.
- [ ] This page committed; commit tagged `v1.0`.

Signed (Kevin), date: ______
