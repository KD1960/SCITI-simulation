# SCITI 1

SCITI 1 is an agent-based simulation of the Ridge Line supply chain: 48 nodes
(suppliers, component makers, factories, distribution centers, and stores),
each deciding on its own whether to adopt supply chain technologies. It runs
week by week for up to three years and tracks profit, cost, service, and CO2.
A browser view replays a finished run for teaching; the CSV/JSON outputs
support research (batch experiments, paired no-tech baselines, exact replay).

## Requirements

- Python 3.13
- The Ridge Line source workbook, `Master Data Set_4.xlsx` — not part of this
  repo. `sciti prepare` needs a path to it (default:
  `~/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx`).

## Install

```
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Prepare the data

The engine never reads the Excel file directly; `sciti prepare` reads it once
and writes a git-ignored `data/baseline.json` (plus a
`data/validation_report.md` listing row counts and any dropped rows):

```
.venv/bin/sciti prepare --xlsx "/path/to/Master Data Set_4.xlsx"
```

Re-run `prepare` if the workbook changes. Everything below assumes
`data/baseline.json` already exists.

## Run a simulation

```
.venv/bin/sciti run configs/baseline.yaml               # no technology adopted (the no-tech baseline)
.venv/bin/sciti run configs/rules.yaml                   # agents decide with a transparent payback rule
.venv/bin/sciti run configs/classroom_shanghai_tower.yaml # classroom preset: forced adoption + a disruption
```

Each run writes to a new folder under `runs/` (git-ignored) and prints its
path. Add `--run-dir PATH` to choose the folder yourself.

## Batch experiments

```
.venv/bin/sciti batch configs/rules.yaml --seeds 1-30 --with-baseline
```

Runs seeds 1 through 30 and, with `--with-baseline`, a paired same-seed
`none` (no-tech) run for each one, so you can isolate the effect of the
agents' own adoption decisions. Writes `runs/batch_<name>/results.csv`, one
row per run, ready for R/Stata/pandas.

## Replay a run

```
.venv/bin/sciti replay runs/RUN_DIR
```

Re-runs a finished run from its logged decisions (`decisions.jsonl`) with no
API calls, and reports whether the outputs match byte-for-byte. This is the
way to verify or publish an LLM-driven run, since LLM output is not exactly
repeatable but the logged decisions are.

## View a run

```
.venv/bin/sciti view runs/RUN_DIR --baseline runs/BASELINE_RUN_DIR
```

Serves the replay web view on `127.0.0.1` and opens it in a browser
(`--no-open` to skip that, `--port` to change the port; `--baseline` is
optional). Use Ctrl+C to stop the server.

## LLM-driven runs

Agents can also decide with a live Claude model instead of the `rules`
policy. Before spending any money:

1. Set the model's current per-token prices in `configs/mvp_llm.yaml`
   (`decision.price_per_mtok_in` / `price_per_mtok_out`). The shipped config
   has them at zero on purpose, so it refuses to run until you set them.
2. Set `ANTHROPIC_API_KEY` in your environment.
3. Estimate calls and spend before running anything:
   ```
   .venv/bin/sciti estimate configs/mvp_llm.yaml
   ```
   It reports `usd_expected` (no retries) and `usd_with_retries` (every reply
   retried once, the rate measured in the 2026-09-16 pilot). Budget for the
   larger one.
4. Only after you've reviewed the estimate and approved the spend:
   ```
   .venv/bin/sciti run configs/mvp_llm.yaml
   ```
   The run stops on its own at `decision.max_llm_calls` or
   `decision.max_spend_usd`, whichever comes first, and falls back to the
   `rules` policy for the rest of the run.

## Interpreting results

- **Tech effects, costs, and markups are placeholder assumptions.** No
  technology in `sciti/tech/catalog.yaml` has a cited effect size yet; every
  one is marked `assumption: true`. Treat outcome differences between runs as
  illustrative, not as a validated estimate of any real technology's impact.
  Every run's manifest lists exactly which assumptions it used
  (`manifest.json` → `assumptions`), and the view shows the same list in the
  header badge's tooltip.
- **Paired baselines share demand and shipment draws.** A `--with-baseline`
  pair (or any `llm`/`rules` run compared against a same-seed `none` run)
  draws the same demand, and each shipment's lead time and mode come from
  draws keyed by its lane (sender, receiver, item) and ship week. So a
  shipment on the same lane in the same week gets the same draws in both
  runs, however their earlier shipments differed. In a 10-seed rules batch
  this cut the spread of paired profit differences to about a third of the
  baseline's seed-to-seed spread (it was 1.5 times larger before).
- **CO2 uses assumed weights.** A finished product weighs 0.05 t (from the
  workbook Glossary); each part weighs that spread over the 160 parts in a
  product (`assumptions.part_weight_tons`). The workbook itself applies 0.05 t
  to every part, which made CO2 about 75 times too high.
- **Shippers pay their own freight.** The cost of a shipment is booked to
  the sender, in the week it ships, not to the receiver. This matters when
  comparing profit by tier.
- **Defects are random, per shipment.** Each shipment's share of defective
  units is drawn at random around the supplier's average defect rate, not
  fixed. `assumptions.defect_concentration` controls how tight that spread
  is (higher = closer to the average, lower = more spread out).
- **`scrap_value` is a memo item, not a cost column.** It reports the value
  of scrapped units for reference. That value is already counted inside
  purchases, so do not add `scrap_value` to the cost columns — it would
  double-count.
- **Control tower = echelon ordering.** A node with a control tower orders for
  all stock at and below it (its share of each downstream partner's stock and
  pipeline), using an end-customer demand forecast and the lead time down to
  the stores. Partial adoption blends this with the normal order. See
  `docs/superpowers/specs/2026-09-14-control-tower-echelon-design.md` and the
  acceptance results in `docs/sciti2/control-tower-acceptance.md`.
- **Forced group adoptions get the group bonus.** A `forced_adoptions` entry
  with more than one member forms a coalition, so its members receive the
  technology's `group_bonus` (+25% by default), just like a group the agents
  form themselves. Force members in separate entries to test adoption without
  the bonus.
- **Config paths are relative to the working directory** you run `sciti`
  from, not to the config file's own location. Run commands from the project
  root (as in the examples above), or use absolute paths.

## Tests

```
.venv/bin/pytest -m "realdata or not realdata"
```

Most tests run against a synthetic baseline with the real schema and need no
external data. Tests marked `realdata` additionally need the source workbook
on disk; the marker expression above runs everything, real-data tests
included, when the workbook is available (they're skipped automatically if
it isn't set up for you).
