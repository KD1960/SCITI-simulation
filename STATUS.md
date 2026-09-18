# SCITI 1 — Status

**Last updated:** 2026-09-18 (catalog v2 on `main`; E1–E5 rerun on it; suppliers-follow rule added; 212 tests pass)
**Phase:** MVP merged to `main`; engine corrected after the 2026-09-17 test audit. See README.md for how to use it.
**Next step:** a paid LLM run with suppliers as followers (about $7; ask Kevin first) to confirm control tower chains form again; then more LLM seeds and a disruption arm. Also open: shrink baseline (0.2%/week); cost evidence for control tower, APS, and ML forecasting; a random-disruption experiment using the evidence table's base rates.

Read this file first in any new thread. Then read the spec and the plan index.

---

## 1. What SCITI 1 is

An agent-based simulation of the Ridge Line supply chain. Each of the 48 nodes is an agent: 30 suppliers, 4 component makers, 2 factories, 4 DCs, and 8 stores. Agents can adopt supply chain technologies alone, or in groups (dyad, triad, chain, or the whole network). The goal is to see how innovation changes profit and customer satisfaction.

It has two planned uses:
- **Research:** replicable runs, full provenance, batch experiments.
- **Teaching:** an animated replay for students and practitioners.

## 2. Where things are

| Item | Path |
|---|---|
| Project root (own git repo) | `~/Claude/Projects/SCITI simulation/` |
| Design spec | `docs/superpowers/specs/2026-09-12-sciti-1-design.md` |
| Plan index (start here) | `docs/superpowers/plans/2026-09-12-sciti-1.md` |
| Plan Part A: data (Tasks 1–5) | `docs/superpowers/plans/2026-09-12-sciti-1-partA-data.md` |
| Plan Part B: engine (Tasks 6–10) | `docs/superpowers/plans/2026-09-12-sciti-1-partB-engine.md` |
| Plan Part C: decisions (Tasks 11–16) | `docs/superpowers/plans/2026-09-12-sciti-1-partC-decisions.md` |
| Plan Part D: view (Tasks 17–19) | `docs/superpowers/plans/2026-09-12-sciti-1-partD-view.md` |
| Ridge Line overview (source) | `~/Docs/School/LE/SCM and AI Oct2026 workshop/RidgeLine_SupplyChain_Overview.docx` |
| Master data set (source, read-only) | `~/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx` |
| Technology list (source) | `~/Claude/Projects/Supply chain innovation/output/technologies-2026-Q2.pdf` (Observatory lexicon v10, 48 techs) |

Git log so far:
- `94c12e6` Add SCITI 1 design spec
- `a047d4f` Spec: align data notes, APS effect, calibration test with workbook profile
- `2458d68` Add SCITI 1 implementation plan (19 tasks in 4 parts)
- `33b64fa` Add STATUS.md for thread handoff (last commit on `main`)
- `ba198c7` Task 1: scaffold, strict config schema, named RNG streams (branch `sciti-mvp`)

## 3. Decisions made (from brainstorming, 2026-09-12)

| # | Topic | Decision |
|---|---|---|
| 1 | Platform | Python engine + browser replay view |
| 2 | Who innovates | Agents decide on their own; configs can also force starting adopters |
| 3 | Technologies | 8 of the 48: ML forecasting, control tower, RFID, APS, routing, warehouse robotics, blockchain, risk intelligence |
| 4 | Time | Weekly steps, 3-year horizon (156 weeks), decisions each quarter |
| 5 | Visual | World map + dashboard (replay of a saved run) |
| 6 | Decision engine | **LLM agents** (chosen over rule-based). Made safe with: every decision logged, exact replay mode, spend caps, and a rule-based fallback |

Later plan-level choices (made during planning; change them if you like):
- Continuous (float) quantities; lost sales at stores; backlog upstream.
- Transfer and retail prices are not in the data. They use markup assumptions: CM +20%, MFG +25%, DC +10%, retail +40%.
- Customer satisfaction index = 0.5 fill rate + 0.3 on-time + 0.2 quality.
- Tech effect sizes and costs are placeholders, marked `assumption: true`.
- View uses plain JS + Canvas, with no libraries and no CDN.
- CSV/JSON outputs (not Parquet), so students can open them in Excel.

## 4. What we learned about the data (verified 2026-09-12)

- **Demand_Retailer:** weekly A/B/C demand for 8 stores, 2020–2024 (260 weeks). Retailer r's columns start at `3 + 3*(r-1)`. Growth rates per year: Product A about +10%, B about 0%, C about −7%.
- **Supplier Data:** 250,000 rows, but only **500 are valid**, and they cover only **10 of 30 suppliers** (the first supplier of each sub-component). Columns Q:W, rows 2–31, hold a parameter table for all 30 suppliers (lead time, price, units). The plan uses that table and pools the rest.
- **Shipments sheet:** three side-by-side tables (columns 0–13 CM→MFG, 15–28 MFG→DC, 30–43 DC→Retailer), 500 rows each. The data names the US plant `MFG_LA`; it is treated as `MFG_US`.
- **DC→Retailer rows are spread evenly across all DC–store pairs** (synthetic data). So network links follow the document, and lane statistics come from the data by mode.
- **Glossary sheet:** BOM (160 units per product), node addresses, and the CO2 formula: `qty × 0.05 t × miles × factor` (Air 2.1, Road 0.163, Rail 0.028, Ship 0.037 kg/ton-mile).
- Reading the Excel with pandas takes about 6 seconds. It needs `openpyxl`, which the system Python does not have; the plan uses a project `.venv`.

