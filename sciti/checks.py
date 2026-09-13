"""Weekly invariants (spec §9.4)."""
from __future__ import annotations

import math


class SimulationError(Exception):
    pass


def check_invariants(s, t: int) -> list[str]:
    out = []
    for n in s.net.order:
        ns = s.nodes[n]
        for item in sorted(set(ns.stock) | set(ns.opening)):
            now = ns.stock.get(item, 0.0)
            if not math.isfinite(now):
                out.append(f"week {t} {n} {item}: non-finite stock {now}")
            if now < 0:
                out.append(f"week {t} {n} {item}: negative stock {now}")
            expect = ns.opening.get(item, 0.0) + ns.delta.get(item, 0.0)
            if abs(now - expect) > 1e-6 * max(1.0, abs(now)):
                out.append(f"week {t} {n} {item}: conservation broken, stock {now} vs expected {expect}")
        if ns.role == "MFG":
            for sku, u in s.net.bom.items():
                if abs(ns.consumed.get(sku, 0.0) - ns.counts["built"] * u) > 1e-6 * max(1.0, ns.counts["built"] * u):
                    out.append(f"week {t} {n} {sku}: BOM consumption {ns.consumed.get(sku)} != built*{u}")
        # Flow balance check using weekly counters (independent of delta)
        total_stock = sum(ns.stock.values())
        built_add = ns.counts["built"] if ns.role in ("Supplier", "MFG") else 0.0
        consumed_total = sum(ns.consumed.values()) if ns.role == "MFG" else 0.0
        sales = ns.counts["sales"] if ns.role == "Retail" else 0.0
        expected_total = (sum(ns.opening.values()) + ns.counts["received"] - ns.counts["defects_caught"] +
                          built_add - consumed_total - ns.counts["shipped"] - sales - ns.counts["shrink"])
        if abs(total_stock - expected_total) > 1e-6 * max(1.0, abs(total_stock)):
            out.append(f"week {t} {n}: flow balance broken, stock total {total_stock} vs expected {expected_total}")
        values = list(ns.ledger.values()) + [ns.cash]
        if not all(math.isfinite(v) for v in values) or abs(ns.cash) >= 1e15:
            out.append(f"week {t} {n}: non-finite or out-of-range money (cash {ns.cash})")
    ids = [sh.id for sh in s.arrived] + [sh.id for sh in s.in_transit]
    if len(ids) != len(set(ids)):
        out.append(f"week {t}: duplicate shipment ids")
    late = [sh.id for sh in s.in_transit if sh.arrive_week <= t]
    if late:
        out.append(f"week {t}: shipments past arrival still in transit: {late[:5]}")
    return out


def enforce(s, t: int, strict: bool) -> None:
    violations = check_invariants(s, t)
    if not violations:
        return
    if strict:
        raise SimulationError("\n".join(violations))
    for v in violations:
        s.events.append({"week": t, "type": "check_warning", "detail": v})
