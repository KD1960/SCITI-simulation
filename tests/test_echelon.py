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
    # Each non-retail stage adds its own one-week review period (spec §3.4).
    shanghai = 2 + 1 + (0.5 * 1 + 3 * 5) / 3.5
    assert le[("DC_Shanghai", "A")] == pytest.approx(shanghai)
    assert le[("DC_Houston", "B")] == pytest.approx(2 + 1 + 1)
    # MFG_China: DCs weighted by the share they buy from MFG_China (Houston .2, Sofia .4, Dubai .6, Shanghai .9).
    w = {d: net.source_share[d]["MFG_China"] for d in net.by_role("DC")}
    dc_le = {"DC_Houston": 4, "DC_Dubai": 4, "DC_Sofia": 4, "DC_Shanghai": shanghai}
    expected = 3 + 1 + sum(w[d] * dc_le[d] for d in w) / sum(w.values())
    assert le[("MFG_China", "SR_MCU")] == pytest.approx(expected)
    us = {d: net.source_share[d]["MFG_US"] for d in net.by_role("DC")}
    mfg_us = 3 + 1 + sum(us[d] * dc_le[d] for d in us) / sum(us.values())
    assert le[("CM_1", "SR_MCU")] == pytest.approx(4 + 1 + (mfg_us + expected) / 2)


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


def test_echelon_safety_floor_adds_installation_safety_below(baseline):
    import math

    from sciti.engine import ops
    s = make_state(baseline)
    for t in range(1, 6):
        ops.step_week(s, t)
    net, exp_next, z = s.net, s.flows[6], 1.645

    def own(n, item):
        sigma = {i: sg for i, _, _, sg in ops._needs(s, n, exp_next)}[item]
        return z * sigma * math.sqrt(s.lead_weeks[(n, item)] + 1)

    dc = {(d, p): own(d, p) + sum(net.source_share[r][d] * own(r, p) for r in net.downstream[d])
          for d in net.by_role("DC") for p in "ABC"}
    assert ops._echelon_safety_floor(s, "DC_Dubai", "A", exp_next, z) == pytest.approx(dc[("DC_Dubai", "A")])
    # EPDM is 40 units per product.
    mfg_us = own("MFG_US", "EPDM") + 40 * sum(net.source_share[d]["MFG_US"] * dc[(d, p)]
                                              for d in net.by_role("DC") for p in "ABC")
    assert ops._echelon_safety_floor(s, "MFG_US", "EPDM", exp_next, z) == pytest.approx(mfg_us)
    mfg_china = own("MFG_China", "EPDM") + 40 * sum(net.source_share[d]["MFG_China"] * dc[(d, p)]
                                                    for d in net.by_role("DC") for p in "ABC")
    assert ops._echelon_safety_floor(s, "CM_3", "EPDM", exp_next, z) == pytest.approx(
        own("CM_3", "EPDM") + mfg_us + mfg_china)
