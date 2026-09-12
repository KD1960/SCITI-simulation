# SCITI 1 — Design Spec

**Project:** SCITI 1 (Supply Chain Innovation — Technology & Interaction simulator, version 1)
**Date:** 2026-09-12
**Status:** Design approved in brainstorming; awaiting spec review
**Location:** `~/Claude/Projects/SCITI simulation/`

---

## 1. Purpose

SCITI 1 is an agent-based simulation of the Ridge Line supply chain in which each node is an agent that can adopt supply chain technologies — alone or together with partners (dyads, triads, chains, the whole network). The goal is to see how innovation, and who innovates with whom, changes economic outcomes and customer satisfaction.

This spec covers a **minimum viable product (MVP)**. It is built from the start for two later uses:

- **(a) Formal research tool** — replicable runs, full provenance, batch experiments, clean output tables.
- **(b) Education and training** — an animated replay that students and practitioners can watch and question.

## 2. Sources

| Source | Path | Used for |
|---|---|---|
| Ridge Line overview | `~/Docs/School/LE/SCM and AI Oct2026 workshop/RidgeLine_SupplyChain_Overview.docx` | Network structure, BOM, node roles, store demand scales |
| Master data set | `~/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx` | Baseline parameters (sheets below) |
| Technology list | `~/Claude/Projects/Supply chain innovation/output/technologies-2026-Q2.pdf` | Candidate technologies (Observatory lexicon v10, 48 entries) |

Workbook sheets:

- `Glossary` — BOM (product → component → sub-component → units).
- `Supplier Data` — supplier transactions: sub-component, supplier, CM, lead time, unit price, order qty, feedback text, sentiment score (1–3). The sheet is 500,000 rows but mostly `#N/A`; the loader keeps only valid rows.
- `Shipment_CM_MFG_DC_Retailers` — three side-by-side shipment tables (CM→MFG, MFG→DC, DC→Retailer): mode, distance, lead time, quantity, cost per unit, CO2.
- `Demand_Retailer` — weekly demand for Products A, B, C at 8 retailers, 2020–2024 (5 × 52 weeks).

### 2.1 Known data conflicts and the rule for each

The loader writes every conflict it finds to a validation report (§9). Default rules:

| Conflict | Rule |
|---|---|
| Doc says `MFG_US`, shipment data says `MFG_LA` | Treat as the same node, canonical id `MFG_US` |
| Doc's retailer→DC assignment differs from DC→Retailer shipment rows (e.g., Shanghai → São Paulo in data) | Network links follow the **document**. Lane statistics (mode mix, lead time, cost/unit, CO2/unit-mile) come from the **data**, pooled by lane type and mode, scaled by great-circle distance |
| Doc's supplier ranges per sub-component differ slightly from the BOM table (e.g., SR_MCU "Suppliers 1–6" vs "1–3") | Use the BOM table (Table 3): three suppliers per sub-component |
| A supplier or lane has too few valid rows to estimate a parameter | Fall back to the pooled value for its material family / lane type; flag in the report |

## 3. Scope

### In the MVP

- 48 agents: 30 suppliers, 4 component manufacturers (CMs), 2 manufacturers (MFGs), 4 distribution centers (DCs), 8 retailers.
- Weekly time step, 156-week (3-year) horizon starting the week after the last data week.
- Future demand generated from the 2020–2024 baseline.
- 8 technologies (§6).
- LLM-driven agent adoption decisions, quarterly, with coalition formation (§7).
- Optional disruptions from config.
- Replay web view: world map + dashboard (§10).
- Batch runs across seeds with one tidy results table.
- Safeguards (§9) and tests (§11).

### Not in the MVP

- The other 40 technologies (the catalog format allows adding them without code changes).
- Learning (reinforcement-learning) agents; the decision interface allows adding them later.
- Live streaming of a running simulation into the browser (the view replays saved runs).
- Price competition, new entrants, supplier exit, or network redesign.
- A GUI for editing configs.

## 4. Architecture

Python 3.13 engine plus a static browser view. No simulation framework (e.g., Mesa): a small custom loop with a fixed, documented update order is easier to replicate and audit.

