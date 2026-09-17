# Test-Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 6 confirmed defects from `docs/sciti2/test-audit-2026-09-17.md` and add the missing value tests, so technology effects and outcome measures are verified by hand-computed assertions.

**Architecture:** Small, targeted engine changes, each stated first as a failing test. Kevin's rulings (2026-09-17): blockchain works only when both ends of a supplier→CM shipment hold it, so factories are no longer eligible; the shipper pays freight; each supplier shipment's defective share is a random draw around the supplier's rate, keyed to the shipment; risk intelligence's early-warning boost stays on from the warning through the end of the disruption, with fractional warning weeks rounded up. Also: forced group adoptions follow `decision.cost_split`; the run summary reports scrap separately (`scrap_value`) so its `costs` add up with revenue to network profit.

**Tech Stack:** Python 3.13, numpy, pydantic, pytest (project `.venv`).

## Global Constraints

- Work from `cd "/Users/kevindooley/Claude/Projects/SCITI simulation"` (quote the path; it has a space). Branch `audit-fixes` (created by the controller; stay on it).
- `.venv/bin/python`, `.venv/bin/pytest`. Full suite: `.venv/bin/pytest -q -m "realdata or not realdata"` (185 pass before this plan; one pre-existing openpyxl warning is known).
- Stage files **by name**. Never `git add -A` or `git add .`.
- Every commit message ends with a blank line and `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
- Tests never call the Anthropic API. Don't loosen existing test thresholds.
- Reproduce before fixing: each fix starts with a failing test.
- No new randomness may shift other draws: any new random draw must come from the per-shipment generator `shipment_rng(seed, src, dst, item, week)` after the existing draws, or from a new keyed generator — never from the shared named streams.
- Golden files (`tests/golden/none_seed7_summary.json`, `tests/golden/notech_seed3_summary.json`) may be regenerated **only** in the task that intentionally changes behaviour, with the old → new values of changed fields in the commit message.
- Tests-only tasks must not change engine code. If a new test shows the code disagrees with the spec or catalog, stop and report (status DONE_WITH_CONCERNS or BLOCKED) with the numbers; don't fix it.

## File map

| File | Change | Task |
|---|---|---|
| `sciti/engine/ops.py` | freight booked to shipper at ship time; defective-share draw | 1, 2 |
| `sciti/engine/adoption.py` | forced adoption uses `cost_split` | 1 |
| `sciti/metrics.py` | `costs` = profit cost keys only; new `scrap_value` | 1 |
| `docs/sciti2/experiments/*.py` | `costs_scrap` column → `scrap_value` | 1 |
| `sciti/tech/catalog.yaml` | blockchain eligible roles: Supplier, CM | 2 |
| `sciti/config.py` | `Assumptions.defect_concentration` | 2 |
| `sciti/disruptions.py` | early warning through the disruption; rounds up | 2 |
| `tests/test_audit_fixes.py` (new) | tests for Tasks 1–2 | 1, 2 |
| `tests/test_mechanisms.py` (new) | missing value tests | 3 |
| `tests/golden/*.json` | regenerated | 1, 2 |
| spec, README, STATUS, E1/E4 docs | describe changes and affected results | 4 |

Test helpers already available: `tests/helpers.py::make_state(baseline, weeks=30, seed=1)` (synthetic baseline fixture `baseline`, real schema; see `tests/conftest.py`), `sciti.engine.ops.step_week`, `make_shipment`, `_needs`, `_forecast_and_order`, `_arrivals`, `_retail_sales`, `_production`, `_close_week`; `sciti.metrics.summarize(s, rows)` and `week_rows(s, t)`; `sciti.runner.run(cfg, run_dir=...)`; `sciti.config.Config/DecisionCfg/ForcedAdoption/Disruption/Assumptions`.

---

### Task 1: Accounting fixes (freight, forced cost split, scrap reporting)

**Files:** Modify `sciti/engine/ops.py`, `sciti/engine/adoption.py`, `sciti/metrics.py`, `docs/sciti2/experiments/control_tower_acceptance.py`, `docs/sciti2/experiments/tech_screen.py`, `docs/sciti2/experiments/who_with_whom.py`, both golden files. Create `tests/test_audit_fixes.py`.

**Interfaces:**
- Produces: summary dict key `"scrap_value"` (float); `summary["costs"]` keys are exactly `PROFIT_COST_KEYS` (`purchases, shipping, holding, stockout, handling, tech, cogs`). In `results.csv` this means column `scrap_value` replaces `costs_scrap`.
- Shipping cost of a shipment is added to the **sender's** `ledger["shipping"]` in the week it ships (in `_shipping`, next to revenue and purchases), and no longer at arrival.

- [ ] **Step 1: Write failing tests** in `tests/test_audit_fixes.py`:

```python
import json

import pytest

from sciti.config import Config, DecisionCfg, ForcedAdoption
from sciti.engine.ops import step_week
from sciti.engine.state import PROFIT_COST_KEYS
from sciti.runner import run
from tests.helpers import make_state


def test_shipper_pays_freight_in_the_week_it_ships(baseline):
    s = make_state(baseline)
    for t in range(1, 6):
        step_week(s, t)
        shipped = [sh for sh in s.in_transit + s.arrived if sh.ship_week == t]
        by_sender = {}
        for sh in shipped:
            by_sender[sh.src] = by_sender.get(sh.src, 0.0) + sh.cost
        for n, ns in s.nodes.items():
            assert ns.ledger["shipping"] == pytest.approx(by_sender.get(n, 0.0)), (t, n)


def test_forced_group_follows_cost_split_by_size(baseline_path, tmp_path):
    members = ["DC_Shanghai", "Retail_5"]
    cfg = Config(name="fs", seed=1, weeks=2, baseline_path=str(baseline_path), output_dir=str(tmp_path),
                 decision=DecisionCfg(policy="none", cost_split="by_size"),
                 forced_adoptions=[ForcedAdoption(week=1, tech="control_tower", members=members)])
    d = run(cfg, run_dir=tmp_path / "r")
    ev = [json.loads(l) for l in (d / "events.jsonl").read_text().splitlines()]
    one_time = {e["node"]: e["one_time"] for e in ev if e["type"] == "adopt"}
    assert one_time == {"DC_Shanghai": 700000, "Retail_5": 250000}


def test_summary_costs_add_up_to_network_profit(baseline_path, tmp_path):
    cfg = Config(name="sc", seed=2, weeks=26, baseline_path=str(baseline_path), output_dir=str(tmp_path))
    summary = json.loads((run(cfg, run_dir=tmp_path / "r") / "summary.json").read_text())
    assert set(summary["costs"]) == set(PROFIT_COST_KEYS)
    assert summary["revenue"] - sum(summary["costs"].values()) == pytest.approx(summary["network_profit"], rel=1e-7)  # weekly rows are rounded to cents
    assert summary["scrap_value"] > 0
```

- [ ] **Step 2: Run** `.venv/bin/pytest -q tests/test_audit_fixes.py` — expect all 3 to FAIL (freight booked at arrival to the buyer; forced split equal = 475000 each; `costs` contains `scrap`, no `scrap_value`).

- [ ] **Step 3: Implement.**
  - `sciti/engine/ops.py` `_arrivals`: delete `dst.ledger["shipping"] += sh.cost`. In `_shipping`, after `s.nodes[b].ledger["purchases"] += sh.value ...`, add `ns.ledger["shipping"] += sh.cost  # the shipper pays freight, in the week it ships`.
  - `sciti/engine/adoption.py` `apply_forced`: replace the single `share` with a per-member cost: if `s.cfg.decision.cost_split == "by_size"`, `tech.cost_one_time[s.nodes[m].role]`; otherwise the existing equal average. Pass it to `adopt(...)` for each member.
  - `sciti/metrics.py` `summarize`: `"costs": {k: tot(k) for k in PROFIT_COST_KEYS}` and add `"scrap_value": tot("scrap"),` right after `"costs"`.
  - In the three experiment scripts, replace the column name `"costs_scrap"` with `"scrap_value"`.

- [ ] **Step 4: Run** `tests/test_audit_fixes.py` → PASS. Run the full suite. The two golden tests will fail (intended). Regenerate: `SCITI_UPDATE_GOLDEN=1 .venv/bin/pytest -q tests/test_golden.py::test_golden_summary` and `SCITI_UPDATE_NOTECH_GOLDEN=1 .venv/bin/pytest -q tests/test_golden.py::test_notech_summary_unchanged`. Use `git diff tests/golden/` to list changed fields and old → new values. Physical flows (fill_rate, bullwhip, lead/transit, co2, quality) must be unchanged; if any of them changed, stop and report. Run the full suite again → all pass (expect 188).

- [ ] **Step 5: Commit** the changed files by name with message `fix: shipper pays freight, forced groups follow cost_split, summary reports scrap separately` plus a body listing the golden field changes, ending with the Co-Authored-By line.

---

### Task 2: Mechanism fixes (blockchain pairing, random defects, early warning)

**Files:** Modify `sciti/tech/catalog.yaml`, `sciti/config.py`, `sciti/engine/ops.py`, `sciti/disruptions.py`, `docs/superpowers/specs/2026-09-12-sciti-1-design.md` (§5.3 step 8, §6 blockchain and risk_intel rows), both golden files; append to `tests/test_audit_fixes.py`.

**Interfaces:**
- Produces: `Assumptions.defect_concentration: float = 50.0`. For a supplier shipment with mean defect rate `m = min(1, defect_share × defect_mult)`: `defective = 0` if `m <= 0`; `defective = q` if `m >= 1`; otherwise `defective = q × rng.beta(m × c, (1 − m) × c)` with `c = defect_concentration`, where `rng` is the same `shipment_rng` generator already used in `make_shipment`, drawn **after** the lead-time draw.
- Blockchain `eligible_roles: [Supplier, CM]`; remove the MFG entries from its `cost_one_time` and `cost_per_week`.
- Early warning: a node gets `z_boost = 1.0` in week `t` if a disruption `d` targets the node or one of its direct upstream partners and either `t < d.start_week <= t + ceil(early_warning_weeks)` or (`d` has started and `d.start_week <= t < s.disruption_end[i]`).

- [ ] **Step 1: Append failing tests** to `tests/test_audit_fixes.py`:

```python
def test_blockchain_is_for_suppliers_and_cms_only():
    from sciti.tech.catalog import load_catalog
    assert load_catalog()["blockchain"].eligible_roles == ("Supplier", "CM")


def test_blockchain_pair_cuts_supplier_defects_on_average(baseline):
    import numpy as np
    from sciti.engine.adoption import adopt
    from sciti.engine.ops import make_shipment
    from sciti.tech.effects import effective_params
    plain, paired = make_state(baseline), make_state(baseline)
    for n in ("Supplier_1", "CM_1"):
        adopt(paired, n, "blockchain", 0)
    paired.nodes["Supplier_1"].params = effective_params("Supplier_1", 20, paired.holdings, paired.catalog,
                                                         paired.net, paired.base["Supplier_1"])
    share = baseline["suppliers"]["Supplier_1"]["defect_share"]
    d0 = [make_shipment(plain, "Supplier_1", "CM_1", "SR_MCU", 1000, t).defective for t in range(1, 401)]
    d1 = [make_shipment(paired, "Supplier_1", "CM_1", "SR_MCU", 1000, t).defective for t in range(1, 401)]
    assert np.mean(d0) == pytest.approx(1000 * share, rel=0.1)
    assert np.mean(d1) == pytest.approx(1000 * share * 0.6, rel=0.1)
    assert np.std(d0) > 0  # random, not a fixed rate


def test_defect_draw_is_keyed_to_the_shipment(baseline):
    from sciti.engine.ops import make_shipment
    a, b = make_state(baseline), make_state(baseline)
    for t in (1, 2, 3):
        make_shipment(b, "Supplier_4", "CM_1", "SR_MOS_KIT", 50, t)
    x = make_shipment(a, "Supplier_1", "CM_1", "SR_MCU", 500, 7)
    y = make_shipment(b, "Supplier_1", "CM_1", "SR_MCU", 500, 7)
    assert (x.defective, x.lead_days) == (y.defective, y.lead_days)


def test_early_warning_stays_on_through_the_disruption_and_rounds_up(baseline):
    from sciti.config import Disruption
    from sciti.disruptions import apply_disruptions
    s = make_state(baseline, weeks=30)
    s.cfg.disruptions = [Disruption(target="CM_3", start_week=10, weeks=4, capacity_mult=0.2)]
    boosted = []
    for t in range(1, 20):
        s.nodes["MFG_US"].params["early_warning_weeks"] = 2.5
        s.nodes["CM_3"].params["recovery_mult"] = 1.0
        apply_disruptions(s, t)
        boosted.append(s.nodes["MFG_US"].z_boost == 1.0)
    on = [t for t, b in zip(range(1, 20), boosted) if b]
    assert on == list(range(7, 14))  # warning from week 7 (ceil 2.5 = 3 weeks ahead) through week 13
```

- [ ] **Step 2: Run** `.venv/bin/pytest -q tests/test_audit_fixes.py` — expect the 4 new tests to FAIL.

- [ ] **Step 3: Implement** per the Interfaces block. In `make_shipment`'s supplier branch, keep the lead-time draw first, then compute `defective` from the Beta draw. In `sciti/disruptions.py`, use `math.ceil` and `enumerate(s.cfg.disruptions)` so `s.disruption_end[i]` is available. Update the spec text: §5.3 step 8 ("each supplier shipment's defective share is drawn from a Beta distribution with mean = the supplier's sentiment-1 share × blockchain multiplier and concentration `defect_concentration` (default 50, an assumption), keyed to the shipment"), §6 blockchain row (eligible: Supplier, CM; "defect escapes −40% on supplier shipments when supplier and CM both hold it"), §6 risk_intel row ("early warning: extra safety stock from 2 weeks before a disruption at the node or a direct supplier through its end").

- [ ] **Step 4: Run** the new tests → PASS. Full suite: the two golden tests fail (intended); regenerate both as in Task 1 and list changed fields in the commit body. `test_echelon` and calibration tests must still pass; if any non-golden test fails, stop and report. Expect 192 passing.

- [ ] **Step 5: Commit** by name: `fix: blockchain pairs supplier and CM, random per-shipment defects, early warning through disruption`, body with golden changes, Co-Authored-By line.

---

### Task 3: Missing value tests (tests only)

**Files:** Create `tests/test_mechanisms.py`. No engine changes.

Write one test per item. Each asserts a hand-computed value on a state from `make_state(baseline)` (set params/stock directly where needed) or on a small synthetic state. Use `pytest.approx`. Where an assertion needs the defect draw, set the shipment's `defective` directly rather than relying on the random share.

1. **RFID:** with `rfid` active on `DC_Houston` (adopt at week 0, `effective_params` at week ≥ setup), `params["record_error_sd"] == 0.05 * 0.2` and `params["shrink_rate"] == 0.002 * 0.5`; after `_close_week`, `counts["shrink"]` for one item equals opening stock × 0.001 (set other items' stock to 0).
2. **Warehouse robotics:** active on `DC_Houston`: `handling_cost_per_unit == 0.5 * 0.8`; a `make_shipment` from `DC_Houston` to `Retail_1` has `lead_days` exactly 1.0 lower than the same call on a state without robotics (same seed/week), and the same `due_week`.
3. **APS:** active on `CM_1`: `capacity_mult == 1.08`; with raw stock and target both far above capacity, one `_production` call builds `capacity[sku] × 1.08` of each CM_1 part.
4. **ML forecasting in `_needs`:** set `forecast_skill = 0.3` on `DC_Houston`, `forecast["A"] = 100`, `err["A"] = 10`, and a known `exp_next["DC_Houston"]["A"] = 200`: the `DC_Houston` item `A` tuple has forecast `0.7*100 + 0.3*200` and sigma `1.25 * 10 * (1 - 0.15)`.
5. **Order position:** in a hand-built state for `DC_Houston` item `A` (known recorded stock with `record_error_sd = 0`, one in-transit shipment, known owed-to-me and backlog), the order placed equals `order_up_to(fc, sigma, L, z, recorded + pipe + owed_to_me - backlog)` split by source shares; for `MFG_US`, backlog for a part = `max(0, owed products − product stock) × bom[part]`.
6. **Arrival and costs:** a shipment of 100 units with `defective = 10` arriving at `CM_1` with `inspection_catch = 0.8` adds 92 to raw stock, `counts["defects_caught"] == 8`, `ledger["scrap"] == 8 × value/units`; `_close_week` holding for a single item = stock × unit value × 0.25/52; `_retail_sales` stockout = lost × (retail price − DC price + 5).
7. **Metrics on synthetic inputs:** build a minimal fake state object (or use `make_state`) with a controlled `arrived` list, `quality` list, and `rows` so that on-time, retail on-time, fill, quality, satisfaction = `0.5·fill + 0.3·retail_on_time + 0.2·quality`, and bullwhip (weeks 14+, MFG/CM orders ÷ 160) come out to hand-computed values.
8. **Chain acceptance threshold:** in `run_decision_round` with a mock policy, a chain proposal with 5 invitees forms when 3 accept (60%) and fails when 2 accept, with `chain_accept_share = 0.6`.
9. **Group bonus on additive effects and the visibility cap:** `ml_forecast` in a coalition gives `forecast_skill == 0.3 * 1.25`; `control_tower` in a coalition with chain share 0.8 gives `visibility == 1.0` (0.8 × 1.25 = 1.0; with share 1.0 still capped at 1.0).
10. **Extra lead days:** a disruption with `extra_lead_days = 14` on `MFG_US` makes a `make_shipment` from `MFG_US` in a disrupted week have `lead_days` exactly 14 more than the same call without the disruption, and its `arrive_week` 2 weeks later when the base lead is a whole number of weeks (choose inputs so rounding is unambiguous, e.g. set the lane residual to 0 by using a patched baseline copy).

- [ ] **Step 1:** Write the tests. **Step 2:** Run them. Any failing test is either a test mistake (fix the test) or an engine/spec disagreement — if the latter, do not change engine code; mark the test `@pytest.mark.xfail(reason="...", strict=True)` with the numbers in the reason and report DONE_WITH_CONCERNS. **Step 3:** Full suite passes. **Step 4:** Commit `tests: value tests for tech effects, costs, metrics, and coalition rules` with Co-Authored-By.

---

### Task 4: Docs and affected results

**Files:** Modify `README.md`, `STATUS.md`, `docs/sciti2/tech-screen-e1.md`, `docs/sciti2/decision-rules-e4.md`, `docs/sciti2/test-audit-2026-09-17.md`.

- [ ] README "Interpreting results": add bullets — shipper pays freight; defects are random per shipment (`assumptions.defect_concentration`); `scrap_value` is a memo item already inside purchases (not a cost column).
- [ ] At the top of `tech-screen-e1.md` and `decision-rules-e4.md`, add a boxed note: "**Engine changed 2026-09-17** (audit fixes: freight, blockchain eligibility, random defects, early warning). Numbers below come from the earlier engine; rows for routing and blockchain, and anything that depends on who pays freight, should be rerun before citing."
- [ ] In `test-audit-2026-09-17.md`, add a "Resolution" section listing each defect with the commit that fixed it and each missing test with its test name (or xfail).
- [ ] STATUS: new dated note summarizing Tasks 1–3 (tests count, xfails if any), and the `**Next step:**` line → calibration groundwork (evidence table + sensitivity screen).
- [ ] Full suite passes. Commit `docs: audit fixes and affected-results notes` with Co-Authored-By.
