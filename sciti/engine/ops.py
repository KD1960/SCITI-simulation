"""Weekly operations in the fixed order of spec §5.3."""
from __future__ import annotations

import math

import numpy as np

from sciti.disruptions import apply_disruptions
from sciti.engine.echelon import echelon_stock
from sciti.engine.economics import inventory_cost, propagate, sell_price, unit_value
from sciti.engine.state import Shipment, SimState, input_key, lane_type, output_items
from sciti.network import PRODUCTS
from sciti.rng import shipment_rng
from sciti.tech.effects import effective_params

SHORT_HAUL_MILES = 2500


def order_up_to(forecast: float, sigma: float, lead_weeks: float, z: float, position: float) -> float:
    L = lead_weeks + 1
    return max(0.0, forecast * L + z * sigma * math.sqrt(L) - position)


def ration(available: float, owed: dict[str, float]) -> dict[str, float]:
    total = sum(owed.values())
    if total <= 0:
        return {b: 0.0 for b in sorted(owed)}
    f = min(1.0, available / total)
    return {b: owed[b] * f for b in sorted(owed)}


def build_qty(parts: dict[str, float], bom: dict[str, int], capacity: float, target: float) -> float:
    feasible = min(parts.get(sku, 0.0) / u for sku, u in bom.items())
    return max(0.0, min(feasible, capacity, target))


def allowed_modes(mix: dict[str, float], miles: float) -> dict[str, float]:
    ok = {m: w for m, w in mix.items() if m not in ("Road", "Rail") or miles < SHORT_HAUL_MILES}
    if not ok:
        return {"Air": 1.0}
    total = sum(ok.values())
    return {m: ok[m] / total for m in sorted(ok)}


def sample_lane(stats: dict, miles: float, rng) -> tuple[str, float, float, float]:
    mix = allowed_modes(stats["mode_mix"], miles)
    names = sorted(mix)
    mode = names[int(rng.choice(len(names), p=[mix[m] for m in names]))]
    m = stats["modes"][mode]
    quote = max(1.0, m["lead_a"] + m["lead_b"] * miles)
    lead = max(1.0, quote + m["lead_resid_sd"] * float(rng.standard_normal()))
    return mode, lead, quote, m["cost_per_unit"]


def step_week(s: SimState, t: int) -> None:
    s.week = t
    for n in s.net.order:
        ns = s.nodes[n]
        ns.reset_week()
        ns.params = effective_params(n, t, s.holdings, s.catalog, s.net, s.base[n])
    apply_disruptions(s, t)
    _arrivals(s, t)
    _retail_sales(s, t)
    _production(s)
    _forecast_and_order(s, t)
    _shipping(s, t)
    _close_week(s)


def _arrivals(s: SimState, t: int) -> None:
    catch = s.cfg.assumptions.inspection_catch
    keep = []
    for sh in s.in_transit:
        if sh.arrive_week != t:
            keep.append(sh)
            continue
        dst = s.nodes[sh.dst]
        caught = sh.defective * catch
        dst.add(input_key(dst.role, sh.item), sh.units - caught)
        dst.counts["received"] += sh.units
        dst.counts["defects_caught"] += caught
        dst.counts["defects_escaped"] += sh.defective - caught
        dst.ledger["scrap"] += caught * (sh.value / sh.units if sh.units else 0.0)
        s.arrived.append(sh)
    s.in_transit = keep


def _retail_sales(s: SimState, t: int) -> None:
    A, pr = s.cfg.assumptions, s.prices
    for r in s.net.by_role("Retail"):
        ns = s.nodes[r]
        for p in PRODUCTS:
            d = float(s.demand[(r, p)][t - 1])
            sold = min(ns.stock[p], d)
            ns.remove(p, sold)
            ns.orders_in[p] = d
            ns.counts["demand"] += d
            ns.counts["sales"] += sold
            ns.counts["lost"] += d - sold
            ns.ledger["revenue"] += sold * pr["retail"]
            ns.ledger["stockout"] += (d - sold) * (pr["retail"] - pr["dc"] + A.goodwill_penalty_per_unit)


def _fg_target(ns, item, cover) -> float:
    return max(0.0, ns.forecast[item] * cover - (ns.stock[item] - ns.owed_total(item)))


