"""Technology adoption bookkeeping (spec §6, §7.3)."""
from __future__ import annotations

from sciti.tech.catalog import TechHolding


class AdoptionError(Exception):
    pass


def adopt(s, node_id: str, tech_id: str, week: int, coalition_id: str | None = None,
          one_time: float | None = None) -> dict:
    if tech_id not in s.catalog:
        raise AdoptionError(f"unknown tech {tech_id!r}")
    tech = s.catalog[tech_id]
    ns = s.nodes[node_id]
    if ns.role not in tech.eligible_roles:
        raise AdoptionError(f"{node_id} ({ns.role}) is not eligible for {tech_id}")
    if tech_id in s.holdings[node_id]:
        raise AdoptionError(f"{node_id} already holds {tech_id}")
    cost = tech.cost_one_time[ns.role] if one_time is None else one_time
    s.holdings[node_id][tech_id] = TechHolding(tech_id, week, week + tech.setup_weeks, coalition_id)
    ns.pending_tech_cost += cost
    ev = {"week": week, "type": "adopt", "node": node_id, "tech": tech_id,
          "coalition": coalition_id, "one_time": cost}
    s.events.append(ev)
    return ev


def drop(s, node_id: str, tech_id: str, week: int) -> dict:
    if tech_id not in s.holdings[node_id]:
        raise AdoptionError(f"{node_id} does not hold {tech_id}")
    del s.holdings[node_id][tech_id]
    ev = {"week": week, "type": "drop", "node": node_id, "tech": tech_id}
    s.events.append(ev)
    return ev


def apply_forced(s, week: int) -> None:
    for i, fa in enumerate(s.cfg.forced_adoptions):
        if fa.week != week:
            continue
        tech = s.catalog[fa.tech]
        coalition = f"forced_{i}" if len(fa.members) > 1 else None
        share = sum(tech.cost_one_time[s.nodes[m].role] for m in fa.members) / len(fa.members)
        if coalition:
            s.events.append({"week": week, "type": "coalition", "id": coalition, "tech": fa.tech,
                             "members": sorted(fa.members), "kind": coalition_kind(s.net, fa.members)})
        for m in sorted(fa.members):
            adopt(s, m, fa.tech, week, coalition, share)


def coalition_kind(net, members) -> str:
    n = len(members)
    if n == len(net.order):
        return "network"
    if n == 2:
        return "dyad"
    if n == 3:
        return "triad"
    return "chain"
