# Control Tower Echelon Ordering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the control tower's "swap orders for end demand" effect with echelon ordering: a node with visibility orders for all stock at and below it.

**Architecture:** A new pure module `sciti/engine/echelon.py` computes echelon stock and echelon lead time. `init_state` adds an echelon forecast per ordering node and the static echelon lead times. `_forecast_and_order` always forecasts from orders, updates the echelon forecast from propagated end demand, and blends the installation order with the echelon order by `visibility`. Nodes without a control tower behave exactly as before.

**Tech Stack:** Python 3.13, numpy, pydantic, pytest (project `.venv`).

**Spec:** `docs/superpowers/specs/2026-09-14-control-tower-echelon-design.md`

## Global Constraints

- Run everything from the project root: `cd "/Users/kevindooley/Claude/Projects/SCITI simulation"` (quote the path; it has a space).
- Python is `.venv/bin/python`; tests are `.venv/bin/pytest`. Full suite: `.venv/bin/pytest -q -m "realdata or not realdata"` (171 tests pass before this plan).
- Stage files **by name**. Never `git add -A` or `git add .`.
- Every commit message ends with a blank line and `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Tests never call the Anthropic API.
- The source Excel is read-only.
- Don't loosen any existing test threshold. Don't tune parameters to make the acceptance experiment pass; if a criterion fails, stop and report.
- Nodes with `visibility == 0` must order exactly as before (byte-identical no-tech runs).
- No randomness may be added to ordering (replay and paired runs depend on it).

## File map

| File | Responsibility | Task |
|---|---|---|
| `sciti/engine/echelon.py` (new) | `echelon_stock`, `echelon_lead_weeks` — pure functions of network/state | 1 |
| `tests/test_echelon.py` (new) | Unit tests for the module and the blended order | 1, 2 |
| `tests/test_golden.py`, `tests/golden/notech_seed3_summary.json` (new) | Locks no-tech behavior | 1 |
| `sciti/engine/state.py` | `NodeState.fc_end`, `NodeState.err_end`, `SimState.echelon_lead_weeks`, init | 2 |
| `sciti/engine/ops.py` | `_echelon_signal`, new ordering blend in `_forecast_and_order` | 2 |
| `tests/golden/none_seed7_summary.json` | Regenerated (golden config forces a control tower) | 2 |
| `docs/sciti2/experiments/control_tower_acceptance.py` (new) | Acceptance experiment | 3 |
| `docs/sciti2/control-tower-acceptance.md` (new) | Results | 3 |
| Spec `2026-09-12-sciti-1-design.md`, `README.md`, `STATUS.md` | Describe the new effect | 3 |

---

### Task 1: Lock no-tech behavior; echelon stock and lead time functions

**Files:**
- Modify: `tests/test_golden.py`
- Create: `tests/golden/notech_seed3_summary.json` (generated)
- Create: `sciti/engine/echelon.py`
- Create: `tests/test_echelon.py`

**Interfaces:**
- Consumes: `make_state(baseline, weeks=30, seed=1)` from `tests/helpers.py`; `SimState.net` (`Network` with `order`, `downstream`, `source_share`, `bom`, `nodes[n].skus`, `by_role(role)`); `NodeState.stock`, `NodeState.role`; `SimState.lead_weeks: dict[tuple[str, str], int]`; `SimState.flows[0][n]` (dict of item → float for every node).
- Produces:
  - `echelon_stock(s, n: str, item: str, pipe: dict[tuple[str, str], float], own_input: float | None = None) -> float`
  - `echelon_lead_weeks(net, lead_weeks: dict[tuple[str, str], int], mean: dict[str, dict[str, float]]) -> dict[tuple[str, str], float]` — keys for every (Retail, product), (DC, product), (MFG, part), (CM, part).

- [ ] **Step 1: Add the no-tech golden test (before any engine change)**

Append to `tests/test_golden.py`:

```python
NOTECH = Path(__file__).parent / "golden" / "notech_seed3_summary.json"


