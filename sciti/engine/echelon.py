"""Echelon stock and lead time for control-tower ordering (spec 2026-09-14 §3.3-3.4)."""
from __future__ import annotations

from sciti.network import PRODUCTS


def echelon_stock(s, n: str, item: str, pipe: dict[tuple[str, str], float],
                  own_input: float | None = None) -> float:
    """Units of `item` at or below node `n`, on hand or in transit, in `item`'s units.
    `own_input` replaces n's own input stock (the ordering node uses its recorded value)."""
    net, ns = s.net, s.nodes[n]
    key = f"RAW:{item}" if ns.role == "CM" else item
    own = ns.stock.get(key, 0.0) if own_input is None else own_input
    total = own + pipe.get((n, item), 0.0)
    if ns.role == "Retail":
        return total
    if ns.role == "DC":
        return total + sum(net.source_share[r][n] * echelon_stock(s, r, item, pipe) for r in net.downstream[n])
    if ns.role == "MFG":
        products = sum(ns.stock.get(p, 0.0) + sum(net.source_share[d][n] * echelon_stock(s, d, p, pipe)
                                                  for d in net.downstream[n])
                       for p in PRODUCTS)
        return total + net.bom[item] * products
    if ns.role == "CM":
        return total + ns.stock.get(item, 0.0) + sum(echelon_stock(s, m, item, pipe) for m in net.downstream[n])
    raise ValueError(f"{n}: suppliers have no echelon stock")


def _weighted(pairs: list[tuple[float, float]]) -> float:
    total = sum(w for w, _ in pairs)
    return sum(w * x for w, x in pairs) / total if total > 0 else 0.0


def echelon_lead_weeks(net, lead_weeks: dict[tuple[str, str], int],
                       mean: dict[str, dict[str, float]]) -> dict[tuple[str, str], float]:
    """Own lead time and review week plus the flow-weighted echelon lead time of the nodes below (spec §3.4)."""
    le: dict[tuple[str, str], float] = {}
    for r in net.by_role("Retail"):
        for p in PRODUCTS:
            le[(r, p)] = float(lead_weeks[(r, p)])
    for d in net.by_role("DC"):
        for p in PRODUCTS:
            le[(d, p)] = lead_weeks[(d, p)] + 1 + _weighted(
                [(net.source_share[r][d] * mean[r][p], le[(r, p)]) for r in net.downstream[d]])
    for m in net.by_role("MFG"):
        below = _weighted([(net.source_share[d][m] * mean[d][p], le[(d, p)])
                           for d in net.downstream[m] for p in PRODUCTS])
        for k in net.bom:
            le[(m, k)] = lead_weeks[(m, k)] + 1 + below
    for c in net.by_role("CM"):
        for k in net.nodes[c].skus:
            le[(c, k)] = lead_weeks[(c, k)] + 1 + _weighted([(mean[m][k], le[(m, k)]) for m in net.downstream[c]])
    return le