def _production(s: SimState) -> None:
    A, net = s.cfg.assumptions, s.net
    for n in net.order:
        ns = s.nodes[n]
        cf = ns.capacity_factor * ns.params["capacity_mult"]
        if ns.role == "Supplier":
            sku = net.nodes[n].skus[0]
            q = min(ns.capacity[sku] * cf, _fg_target(ns, sku, A.fg_cover_weeks))
            ns.add(sku, q)
            ns.counts["built"] += q
            ns.ledger["cogs"] += q * s.prices["supplier"][n] * A.supplier_cogs_share
        elif ns.role == "CM":
            for sku in net.nodes[n].skus:
                q = min(ns.capacity[sku] * cf, ns.stock[f"RAW:{sku}"], _fg_target(ns, sku, A.fg_cover_weeks))
                ns.remove(f"RAW:{sku}", q)
                ns.add(sku, q)
                ns.counts["built"] += q
        elif ns.role == "MFG":
            targets = {p: _fg_target(ns, p, A.fg_cover_weeks) for p in PRODUCTS}
            tt = sum(targets.values())
            total = build_qty({k: ns.stock[k] for k in net.bom}, net.bom, ns.capacity["BUILD"] * cf, tt)
            for sku, u in net.bom.items():
                ns.remove(sku, total * u)
                ns.consumed[sku] = total * u
            if total > 0:
                for p in PRODUCTS:
                    ns.add(p, total * targets[p] / tt)
            ns.counts["built"] += total


def _needs(s: SimState, n: str, exp_next: dict) -> list[tuple[str, list[tuple[str, float]], float, float]]:
    """(item to order, [(source, share)], forecast, sigma) for one buyer."""
    net, ns = s.net, s.nodes[n]
    w = ns.params["forecast_skill"]
    blend = lambda item: (1 - w) * ns.forecast[item] + w * exp_next[n][item]
    sig = lambda e: 1.25 * e
    if ns.role in ("Retail", "DC"):
        srcs = sorted(net.source_share[n].items())
        return [(p, srcs, blend(p), sig(ns.err[p])) for p in PRODUCTS]
    if ns.role == "MFG":
        f_prod = sum(blend(p) for p in PRODUCTS)
        e_prod = math.sqrt(sum(ns.err[p] ** 2 for p in PRODUCTS))
        return [(sku, [(net.cm_of[sku], 1.0)], f_prod * u, sig(e_prod) * u) for sku, u in net.bom.items()]
    out = []
    for sku in net.nodes[n].skus:
        sups = net.suppliers_of[sku]
        out.append((sku, [(x, 1.0 / len(sups)) for x in sups], blend(sku), sig(ns.err[sku])))
    return out


def _backlog_in_input_units(s: SimState, n: str, item: str) -> float:
    """Net backlog a selling buyer (DC, MFG, CM) owes downstream, in units of its input `item`."""
    ns = s.nodes[n]
    if ns.role == "DC":
        return ns.owed_total(item)  # input and output share the product key
    if ns.role == "MFG":
        owed = sum(ns.owed_total(p) for p in PRODUCTS)
        stock = sum(ns.stock.get(p, 0.0) for p in PRODUCTS)
        return max(0.0, owed - stock) * s.net.bom[item]
    if ns.role == "CM":
        return max(0.0, ns.owed_total(item) - ns.stock.get(item, 0.0))
    return 0.0


def _echelon_signal(s: SimState, n: str, item: str, exp_next: dict) -> tuple[float, float]:
    """Echelon forecast and sigma for one ordering item, with ML forecasting applied (spec 2026-09-14 §3.2)."""
    ns = s.nodes[n]
    w = ns.params["forecast_skill"]
    return (1 - w) * ns.fc_end[item] + w * exp_next[n][item], 1.25 * ns.err_end[item]


