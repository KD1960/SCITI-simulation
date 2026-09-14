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