def test_notech_summary_unchanged(baseline_path, tmp_path):
    # No technology at all: control-tower changes must not move this run by a single byte.
    c = Config(name="notech", seed=3, weeks=52, baseline_path=str(baseline_path), output_dir=str(tmp_path))
    got = json.loads((run(c, run_dir=tmp_path / "n") / "summary.json").read_text())
    if os.environ.get("SCITI_UPDATE_NOTECH_GOLDEN") == "1":
        NOTECH.write_text(json.dumps(got, indent=1, sort_keys=True))
        pytest.skip("notech golden file updated")
    assert got == json.loads(NOTECH.read_text())
```

- [ ] **Step 2: Generate the no-tech golden file on the current code**

Run: `SCITI_UPDATE_NOTECH_GOLDEN=1 .venv/bin/pytest -q tests/test_golden.py::test_notech_summary_unchanged`
Expected: `1 skipped`; `tests/golden/notech_seed3_summary.json` exists.

Run: `.venv/bin/pytest -q tests/test_golden.py::test_notech_summary_unchanged`
Expected: `1 passed`.

- [ ] **Step 3: Write the failing echelon tests**

Create `tests/test_echelon.py`:

```python
import pytest

from sciti.engine.echelon import echelon_lead_weeks, echelon_stock
from tests.helpers import make_state


def zeroed(baseline):
    s = make_state(baseline)
    for ns in s.nodes.values():
        for k in ns.stock:
            ns.stock[k] = 0.0
    return s


def test_dc_echelon_stock_counts_its_share_of_each_store(baseline):
    # DC_Dubai serves Retail_3 (50/50 with DC_Sofia), Retail_4 (100%), Retail_5 (50/50 with DC_Shanghai).
    s = zeroed(baseline)
    s.nodes["DC_Dubai"].stock["A"] = 100.0
    s.nodes["Retail_3"].stock["A"] = 40.0
    s.nodes["Retail_4"].stock["A"] = 30.0
    s.nodes["Retail_5"].stock["A"] = 8.0
    pipe = {("DC_Dubai", "A"): 10.0, ("Retail_3", "A"): 20.0}
    assert echelon_stock(s, "DC_Dubai", "A", pipe) == pytest.approx(100 + 10 + 0.5 * (40 + 20) + 30 + 0.5 * 8)


def test_own_input_replaces_the_nodes_own_stock(baseline):
    s = zeroed(baseline)
    s.nodes["DC_Dubai"].stock["A"] = 100.0
    s.nodes["Retail_4"].stock["A"] = 30.0
    assert echelon_stock(s, "DC_Dubai", "A", {}, own_input=90.0) == pytest.approx(90 + 30)


def test_mfg_echelon_stock_converts_products_to_parts(baseline):
    # SR_MCU is 10 units per product; DC_Houston buys 80% from MFG_US.
    s = zeroed(baseline)
    s.nodes["MFG_US"].stock["SR_MCU"] = 500.0
    s.nodes["MFG_US"].stock["A"] = 2.0
    s.nodes["MFG_US"].stock["B"] = 1.0
    s.nodes["DC_Houston"].stock["A"] = 10.0
    pipe = {("MFG_US", "SR_MCU"): 50.0}
    share = s.net.source_share["DC_Houston"]["MFG_US"]
    assert share == pytest.approx(0.8)
    assert echelon_stock(s, "MFG_US", "SR_MCU", pipe) == pytest.approx(500 + 50 + 10 * (2 + 1 + share * 10))


def test_cm_echelon_stock_includes_raw_finished_and_both_factories(baseline):
    s = zeroed(baseline)
    s.nodes["CM_1"].stock["RAW:SR_MCU"] = 300.0
    s.nodes["CM_1"].stock["SR_MCU"] = 200.0
    s.nodes["MFG_US"].stock["SR_MCU"] = 40.0
    s.nodes["MFG_China"].stock["SR_MCU"] = 60.0
    pipe = {("CM_1", "SR_MCU"): 25.0}
    assert echelon_stock(s, "CM_1", "SR_MCU", pipe) == pytest.approx(300 + 25 + 200 + 40 + 60)


