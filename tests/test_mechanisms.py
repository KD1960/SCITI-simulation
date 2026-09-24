"""Hand-computed value tests for tech effects, costs, and outcome metrics (test audit, 2026-09-17).

Each test pins down one formula with arithmetic written into the assertion itself, not a value
copied from a run. Where a draw would make a result unpredictable (lane residuals, defect shares),
the test isolates it: a direct comparison of two otherwise-identical calls, a directly-set value,
or a patched baseline copy with the residual sd forced to zero.
"""
from __future__ import annotations

import copy
import json
import math
import statistics

import pytest

import sciti.coalitions as coalitions
import sciti.engine.ops as ops_mod
from sciti.coalitions import DecisionContext, run_decision_round
from sciti.config import Assumptions, Disruption
from sciti.decide.briefs import make_personas
from sciti.decide.mock import MockPolicy
from sciti.disruptions import apply_disruptions
from sciti.engine.adoption import adopt
from sciti.engine.economics import unit_value
from sciti.engine.ops import (_backlog_in_input_units, _close_week, _needs, _production,
                              _retail_sales, make_shipment, order_up_to)
from sciti.engine.state import PROFIT_COST_KEYS, Shipment, input_key
from sciti.metrics import summarize
from sciti.network import build_network
from sciti.tech.catalog import DEFAULT_PATH, TechHolding, load_catalog
from sciti.tech.effects import base_params, effective_params
from tests.helpers import make_state

CATALOG_V1 = DEFAULT_PATH.with_name("catalog_v1.yaml")


def test_rfid_cuts_record_error_and_shrink(baseline):
    """RFID (solo): record_error_sd *0.2, shrink_rate *0.8; the weekly shrink count is
    opening stock times the resulting rate (0.002*0.8 = 0.0016/week)."""
    s = make_state(baseline)
    adopt(s, "DC_Houston", "rfid", 0)  # setup_weeks=6 -> active_week=6
    params = effective_params("DC_Houston", 6, s.holdings, s.catalog, s.net, s.base["DC_Houston"])
    assert params["record_error_sd"] == pytest.approx(0.05 * 0.2)
    assert params["shrink_rate"] == pytest.approx(0.002 * 0.8)

    ns = s.nodes["DC_Houston"]
    ns.params = params
    for item in list(ns.stock):
        ns.stock[item] = 0.0
    ns.stock["A"] = 1000.0
    ns.reset_week()
    _close_week(s)
    assert ns.counts["shrink"] == pytest.approx(1000.0 * 0.0016)
    assert ns.stock["A"] == pytest.approx(1000.0 - 1000.0 * 0.0016)


def test_warehouse_robotics_cuts_handling_and_dispatch_delay(baseline):
    """Warehouse robotics (solo, DC): handling_cost_per_unit *0.8; dispatch_delay_days -0.6 shows
    up as exactly 0.6 fewer lead_days on an otherwise identical shipment.

    due_week must stay the same, because the quote always adds the BASE dispatch delay
    (s.base[src]), never the adopter's reduced one. The dc_retail lane is patched to a quote of
    exactly 5.5 days so 5.5+2.0=7.5 (2 weeks) vs a wrongly-wired 5.5+1.4=6.9 (1 week) actually
    crosses a week boundary -- with the unpatched lane (~9 vs ~10 days) both wirings round to the
    same week and the check can't fail either way."""
    patched = copy.deepcopy(baseline)
    for mode in patched["lanes"]["dc_retail"]["modes"].values():
        mode["lead_a"], mode["lead_b"], mode["lead_resid_sd"] = 5.5, 0.0, 0.0

    s = make_state(patched)
    adopt(s, "DC_Houston", "wh_robotics", 0)  # setup_weeks=16 -> active_week=16
    params = effective_params("DC_Houston", 16, s.holdings, s.catalog, s.net, s.base["DC_Houston"])
    assert params["handling_cost_per_unit"] == pytest.approx(0.5 * 0.8)
    s.nodes["DC_Houston"].params = params
    sh_with = make_shipment(s, "DC_Houston", "Retail_1", "A", 100.0, 20)

    s2 = make_state(patched)  # no robotics: default base params
    sh_without = make_shipment(s2, "DC_Houston", "Retail_1", "A", 100.0, 20)

    assert sh_without.lead_days - sh_with.lead_days == pytest.approx(0.6)
    assert sh_without.lead_days == pytest.approx(7.5) and sh_with.lead_days == pytest.approx(6.9)
    assert sh_with.due_week == 20 + math.ceil((5.5 + 2.0) / 7)  # base dispatch delay, both cases
    assert sh_with.due_week == sh_without.due_week


