"""Prices, unit values, and demand propagation through the network (spec §5.4)."""
from __future__ import annotations

import numpy as np

from sciti.network import PRODUCTS


def _lane_freight_per_unit(baseline, lane_name: str) -> float:
    lane = baseline["lanes"][lane_name]
    return sum(mix * lane["modes"][mode]["cost_per_unit"] for mode, mix in lane["mode_mix"].items())


def price_table(net, baseline, markup) -> dict:
    f_cm_mfg = _lane_freight_per_unit(baseline, "cm_mfg")
    f_mfg_dc = _lane_freight_per_unit(baseline, "mfg_dc")
    f_dc_retail = _lane_freight_per_unit(baseline, "dc_retail")
    sup = {sid: float(v["price"]) for sid, v in baseline["suppliers"].items()}
    raw = {sku: float(np.mean([sup[s] for s in net.suppliers_of[sku]])) for sku in net.skus}
    cm = {sku: (raw[sku] + f_cm_mfg) * (1 + markup["CM"]) for sku in net.skus}
    mfg = (sum(cm[sku] * u for sku, u in net.bom.items()) + f_mfg_dc) * (1 + markup["MFG"])
    dc = (mfg + f_dc_retail) * (1 + markup["DC"])
    return {"supplier": sup, "raw": raw, "cm": cm, "mfg": mfg, "dc": dc,
            "retail": dc * (1 + markup["Retail"])}


def sell_price(prices, net, node_id, item) -> float:
    role = net.nodes[node_id].role
    if role == "Supplier":
        return prices["supplier"][node_id]
    if role == "CM":
        return prices["cm"][item]
    return prices[{"MFG": "mfg", "DC": "dc", "Retail": "retail"}[role]]


def unit_value(prices, net, node_id, item) -> float:
    role = net.nodes[node_id].role
    if role == "Supplier":
        return prices["supplier"][node_id]
    if role == "CM":
        return prices["raw"][item[4:]] if item.startswith("RAW:") else prices["cm"][item]
    if role == "MFG":
        return prices["mfg"] if item in PRODUCTS else prices["cm"][item]
    return prices["mfg"] if role == "DC" else prices["dc"]


def unit_cost(prices, net, node_id, item, supplier_cogs_share: float) -> float:
    """What the holder paid for one unit of stock (inventory at cost)."""
    role = net.nodes[node_id].role
    if role == "Supplier":
        return prices["supplier"][node_id] * supplier_cogs_share
    if role == "CM":
        return prices["raw"][item[4:] if item.startswith("RAW:") else item]
    if role == "MFG":
        return sum(prices["cm"][k] * u for k, u in net.bom.items()) if item in PRODUCTS else prices["cm"][item]
    return prices["mfg"] if role == "DC" else prices["dc"]


def inventory_cost(s) -> float:
    """Stock on hand at cost plus goods in transit at invoice value (the buyer has already booked them)."""
    share = s.cfg.assumptions.supplier_cogs_share
    on_hand = sum(q * unit_cost(s.prices, s.net, n, item, share)
                  for n, ns in s.nodes.items() for item, q in ns.stock.items())
    return on_hand + sum(sh.value for sh in s.in_transit)


def propagate(net, retail: dict[tuple[str, str], float]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {n: {} for n in net.order}
    for r in net.by_role("Retail"):
        out[r] = {p: float(retail.get((r, p), 0.0)) for p in PRODUCTS}
    for d in net.by_role("DC"):
        out[d] = {p: sum(net.source_share[r].get(d, 0.0) * out[r][p] for r in net.downstream[d]) for p in PRODUCTS}
    for m in net.by_role("MFG"):
        prod = {p: sum(net.source_share[d].get(m, 0.0) * out[d][p] for d in net.downstream[m]) for p in PRODUCTS}
        total = sum(prod.values())
        out[m] = {**prod, **{sku: total * u for sku, u in net.bom.items()}}
    for c in net.by_role("CM"):
        out[c] = {sku: sum(out[m][sku] for m in net.by_role("MFG")) for sku in net.nodes[c].skus}
    for s in net.by_role("Supplier"):
        sku = net.nodes[s].skus[0]
        out[s] = {sku: out[net.cm_of[sku]][sku] / len(net.suppliers_of[sku])}
    return out