def test_echelon_lead_weeks_adds_flow_weighted_downstream_lead(baseline):
    s = make_state(baseline)
    net = s.net
    base_lead = {"Retail": 1, "DC": 2, "MFG": 3, "CM": 4}
    lead = {k: base_lead[net.nodes[k[0]].role] for k in s.lead_weeks}
    for r in ("Retail_6", "Retail_7", "Retail_8"):
        for p in "ABC":
            lead[(r, p)] = 5
    mean = {n: {i: 1.0 for i in s.flows[0][n]} for n in net.order}
    le = echelon_lead_weeks(net, lead, mean)
    # DC_Shanghai: Retail_5 has weight 0.5 (split with Dubai) and lead 1; Retail_6-8 weight 1, lead 5.
    shanghai = 2 + (0.5 * 1 + 3 * 5) / 3.5
    assert le[("DC_Shanghai", "A")] == pytest.approx(shanghai)
    assert le[("DC_Houston", "B")] == pytest.approx(2 + 1)
    # MFG_China: DCs weighted by the share they buy from MFG_China (Houston .2, Sofia .4, Dubai .6, Shanghai .9).
    w = {d: net.source_share[d]["MFG_China"] for d in net.by_role("DC")}
    dc_le = {"DC_Houston": 3, "DC_Dubai": 3, "DC_Sofia": 3, "DC_Shanghai": shanghai}
    expected = 3 + sum(w[d] * dc_le[d] for d in w) / sum(w.values())
    assert le[("MFG_China", "SR_MCU")] == pytest.approx(expected)
    us = {d: net.source_share[d]["MFG_US"] for d in net.by_role("DC")}
    mfg_us = 3 + sum(us[d] * dc_le[d] for d in us) / sum(us.values())
    assert le[("CM_1", "SR_MCU")] == pytest.approx(4 + (mfg_us + expected) / 2)
```

- [ ] **Step 4: Run to verify the tests fail**

Run: `.venv/bin/pytest -q tests/test_echelon.py`
Expected: FAIL / error with `ModuleNotFoundError: No module named 'sciti.engine.echelon'`.

- [ ] **Step 5: Implement the module**

Create `sciti/engine/echelon.py`:

```python
"""Echelon stock and lead time for control-tower ordering (spec 2026-09-14 §3.3-3.4)."""
from __future__ import annotations

from sciti.network import PRODUCTS


def echelon_stock(s, n: str, item: str, pipe: dict[tuple[str, str], float],
                  own_input: float | None = None) -> float:
    """Units of `item` at or below node `n`, on hand or in transit, in `item`'s units.
    `own_input` replaces n's own input stock (the ordering node uses its recorded value)."""
    net, ns = s.net, s.nodes[n]
    key = f"RAW:{item}" if ns.role == "CM" else item
    own = ns.stock.get(key, 0.0) if own_input is None else own_input
    total = own + pipe.get((n, item), 0.0)
    if ns.role == "Retail":
        return total
    if ns.role == "DC":
        return total + sum(net.source_share[r][n] * echelon_stock(s, r, item, pipe) for r in net.downstream[n])
    if ns.role == "MFG":
        products = sum(ns.stock.get(p, 0.0) + sum(net.source_share[d][n] * echelon_stock(s, d, p, pipe)
                                                  for d in net.downstream[n])
                       for p in PRODUCTS)
        return total + net.bom[item] * products
    if ns.role == "CM":
        return total + ns.stock.get(item, 0.0) + sum(echelon_stock(s, m, item, pipe) for m in net.downstream[n])
    raise ValueError(f"{n}: suppliers have no echelon stock")


def _weighted(pairs: list[tuple[float, float]]) -> float:
    total = sum(w for w, _ in pairs)
    return sum(w * x for w, x in pairs) / total if total > 0 else 0.0