def test_aps_raises_capacity_mult(baseline):
    """APS (solo, CM): capacity_mult +0.08. With raw stock and target far above capacity,
    _production builds exactly capacity[sku] * 1.08 of each CM_1 part."""
    s = make_state(baseline)
    adopt(s, "CM_1", "aps", 0)  # setup_weeks=10 -> active_week=10
    params = effective_params("CM_1", 10, s.holdings, s.catalog, s.net, s.base["CM_1"])
    assert params["capacity_mult"] == pytest.approx(1.08)
    ns = s.nodes["CM_1"]
    ns.params = params
    skus = s.net.nodes["CM_1"].skus
    for sku in skus:
        ns.forecast[sku] = 1e9  # push the FG target far above capacity
    ns.reset_week()
    for sku in skus:
        ns.stock[f"RAW:{sku}"] = 1e9  # raw material never the binding constraint
    before = {sku: ns.stock.get(sku, 0.0) for sku in skus}
    _production(s)
    for sku in skus:
        built = ns.stock[sku] - before[sku]
        assert built == pytest.approx(ns.capacity[sku] * 1.08)


def test_needs_blends_forecast_and_sigma_by_ml_skill(baseline):
    """ML forecasting in _needs: forecast = (1-w)*own_forecast + w*echelon_forecast,
    sigma = 1.25 * err with no assumed cut (err itself is measured against the blended forecast),
    at forecast_skill w = 0.3."""
    s = make_state(baseline)
    ns = s.nodes["DC_Houston"]
    ns.params["forecast_skill"] = 0.3
    ns.forecast["A"] = 100.0
    ns.err["A"] = 10.0
    exp_next = {"DC_Houston": {"A": 200.0, "B": ns.forecast.get("B", 0.0), "C": ns.forecast.get("C", 0.0)}}
    results = {item: (fc, sigma) for item, _srcs, fc, sigma in _needs(s, "DC_Houston", exp_next)}
    fc_a, sigma_a = results["A"]
    assert fc_a == pytest.approx(0.7 * 100.0 + 0.3 * 200.0)
    assert sigma_a == pytest.approx(1.25 * 10.0)


def test_forecast_error_is_measured_against_the_blended_forecast(baseline):
    """With ML forecasting, err and err_end track the error of the forecast the node orders on:
    used = (1-w)*smoothed + w*expected flow for the observed week (flows[t-1]), w = 0.3."""
    s = make_state(baseline)
    t, n = 1, "DC_Houston"
    ns = s.nodes[n]
    alpha = s.cfg.assumptions.smoothing_alpha
    ns.params["forecast_skill"] = 0.3
    ns.forecast["A"], ns.err["A"], ns.orders_in["A"] = 100.0, 10.0, 170.0
    ns.fc_end["A"], ns.err_end["A"] = 100.0, 10.0
    s.flows[t - 1][n]["A"] = 200.0
    actual = ops_mod.propagate(s.net, {k: float(s.demand[k][t - 1]) for k in sorted(s.demand)})[n]["A"]
    ops_mod._forecast_and_order(s, t)
    used = 0.7 * 100.0 + 0.3 * 200.0
    assert ns.err["A"] == pytest.approx(alpha * abs(170.0 - used) + (1 - alpha) * 10.0)
    assert ns.err_end["A"] == pytest.approx(alpha * abs(actual - used) + (1 - alpha) * 10.0)
    assert ns.forecast["A"] == pytest.approx(alpha * 170.0 + (1 - alpha) * 100.0)


