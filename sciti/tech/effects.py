"""Turn a node's active technologies into effective parameters (spec §6)."""
from __future__ import annotations

PARAMS = ("forecast_skill", "visibility", "record_error_sd", "shrink_rate", "capacity_mult",
          "ship_cost_mult", "co2_mult", "handling_cost_per_unit", "dispatch_delay_days",
          "defect_mult", "recovery_mult", "recovery_weeks_saved", "early_warning_weeks", "warning_prob")


def base_params(role: str, assumptions) -> dict[str, float]:
    is_dc = role == "DC"
    return {"forecast_skill": 0.0, "visibility": 0.0,
            "record_error_sd": assumptions.record_error_sd,
            "shrink_rate": assumptions.shrink_rate_weekly,
            "capacity_mult": 1.0, "ship_cost_mult": 1.0, "co2_mult": 1.0,
            "handling_cost_per_unit": assumptions.handling_cost_per_unit if is_dc else 0.0,
            "dispatch_delay_days": assumptions.dispatch_delay_days if is_dc else 0.0,
            "defect_mult": 1.0, "recovery_mult": 1.0, "recovery_weeks_saved": 0.0,
            "early_warning_weeks": 0.0, "warning_prob": 0.0}


def _active(holdings, node_id, tech_id, week) -> bool:
    h = holdings.get(node_id, {}).get(tech_id)
    return h is not None and week >= h.active_week and h.fails_week is None


def effective_params(node_id, week, holdings, catalog, network, base) -> dict[str, float]:
    p = dict(base)
    mine = holdings.get(node_id, {})
    for tech_id in sorted(mine):
        if not _active(holdings, node_id, tech_id, week):
            continue
        tech = catalog[tech_id]
        if tech.network_requirement == "solo":
            s = 1.0
        elif tech.network_requirement == "pair":
            s = 1.0 if any(_active(holdings, q, tech_id, week) for q in network.partners(node_id)) else 0.0
        else:
            role = network.nodes[node_id].role
            ref = network.upstream[node_id] if role == "Retail" else network.downstream[node_id]
            s = sum(_active(holdings, q, tech_id, week) for q in ref) / len(ref) if ref else 0.0
        s *= mine[tech_id].fraction ** tech.depth_exponent  # partial success delivers a share of the effect
        bonus = tech.group_bonus if mine[tech_id].coalition_id else 0.0
        role = network.nodes[node_id].role
        for e in tech.effects:
            value = (e.by_role or {}).get(role, e.value)
            if e.op == "mul":
                m = 1 - (1 - value) * s
                m = max(0.0, 1 - (1 - m) * (1 + bonus))
                p[e.param] *= m
            else:
                p[e.param] += value * s * (1 + bonus)
    p["dispatch_delay_days"] = max(0.0, p["dispatch_delay_days"])
    p["forecast_skill"] = min(1.0, p["forecast_skill"])
    p["visibility"] = min(1.0, p["visibility"])
    p["warning_prob"] = min(1.0, p["warning_prob"])
    return p
