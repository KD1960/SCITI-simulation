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


def test_early_warning_recovery_mult_shortens_disruption_end(baseline):
    from sciti.config import Disruption
    from sciti.disruptions import apply_disruptions
    s = make_state(baseline, weeks=30)
    s.cfg.disruptions = [Disruption(target="CM_3", start_week=10, weeks=4, capacity_mult=0.2)]
    boosted = []
    for t in range(1, 20):
        s.nodes["MFG_US"].params["early_warning_weeks"] = 2.5
        s.nodes["CM_3"].params["recovery_mult"] = 0.5
        apply_disruptions(s, t)
        boosted.append(s.nodes["MFG_US"].z_boost == 1.0)
    on = [t for t, b in zip(range(1, 20), boosted) if b]
    # disruption_end = 10 + ceil(4 * 0.5) = 12; warning from week 7 (ceil 2.5 = 3 weeks ahead) through week 11
    assert on == list(range(7, 12))