def test_order_position_and_split_by_source_share(baseline, monkeypatch):
    """Order quantity = order_up_to(fc, sigma, L, z, recorded + pipe + owed_to_me - backlog),
    split across sources by source_share; and MFG backlog = max(0, owed products - product
    stock) * bom[part]."""
    s = make_state(baseline)
    t = 1
    n = "DC_Houston"
    item = "A"
    ns = s.nodes[n]
    ns.params["record_error_sd"] = 0.0  # recorded stock == actual stock, no draw
    ns.stock[item] = 500.0
    srcs = sorted(s.net.source_share[n].items())  # [('MFG_China', 0.2), ('MFG_US', 0.8)]
    fc, sigma = 300.0, 20.0

    sh = Shipment(id=999, src="MFG_US", dst=n, item=item, units=50.0, mode="Air", ship_week=t - 1,
                  due_week=t + 2, arrive_week=t + 3, lead_days=5.0, miles=100.0, cost=0.0, co2=0.0,
                  value=0.0)
    s.in_transit.append(sh)  # pipeline = 50 units of A already inbound

    s.nodes["MFG_US"].owed.setdefault(n, {})["A"] = 40.0
    s.nodes["MFG_China"].owed.setdefault(n, {})["A"] = 10.0  # owed_to_me = 40 + 10 = 50
    ns.owed.setdefault("Retail_1", {})["A"] = 70.0  # backlog DC_Houston owes downstream = 70

    real_needs = ops_mod._needs

    def fake_needs(state, node, exp_next):
        if node == n:
            return [(item, srcs, fc, sigma)]
        return real_needs(state, node, exp_next)

    monkeypatch.setattr(ops_mod, "_needs", fake_needs)
    before = {src: s.nodes[src].owed[n]["A"] for src, _ in srcs}
    ops_mod._forecast_and_order(s, t)

    L = s.lead_weeks[(n, item)]
    z = s.z + ns.z_boost
    position = 500.0 + 50.0 + (40.0 + 10.0) - 70.0
    q_expected = order_up_to(fc, sigma, L, z, position)
    assert ns.counts["orders_placed"] == pytest.approx(q_expected)
    for src, share in srcs:
        placed = s.nodes[src].owed[n]["A"] - before[src]
        assert placed == pytest.approx(q_expected * share)

    # MFG backlog formula (spec §5.3 _needs / _backlog_in_input_units), checked directly.
    mfg = s.nodes["MFG_US"]
    mfg.owed.clear()
    mfg.owed["DC_Houston"] = {"A": 100.0, "B": 30.0}
    mfg.stock["A"], mfg.stock["B"], mfg.stock["C"] = 40.0, 10.0, 0.0
    part = s.net.skus[0]
    expected_backlog = max(0.0, (100.0 + 30.0) - (40.0 + 10.0 + 0.0)) * s.net.bom[part]
    assert _backlog_in_input_units(s, "MFG_US", part) == pytest.approx(expected_backlog)


def test_arrival_inspection_and_holding_and_stockout_costs(baseline):
    """A 100-unit shipment with 10 defective, inspection_catch 0.8: 92 added to raw stock,
    8 caught, scrap = 8 * (value/units). _close_week holding = stock * unit_value * 0.25/52
    (shrink zeroed to isolate it). _retail_sales stockout = lost * (retail - dc + 5)."""
    s = make_state(baseline)
    t = 5
    ns = s.nodes["CM_1"]
    ns.reset_week()
    item = s.net.nodes["CM_1"].skus[0]
    key = input_key("CM", item)
    before = ns.stock.get(key, 0.0)
    sh = Shipment(id=1, src="Supplier_1", dst="CM_1", item=item, units=100.0, mode="Supplier",
                  ship_week=t - 1, due_week=t, arrive_week=t, lead_days=10.0, miles=0.0, cost=0.0,
                  co2=0.0, value=100.0 * 20.0, defective=10.0)
    s.in_transit = [sh]
    ops_mod._arrivals(s, t)
    assert ns.stock[key] - before == pytest.approx(92.0)
    assert ns.counts["defects_caught"] == pytest.approx(8.0)
    assert ns.ledger["scrap"] == pytest.approx(8.0 * (sh.value / sh.units))

    s2 = make_state(baseline)
    ns2 = s2.nodes["CM_1"]
    ns2.params["shrink_rate"] = 0.0  # isolate holding from shrink
    for k in list(ns2.stock):
        ns2.stock[k] = 0.0
    ns2.stock[item] = 1000.0
    ns2.reset_week()
    _close_week(s2)
    uv = unit_value(s2.prices, s2.net, "CM_1", item)
    assert ns2.ledger["holding"] == pytest.approx(1000.0 * uv * (0.25 / 52))

    s3 = make_state(baseline)
    r, p = "Retail_1", "A"
    ns3 = s3.nodes[r]
    ns3.stock[p] = 10.0
    d = float(s3.demand[(r, p)][t - 1])
    ns3.reset_week()
    _retail_sales(s3, t)
    lost = d - 10.0
    assert ns3.counts["lost"] == pytest.approx(lost)
    assert ns3.ledger["stockout"] == pytest.approx(lost * (s3.prices["retail"] - s3.prices["dc"] + 5.0))


