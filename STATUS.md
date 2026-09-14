# SCITI 1 — Status

**Last updated:** 2026-09-14 (all 19 tasks done; final review fixes done)
**Phase:** MVP built, reviewed, and merged to `main` (2026-09-14). See README.md for how to use it.
**Next step:** per-shipment lane random draws (experiments report E0), then check the pilot anomalies, then tune placeholder tech costs/effects, then (with approval) the first paid LLM run.

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
- Commit messages end with `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
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

## 8. Known risks to watch during the build

- **Engine tuning:** the baseline inventory policy may give a low fill rate on real data (Task 10 calibration). If so, debug the policy; don't lower the bar.
- **Plan code is unrun.** The plan's code was written carefully but never executed. Expect small fixes. Follow TDD, and note deviations in commit messages.
- **Tech effects are placeholders.** Research use needs cited effect sizes (§6 of the spec).
- **LLM replication** comes from the decision log plus `sciti replay`, not from the model itself.
