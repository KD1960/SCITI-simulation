"""Scheduled capacity and lead-time shocks (spec §5.3 step 1, §6 risk_intel)."""
from __future__ import annotations

import math


def validate_disruptions(disruptions, net) -> None:
    for i, d in enumerate(disruptions):
        if d.target not in net.nodes:
            raise ValueError(f"disruption {i}: unknown target {d.target!r}")
        if d.weeks <= 0 or d.start_week < 1:
            raise ValueError(f"disruption {i}: start_week must be >= 1 and weeks > 0")


def apply_disruptions(s, t: int) -> None:
    for ns in s.nodes.values():
        ns.capacity_factor, ns.extra_lead_days, ns.z_boost = 1.0, 0.0, 0.0
    for i, d in enumerate(s.cfg.disruptions):
        if t == d.start_week:
            mult = s.nodes[d.target].params["recovery_mult"]
            s.disruption_end[i] = d.start_week + math.ceil(d.weeks * mult)
            s.events.append({"week": t, "type": "disruption_start", "target": d.target,
                             "until": s.disruption_end[i]})
        if i in s.disruption_end and d.start_week <= t < s.disruption_end[i]:
            s.nodes[d.target].capacity_factor *= d.capacity_mult
            s.nodes[d.target].extra_lead_days += d.extra_lead_days
    for n in s.net.order:
        ew = s.nodes[n].params["early_warning_weeks"]
        if ew <= 0:
            continue
        watch = set(s.net.upstream[n]) | {n}
        if any(d.target in watch and t < d.start_week <= t + ew for d in s.cfg.disruptions):
            s.nodes[n].z_boost = 1.0
