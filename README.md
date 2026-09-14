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
- **Paired baselines share demand, not lane noise.** A `--with-baseline` pair
  (or any `llm`/`rules` run compared against a same-seed `none` run) draws
  demand from the same stream, but lead-time and shipping-mode draws come
  from one sequential stream per lane. Once the two runs' shipment counts
  diverge — because one run adopted technology and the other did not — later
  draws in that stream no longer line up between them. So a paired profit or
  cost difference includes some lane noise on top of the technology effect
  being measured, not just the technology effect in isolation.
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