def echelon_lead_weeks(net, lead_weeks: dict[tuple[str, str], int],
                       mean: dict[str, dict[str, float]]) -> dict[tuple[str, str], float]:
    """Own lead time plus the flow-weighted echelon lead time of the nodes below (spec §3.4)."""
    le: dict[tuple[str, str], float] = {}
    for r in net.by_role("Retail"):
        for p in PRODUCTS:
            le[(r, p)] = float(lead_weeks[(r, p)])
    for d in net.by_role("DC"):
        for p in PRODUCTS:
            le[(d, p)] = lead_weeks[(d, p)] + _weighted(
                [(net.source_share[r][d] * mean[r][p], le[(r, p)]) for r in net.downstream[d]])
    for m in net.by_role("MFG"):
        below = _weighted([(net.source_share[d][m] * mean[d][p], le[(d, p)])
                           for d in net.downstream[m] for p in PRODUCTS])
        for k in net.bom:
            le[(m, k)] = lead_weeks[(m, k)] + below
    for c in net.by_role("CM"):
        for k in net.nodes[c].skus:
            le[(c, k)] = lead_weeks[(c, k)] + _weighted([(mean[m][k], le[(m, k)]) for m in net.downstream[c]])
    return le
```

- [ ] **Step 6: Run the tests**

Run: `.venv/bin/pytest -q tests/test_echelon.py tests/test_golden.py`
Expected: all pass.

Run: `.venv/bin/pytest -q -m "realdata or not realdata"`
Expected: 177 passed (171 + 1 no-tech golden + 5 echelon tests), no failures.

- [ ] **Step 7: Commit**

```bash
git add sciti/engine/echelon.py tests/test_echelon.py tests/test_golden.py tests/golden/notech_seed3_summary.json
git commit -m "feat: echelon stock and lead time for control-tower ordering

Pure functions (spec 2026-09-14 §3.3-3.4), not yet used by the engine.
Adds a no-tech golden summary to lock behavior of runs without technology.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Echelon forecast and blended ordering in the engine

**Files:**
- Modify: `sciti/engine/state.py` (`NodeState`, `SimState`, `init_state`)
- Modify: `sciti/engine/ops.py` (`_forecast_and_order`, new `_echelon_signal`)
- Modify: `tests/test_echelon.py`
- Modify: `tests/golden/none_seed7_summary.json` (regenerated)

**Interfaces:**
- Consumes: `echelon_stock`, `echelon_lead_weeks` from Task 1; `order_up_to(forecast, sigma, lead_weeks, z, position)` in `ops.py`; `propagate` output `actual[n][item]` and `s.flows[t][n][item]`.
- Produces:
  - `NodeState.fc_end: dict[str, float]`, `NodeState.err_end: dict[str, float]` — present for DC (products), MFG (parts), CM (parts); empty for Supplier and Retail.
  - `SimState.echelon_lead_weeks: dict[tuple[str, str], float]`
  - `_echelon_signal(s, n: str, item: str, exp_next: dict) -> tuple[float, float]` (forecast, sigma)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_echelon.py`:

```python
def test_init_state_sets_echelon_forecast_and_lead(baseline):
    s = make_state(baseline)
    assert set(s.nodes["DC_Houston"].fc_end) == {"A", "B", "C"}
    assert set(s.nodes["MFG_US"].fc_end) == set(s.net.bom)
    assert set(s.nodes["CM_1"].fc_end) == set(s.net.nodes["CM_1"].skus)
    assert s.nodes["Retail_1"].fc_end == {} and s.nodes["Supplier_1"].fc_end == {}
    assert s.nodes["DC_Houston"].err_end["A"] == pytest.approx(0.2 * s.nodes["DC_Houston"].fc_end["A"])
    assert s.echelon_lead_weeks[("DC_Houston", "A")] > s.lead_weeks[("DC_Houston", "A")]
    assert s.echelon_lead_weeks[("CM_1", "SR_MCU")] > s.echelon_lead_weeks[("MFG_US", "SR_MCU")]