```
sciti/
  data/loader.py        # Excel → baseline.json (+ validation report)
  data/demand.py        # baseline → future demand paths
  network.py            # nodes, links, BOM, lanes
  agents/base.py        # weekly ops: receive, sell/build, order, ship
  agents/roles.py       # Supplier, CM, Manufacturer, DC, Retailer
  tech/catalog.yaml     # technology definitions (data, not code)
  tech/effects.py       # apply adopted-tech effects to agent parameters
  decide/interface.py   # DecisionPolicy protocol
  decide/llm.py         # Claude-backed policy
  decide/rules.py       # rule-based fallback policy
  decide/replay.py      # replays logged decisions
  decide/mock.py        # deterministic fake for tests
  coalitions.py         # proposal/response rounds, cost sharing
  disruptions.py        # scheduled capacity / lane shocks
  checks.py             # invariants and sanity checks
  runner.py             # one run: loop, logging, manifest
  batch.py              # many runs → results.csv
  cli.py                # `sciti` command
view/
  index.html, app.js, style.css
  world-110m.json       # bundled Natural Earth outline (public domain), no network needed
configs/
  baseline.yaml         # no innovation
  mvp_llm.yaml          # LLM agents decide
  classroom_*.yaml      # teaching presets
tests/
runs/                   # outputs (git-ignored)
```

Each unit has one job and a narrow interface. The engine never imports the view; the view reads only run output files.

### 4.1 Command line

```
sciti prepare            # read Excel once → data/baseline.json + validation report
sciti run CONFIG         # one run → runs/<run_id>/
sciti batch CONFIG --seeds 1-30
sciti replay RUN_DIR     # re-run using logged decisions; must match original outputs
sciti view RUN_DIR       # serve the web view for a run on localhost
sciti estimate CONFIG    # estimated LLM calls and spend, no calls made
```

### 4.2 Run modes (the `decision.policy` config value)

| Mode | Who decides | Repeatable? | Use |
|---|---|---|---|
| `llm` | Claude | Via the decision log | Main MVP mode |
| `rules` | Rule-based policy | Exactly, from seed | Fallback, baseline comparisons, cheap sweeps |
| `replay` | Logged decisions from a prior run | Exactly | Replication, teaching |
| `mock` | Scripted fake | Exactly | Tests |
| `none` | No adoption | Exactly | No-innovation baseline |

## 5. The supply chain model

### 5.1 Network

- **Suppliers 1–30** each supply one sub-component to one CM (BOM Table 3; three suppliers per sub-component).
- **CMs** convert raw material to sub-components (1:1 units) and ship to **both** MFGs.
- **MFGs** assemble Products A, B, C. All share one BOM: 160 sub-component units per product (SR_MCU 10, SR_MOS_KIT 10, AL_Sheet 5, HSS_Coil 5, PP_Resin 15, Poly_F_EU 15, EPDM 40, NR_201 40, LGS_4_W 10, TGP_5_Q 10). A product is built only when all parts are on hand.
- **MFGs** ship to all four DCs.
- **DCs** ship to retailers per the document (Houston → Columbus, São Paulo; Dubai → Barcelona, Nairobi, Mumbai; Sofia → Barcelona; Shanghai → Mumbai, Singapore, Tokyo, Melbourne). Retailers with two DCs split orders by a config share (default 50/50).
- **Retailers** face customer demand.

Node coordinates are the document's cities (supplier coordinates: placed near their CM by family, marked as illustrative).

### 5.2 Future demand

Per retailer × product, fitted on 2020–2024 weekly data:

- Multiplicative model: `demand_t = level × (1 + trend)^t × season[week_of_year] × noise_t`
- `trend`: annual growth from a log-linear fit, capped at ±15% per year (config).
- `season`: 52 weekly indices averaged over years, normalized to mean 1.
- `noise`: lognormal with the fitted residual SD; optional AR(1) term if residual autocorrelation > 0.2.
- Values are rounded to whole units and floored at 0.
- A config `demand.scenario` can multiply growth (e.g., `high`, `low`) for experiments.

Each run draws demand from a seeded random stream separate from all other randomness, so a tech experiment and its no-tech baseline see **identical demand** (common random numbers).

### 5.3 Weekly operations (fixed order)

Every week `t`:

1. **Disruptions** update node capacity and lane lead times.
2. **Arrivals**: shipments due this week are added to receivers' stock.
3. **Retail sales**: retailers sell `min(stock, demand)`. Unmet demand is lost (config: `backorder: false`) and recorded.
4. **Production**: MFGs build up to capacity and parts on hand; CMs convert raw material up to capacity.
5. **Forecast**: each node updates its demand forecast (exponential smoothing on the orders it receives; retailers on sales).
6. **Ordering**: periodic-review order-up-to policy. `S = forecast × (lead_time + 1) + z × σ_forecast × sqrt(lead_time + 1)`; order `max(0, S − inventory_position)`. `z` from a target cycle service level (default 95%).
7. **Shipping**: upstream nodes fill orders from stock (proportional rationing if short), choose a mode by the lane's historic mode mix, and create shipments with lead time, cost, and CO2.
8. **Quality**: each supplier lot fails with a probability from that supplier's share of sentiment-1 feedback; failed units are scrapped at the receiving CM.
9. **Tech effects** already in force are applied to the parameters above (§6).
10. **Accounting and checks** (§8, §9).