## 5. Standing rules for this project

- Stage files **by name**. Never `git add -A` or `git add .`.
- Commit messages end with a `Co-Authored-By:` line naming the Claude model that did the work (from 2026-09-17: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; earlier commits say Opus 5).
- The repo has a local git identity (Kevin Dooley). Don't change the global git config.
- Quote the project path in shell commands (it has a space).
- Reproduce before fixing; a failing test is the preferred statement of a bug.
- Tests never call the Anthropic API.
- The source Excel is read-only.
- **Ask Kevin first** before:
  - Downloading `ne_110m_land.geojson` (Task 18). Tell him the file size.
  - Any paid LLM run. Confirm the model id, current prices, and that `ANTHROPIC_API_KEY` is set, and get approval for the estimated spend.
- Don't loosen a failing test threshold (e.g., the calibration fill rate > 0.80) without Kevin's agreement.

## 6. How we build

Chosen 2026-09-12: **subagent-driven** (`superpowers:subagent-driven-development`). A fresh helper implements each task; a reviewer checks spec + quality; fixes loop until clean. Work happens on branch `sciti-mvp` (not `main`). Each part has its own git-ignored ledger under `.superpowers/sdd/<plan-part-name>/progress.md`; trust the ledger and `git log` when resuming.

## 7. Progress tracker

| Task | Part | Status |
|---|---|---|
| 1 Scaffold, config, RNG | A | done (ba198c7) |
| 2 Workbook loader | A | done (99bdbc7..00801e8; added required-column check per Kevin) |
| 3 Demand model | A | done (d1765e5..14e8677; fixed AR(1) start bias) |
| 4 Network builder | A | done (9b2a1e8) |
| 5 Tech catalog + effects | A | done (286def4) |
| 6 Engine core | B | done (9f0d8d0..bb01d03; backlog counted in MFG/CM orders) |
| 7 Disruptions | B | done (3e852f8) |
| 8 Invariant checks | B | done (68dcaa9..303da12; added flow-balance + NaN checks) |
| 9 Adoption, outputs, runner, CLI | B | done (89fba42..38f2823; bullwhip in product units, order-to-arrival lead time) |
| 10 Golden + calibration tests | B | done (2aaf156..7c34936; real-data per-mode transit check, flat lane model for thin data) |
| 11 Decision interface, briefs, mock | C | done (379024c..ab321b8; stricter reply checks, CO2 in briefs) |
| 12 Coalitions + decision round | C | done (171b738..d4ed130; budget re-check, fallback safety) |
| 13 Rules policy | C | done (a6e1634..5a2e6bd; quota counts formed groups only) |
| 14 LLM policy | C | done (4ab14ea..a27c616; price floor, timeout, key check) |
| 15 Replay | C | done (3ac74a2; real replay exact) |
| 16 Batch + estimate | C | done (847d9e6..b61e562; failure-tolerant, factor columns, tech-free baseline) |
| 17 View server + page shell | D | done (0a7b505..bd1a63f; HEAD allow-list, /config.json) |
| 18 Map animation | D | done (9b5f8d9..1541ccc; coastlines, no-red tech palette, pulses, hatched disruptions) |
| 19 Dashboard + final verification | D | done (67fc9eb..11e1472; grouped feed, Groups in node panel, click picking, spec revised) |

Update this table and the "Last updated" line as each task lands.

**Part A notes (2026-09-12):**
- 31 tests pass. `data/baseline.json` and `data/validation_report.md` were built from the real workbook (git-ignored).
- Real data: 20 of 30 suppliers use pooled lead-time spread and defect share; 9 of 24 store×product demand series have autocorrelated noise (so the Task 3 AR(1) fix matters).
- Kevin's rulings on Task 2 review: add required-column check; keep report-on-success only; supplier/BOM mismatch stays a hard stop.
- Deferred minor findings for the final review are in the Part A ledger. One to reconcile: spec §6 says ML forecasting cuts error SD ×0.7, but the catalog models it as `forecast_skill +0.3`.

