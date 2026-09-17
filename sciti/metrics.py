"""Per-week rows and run summary (spec §5.5)."""
from __future__ import annotations

import numpy as np

from sciti.engine.economics import inventory_cost
from sciti.engine.state import COUNT_KEYS, LEDGER_KEYS, PROFIT_COST_KEYS

WEEK_COLUMNS = (["week", "node", "role", "stock_units", "cash", "profit", "capacity_factor", "techs"]
                + list(COUNT_KEYS) + list(LEDGER_KEYS))


def week_rows(s, t: int) -> list[dict]:
    rows = []
    for n in s.net.order:
        ns = s.nodes[n]
        row = {"week": t, "node": n, "role": ns.role, "stock_units": round(sum(ns.stock.values()), 4),
               "cash": round(ns.cash, 2), "profit": round(ns.profit(), 2),
               "capacity_factor": ns.capacity_factor,
               "techs": ";".join(sorted(k for k, h in s.holdings[n].items() if t >= h.active_week))}
        row.update({k: round(ns.counts[k], 4) for k in COUNT_KEYS})
        row.update({k: round(ns.ledger[k], 2) for k in LEDGER_KEYS})
        rows.append(row)
    return rows


def _series(rows, role, key, weeks):
    agg = np.zeros(weeks)
    for r in rows:
        if r["role"] == role:
            agg[r["week"] - 1] += r[key]
    return agg


def summarize(s, rows: list[dict]) -> dict:
    A = s.cfg.assumptions
    weeks = s.cfg.weeks
    tot = lambda key: float(sum(r[key] for r in rows))
    retail = [r for r in rows if r["role"] == "Retail"]
    demand = sum(r["demand"] for r in retail)
    fill = sum(r["sales"] for r in retail) / demand if demand else 1.0
    arrived = s.arrived
    on_time = float(np.mean([sh.arrive_week <= sh.due_week for sh in arrived])) if arrived else 1.0
    r_in = [sh for sh in arrived if s.nodes[sh.dst].role == "Retail"]
    r_on_time = float(np.mean([sh.arrive_week <= sh.due_week for sh in r_in])) if r_in else 1.0
    transit = np.array([sh.lead_days for sh in arrived]) if arrived else np.array([0.0])
    order_to_arrival = (np.array([(sh.ship_week - sh.order_week) * 7 + sh.lead_days for sh in r_in])
                        if r_in else np.array([0.0]))
    quality = float(np.mean(s.quality[1:])) if len(s.quality) > 1 else s.quality[0]
    w = A.satisfaction_weights
    csi = w["fill_rate"] * fill + w["on_time"] * r_on_time + w["quality"] * quality
    dem = _series(rows, "Retail", "demand", weeks)[13:]
    bom_units = sum(s.net.bom.values())
    bullwhip = {}
    for role in ("Retail", "DC", "MFG", "CM"):
        orders = _series(rows, role, "orders_placed", weeks)[13:]
        if role in ("MFG", "CM"):
            orders = orders / bom_units
        bullwhip[role] = float(np.var(orders) / np.var(dem)) if len(dem) > 1 and np.var(dem) > 0 else None
    adopt_ev = [e for e in s.events if e["type"] == "adopt"]
    closing = inventory_cost(s)
    profit_by_role = {}
    for r in rows:
        profit_by_role[r["role"]] = profit_by_role.get(r["role"], 0.0) + r["profit"]
    return {
        "weeks": weeks,
        "revenue": tot("revenue"),
        "costs": {k: tot(k) for k in PROFIT_COST_KEYS},
        "scrap_value": tot("scrap"),
        "network_profit": tot("profit"),
        "inventory_opening": s.opening_inventory,
        "inventory_closing": closing,
        "inventory_change": closing - s.opening_inventory,
        "network_profit_with_inventory": tot("profit") + closing - s.opening_inventory,
        "profit_by_role": {k: round(v, 2) for k, v in sorted(profit_by_role.items())},
        "fill_rate": fill,
        "on_time_rate": on_time,
        "retail_on_time_rate": r_on_time,
        "mean_lead_days": float(order_to_arrival.mean()),
        "p95_lead_days": float(np.percentile(order_to_arrival, 95)),
        "mean_transit_days": float(transit.mean()),
        "p95_transit_days": float(np.percentile(transit, 95)),
        "quality_mean": quality,
        "satisfaction_index": csi,
        "co2_kg": float(sum(sh.co2 for sh in arrived)),
        "bullwhip": bullwhip,
        "adoptions": len(adopt_ev),
        "coalitions": len([e for e in s.events if e["type"] == "coalition"]),
        "tech_spend": tot("tech"),
    }