def test_control_tower_order_blends_installation_and_echelon(baseline):
    import copy

    from sciti.engine import ops
    s = make_state(baseline)
    for t in range(1, 6):
        ops.step_week(s, t)
    placed = {}
    for v in (0.0, 0.5, 1.0):
        c = copy.deepcopy(s)
        c.nodes["DC_Houston"].params["visibility"] = v
        before = c.nodes["DC_Houston"].counts["orders_placed"]
        ops._forecast_and_order(c, 6)
        placed[v] = c.nodes["DC_Houston"].counts["orders_placed"] - before
    assert placed[1.0] != pytest.approx(placed[0.0])
    assert placed[0.5] == pytest.approx(0.5 * (placed[0.0] + placed[1.0]))


def test_whole_network_control_tower_runs_clean_and_replays(baseline_path, tmp_path):
    import json

    from sciti.config import Config, DecisionCfg, ForcedAdoption
    from sciti.network import build_network
    from sciti.runner import replay_run, run
    cfg = Config(name="ct", seed=4, weeks=156, baseline_path=str(baseline_path), output_dir=str(tmp_path),
                 decision=DecisionCfg(policy="rules"))
    members = list(build_network(json.loads(baseline_path.read_text()), cfg.assumptions).order)
    cfg.forced_adoptions = [ForcedAdoption(week=1, tech="control_tower", members=members)]
    orig = run(cfg, run_dir=tmp_path / "orig")  # strict invariant checks raise on any violation
    assert replay_run(orig, tmp_path / "again") == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest -q tests/test_echelon.py -k "init_state or blends or whole_network"`
Expected: `test_init_state_sets_echelon_forecast_and_lead` fails with `AttributeError: 'NodeState' object has no attribute 'fc_end'`; `test_control_tower_order_blends_installation_and_echelon` fails (today `v` changes the forecast, not a blend, so the halfway assertion fails). The whole-network test may already pass; that is fine (it guards the change).

- [ ] **Step 3: Add state fields and initialization**

In `sciti/engine/state.py`:

Add the import next to the existing engine imports:

```python
from sciti.engine.echelon import echelon_lead_weeks
```

In `NodeState`, after `err: dict[str, float] = field(default_factory=dict)`:

```python
    fc_end: dict[str, float] = field(default_factory=dict)   # echelon forecast of end demand (control tower)
    err_end: dict[str, float] = field(default_factory=dict)
```

In `SimState`, after `next_id: int = 1` / `week: int = 0` (keep it among the defaulted fields):

```python
    echelon_lead_weeks: dict[tuple[str, str], float] = field(default_factory=dict)
```

In `init_state`, inside `if role != "Supplier":` → `for item in needs:`, after the line that sets `ns.stock[input_key(role, item)]`:

```python
                if role != "Retail":
                    ns.fc_end[item] = mean[n][item]
                    ns.err_end[item] = 0.2 * mean[n][item]
```

In the `return SimState(...)` call, add the argument:

```python
                    echelon_lead_weeks=echelon_lead_weeks(net, lead_weeks, mean),
```

- [ ] **Step 4: Change ordering in `ops.py`**

Add the import:

```python
from sciti.engine.echelon import echelon_stock
```

Add this function directly above `_forecast_and_order`:

```python
def _echelon_signal(s: SimState, n: str, item: str, exp_next: dict) -> tuple[float, float]:
    """Echelon forecast and sigma for one ordering item, with ML forecasting applied (spec 2026-09-14 §3.2)."""
    ns = s.nodes[n]
    w = ns.params["forecast_skill"]
    return (1 - w) * ns.fc_end[item] + w * exp_next[n][item], 1.25 * ns.err_end[item] * (1 - w / 2)
```

In `_forecast_and_order`, replace:

```python
        for item in sorted(ns.forecast):
            obs = (1 - v) * ns.orders_in[item] + v * actual[n][item]
            prev = ns.forecast[item]
            ns.err[item] = alpha * abs(obs - prev) + (1 - alpha) * ns.err[item]
            ns.forecast[item] = alpha * obs + (1 - alpha) * prev