def _echelon_safety_floor(s: SimState, n: str, item: str, exp_next: dict, z: float) -> float:
    """Installation safety stock at and below n, in n's input units, at n's z (spec 2026-09-14 §3.5)."""
    net, role = s.net, s.nodes[n].role
    sigma = {i: sg for i, _, _, sg in _needs(s, n, exp_next)}[item]
    own = z * sigma * math.sqrt(s.lead_weeks[(n, item)] + 1)
    if role == "Retail":
        return own
    if role == "DC":
        return own + sum(net.source_share[r][n] * _echelon_safety_floor(s, r, item, exp_next, z)
                         for r in net.downstream[n])
    if role == "MFG":
        return own + net.bom[item] * sum(net.source_share[d][n] * _echelon_safety_floor(s, d, p, exp_next, z)
                                         for d in net.downstream[n] for p in PRODUCTS)
    return own + sum(_echelon_safety_floor(s, m, item, exp_next, z) for m in net.downstream[n])


def _forecast_and_order(s: SimState, t: int) -> None:
    net, A = s.net, s.cfg.assumptions
    alpha = A.smoothing_alpha
    actual = propagate(net, {k: float(s.demand[k][t - 1]) for k in sorted(s.demand)})
    exp_next = s.flows[t]
    rng = s.streams["ops"]
    pipe: dict[tuple[str, str], float] = {}
    for sh in s.in_transit:
        pipe[(sh.dst, sh.item)] = pipe.get((sh.dst, sh.item), 0.0) + sh.units
    for n in reversed(net.order):
        ns = s.nodes[n]
        v = 0.0 if ns.role == "Retail" else ns.params["visibility"]
        w = ns.params["forecast_skill"]  # errors are measured against the blended forecast the node ordered on
        for item in sorted(ns.forecast):
            obs = ns.orders_in[item]
            prev = ns.forecast[item]
            used = (1 - w) * prev + w * s.flows[t - 1][n][item] if w > 0 else prev
            ns.err[item] = alpha * abs(obs - used) + (1 - alpha) * ns.err[item]
            ns.forecast[item] = alpha * obs + (1 - alpha) * prev
        for item in sorted(ns.fc_end):
            d, prev = actual[n][item], ns.fc_end[item]
            used = (1 - w) * prev + w * s.flows[t - 1][n][item] if w > 0 else prev
            ns.err_end[item] = alpha * abs(d - used) + (1 - alpha) * ns.err_end[item]
            ns.fc_end[item] = alpha * d + (1 - alpha) * prev
        if ns.role == "Supplier":
            continue
        z = s.z + ns.z_boost
        for item, srcs, fc, sigma in _needs(s, n, exp_next):
            key = input_key(ns.role, item)
            recorded = max(0.0, ns.stock.get(key, 0.0) * (1 + ns.params["record_error_sd"] * float(rng.standard_normal())))
            owed_to_me = sum(s.nodes[src].owed.get(n, {}).get(item, 0.0) for src, _ in srcs)
            owed_by_me = _backlog_in_input_units(s, n, item)
            position = recorded + pipe.get((n, item), 0.0) + owed_to_me - owed_by_me
            q = order_up_to(fc, sigma, s.lead_weeks[(n, item)], z, position)
            if v > 0:  # control tower: blend toward ordering for the whole echelon (spec 2026-09-14 §3.5)
                fc_e, sigma_e = _echelon_signal(s, n, item, exp_next)
                ip_e = echelon_stock(s, n, item, pipe, own_input=recorded) + owed_to_me
                horizon = s.echelon_lead_weeks[(n, item)] + 1
                safety = max(z * sigma_e * math.sqrt(horizon), _echelon_safety_floor(s, n, item, exp_next, z))
                q = (1 - v) * q + v * max(0.0, fc_e * horizon + safety - ip_e)
            if q <= 0:
                continue
            for src, share in srcs:
                seller = s.nodes[src]
                seller.owed.setdefault(n, {})
                seller.owed[n][item] = seller.owed[n].get(item, 0.0) + q * share
                seller.owed_fifo.setdefault(n, {}).setdefault(item, []).append([t, q * share])
                seller.orders_in[item] += q * share
            ns.counts["orders_placed"] += q


