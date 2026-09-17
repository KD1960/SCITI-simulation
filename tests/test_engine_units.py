import numpy as np
import pytest

from sciti.config import Assumptions
from sciti.engine.economics import price_table, propagate, sell_price, unit_value
from sciti.engine.ops import allowed_modes, build_qty, order_up_to, ration, sample_lane
from sciti.network import build_network


def test_order_up_to():
    # f=100, L=1 → (L+1)=2: 200 + 1.645*20*sqrt(2) − 150
    assert order_up_to(100, 20, 1, 1.645, 150) == pytest.approx(200 + 1.645 * 20 * 2 ** 0.5 - 150)
    assert order_up_to(100, 20, 1, 1.645, 10_000) == 0.0


def test_ration_proportional_and_capped():
    assert ration(50, {"b": 60, "a": 40}) == {"a": 20.0, "b": 30.0}
    assert ration(500, {"a": 40}) == {"a": 40.0}
    assert ration(5, {}) == {}


def test_build_limited_by_scarcest_part():
    bom = {"x": 10, "y": 40}
    assert build_qty({"x": 1000, "y": 400}, bom, capacity=1e9, target=1e9) == 10
    assert build_qty({"x": 1000, "y": 4000}, bom, capacity=5, target=1e9) == 5
    assert build_qty({"x": 1000}, bom, capacity=5, target=1e9) == 0


def test_modes_filtered_by_distance():
    mix = {"Air": 0.5, "Ship": 0.3, "Road": 0.1, "Rail": 0.1}
    assert allowed_modes(mix, 1000) == pytest.approx(mix)
    assert allowed_modes(mix, 6000) == pytest.approx({"Air": 0.625, "Ship": 0.375})


def test_sample_lane_floor_and_quote(baseline):
    stats = baseline["lanes"]["mfg_dc"]
    mode, lead, quote, cpu = sample_lane(stats, 6000, np.random.default_rng(0))
    m = stats["modes"][mode]
    assert mode in ("Air", "Ship")
    assert quote == pytest.approx(max(1.0, m["lead_a"] + m["lead_b"] * 6000))
    assert lead >= 1.0 and cpu == m["cost_per_unit"]


def test_prices_chain_markups(baseline):
    net = build_network(baseline, Assumptions())
    pr = price_table(net, baseline, Assumptions().markup)
    # f = 0.55*10 + 0.35*2.5 + 0.05*1.9 + 0.05*1.8 = 6.56, same for every lane in the synthetic baseline
    f = 6.56
    assert pr["cm"]["SR_MCU"] == pytest.approx((20 + f) * 1.2)
    assert pr["mfg"] == pytest.approx(
        (sum(pr["cm"][k] * u for k, u in net.bom.items()) + f) * 1.25)
    assert pr["dc"] == pytest.approx((pr["mfg"] + f) * 1.1)
    assert pr["retail"] == pytest.approx(pr["dc"] * 1.4)
    assert sell_price(pr, net, "DC_Dubai", "A") == pr["dc"]
    assert unit_value(pr, net, "CM_1", "RAW:SR_MCU") == pr["raw"]["SR_MCU"]
    assert unit_value(pr, net, "Retail_1", "B") == pr["dc"]


def test_propagate_conserves_units(baseline):
    net = build_network(baseline, Assumptions())
    retail = {(f"Retail_{r}", p): 100.0 for r in range(1, 9) for p in "ABC"}
    f = propagate(net, retail)
    total_products = 2400.0
    assert sum(f[d]["A"] + f[d]["B"] + f[d]["C"] for d in net.by_role("DC")) == pytest.approx(total_products)
    assert sum(f[m]["A"] + f[m]["B"] + f[m]["C"] for m in net.by_role("MFG")) == pytest.approx(total_products)
    assert sum(f[c]["EPDM"] for c in ["CM_3"]) == pytest.approx(total_products * 40)
    assert f["Supplier_19"]["EPDM"] == pytest.approx(total_products * 40 / 3)