```

with:

```python
        for item in sorted(ns.forecast):
            obs = ns.orders_in[item]
            prev = ns.forecast[item]
            ns.err[item] = alpha * abs(obs - prev) + (1 - alpha) * ns.err[item]
            ns.forecast[item] = alpha * obs + (1 - alpha) * prev
        for item in sorted(ns.fc_end):
            d, prev = actual[n][item], ns.fc_end[item]
            ns.err_end[item] = alpha * abs(d - prev) + (1 - alpha) * ns.err_end[item]
            ns.fc_end[item] = alpha * d + (1 - alpha) * prev
```

Then replace:

```python
            q = order_up_to(fc, sigma, s.lead_weeks[(n, item)], z, position)
            if q <= 0:
                continue
```

with:

```python
            q = order_up_to(fc, sigma, s.lead_weeks[(n, item)], z, position)
            if v > 0:  # control tower: blend toward ordering for the whole echelon (spec 2026-09-14 §3.5)
                fc_e, sigma_e = _echelon_signal(s, n, item, exp_next)
                ip_e = echelon_stock(s, n, item, pipe, own_input=recorded) + owed_to_me
                q = (1 - v) * q + v * order_up_to(fc_e, sigma_e, s.echelon_lead_weeks[(n, item)], z, ip_e)
            if q <= 0:
                continue
```

Leave `v = 0.0 if ns.role == "Retail" else ns.params["visibility"]` as it is.

- [ ] **Step 5: Run the new tests and the no-tech golden**

Run: `.venv/bin/pytest -q tests/test_echelon.py tests/test_golden.py::test_notech_summary_unchanged`
Expected: all pass. If `test_notech_summary_unchanged` fails, stop: a `v == 0` path changed. Find and fix it; never regenerate that file in this task.

- [ ] **Step 6: Regenerate the control-tower golden and check what moved**

Run: `SCITI_UPDATE_GOLDEN=1 .venv/bin/pytest -q tests/test_golden.py::test_golden_summary`
Expected: `1 skipped`.
Run: `git diff tests/golden/none_seed7_summary.json`
Expected: the file changed (the golden config forces a control tower on the Shanghai chain). Note the old and new `fill_rate`, `bullwhip`, `costs.holding`, and `network_profit` values from the diff for the commit message.

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/pytest -q -m "realdata or not realdata"`
Expected: 180 passed, including calibration and replay tests.

- [ ] **Step 8: Commit**