Nodes are processed downstream to upstream in steps 3–6 and upstream to downstream in step 7, in a fixed id order. No step depends on dict or set iteration order.

### 5.4 Economics

Per node, per week:

- **Revenue:** units shipped × transfer price (retailers: units sold × retail price).
- **Costs:** purchases, shipping (paid by the receiver), holding (annual rate × unit value / 52), stockout penalty (retailers: lost margin + goodwill penalty), scrap, technology (one-time and running).
- **Cash:** cumulative profit; feeds the agent's budget for tech decisions.

Unit prices for sub-components come from `Supplier Data`. Transfer prices up the chain and retail prices are **not** in the data; they are set in config as cost-plus markups (defaults: CM +20%, MFG +25%, DC +10%, retail +40%) and labeled as assumptions in every output.

### 5.5 Outcome measures

| Group | Measure | Definition |
|---|---|---|
| Economic | Profit | By node, tier, and network |
| | Total cost | By cost type |
| | Tech ROI / payback | Discounted gain vs. same-seed no-tech baseline |
| Customer | Fill rate | Units sold ÷ units demanded (retailers) |
| | On-time delivery | Share of shipments arriving within quoted lead time |
| | Delivery lead time | Mean and 95th percentile, order to arrival |
| | Quality | Share of good units (maps to sentiment score) |
| | Customer satisfaction index | Weighted mean of fill rate, on-time, quality (default weights 0.5, 0.3, 0.2; config) |
| Other | CO2 | kg by lane and mode |
| | Bullwhip ratio | Variance of orders ÷ variance of demand, per tier |
| Innovation | Adoption | Who adopted what, when, alone or in which coalition |

## 6. Technology catalog

Technologies are rows in `tech/catalog.yaml`. Each entry has:

- `id`, `name`, `observatory_name` (link to the lexicon)
- `eligible_roles`
- `cost_one_time`, `cost_per_week` (scaled by node size)
- `setup_weeks` (delay before effects start)
- `effects`: list of `{parameter, change}` (e.g., `forecast_error_sd: ×0.7`)
- `network_requirement`: `solo` (works alone), `pair` (needs the linked partner to adopt), or `chain` (grows with the share of the connected chain that adopts)
- `group_bonus`: extra effect when adopted in a coalition
- `evidence`: source note, and `assumption: true` until backed by a citation

MVP catalog (default effect sizes; all marked `assumption: true`):

| id | Technology | Eligible | Main effect (default) | Network |
|---|---|---|---|---|
| `ml_forecast` | ML demand forecasting | Retailer, DC, MFG | Forecast error SD ×0.7 | solo |
| `control_tower` | Supply chain control towers | All | Upstream sees downstream sales, not just orders; bullwhip damped | chain |
| `rfid` | Item-level RFID | CM, MFG, DC, Retailer | Inventory record error 5% → 1%; shrink −50% | solo |
| `aps` | Advanced planning and scheduling | CM, MFG | Effective capacity +8%; late builds −30% | solo |
| `routing` | Vehicle routing and path optimization | CM, MFG, DC | Shipping cost −8%; CO2 −10% on its outbound lanes | solo |
| `wh_robotics` | Warehouse robotics | DC | Handling cost −20%; dispatch delay −1 day | solo |
| `blockchain` | Blockchain traceability | Supplier, CM, MFG | Defect escapes −40% | pair |
| `risk_intel` | Supply chain risk intelligence | CM, MFG, DC | Disruption recovery time −40%; early warning of 2 weeks | solo |

Adding one of the remaining 40 technologies means adding a catalog row and, only if it needs a new parameter, one effect handler.

## 7. Agent decisions (LLM)

### 7.1 When

At the start of each quarter (weeks 1, 14, 27, …; 12 rounds per run). Operational decisions (ordering, shipping) stay rule-based every week; the LLM decides only about technology and partnering.

### 7.2 What an agent sees

A short, structured brief, built only from information that node could plausibly have:

- Its role, location, and a persona drawn from a seeded distribution: risk attitude (cautious / balanced / bold), budget rule (max share of cash for tech), planning horizon.
- Last quarter: revenue, costs by type, profit, cash, fill rate or on-time rate, stockouts, scrap, CO2.
- Its current technologies and time since adoption.
- Direct partners (one tier up and down): which technologies they have, and any group proposals sent to it.
- The catalog entries it is eligible for: cost, setup time, stated effects, network requirement.
- Network-wide adoption counts (not individual firms' finances), if `visibility: network` in config.

No agent sees the simulation's future demand, other nodes' private finances, or the baseline run.

### 7.3 What an agent may do

The reply must be JSON matching this schema (validated):

```json
{
  "decisions": [
    {
      "tech": "ml_forecast",
      "action": "adopt | skip | propose_group | accept_group | decline_group | drop",
      "partners": ["DC_Houston", "MFG_US"],
      "reason": "max 40 words"
    }
  ]
}
```

Rules enforced in code, not trusted to the model:

- `tech` must be in the catalog and eligible for the role.
- `partners` must be direct partners, or `"chain"` / `"network"` for group proposals.
- Spend cannot exceed the agent's budget rule; over-budget adopts are rejected and logged.
- `drop` ends running costs; one-time cost is sunk.
- At most one new adoption per agent per quarter (config).

### 7.4 Coalitions (alone → dyad → triad → chain → network)

Each quarter runs two passes:

1. **Proposal pass:** all agents reply; `adopt` (solo) and `propose_group` actions are collected.
2. **Response pass:** agents who received proposals get a second brief listing them and reply `accept_group` / `decline_group`.

A coalition forms if every named partner accepts (for `pair`) or at least a config share accepts (default 60%, for `chain` / `network`). Members share the one-time cost equally (config: `equal` or `by_size`) and receive `group_bonus`. Coalition size and type (dyad, triad, chain, network) are recorded.

**Experiment control:** the config may also force starting adopters or coalitions (e.g., "the Shanghai chain adopts `control_tower` in week 1") so researchers can test fixed structures while the rest of the agents decide.

### 7.5 Model and calls

- Model is a config value (`decision.model`); no model id is hard-coded.
- Calls per run ≈ 48 agents × 12 quarters × (1 proposal + response passes only for agents with proposals). `sciti estimate` reports the expected count and spend before any call.
- Prompts are versioned files (`decide/prompts/v1_*.md`); the prompt version is recorded in the manifest.

## 8. Outputs (per run)

`runs/<run_id>/`:

- `manifest.json` — run id, timestamp, config (full, resolved), config hash, seed, git commit and dirty flag, Python and package versions, Excel file SHA-256, baseline.json hash, catalog hash, prompt version, model id, decision policy, fallbacks used, LLM calls and spend, check results.
- `decisions.jsonl` — one line per agent decision: quarter, pass, agent, brief hash, full prompt, raw reply, parsed reply, validation result, fallback flag, tokens, latency.
- `weekly_nodes.csv` — node × week: stock, orders, shipments in/out, sales, lost sales, costs by type, revenue, profit, cash, techs active.
- `shipments.csv` — every shipment: from, to, mode, units, ship week, due week, arrival week, cost, CO2.
- `events.jsonl` — adoptions, coalitions formed/failed, disruptions, check warnings.
- `summary.json` — outcome measures (§5.5) for the run.
- `validation_report.md` — copy of the data validation report used.

Batch: `runs/batch_<id>/results.csv` — one row per run, with config factors, seed, and all summary measures, ready for R/Stata/pandas.

CSV and JSON are used (not Parquet) so students can open outputs in Excel.

## 9. Safeguards

### 9.1 Replicability

- One master seed; separate named random streams for demand, operations, quality, personas, disruptions, and rules policy.
- Manifest (§8) captures everything needed to rerun.
- `sciti replay` re-runs a finished LLM run from `decisions.jsonl` with no API calls; outputs must match byte-for-byte except timestamps. This is the replication path for published results, since LLM output is not exactly repeatable.
- Every `llm` run can be paired with a same-seed `none` baseline.

### 9.2 LLM guardrails

- Strict JSON schema; one retry with the validation error shown to the model; then the `rules` policy decides for that agent and the fallback is logged.
- Allowed actions and targets enforced in code (§7.3).
- Timeouts and exponential backoff on API errors; after a config number of consecutive failures the run switches to `rules` for the remainder and marks the manifest.
- The model's reason text is stored and shown, never executed or used to change code paths.

### 9.3 Cost control

- `sciti estimate` before any run.
- Config caps: `max_llm_calls`, `max_spend_usd`. Before each call the runner checks the running total; at the cap it switches to `rules`, logs it, and finishes the run.
- Batch runs require `--confirm-spend` when estimated spend exceeds a config threshold.

### 9.4 Simulation invariants (checked every week)

- No negative stock or negative shipments.
- Unit conservation per node: `stock_t = stock_{t-1} + arrivals − outflows − scrap`.
- BOM conservation at MFGs: parts consumed = 160 × units built (by sub-component).
- Every shipment arrives exactly once.
- Costs and prices finite and within configured bounds.

A broken invariant stops the run with the node, week, and values in the error. `checks.strict: false` downgrades to warnings for classroom use.

### 9.5 Inputs

- Config validated against a schema at load; unknown keys are errors.
- `sciti prepare` stops if a required sheet or column is missing, and writes `validation_report.md` listing row counts, dropped rows, conflicts (§2.1), and fallbacks.
- The Excel file is read-only; the engine uses `baseline.json` thereafter and checks its hash matches the Excel file.

### 9.6 Security and privacy

- The API key is read only from the `ANTHROPIC_API_KEY` environment variable; it is never written to config, logs, or manifests. Logs are scanned for key-like strings before writing.
- The view server binds to `127.0.0.1` only.
- `runs/` and `data/baseline.json` are git-ignored. Files are staged by name; never `git add -A`.

### 9.7 Honest labeling

- Every assumed parameter (tech effects, prices, markups, persona distributions) carries `assumption: true` and a source note in config/catalog; the manifest and the view list which assumptions a run used.
- The view shows a persistent "Simulation — illustrative parameters" label.

## 10. Web view (replay)

Static HTML/JS (D3 vendored into `view/vendor/`), served by `sciti view RUN_DIR`. Reads the run's output files. No network access required.

- **Map:** equirectangular world outline; 48 nodes at their locations (suppliers clustered near their CM). Shipments animate as dots along great-circle lanes; dot size ∝ units, color by mode (air, sea, road, rail).
- **Adoption:** node fill shows technologies (small multi-segment ring, one color per tech); a coalition outline links members; a brief pulse when an adoption or coalition happens.
- **Problems:** red flash for stockouts; hatched overlay on disrupted nodes/lanes.
- **Dashboard:** time-series panels for network profit, total cost, customer satisfaction index, fill rate, CO2, and adoption count; each with the same-seed no-tech baseline as a dashed line when a paired baseline run is supplied.
- **Controls:** play / pause, speed (1–20 weeks per second), week slider, tech filter, tier filter.
- **Node panel (click):** stock, costs, service, techs, coalition, and the LLM's reason text for each decision.
- **Event feed:** plain-language log ("Q3: Dist_Shanghai and MFG_China formed a dyad to adopt control_tower").

## 11. Testing

- **Unit tests** for demand generation, order-up-to logic, BOM assembly, shipping and arrival, quality scrap, each tech effect, coalition rules, budget rules, cost caps, and JSON validation.
- **Mock policy** for all decision tests; tests never call the API.
- **Golden run:** a small fixed config with `rules` policy and a fixed seed; `summary.json` must match a committed reference.
- **Replay test:** run with `mock` policy logging decisions, then `replay`; outputs must match.
- **Invariant test:** 156-week runs across 5 seeds with `checks.strict: true` must finish clean.
- **Baseline calibration:** with policy `none`, simulated retailer demand over the first 52 weeks must match the fitted 2024 annual totals within ±5% (mean over 10 seeds), and simulated lane lead times must match the data's lane means within ±10%. Failures are reported, not hidden.
- **Adversarial LLM replies** (via mock): malformed JSON, ineligible tech, over-budget adopt, unknown partner, huge reason text — each must be rejected and fall back correctly.

## 12. MVP success criteria

1. `sciti prepare` builds `baseline.json` and a validation report from the real workbook.
2. A 156-week `rules` run and a `none` baseline finish with all invariants passing.
3. A 156-week `llm` run finishes under its spend cap, with every decision logged, and `sciti replay` reproduces it exactly.
4. At least one tech run shows a measurable difference from its same-seed baseline in profit and in the customer satisfaction index (direction not prescribed).
5. The web view replays a run with moving shipments, adoption changes, coalitions, and the dashboard.
6. A 30-seed batch produces `results.csv`.
7. All tests in §11 pass.

## 13. Decisions log (from brainstorming, 2026-09-12)

| # | Decision | Chosen |
|---|---|---|
| 1 | Platform | Python engine + browser replay view |
| 2 | How agents innovate | Agents decide on their own (config may also force starting adopters for experiments) |
| 3 | Technologies in MVP | 8 of the 48 |
| 4 | Time | Weekly steps, 3-year horizon |
| 5 | Visual | World map + dashboard |
| 6 | Decision engine | LLM agents, quarterly, with logged decisions, replay, spend caps, and rule-based fallback |