def test_summarize_satisfaction_and_bullwhip(baseline):
    """summarize(): satisfaction_index = 0.5*fill + 0.3*retail_on_time + 0.2*quality (the config
    defaults), and bullwhip for MFG = var(orders/160) / var(retail demand) over weeks 14+ only.

    Weeks 1-13 carry demand/orders that are NOT proportional to each other (a demand/order spike
    unrelated in scale to weeks 14-20), and the weeks-14-20 relationship itself isn't a constant
    multiple either. That way a wrong window -- an off-by-few slice like [10:] (pulls in the
    week 11-13 spike) or [15:] (drops weeks 14-15, a subset of a non-proportional series) -- gives
    a materially different ratio than the correct [13:], so the assertion can actually fail on a
    wrong window instead of the (window-invariant) proportional design used before."""
    s = make_state(baseline, weeks=20)

    class FakeNode:
        def __init__(self, role):
            self.role = role
            self.stock = {}  # summarize values closing stock

    s.nodes = {"Retail_1": FakeNode("Retail"), "DC_Houston": FakeNode("DC")}
    s.arrived = [
        Shipment(1, "DC_Houston", "Retail_1", "A", 10, "Air", 10, 11, 11, 3.0, 0, 0, 1.0, 0, order_week=9),
        Shipment(2, "DC_Houston", "Retail_1", "A", 10, "Air", 10, 11, 13, 5.0, 0, 0, 1.0, 0, order_week=9),
        Shipment(3, "MFG_US", "DC_Houston", "A", 10, "Air", 10, 12, 12, 4.0, 0, 0, 1.0, 0, order_week=9),
        Shipment(4, "MFG_US", "DC_Houston", "A", 10, "Air", 10, 12, 12, 4.0, 0, 0, 1.0, 0, order_week=9),
    ]
    s.quality = [1.0, 0.9, 0.95]  # summarize averages [1:] -> (0.9+0.95)/2 = 0.925

    def blank_row(week, role, **kw):
        row = dict(week=week, node="x", role=role, demand=0.0, sales=0.0, orders_placed=0.0,
                   profit=0.0, revenue=0.0)
        row.update({k: 0.0 for k in PROFIT_COST_KEYS + ("scrap",)})
        row.update(kw)
        return row

    # Weeks 1-13: a demand/orders spike, deliberately not in proportion to weeks 14-20.
    early_dem = [10.0, 20.0] * 6 + [10.0]
    early_orders_raw = [16000000.0, 1.0] * 6 + [16000000.0]
    # Weeks 14-20: the window that must be used; also not a single constant multiple within
    # itself, so a sub-window of it (e.g. [15:]) gives a different ratio than the full window.
    dem = [50.0, 150.0, 80.0, 220.0, 60.0, 180.0, 90.0]
    orders_raw = [900.0, 1400.0, 3500.0, 500.0, 2600.0, 300.0, 3100.0]

    rows = []
    for i, w in enumerate(range(1, 14)):
        d = early_dem[i]
        rows.append(blank_row(w, "Retail", demand=d, sales=0.8 * d))
        rows.append(blank_row(w, "MFG", orders_placed=early_orders_raw[i]))
    for i, w in enumerate(range(14, 21)):
        d = dem[i]
        rows.append(blank_row(w, "Retail", demand=d, sales=0.8 * d))
        rows.append(blank_row(w, "MFG", orders_placed=orders_raw[i]))

    out = summarize(s, rows)

    total_demand = sum(early_dem) + sum(dem)
    total_sales = sum(0.8 * x for x in early_dem) + sum(0.8 * x for x in dem)
    assert out["fill_rate"] == pytest.approx(0.8)
    assert out["fill_rate"] == pytest.approx(total_sales / total_demand)
    assert out["on_time_rate"] == pytest.approx(3 / 4)  # 3 of 4 arrivals on time
    assert out["retail_on_time_rate"] == pytest.approx(1 / 2)  # 1 of 2 retail arrivals on time
    assert out["quality_mean"] == pytest.approx(0.925)
    assert out["satisfaction_index"] == pytest.approx(0.5 * 0.8 + 0.3 * 0.5 + 0.2 * 0.925)

    orders_scaled = [x / 160 for x in orders_raw]  # weeks 14-20 only, matching spec's weeks[13:]
    expected_bullwhip = statistics.pvariance(orders_scaled) / statistics.pvariance(dem)
    assert out["bullwhip"]["MFG"] == pytest.approx(expected_bullwhip)


