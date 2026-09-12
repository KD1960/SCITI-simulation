# SCITI 1 — Status

**Last updated:** 2026-09-12
**Phase:** Spec and plan done. No code written yet.
**Next step:** Start the build at Task 1 (Part A). First, pick how to run it (see §6).

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

## 6. Open choice before building

How to run the plan:
1. **Subagent-driven (recommended):** a fresh subagent per task, with a review between tasks. Uses `superpowers:subagent-driven-development`.
2. **Inline:** build in one thread with checkpoints. Uses `superpowers:executing-plans`.

## 7. Progress tracker

| Task | Part | Status |
|---|---|---|
| 1 Scaffold, config, RNG | A | not started |
| 2 Workbook loader | A | not started |
| 3 Demand model | A | not started |
| 4 Network builder | A | not started |
| 5 Tech catalog + effects | A | not started |
| 6 Engine core | B | not started |
| 7 Disruptions | B | not started |
| 8 Invariant checks | B | not started |
| 9 Adoption, outputs, runner, CLI | B | not started |
| 10 Golden + calibration tests | B | not started |
| 11 Decision interface, briefs, mock | C | not started |
| 12 Coalitions + decision round | C | not started |
| 13 Rules policy | C | not started |
| 14 LLM policy | C | not started |
| 15 Replay | C | not started |
| 16 Batch + estimate | C | not started |
| 17 View server + page shell | D | not started |
| 18 Map animation | D | not started |
| 19 Dashboard + final verification | D | not started |

Update this table and the "Last updated" line as each task lands.

## 8. Known risks to watch during the build

- **Engine tuning:** the baseline inventory policy may give a low fill rate on real data (Task 10 calibration). If so, debug the policy; don't lower the bar.
- **Plan code is unrun.** The plan's code was written carefully but never executed. Expect small fixes. Follow TDD, and note deviations in commit messages.
- **Tech effects are placeholders.** Research use needs cited effect sizes (§6 of the spec).
- **LLM replication** comes from the decision log plus `sciti replay`, not from the model itself.
