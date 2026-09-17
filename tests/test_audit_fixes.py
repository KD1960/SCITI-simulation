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