**Part B notes (2026-09-13):**
- 78 tests pass (including realdata). `sciti prepare` and `sciti run CONFIG` work.
- Real baseline run (seed 1, 156 weeks, no tech): fill rate 0.984; bullwhip Retail 2.5, DC 8.9, MFG 27, CM 116; order-to-arrival lead time into stores 8.0 days; transit 8.7 days.
- Calibration on real data: demand sim/expected 1.000; fill 0.989; transit per mode vs workbook: Air 0.99, Rail 1.04, Road 1.00, Ship 0.76 (inside the ±25% band, near its floor).
- Kevin's rulings from reviews (all approved changes from the plan):
  1. MFG and CM count net backlog owed downstream in their order position (plan's DC-only rule made fill fall to 67% by year 3).
  2. Invariants add a per-node flow-balance check from weekly counts, plus a non-finite-stock check.
  3. Bullwhip for MFG/CM is converted to product units (÷160).
  4. `mean_lead_days`/`p95_lead_days` = order-to-arrival for shipments into stores (FIFO order-week tracking); new `mean_transit_days`/`p95_transit_days`.
  5. Lead-time calibration relabeled as an engine/lane-model check; new real-data per-mode test (±25%).
  6. Loader uses a flat lead model (data mean, no distance slope) when a lane mode has < 50 rows or a negative fitted slope.
- `run()` applies forced adoptions every week, not only at quarter starts (controller fix). Part C Task 12 edits the same block: keep that.
- Spec wording to update at the end: §5.3 ordering rule (backlog), §5.5 lead time and bullwhip units, §9.4 checks, §11 calibration.
- Deferred minors for the final review are in the Part B ledger. The most important: forced adoptions aren't validated up front (an ineligible member crashes mid-run).

**Part C notes (2026-09-13):**
- 144 tests pass (including realdata). New commands: `sciti replay`, `sciti batch`, `sciti estimate`. No paid LLM run has been made.
- Real data, rules policy, 156 weeks, seed 1: 51 adoptions, 4 coalitions (2 dyad, 1 triad, 1 chain); fill 0.985. Replay of a rules run: `replication: exact`.
- **Economic finding to discuss:** in batches, rules runs earn ~1% less profit than the same-seed no-tech baseline (e.g. $31.3B vs $31.6B) with about the same satisfaction index. Tech costs outweigh modeled savings. The catalog costs and effects are placeholders (`assumption: true`), so this is about the parameters, not a result.
- Rules can't act in quarter 1 (no cost history yet); first adoptions are at week 14.
- Kevin's rulings from Part C reviews:
  1. Reply validation rejects wrong types (no crash); accept must name the proposal's tech; briefs include last-quarter CO2.
  2. Group formation re-checks budgets until stable; a bad fallback reply skips the agent instead of crashing.
  3. The one-new-tech-per-quarter limit counts solo adopts and FORMED groups only (proposing/accepting don't use it up).
  4. LLM safety: refuses zero prices and missing key before creating a run folder; 60 s request timeout, no stacked SDK retries; 529 retried; auth errors stop the AI at once; rules fallbacks on retry are logged as fallbacks.
  5. Batch: a failed seed is recorded and the batch continues; bad seed ranges rejected; results.csv has readable settings columns and `baseline_for`; the paired baseline has no technology at all (forced adoptions removed).
- `configs/mvp_llm.yaml` has prices 0.0 on purpose: it refuses to run until Kevin sets the model's current prices. `anthropic` SDK is 1.5.0 (uses `httpx2`).

**Part D notes (2026-09-14):**
- `sciti view RUN_DIR [--baseline BASE_RUN_DIR]` serves a local-only replay page: world map (Natural Earth coastlines, Kevin approved the 138 KB download), moving shipments, tech rings, group lines, pulses, hatched disruptions; 6 dashboard charts with dashed baseline; node panel (stats, Groups, decisions with reasons); event feed (failed group proposals grouped per week).
- Browser checks were done by the controller in the in-app browser after each view task (subagents had no browser). Notes live in the Part D ledger folder.
- Kevin's rulings: fix all map encoding issues (no red tech colors, drop-aware group lines, pulses, hatched disruptions + red outgoing lanes) and all dashboard issues (grouped feed, Groups section, click picks the node under the cursor, -$ formatting).

**Final whole-branch review (2026-09-14):** "Ready with fixes", no critical issues. The reviewer confirmed replay stays exact even through AI fallbacks and spend-cap switching. One fix wave (cdcb9ee..9de465d), re-reviewed clean:
1. Forced adoptions are validated before a run starts; an already-held tech is skipped with a `forced_skipped` event.
2. Any crash mid-run still writes the manifest (with spend and fallback stats) and closes files.
3. `sciti replay` works on `none` runs.
4. Manifest lists assumed parameters; the view header tooltip shows them.
5. Documented: paired baselines share demand draws but not lane (lead/mode) draws, so paired differences include some lane noise.
6. End-to-end test: an LLM run (fake client with failures and a spend cap) replays exactly.
7. README.md added. Spec reconciled with the build.
- 167 tests pass (including realdata). A 156-week run takes ~1.5 s; a 30-seed batch with baselines ~90 s.
- §12 success criteria: 1, 2, 4, 5, 6, 7 met. 3 (a paid LLM run replayed exactly) is ready but not run — needs Kevin's approval, current prices set in `configs/mvp_llm.yaml`, and `ANTHROPIC_API_KEY`.
- Before presenting results as research (reviewer recommendation): per-shipment lane random draws for cleaner paired comparisons; 30-seed rules-vs-baseline batch with confidence intervals; replace placeholder tech costs/effects with cited values.
- The SDD ledgers under `.superpowers/sdd/` (git-ignored) were deleted after the final review; this file and git history are the record.

**Thread "SCITI sim 2" (2026-09-14):** no code changed. New files in `docs/sciti2/`: infographic (PNG + HTML), Ridge Line data corrections report (for the case authors), experiments recommendation, project plan, and the data-audit scripts.
- **Merged `sciti-mvp` into `main`** (fast-forward), per Kevin.
- **Demand bug fixed:** workbook formulas for Retailer 5 (P, R) and Retailer 7 (V, W) scale the wrong Retailer 1 product (Mumbai A = B = C; Tokyo A shrank ~7%/yr). `parse_demand` now detects a store column matching scale × a different Retailer 1 product, rebuilds it from the intended product, and logs it (4 columns fixed). 168 tests pass incl. realdata. Seed-1 no-tech run after the fix: fill 0.978, profit $34.1B (was 0.984, ~$31.4B). The pilot/screen numbers below predate the fix.
- **Pilot (10 seeds, rules vs none):** paired profit-difference SD ($220M) is larger than baseline seed SD ($162M), so lane noise defeats pairing. Satisfaction index 0.963 baseline (ceiling).
- **Screen (5 seeds, each tech forced on all eligible firms):** routing +$403M, blockchain +$571M; ML forecasting −$358M and control tower −$199M despite large bullwhip cuts; risk intel recovers ~all of a CM_3 disruption loss. CO2 ≈ 50 t per product sold. All three flagged for checking.

- **Per-shipment random draws (2026-09-14):** `make_shipment` now uses `shipment_rng(seed, src, dst, item, week)` instead of the sequential `lead` stream (removed from `STREAMS`; other streams unchanged). New test: a lane-week's draws don't depend on earlier shipments. Golden summary regenerated (seed-level changes only). 169 tests pass incl. realdata; a 156-week run still ~2 s. 10-seed rules-vs-none batch, old → new code: paired profit SD / baseline SD 1.55 → 0.35; satisfaction 1.51 → 0.19; fill 1.05 → 0.27. With the new code, rules adoption costs −$107M profit (SE ≈ $24M) vs baseline.
- **Three odd results checked (2026-09-14, 10 seeds each, no code changed):**
  1. *ML forecasting's profit loss is an accounting artifact.* Sellers book revenue at ship week (`ops.py` `_shipping`); buyers book purchases at arrival (`_arrivals`). Goods still in transit at the horizon end count as network profit (~$1.8B in a baseline run). ML forecasting's −$293M equals its drop in end-of-run in-transit value; excluding it, the effect is −$0.6M ± $18M. Control tower: −$48M of its −$109M is the same artifact.
  2. *Control tower's remaining −$62M and −0.23 pt fill are a safety-stock design effect.* With visibility, a node's forecast error `err` is measured against smooth end-customer demand, not the lumpy orders it must fill, so DC stock falls ~20% and store lost sales rise ~15%. Scratch test measuring `err` against `orders_in`: control tower fill +0.31 pt, stockout −$51M, but adjusted profit −$147M (not yet explained).
  3. *Risk intelligence is not a bug.* ~90% of its gain is CM_3's own shorter disruption (8 → 5 weeks; MFG early warning adds ~$9M). Losses are steeply convex in length (no tech, CM_3 at 20%: 4 wk −$14M, 5 wk −$84M, 6 wk −$213M, 8 wk −$641M). Forced adoption with >1 member forms a coalition, so screens also get the +25% group bonus (8 → 4 weeks).
  4. *CO2 is a data assumption.* 99.3% comes from CM→MFG shipments: 0.05 t per part × 160 parts = 8 t of parts per product, 53% by air. Needs a per-part weight.
  - **Kevin's rulings and fixes (2026-09-14):**
    1. Purchases now book in the week the seller ships (`3d08bab`); money fields only change. New test: internal sales = purchases every week.
    2. Parts weigh 0.05 t ÷ 160 (`assumptions.part_weight_tons`, `e143284`); baseline CO2 ≈ 2.9 Mt over 3 yrs, ~0.68 t per product sold.
    3. Forced multi-member adoptions keep the group bonus; README says so.
    4. Control tower: dig into profit before changing the rule. Finding (10 seeds, corrected code): measuring `err` against demand gives too little safety stock (fill −0.23 pt, profit −$62M); against orders gives too much (fill +0.31 pt but holding +$143M, scrap +$74M, supplier cogs +$185M; profit −$147M). Root cause is the visibility effect itself: a node swaps downstream orders for end-customer demand and loses sight of downstream replenishment needs. Needs a redesign decision (e.g., upstream forecasts downstream orders from end demand plus downstream inventory positions). Not changed. (Superseded: see the control tower redesign below.)
  - 171 tests pass. Pilot/screen numbers in `docs/sciti2/experiments-recommendation.md` predate these fixes; rerun E1 before using them.

**Control tower redesign (2026-09-14, branch control-tower-echelon):** plan docs/superpowers/plans/2026-09-14-control-tower-echelon.md; commits 638d43c..c76dd84. Run 1 (acceptance): 3/4 — fill rate fell ~12.2 pt and stockout cost rose ~$2.0B, failing check 2. Fix (spec §3.6, commit c76dd84): add the missing per-stage review week to the echelon lead time and a safety-stock floor so the tower never targets less safety stock than downstream nodes already hold. Run 2 (acceptance, after the fix): 4/4 — whole network vs. no-tech (10 seeds): fill rate +0.09 pt, stockout cost −$14.2M, holding cost −$35.1M, bullwhip DC −2.35 / MFG −13.28 / CM −78.69, network profit +$110.5M. Details in docs/sciti2/control-tower-acceptance.md. 182 tests pass (including realdata), after final-review fixes to the branch (new test covering the v=1 order formula, per-stage horizon).

**E1 technology screen (2026-09-15):** 8 techs × (all eligible firms, one tier), 30 paired seeds, calm conditions, on `de0e9df`. Results: `docs/sciti2/tech-screen-e1.md`; script `docs/sciti2/experiments/tech_screen.py`; numbers `tech_screen_results.csv`. Profit ($M, 3 yrs, all-firms arm): blockchain +686, routing +439, RFID +220, warehouse robotics +154 (also satisfaction +0.010, the only clear service gain), control tower +99 (CM bullwhip −78), risk intel −8 (no disruptions), APS −32, ML forecasting −43 (CM bullwhip −63). Blockchain at suppliers+CMs alone gets the full benefit; control tower needs the whole chain. Placeholder parameters drive the ranking.

**E2 stress test (2026-09-15):** 21 scenarios (growth ×0.5/1/1.5 × no disruption or CM_3/CM_4/DC_Shanghai for 4 or 12 weeks) × 5 arms (none, risk intel, control tower, APS, rules agents), 30 paired seeds, on `810a39a`. Results: `docs/sciti2/stress-test-e2.md`; script `docs/sciti2/experiments/stress_test.py`; numbers `stress_test_results.csv`. Findings: 4-week hits sit inside the buffer; 12-week CM hits cost ~3 pt fill and $1.4–1.6B. Risk intel = insurance (−$8M calm, +$1.2–1.5B in 12-week CM hits). APS = partial insurance (−$30–60M calm, +$250–330M long CM hits). Control tower ~+$100M regardless of disruption, but ~0 at growth ×1.5 (to check). Rules agents never adopt risk intel, APS, or robotics and don't react to disruptions. To check: control tower at high growth; APS losses growing with demand.

**E3 who with whom (2026-09-15):** same tech, 6 adopters in different structures, plus all-firms reference; calm and a 12-week CM_3 hit; 30 paired seeds, on `6ba2678`. Results: `docs/sciti2/who-with-whom-e3.md`; script `docs/sciti2/experiments/who_with_whom.py`; numbers `who_with_whom_results.csv`. Scattered adopters get nothing (pure cost). Control tower: upstream chain best in calm (+$29M, CM bullwhip −51), downstream chain best in disruption (+$61M vs +$3M calm), 3 DC–store pairs ~+$6–8M (n.s.). Blockchain: value ≈ $4M per part-per-product covered by linked suppliers (pairs +$33M, CM_1 hub +$65M, CM_3 hub +$224M); hub shape adds nothing beyond volume. Rules agents' control tower adoptions are all in groups but downstream-leaning (stores 7.1, DCs 3.3, CMs 1.2 per run).

**E4 decision rules (2026-09-15):** payback-rule agents, full 2^5 factorial (budget share, horizon, chain accept share, cost split, max new per quarter) + default, calm and 12-week CM_3 hit, 30 paired seeds, on `5b3687b`. Results: `docs/sciti2/decision-rules-e4.md`; script `docs/sciti2/experiments/decision_rules.py`; CSVs `decision_rules_main_effects.csv`, `decision_rules_points.csv`. Network gain ranges +$145M to +$348M (defaults +$190M). Main effects (calm/disrupted): 2 per quarter +$81M/+$105M; long horizon +$65M/+$70M; by-size split +$19M/+$14M; 80% acceptance −$14M/−$23M (but +$11–19M within the best combination); budget share exactly zero (smallest budget ~$257k exceeds every one-time cost). Agents never adopt risk intel, APS, or warehouse robotics in any setting. Cause: the rule counts only the adopter's own costs, but shipping and defect scrap are charged to buyers and only stores record stockouts (split incentives).

**E5 first paid LLM run (2026-09-16):** Sonnet 5, seed 1, 156 weeks, Kevin approved ~$7.49 with a $20 cap. Actual: **$18.61**, 1,500 calls (call cap hit), 2 h 27 m. Results: `docs/sciti2/llm-pilot-e5.md`; run kept in the session scratchpad (`llm_pilot`), not in the repo. `sciti replay` reproduced it **exactly** — spec §12 criterion 3 now met. LLM vs same-seed no-tech: profit +$554M, fill +0.24 pt, 61 adoptions, 9 groups; payback rule on the same seed: +$133M, fill +0.00. LLM agents adopted risk intel (7), APS (6), and robotics (1) — technologies the rule never adopts. Problems: 419 of 1,110 decisions fell back to rules because replies were truncated (`decision.max_tokens: 600` while Sonnet 5 thinks by default, so thinking eats the reply budget); retries doubled the call count. Fix before the next paid run: raise max_tokens (or disable thinking for this call), use structured outputs, and correct the estimate's calls-per-agent assumption.

**LLM call fixes (2026-09-16, after E5):** `decision.max_tokens` default 600 → 2000 (thinking shares the budget); the reply shape is now requested via structured outputs (`REPLY_SCHEMA` in `sciti/decide/llm.py`, `output_config.format`) as well as validated in code; `sciti estimate` now reports `calls_with_retries`/`usd_with_retries` (2.6 calls per agent-quarter, measured) beside the clean figures. `configs/mvp_llm.yaml` is back to zero prices (it refuses to run until prices are set) with the model left at `claude-sonnet-5` and the cap at $20. 185 tests pass. Not yet exercised against the real API — the next paid run is the first test.

**LLM pilot rerun on fixed settings (2026-09-16, `309f13c`, run `llm_pilot2` in the session scratchpad):** $5.40, 706 calls, 50 min, 1% malformed replies (was 38%), 2 fallbacks (was 419); replay exact. Seed 1 vs same-seed no-tech: profit +$475M, satisfaction +0.0042, fill +0.13 pt, on-time +1.14 pt, 112 adoptions, 14 groups including 5 chains (control tower 47), insurance bought again (risk intel 10, APS 6, robotics 3). Payback rule on the same seed: +$133M, no chains, no insurance. Costs: purchases −$395M, scrap −$228M, shipping −$233M, tech +$92M; CM bullwhip −77; CO2 −7%. Still open: 7 replies truncated at max_tokens 2000; single seed; no disruption arm.

**LLM run under the E2 disruption (2026-09-16, `309f13c`, `llm_pilot3` in the session scratchpad):** CM_3 12-week hit, seed 1. $5.68, 754 calls, 54 min, 4 fallbacks, replay exact. Vs same-seed/scenario no-tech: profit +$1,554M, fill +2.46 pt, satisfaction +0.0163, on-time +1.28 pt, stockout −$402M (payback rule on the same scenario: +$144M, +0.09 pt). Insurance timing: 4 adoptions before week 30 (CM_3 — the site that gets hit — plus CM_4 and MFG_US in week 1, DC_Shanghai week 27, all citing cautious personas), 14 after. Rules agents never adopt these at all.

**Test audit (2026-09-17):** verdict "partly" — plumbing well tested; tech effects (5 of 8) and outcome metrics weakly tested. 6 confirmed defects: blockchain does nothing at CM/MFG; routing savings booked to customer not adopter; forced coalitions ignore cost_split; quality deterministic (quality stream unused); early warning off once disruption starts; summary costs include scrap (profit excludes it). E4's routing/blockchain split-incentive rows and E1's blockchain one-tier result are partly artifacts of defects 1–2. Full report: `docs/sciti2/test-audit-2026-09-17.md`.

**Audit fixes (2026-09-17, branch `audit-fixes`):** fixed all 6 confirmed defects from the 2026-09-17 test audit. `42181db`: the shipper now pays freight (booked to the sender in the ship week); forced group adoptions follow `decision.cost_split`; the run summary's `costs` are now exactly the profit cost keys, with scrap reported separately as `scrap_value` (a memo item — the value of scrapped units, already inside purchases). `617e08c`: blockchain is now eligible for Supplier and CM only, and defects drop on a supplier shipment when the supplier and CM both hold it; each supplier shipment's defective share is now a random Beta draw (mean = supplier defect share × blockchain multiplier, concentration `assumptions.defect_concentration`, default 50), keyed to the shipment; the risk-intelligence early warning now keeps its extra safety stock through the end of the disruption (rounded up to whole weeks). `66c97b7`/`9fccd23`: added `tests/test_mechanisms.py` (10 value tests for tech effects, costs, metrics, and coalition rules) and `tests/test_audit_fixes.py` (7 tests for the fixes above). Full suite: 202 passed, no xfails. Details and the defect-to-commit / missing-test-to-test-name mapping: `docs/sciti2/test-audit-2026-09-17.md` §Resolution. E1 and E4 results predate these fixes; both docs now carry an engine-changed note.

**Audit fixes merged (2026-09-17, `main` at 5673129):** branch `audit-fixes` fast-forwarded and deleted. All 6 confirmed defects fixed (blockchain pairs Supplier+CM only; shipper pays freight; forced groups follow cost_split; per-shipment Beta defect share; early warning through the disruption; scrap reported as `scrap_value`), plus Kevin's ruling that selling prices now add expected freight per unit before the markup — without it CMs ran ~$1.8B in losses and CM_1 ran out of cash. Real-data check after the fix: all CMs profitable (CM total $3.26B over 156 weeks) and cash-positive every week (minimum $268M). 17 new tests in `tests/test_audit_fixes.py` and `tests/test_mechanisms.py`; 203 pass. E1–E5 result docs carry an "Engine changed 2026-09-17" note; their numbers predate these fixes.

**Sensitivity screen (2026-09-17, `97c76bb`):** each tech forced on all eligible firms with effects at 0.5×/1×/1.5×, calm and CM_3 12-week hit, 30 paired seeds; cost sensitivity by arithmetic. Results: `docs/sciti2/sensitivity-screen.md`; script `docs/sciti2/experiments/sensitivity_screen.py`; numbers `sensitivity_screen_results.csv`. Findings: costs almost never matter (break-even cost 4×–200× the placeholder for six techs); effect sizes drive the ranking roughly linearly (blockchain, routing, RFID, robotics are the top evidence-table items); risk intel and APS depend on disruption frequency/length, not parameters; control tower capped (1.5× = 1×). **To check:** ML forecasting profit and fill get worse as forecast skill grows (−$80M, significant, at 1.5× in the CM hit) — looks like a model problem; APS calm loss also grows with capacity (n.s.). Engine assumptions, group bonus, and setup weeks not varied.

**ML forecasting loss reproduced (2026-09-17, `fd29d11`, no code changed):** ML at 1.5× effect, CM_3 12-week hit, 10 paired seeds, scratch probe. As built: all tiers −$69M ± 57, fill −0.10 pt (Retail −$34M, DC −$8M, MFG +$48M). Cause: `_needs` (and `_echelon_signal`) in `sciti/engine/ops.py` cut safety-stock sigma by an assumed `(1 - w/2)`, but `ns.err` is still measured against the plain smoothed forecast, and most of that error is demand/order noise the ML forecast cannot remove. So adopters hold too little safety stock. With the assumed cut removed (scratch patch): all tiers +$181M ± 48, fill +0.51 pt, every tier positive. Needs Kevin's ruling on the fix (e.g., measure `err` against the blended forecast the node actually uses, and drop the assumed cut).

**ML forecasting sigma fix (2026-09-17, merged to `main` at `461082f`, Kevin approved):** `_forecast_and_order` now measures `err`/`err_end` against the blended forecast for the observed week (`flows[t-1]`), and the assumed `(1 - w/2)` sigma cut is gone from `_needs` and `_echelon_signal`. No change when `forecast_skill` is 0 (golden unchanged). One test updated, one added; 204 pass. ML rows of the sensitivity screen rerun (30 seeds): fill no longer falls as skill grows (1.5×: calm −0.05 → +0.03 pt; CM_3 hit −0.10 → +0.08 pt). **Profit still falls with skill** (calm −$33M / −$53M / −$65M at 0.5×/1×/1.5×, all significant; hit n.s.). Breakdown at 1.5× calm: supplier cogs +$77M, holding +$24M, tech +$19M, shipping −$31M; bullwhip CM −68. Profit moves from CMs (−$288M) and DCs (−$127M) to MFG (+$212M) and stores (+$168M). Not yet explained — likely the forward-looking forecast under growing demand raises stock and supplier output, with unsold stock at the horizon carrying no value. To check next. The ML rows in `docs/sciti2/sensitivity-screen.md` predate this fix.

**ML forecasting profit drop explained (2026-09-17, no code changed):** it is unvalued inventory, not an operating loss. `network_profit` is cash-basis: purchases and supplier cogs are expensed when made, and stock on hand or in transit carries no value. Scratch probe (ML 1.5×, all tiers, calm, 30 paired seeds), ML minus no-tech, $M: week 52 cash −38 / inventory value +77 / together +40 ± 9; week 104 −72 / +93 / +21 ± 10; week 130 −156 / +198 / +42 ± 12; week 156 −65 / +97 / +33 ± 15. So ML is worth about +$20–40M after its $19M cost once stock is counted. The cash difference swings by ±$100M with the phase of the order cycle (MFG/CM orders pulse every ~10–15 weeks), so cash-basis paired differences depend on where the horizon falls. Caveat: the probe valued stock at each node's selling price (`unit_value`), which includes margin; at cost the inventory term would be smaller. **This touches every experiment** that reports `network_profit` for a technology that shifts inventory (ML, control tower, APS, risk intel). Needs Kevin's ruling: add an inventory-adjusted profit measure to the summary (and decide the valuation basis), then use it in the E1–E5 reruns.

**Inventory-adjusted profit (2026-09-17, branch `inventory-adjusted-profit`, Kevin's ruling: value stock at cost):** the run summary now has `inventory_opening`, `inventory_closing`, `inventory_change`, and `network_profit_with_inventory` (= `network_profit` + change). `inventory_cost` in `sciti/engine/economics.py` values stock at what the holder paid (supplier: price × cogs share; CM: mean supplier price; MFG parts: CM price, products: BOM at CM prices; DC: MFG price; store: DC price) and goods in transit at invoice value. Goldens regenerated (new keys only); 206 tests pass. **This corrects the note above:** the "+$33M with stock counted" result came from valuing stock at selling price. At cost, ML 1.5× calm (30 seeds) is −$75M ± 32 at week 156 (cash −$65M, inventory −$10M), and the adjusted difference still swings with the horizon: week 26 +$33M, 52 −$79M, 78 +$28M, 104 −$95M, 130 +$35M, 156 −$75M (SE ≈ 10–15). So ML's effect is not settled. Two open problems: (1) holder-cost valuation includes internal margins, so the same part is worth more at MFG than at CM, and ML moves stock upstream to CMs (+6.7M parts) — a consolidated basis (supplier cogs plus freight paid) would not have this; (2) a yearly cycle in the paired difference, cause unknown. Superseded the same day, see below.

**Consolidated inventory basis (2026-09-17, Kevin's ruling A):** `inventory_cost` now values every unit on one network-wide basis — supplier cost (price × cogs share, averaged over a part's suppliers) plus the expected freight paid on each lane so far (`prices["cost"]` from `price_table`); goods in transit at the receiving node's basis. Moving stock between firms no longer changes the total, so the internal-margin problem is gone, and with it the yearly wave: ML 1.5× calm, ML minus no-tech, adjusted profit at weeks 26/52/78/104/130/156 = −12, −15, −20, −39, −37, −33 $M (SE 2–12; cash alone swung −38 to −156). Net of the $19M tech cost, ML forecasting at 1.5× is about −$14M over 3 years: roughly neutral, not a loss. Use `network_profit_with_inventory` for technology comparisons from now on; `network_profit` stays cash-basis. 206 tests pass. Goldens regenerated (new keys only).

**Suppliers on rules (2026-09-17, branch `rules-roles`, Kevin's request):** new `decision.rules_roles` (list of roles). Agents in those roles use the payback rule instead of the main policy; their log records say `policy: rules` (not a fallback), and a replay still takes every agent from the log, so replication stays exact (test). `sciti estimate` counts only the remaining agents. `configs/mvp_llm.yaml` now sets `rules_roles: [Supplier]`: 18 LLM agents instead of 48, so a run should cost about $2 instead of $5.40 at the E5 rerun's rates (measured 2026-09-18: $7.14, see the E5 rerun note below). README updated. 208 tests pass. Not yet exercised against the real API.

**E1 rerun (2026-09-17, `14b0a08`):** same design, corrected engine, plus `network_profit_with_inventory`. Results: `docs/sciti2/tech-screen-e1-2026-09-17.md`; numbers `tech_screen_results_2026-09-17.csv`; `tech_screen.py` now also collects the inventory-adjusted profit. Profit with inventory ($M, all-firms arm): blockchain +706, routing +444, robotics +198, RFID +185, control tower +65, APS +20 (ns), risk intel −8, ML forecasting −35. Ranking unchanged from 2026-09-15. Inventory-adjusted profit moved control tower (+108 cash → +65), RFID (+223 → +185), APS (−22 → +20, both ns), ML (−53 → −35). Control tower at DCs + stores is now clearly positive (+23). E2–E5 still predate the fixes.

**Evidence table (2026-09-17):** `docs/sciti2/evidence-table.md` — sourced LOW/MID/HIGH ranges for all 12 catalog parameters, costs by firm size, disruption base rates, and catalog-v2 candidates. Four research helpers, ~60 sources, quality-flagged. Headlines: blockchain `defect_mult` has no measured evidence (MID 0.82 vs placeholder 0.6; low confidence); control tower `visibility` 1.0 is unsupported for visibility alone (MID 0.6; Cachon & Fisher, Croson & Donohue); RFID shrink ×0.5 is a vendor claim (MID ×0.8) while record error ×0.2 holds; routing cost holds, CO2 a bit optimistic (0.94); robotics handling holds, dispatch −1 day optimistic (−0.6); ML skill 0.3 is top of MID and should be lower at stores (M5 level effect); APS +8% holds but on vendor cases only; risk intel recovery 0.6 optimistic (0.7) and early warning +2 only for forecastable events (+1). Costs matter little for ranking. **Needs Kevin's ruling** on §4 of that doc: catalog v2 values, two model-shape changes (skill by role; risk intel as weeks saved + warning probability), and baseline flags. Catalog unchanged so far.

**Catalog v2 (2026-09-18, Kevin approved all three items of evidence-table §4):** `sciti/tech/catalog.yaml` is now v2 (MID evidence values; v1 kept as `catalog_v1.yaml` for comparison via `catalog_path`). Values: blockchain `defect_mult` 0.82, control tower `visibility` 0.6, RFID shrink ×0.8, routing `co2_mult` 0.94, robotics dispatch −0.6 day; others unchanged. Model-shape changes: effects can carry `by_role` values (ML `forecast_skill` 0.1 at stores, 0.3 at DCs/factories; agent briefs show the role's value); risk intelligence uses `recovery_weeks_saved` (2 weeks, floor of a 1-week outage) and `warning_prob` (0.4; one keyed draw per disruption via `rng.warning_draw`, advance warning only if prob > draw, extra safety stock for every subscriber once it starts). Only blockchain, APS, and risk intel remain `assumption: true`. 210 tests pass; tech golden regenerated, no-tech golden unchanged. **Results** (`docs/sciti2/catalog-v2-results.md`), profit with inventory, $M: routing +444, blockchain +321 (was +706), robotics +124 (+198), RFID +83 (+185), control tower +63 (+65), APS +20 ns, ML −7 ns (−35), risk intel −8 calm / +575 in a 12-week CM hit. Routing is now top; control tower is robust to its visibility value; RFID's value rides on the shrink baseline; costs now matter only for control tower, APS, and ML.

**E2–E4 rerun (2026-09-18, corrected engine + catalog v2):** `docs/sciti2/e2-e4-rerun-v2.md`; numbers `stress_test_results_v2.csv`, `who_with_whom_results_v2.csv`, `decision_rules_main_effects_v2.csv`; the three scripts now also collect `network_profit_with_inventory`. E2: 12-week CM hits cost ~$1.7–2.0B and ~3 pt fill; risk intel recovers +$591M (about a third of v1), APS +$366–442M and no longer loses in calm (+$20M ns), control tower +$60M calm / ~+$100M long hits at every growth level (the "zero at high growth" result was a cash artifact), payback-rule agents +$415–436M everywhere. E3: scattered adopters get nothing; a 6-firm downstream control-tower chain gets +$81M in the CM_3 hit (79% of all 48 firms); blockchain value follows volume covered (~$1.9M per part-per-product). E4: gain +$365M to +$603M; horizon +$97M, two per quarter +$84M, budget never binds; agents now adopt routing (freight fix) but still never APS, robotics, or risk intel in any setting.

**E5 rerun (2026-09-18, paid, Kevin approved):** Sonnet 5, seed 1, calm, corrected engine + catalog v2, `rules_roles: [Supplier]`. Run `runs/mvp_llm_s1_20260918T192217Z` (git-ignored); results `docs/sciti2/llm-run-e5-v2.md`. **$7.14** (estimate said $2.81), 459 calls, 62 min, 27 malformed (22 truncated at max_tokens 2000), 5 fallbacks, replay **exact**. LLM vs same-seed no-tech: profit with inventory +$326M, 30 adoptions, 2 groups; payback rule: +$363M, 59 adoptions, 5 groups. LLM agents bought risk intel (6), APS (1), robotics (1) again; the rule never does. **Side effect found:** with suppliers on rules, no control tower chain ever forms (171 failed proposals): chain invitations go to all 30 suppliers, who accept 3% under the payback rule, so the 60% bar is never met. Needs Kevin's ruling (options in the doc). `sciti estimate` constants corrected to measured values (4,000 in / 800 out tokens, 2.1 calls per LLM agent-quarter); it now says $7.26 for this config. The folder `runs/mvp_llm_s1_20260918T191706Z` is a 2-second auth-failure run (all fallbacks, $0); ignore it.

**Suppliers follow partners (2026-09-18, Kevin's ruling A on the E5 side effect):** a `rules_roles` agent now also accepts a group invitation when its one-time share + 52 weeks of running cost ≤ `decision.follow_revenue_share` (default 0.01) × yearly revenue (4 × last quarter) and the share fits its budget; reason logged as "small cost; going along with partners". The flag travels in the brief (`rules.follow_revenue_share`, only for those roles), so plain rules runs and fallbacks are unchanged (goldens unchanged). 212 tests pass. Free check (policy rules + `rules_roles: [Supplier]`, seed 1): suppliers accepted all 570 invitations, 2 control tower chains + 4 blockchain chains formed, gain +$632M vs +$363M plain rules. At 1% nothing is ever declined; tune the share if suppliers should be choosier. Not yet tried with LLM agents.

## 8. Known risks to watch during the build

- **Engine tuning:** the baseline inventory policy may give a low fill rate on real data (Task 10 calibration). If so, debug the policy; don't lower the bar.
- **Plan code is unrun.** The plan's code was written carefully but never executed. Expect small fixes. Follow TDD, and note deviations in commit messages.
- **Tech effects are placeholders.** Research use needs cited effect sizes (§6 of the spec).
- **LLM replication** comes from the decision log plus `sciti replay`, not from the model itself.