def _reply(*decisions):
    return json.dumps({"decisions": list(decisions)})


def _decision(tech, action, partners=(), group_id=None, reason="ok"):
    out = {"tech": tech, "action": action, "partners": list(partners), "reason": reason}
    if group_id:
        out["group_id"] = group_id
    return out


class _StubWriter:
    def __init__(self):
        self.records = []

    def log_decision(self, record):
        self.records.append(record)


def test_chain_acceptance_forms_at_threshold_fails_below(baseline, monkeypatch):
    """chain_accept_share = 0.6, 5 invitees: 3 acceptances (60%) forms the coalition,
    2 acceptances (40%) does not."""
    invited_pool = ["Supplier_1", "Supplier_2", "Supplier_3", "Supplier_4", "Supplier_5"]
    proposer = "CM_1"
    gid = "q2_CM_1_control_tower"

    def fake_group_members(net, holdings, catalog, prop, tech, partners):
        return sorted([prop] + invited_pool)

    def run_round(n_accept):
        s = make_state(baseline)
        s.cfg.decision.chain_accept_share = 0.6
        monkeypatch.setattr(coalitions, "group_members", fake_group_members)
        script = [{"agent": proposer, "week": 14, "pass": "proposal",
                   "replies": [_reply(_decision("control_tower", "propose_group", ["chain"]))]}]
        for n in invited_pool[:n_accept]:
            script.append({"agent": n, "week": 14, "pass": "response",
                           "replies": [_reply(_decision("control_tower", "accept_group", group_id=gid))]})
        policy = MockPolicy(script)
        personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
        writer = _StubWriter()
        ctx = DecisionContext(policy=policy, fallback=policy, writer=writer, personas=personas, recent={})
        run_decision_round(s, 14, ctx)
        return s.events

    events_3 = run_round(3)
    assert len([e for e in events_3 if e["type"] == "coalition" and e.get("id") == gid]) == 1

    events_2 = run_round(2)
    assert len([e for e in events_2 if e["type"] == "coalition" and e.get("id") == gid]) == 0
    failed = [e for e in events_2 if e["type"] == "coalition_failed" and e.get("id") == gid]
    assert len(failed) == 1 and failed[0]["reason"] == "acceptance"


def test_group_bonus_additive_and_visibility_cap(baseline):
    """Group bonus (0.25) scales an 'add' effect, and effects can differ by role: ml_forecast in a
    coalition gives forecast_skill = 0.1 * 1.25 at a store and 0.3 * 1.25 at a DC. Visibility is
    capped at 1.0, shown with the v1 catalog (visibility 1.0): a chain share of 0.8 gives exactly
    the cap (0.8*1.25=1.0) and a share of 1.0 (1.25 uncapped) is also capped. In catalog v2
    (visibility 0.6) a full chain in a coalition gives 0.6 * 1.25 = 0.75."""
    cat = load_catalog()
    net = build_network(baseline, Assumptions())
    for node, role, skill in (("Retail_1", "Retail", 0.03), ("DC_Houston", "DC", 0.3)):
        h = {node: {"ml_forecast": TechHolding("ml_forecast", 1, 1, coalition_id="c1")}}
        p = effective_params(node, 2, h, cat, net, base_params(role, Assumptions()))
        assert p["forecast_skill"] == pytest.approx(skill * 1.25)
    v2, cat = cat, load_catalog(CATALOG_V1)

    class FakeNode:
        def __init__(self, role):
            self.role = role

    class FakeNet:
        def __init__(self, downstream, roles):
            self.downstream = downstream
            self.upstream = {n: [] for n in roles}
            self.nodes = {n: FakeNode(r) for n, r in roles.items()}

        def partners(self, n):
            return sorted(set(self.upstream.get(n, [])) | set(self.downstream.get(n, [])))

    roles = {"DC_X": "DC", "R1": "Retail", "R2": "Retail", "R3": "Retail", "R4": "Retail", "R5": "Retail"}
    fake_net = FakeNet({"DC_X": ["R1", "R2", "R3", "R4", "R5"]}, roles)
    base_dc = base_params("DC", Assumptions())

    def H(coalition=None):
        return TechHolding("control_tower", 1, 1, coalition)

    holdings_08 = {"DC_X": {"control_tower": H(coalition="c1")}}
    for r in ("R1", "R2", "R3", "R4"):  # 4 of 5 active -> share 0.8
        holdings_08[r] = {"control_tower": H()}
    p_08 = effective_params("DC_X", 2, holdings_08, cat, fake_net, base_dc)
    assert p_08["visibility"] == pytest.approx(min(1.0, 0.8 * 1.25))
    assert p_08["visibility"] == pytest.approx(1.0)

    holdings_10 = {"DC_X": {"control_tower": H(coalition="c1")}}
    for r in ("R1", "R2", "R3", "R4", "R5"):  # 5 of 5 active -> share 1.0
        holdings_10[r] = {"control_tower": H()}
    p_10 = effective_params("DC_X", 2, holdings_10, cat, fake_net, base_dc)
    assert p_10["visibility"] == pytest.approx(min(1.0, 1.0 * 1.25))
    assert p_10["visibility"] == pytest.approx(1.0)
    assert effective_params("DC_X", 2, holdings_10, v2, fake_net, base_dc)["visibility"] == pytest.approx(0.6 * 1.25)