def make_shipment(s: SimState, src: str, dst: str, item: str, q: float, t: int,
                   order_week: float | None = None) -> Shipment:
    sn = s.nodes[src]
    P = sn.params
    miles = s.net.miles(src, dst)
    rng = shipment_rng(s.cfg.seed, src, dst, item, t)
    defective = 0.0
    if sn.role == "Supplier":
        sup = s.baseline["suppliers"][src]
        quote = sup["lead_days"]
        lead = max(1.0, quote + sup["lead_sd_days"] * float(rng.standard_normal()))
        mode, cpu, co2 = "Supplier", 0.0, 0.0
        m = min(1.0, sup["defect_share"] * P["defect_mult"])
        if m <= 0:
            defective = 0.0
        elif m >= 1:
            defective = q
        else:
            c = s.cfg.assumptions.defect_concentration
            defective = q * float(rng.beta(m * c, (1 - m) * c))
    else:
        mode, lead, quote, cpu = sample_lane(s.baseline["lanes"][lane_type(sn.role)], miles, rng)
        tons = s.baseline["co2_ton_per_unit"] if item in PRODUCTS else s.cfg.assumptions.part_weight_tons
        co2 = q * tons * miles * s.baseline["co2_factors"][mode] * P["co2_mult"]
    lead += P["dispatch_delay_days"] + sn.extra_lead_days
    quote += s.base[src]["dispatch_delay_days"]
    sh = Shipment(id=s.next_id, src=src, dst=dst, item=item, units=q, mode=mode, ship_week=t,
                  due_week=t + max(1, math.ceil(quote / 7)), arrive_week=t + max(1, math.ceil(lead / 7)),
                  lead_days=lead, miles=miles, cost=q * cpu * P["ship_cost_mult"], co2=co2,
                  value=q * sell_price(s.prices, s.net, src, item), defective=defective,
                  order_week=t if order_week is None else order_week)
    s.next_id += 1
    return sh


def _consume_fifo(ns, b: str, item: str, q: float, t: int) -> float:
    """Pop q units from the front of the buyer's order fifo; return the qty-weighted mean order week."""
    fifo = ns.owed_fifo.get(b, {}).get(item, [])
    remaining = q
    weighted = 0.0
    while remaining > 1e-9 and fifo:
        entry = fifo[0]
        take = min(entry[1], remaining)
        weighted += take * entry[0]
        entry[1] -= take
        remaining -= take
        if entry[1] <= 1e-9:
            fifo.pop(0)
    consumed = q - remaining
    return weighted / consumed if consumed > 1e-9 else float(t)


def _shipping(s: SimState, t: int) -> None:
    for n in s.net.order:
        ns = s.nodes[n]
        if ns.role == "Retail":
            continue
        for item in output_items(s.net, n):
            owed = {b: ns.owed[b].get(item, 0.0) for b in sorted(ns.owed) if ns.owed[b].get(item, 0.0) > 0}
            if not owed:
                continue
            for b, q in ration(ns.stock[item], owed).items():
                if q <= 1e-9:
                    continue
                ns.remove(item, q)
                ns.owed[b][item] -= q
                order_week = _consume_fifo(ns, b, item, q, t)
                sh = make_shipment(s, n, b, item, q, t, order_week)
                s.in_transit.append(sh)
                ns.counts["shipped"] += q
                ns.ledger["revenue"] += sh.value
                s.nodes[b].ledger["purchases"] += sh.value  # booked at ship, same week as the sale
                ns.ledger["shipping"] += sh.cost  # the shipper pays freight, in the week it ships
                ns.ledger["handling"] += q * ns.params["handling_cost_per_unit"]


def _close_week(s: SimState) -> None:
    rate = s.cfg.assumptions.holding_rate_annual / 52
    received = escaped = 0.0
    for n in s.net.order:
        ns = s.nodes[n]
        for item in sorted(ns.stock):
            lost = ns.stock[item] * ns.params["shrink_rate"]
            val = unit_value(s.prices, s.net, n, item)
            ns.remove(item, lost)
            ns.counts["shrink"] += lost
            ns.ledger["scrap"] += lost * val
            ns.ledger["holding"] += ns.stock[item] * val * rate
        for tech_id in sorted(s.holdings.get(n, {})):
            ns.ledger["tech"] += s.catalog[tech_id].cost_per_week[ns.role]
        ns.cash += ns.profit()
        if ns.role == "CM":
            received += ns.counts["received"]
            escaped += ns.counts["defects_escaped"]
    s.quality.append(1 - escaped / received if received > 0 else s.quality[-1])