```bash
git add sciti/engine/state.py sciti/engine/ops.py tests/test_echelon.py tests/golden/none_seed7_summary.json
git commit -m "feat: control tower orders for its whole echelon

Nodes always forecast from the orders they receive. A node with visibility v
also tracks an echelon forecast of end demand and orders
(1 - v) * installation order + v * echelon order, where the echelon order
covers stock at and below it over the echelon lead time
(spec 2026-09-14). v == 0 is unchanged (no-tech golden identical).

Golden (Shanghai chain tower): <old -> new fill_rate, bullwhip, holding, profit>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Acceptance experiment, results, and docs

**Files:**
- Create: `docs/sciti2/experiments/control_tower_acceptance.py`
- Create: `docs/sciti2/control-tower-acceptance.md`
- Modify: `docs/superpowers/specs/2026-09-12-sciti-1-design.md` (§5.3 step 5, §6 `control_tower` row)
- Modify: `README.md`, `STATUS.md`

**Interfaces:**
- Consumes: `run_batch(cfg, seeds, out_dir) -> Path` (writes `out_dir/results.csv`, one row per seed, `policy` column, summary columns such as `bullwhip_DC`, `fill_rate`, `costs_holding`, `network_profit`); `Config`, `ForcedAdoption`; `build_network(baseline, assumptions)`; `data/baseline.json` (built from the real workbook).
- Produces: a Markdown table on stdout and `docs/sciti2/control-tower-acceptance.md`.

- [ ] **Step 1: Write the experiment script**

Create `docs/sciti2/experiments/control_tower_acceptance.py`:

```python
"""Control tower acceptance experiment (spec 2026-09-14 §2, §6).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/control_tower_acceptance.py OUT_DIR

Runs a no-tech batch and three forced-control-tower arms (seeds 1-10, 156 weeks, policy none)
on data/baseline.json and prints paired differences (arm - same-seed no-tech) as
mean +/- 95% CI half-width, plus the four acceptance checks.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, ForcedAdoption
from sciti.network import build_network

SEEDS = list(range(1, 11))
T_975_DF9 = 2.262  # two-sided 95% t critical value for 10 paired seeds
COLS = ["bullwhip_DC", "bullwhip_MFG", "bullwhip_CM", "fill_rate", "satisfaction_index", "costs_holding",
        "network_profit", "revenue", "costs_purchases", "costs_cogs", "costs_shipping", "costs_stockout",
        "costs_scrap", "costs_tech"]


def load(batch_dir: Path) -> pd.DataFrame:
    d = pd.read_csv(batch_dir / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {batch_dir}: {d.error.dropna().unique()}")
    return d.set_index("seed")[COLS]


def main(out: Path) -> None:
    base_cfg = Config(name="ct_base", seed=1, weeks=156, output_dir=str(out))
    net = build_network(json.loads(Path(base_cfg.baseline_path).read_text()), base_cfg.assumptions)
    arms = {
        "shanghai_chain": ["DC_Shanghai", "Retail_5", "Retail_6", "Retail_7", "Retail_8"],
        "downstream": net.by_role("DC") + net.by_role("Retail"),
        "whole_network": list(net.order),
    }
    base = load(run_batch(base_cfg, SEEDS, out / "base"))
    rows, diffs = [], {}
    for arm, members in arms.items():
        cfg = base_cfg.model_copy(update={"name": f"ct_{arm}"}, deep=True)
        cfg.forced_adoptions = [ForcedAdoption(week=1, tech="control_tower", members=members)]
        d = load(run_batch(cfg, SEEDS, out / arm)) - base
        diffs[arm] = d
        for c in COLS:
            half = T_975_DF9 * d[c].std(ddof=1) / np.sqrt(len(d))
            rows.append({"arm": arm, "measure": c, "mean": d[c].mean(), "ci_low": d[c].mean() - half,
                         "ci_high": d[c].mean() + half, "base_mean": base[c].mean()})
    table = pd.DataFrame(rows)
    print(table.to_markdown(index=False, floatfmt=".4g"))

    w = table[table.arm == "whole_network"].set_index("measure")
    bullwhip_sum = {a: (diffs[a][["bullwhip_DC", "bullwhip_MFG", "bullwhip_CM"]].sum(axis=1)).mean() for a in arms}
    checks = {
        "1 bullwhip falls at DC, MFG, CM (whole network)":
            all(w.loc[c, "mean"] < 0 for c in ("bullwhip_DC", "bullwhip_MFG", "bullwhip_CM")),
        "2 fill rate CI upper bound >= 0 (whole network)": w.loc["fill_rate", "ci_high"] >= 0,
        "3 holding cost CI lower bound <= 0 (whole network)": w.loc["costs_holding", "ci_low"] <= 0,
        "4 bullwhip reduction grows: shanghai < downstream < whole":
            bullwhip_sum["shanghai_chain"] > bullwhip_sum["downstream"] > bullwhip_sum["whole_network"],
    }
    print()
    print("| Check | Result |\n|---|---|")
    for name, ok in checks.items():
        print(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    print()
    print("Mean change in DC+MFG+CM bullwhip by arm:", {a: round(v, 2) for a, v in bullwhip_sum.items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]))
```

If `pandas.DataFrame.to_markdown` raises `ImportError` (it needs `tabulate`), replace that line with `print(table.to_string(float_format=lambda x: f"{x:.4g}"))`. Do not install packages.

- [ ] **Step 2: Rebuild data if needed and run the experiment**

Run: `ls data/baseline.json` — if missing, run `.venv/bin/sciti prepare --xlsx "/Users/kevindooley/Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"`.
Run: `.venv/bin/python docs/sciti2/experiments/control_tower_acceptance.py "$TMPDIR/ct_acceptance" | tee "$TMPDIR/ct_acceptance.txt"`
Expected: about 2–3 minutes; a results table and four PASS/FAIL lines. Use the session scratchpad directory for `$TMPDIR` if one is given.

- [ ] **Step 3: Write the results document**

Create `docs/sciti2/control-tower-acceptance.md` with:
- Date, git commit (`git rev-parse --short HEAD`), and the command used.
- The four checks with PASS/FAIL.
- The results table (whole network first), and the "before" whole-network row from spec §1 for comparison (fill −0.23 pt, profit −$62M).
- One short paragraph per arm in plain language: what changed and by how much.
- If any check FAILED: a "Stopped here" section saying which, with numbers. Do not change code or parameters to make it pass.

- [ ] **Step 4: Update the docs**

In `docs/superpowers/specs/2026-09-12-sciti-1-design.md`:
- §5.3 step 5, replace the sentence about forecasting with: `**Forecast**: each node updates its demand forecast (exponential smoothing on the orders it receives; retailers on sales). Nodes with a control tower also track an echelon forecast of end-customer demand and blend their order toward an echelon order-up-to order (see 2026-09-14-control-tower-echelon-design.md).`
- §6 table, `control_tower` row, replace the "Main effect" cell with: `Orders for its whole echelon: stock at and below it, end-customer forecast, echelon lead time; blend weight = share of downstream partners adopting`.

In `README.md`, under "Interpreting results", add a bullet:

```markdown
- **Control tower = echelon ordering.** A node with a control tower orders for
  all stock at and below it (its share of each downstream partner's stock and
  pipeline), using an end-customer demand forecast and the lead time down to
  the stores. Partial adoption blends this with the normal order. See
  `docs/superpowers/specs/2026-09-14-control-tower-echelon-design.md` and the
  acceptance results in `docs/sciti2/control-tower-acceptance.md`.
```

In `STATUS.md`:
- Replace the "**Next step:**" line with: `**Next step:** rerun the E1 technology screen on the fixed engine; then tune placeholder tech costs/effects, then (with approval) the first paid LLM run.` If any acceptance check failed, instead write: `**Next step:** Kevin reviews the failed control-tower acceptance check(s) in docs/sciti2/control-tower-acceptance.md.`
- Under the "Thread SCITI sim 2" notes, add one bullet: `- **Control tower redesign (echelon ordering) built:** plan docs/superpowers/plans/2026-09-14-control-tower-echelon.md; commits <Task 1 sha>..<Task 3 sha>; acceptance: <checks passed>/4 — <one-line summary of whole-network fill, holding, bullwhip, profit>.`

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest -q -m "realdata or not realdata"`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add docs/sciti2/experiments/control_tower_acceptance.py docs/sciti2/control-tower-acceptance.md docs/superpowers/specs/2026-09-12-sciti-1-design.md README.md STATUS.md
git commit -m "docs: control tower acceptance experiment and results

<n>/4 acceptance checks passed. Whole network vs no-tech (10 seeds):
<fill, holding, bullwhip DC/MFG/CM, profit>.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Self-review notes

- Spec §2 criteria → Task 3 script checks 1–4. Criterion 4 ("effect grows") is measured as the mean change in the sum of DC, MFG, and CM bullwhip.
- Spec §3.1–3.5 → Task 1 (stock, lead) and Task 2 (forecasts, blend, scope via `v`).
- Spec §5 tests 1–7 → Task 1 Step 1 (no-tech), Task 1 Step 3 (DC, MFG, CM stock, lead), Task 2 Step 1 (blend; whole-network strict run + replay). Test 1's "orders match" is covered by the byte-identical no-tech summary.
- Spec §6 → Task 3.