def test_disruption_extra_lead_days_shifts_lead_and_arrival(baseline):
    """A disruption's extra_lead_days=14 adds exactly 14 to lead_days (14 = 2 whole weeks,
    so the ceil(.../7) arrival week shifts by exactly 2), with the lane residual pinned to 0
    on a patched baseline copy so both calls draw the identical mode and quote."""
    patched = copy.deepcopy(baseline)
    for mode in patched["lanes"]["mfg_dc"]["modes"].values():
        mode["lead_resid_sd"] = 0.0
    t = 5

    s = make_state(patched)
    sh_base = make_shipment(s, "MFG_US", "DC_Houston", "A", 50.0, t)

    s2 = make_state(patched)
    s2.cfg.disruptions = [Disruption(target="MFG_US", start_week=t, weeks=5, extra_lead_days=14.0)]
    apply_disruptions(s2, t)
    assert s2.nodes["MFG_US"].extra_lead_days == pytest.approx(14.0)
    sh_dis = make_shipment(s2, "MFG_US", "DC_Houston", "A", 50.0, t)

    assert sh_dis.lead_days - sh_base.lead_days == pytest.approx(14.0)
    assert sh_dis.arrive_week - sh_base.arrive_week == 2


def test_inventory_cost_values_stock_at_what_the_holder_paid(baseline):
    """inventory_cost values stock on one network-wide basis, so moving stock between firms
    never changes it: supplier cost (price * supplier_cogs_share, averaged over a part's
    suppliers) plus the expected freight paid on each lane so far. Goods in transit are valued
    at the receiving node's basis (the shipper has already paid the freight)."""
    s = make_state(baseline)
    for ns in s.nodes.values():
        for item in list(ns.stock):
            ns.stock[item] = 0.0
    P, A = s.prices, s.cfg.assumptions
    sku = s.net.nodes["Supplier_1"].skus[0]
    cm = s.net.cm_of[sku]
    s.nodes["Supplier_1"].stock[sku] = 7.0
    s.nodes[cm].stock[f"RAW:{sku}"] = 3.0
    s.nodes[cm].stock[sku] = 4.0
    s.nodes["MFG_US"].stock[sku] = 6.0
    s.nodes["MFG_US"].stock["A"] = 2.0
    s.nodes["DC_Houston"].stock["A"] = 10.0
    s.nodes["Retail_1"].stock["B"] = 5.0
    sh = make_shipment(s, "DC_Houston", "Retail_1", "A", 8.0, 1)
    s.in_transit.append(sh)
    sup_cost = {k: P["supplier"][k] * A.supplier_cogs_share for k in P["supplier"]}
    part = {k: statistics.mean(sup_cost[x] for x in s.net.suppliers_of[k]) for k in s.net.skus}
    f = {lane: sum(mix * s.baseline["lanes"][lane]["modes"][m]["cost_per_unit"]
                   for m, mix in s.baseline["lanes"][lane]["mode_mix"].items())
         for lane in ("cm_mfg", "mfg_dc", "dc_retail")}
    product = sum((part[k] + f["cm_mfg"]) * u for k, u in s.net.bom.items())
    expected = (7.0 * sup_cost["Supplier_1"] + (3.0 + 4.0) * part[sku] + 6.0 * (part[sku] + f["cm_mfg"])
                + 2.0 * product + 10.0 * (product + f["mfg_dc"]) + (5.0 + 8.0) * (product + f["mfg_dc"] + f["dc_retail"]))
    assert ops_mod.inventory_cost(s) == pytest.approx(expected)
