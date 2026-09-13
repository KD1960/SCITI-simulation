"""Simulation state (spec §5.3)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np

from sciti.engine.economics import price_table, propagate, sell_price
from sciti.network import PRODUCTS
from sciti.tech.effects import base_params

LEDGER_KEYS = ("revenue", "purchases", "shipping", "holding", "stockout", "handling", "tech", "cogs", "scrap")
PROFIT_COST_KEYS = ("purchases", "shipping", "holding", "stockout", "handling", "tech", "cogs")
COUNT_KEYS = ("demand", "sales", "lost", "orders_placed", "shipped", "received", "built", "shrink",
              "defects_caught", "defects_escaped")
LANE_OF = {"CM": "cm_mfg", "MFG": "mfg_dc", "DC": "dc_retail"}


class StockError(Exception):
    pass


def input_key(role: str, item: str) -> str:
    return f"RAW:{item}" if role == "CM" else item


def output_items(net, node_id: str) -> list[str]:
    node = net.nodes[node_id]
    return list(node.skus) if node.role in ("Supplier", "CM") else list(PRODUCTS)


def lane_type(src_role: str) -> str:
    return LANE_OF[src_role]


@dataclass
class Shipment:
    id: int
    src: str
    dst: str
    item: str
    units: float
    mode: str
    ship_week: int
    due_week: int
    arrive_week: int
    lead_days: float
    miles: float
    cost: float
    co2: float
    value: float
    defective: float = 0.0
    order_week: float = 0.0


@dataclass
class NodeState:
    id: str
    role: str
    stock: dict[str, float] = field(default_factory=dict)
    owed: dict[str, dict[str, float]] = field(default_factory=dict)
    owed_fifo: dict[str, dict[str, list[list[float]]]] = field(default_factory=dict)
    forecast: dict[str, float] = field(default_factory=dict)
    err: dict[str, float] = field(default_factory=dict)
    orders_in: dict[str, float] = field(default_factory=dict)
    capacity: dict[str, float] = field(default_factory=dict)
    cash: float = 0.0
    params: dict[str, float] = field(default_factory=dict)
    capacity_factor: float = 1.0
    extra_lead_days: float = 0.0
    z_boost: float = 0.0
    pending_tech_cost: float = 0.0
    ledger: dict[str, float] = field(default_factory=dict)
    counts: dict[str, float] = field(default_factory=dict)
    consumed: dict[str, float] = field(default_factory=dict)
    opening: dict[str, float] = field(default_factory=dict)
    delta: dict[str, float] = field(default_factory=dict)

    def add(self, item: str, qty: float) -> None:
        if qty < -1e-9:
            raise StockError(f"{self.id}: negative add {qty} of {item}")
        self.stock[item] = self.stock.get(item, 0.0) + qty
        self.delta[item] = self.delta.get(item, 0.0) + qty

    def remove(self, item: str, qty: float) -> None:
        have = self.stock.get(item, 0.0)
        if qty < -1e-9 or qty > have + 1e-6 * max(1.0, have):
            raise StockError(f"{self.id}: cannot remove {qty} of {item}, have {have}")
        self.stock[item] = max(0.0, have - qty)
        self.delta[item] = self.delta.get(item, 0.0) - (have - self.stock[item])

    def owed_total(self, item: str) -> float:
        return sum(b.get(item, 0.0) for b in self.owed.values())

    def reset_week(self) -> None:
        self.ledger = {k: 0.0 for k in LEDGER_KEYS}
        self.ledger["tech"] = self.pending_tech_cost
        self.pending_tech_cost = 0.0
        self.counts = {k: 0.0 for k in COUNT_KEYS}
        self.orders_in = {k: 0.0 for k in self.forecast}
        self.consumed = {}
        self.opening = dict(self.stock)
        self.delta = {}

    def profit(self) -> float:
        return self.ledger["revenue"] - sum(self.ledger[k] for k in PROFIT_COST_KEYS)


@dataclass
class SimState:
    cfg: object
    baseline: dict
    net: object
    catalog: dict
    streams: dict
    demand: dict
    demand_model: object
    flows: list[dict]
    prices: dict
    base: dict[str, dict[str, float]]
    nodes: dict[str, NodeState]
    lead_weeks: dict[tuple[str, str], int]
    z: float
    holdings: dict = field(default_factory=dict)
    in_transit: list[Shipment] = field(default_factory=list)
    arrived: list[Shipment] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    quality: list[float] = field(default_factory=list)
    disruption_end: dict[int, int] = field(default_factory=dict)
    next_id: int = 1
    week: int = 0


def _expected_quote_days(baseline, net, src, dst) -> float:
    role = net.nodes[src].role
    if role == "Supplier":
        return baseline["suppliers"][src]["lead_days"]
    from sciti.engine.ops import allowed_modes
    stats = baseline["lanes"][lane_type(role)]
    miles = net.miles(src, dst)
    mix = allowed_modes(stats["mode_mix"], miles)
    return sum(share * max(1.0, stats["modes"][m]["lead_a"] + stats["modes"][m]["lead_b"] * miles)
               for m, share in mix.items())


def init_state(cfg, baseline, net, demand_model, demand, catalog, streams) -> SimState:
    A = cfg.assumptions
    weeks = cfg.weeks
    flows = [propagate(net, {k: demand_model.expected(*k, w) for k in demand_model.keys})
             for w in range(1, weeks + 2)]
    yr = min(52, weeks)
    mean = {n: {i: float(np.mean([flows[w][n][i] for w in range(yr)])) for i in flows[0][n]} for n in net.order}
    prices = price_table(net, baseline, A.markup)
    base = {n: base_params(net.nodes[n].role, A) for n in net.order}
    lead_weeks: dict[tuple[str, str], int] = {}
    nodes: dict[str, NodeState] = {}
    for n in net.order:
        role = net.nodes[n].role
        ns = NodeState(id=n, role=role, params=dict(base[n]))
        outs = output_items(net, n)
        for item in outs:
            ns.forecast[item] = mean[n][item]
            ns.err[item] = 0.2 * mean[n][item]
            ns.stock[item] = A.fg_cover_weeks * mean[n][item] if role in ("Supplier", "CM", "MFG") else 0.0
        cap = A.capacity_mult
        if role == "Supplier":
            ns.capacity = {outs[0]: cap["Supplier"] * mean[n][outs[0]]}
        elif role == "CM":
            ns.capacity = {sku: cap["CM"] * mean[n][sku] for sku in outs}
        elif role == "MFG":
            ns.capacity = {"BUILD": cap["MFG"] * sum(mean[n][p] for p in PRODUCTS)}
        if role != "Supplier":
            needs = list(net.bom) if role == "MFG" else outs
            for item in needs:
                srcs = [net.cm_of[item]] if role == "MFG" else (net.suppliers_of[item] if role == "CM" else net.upstream[n])
                days = float(np.mean([_expected_quote_days(baseline, net, s_, n) +
                                      base[s_]["dispatch_delay_days"] for s_ in srcs]))
                L = max(1, math.ceil(days / 7))
                lead_weeks[(n, item)] = L
                ns.stock[input_key(role, item)] = ns.stock.get(input_key(role, item), 0.0) + (L + 2) * mean[n][item]
        weekly_rev = sum(mean[n][i] * sell_price(prices, net, n, i) for i in outs)
        ns.cash = A.initial_cash_weeks * weekly_rev
        ns.reset_week()
        nodes[n] = ns
    z = NormalDist().inv_cdf(A.target_service_level)
    catch = A.inspection_catch
    q0 = 1 - float(np.mean([s["defect_share"] for s in baseline["suppliers"].values()])) * (1 - catch)
    return SimState(cfg=cfg, baseline=baseline, net=net, catalog=catalog, streams=streams, demand=demand,
                    demand_model=demand_model, flows=flows, prices=prices, base=base, nodes=nodes,
                    lead_weeks=lead_weeks, z=z, holdings={n: {} for n in net.order}, quality=[q0])
