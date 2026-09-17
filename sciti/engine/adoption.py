"""Technology adoption bookkeeping (spec §6, §7.3)."""
from __future__ import annotations

from sciti.tech.catalog import TechHolding


class AdoptionError(Exception):
    pass


def validate_forced_adoptions(forced_adoptions, net, catalog, weeks: int) -> None:
    """Fail early on a bad forced-adoption config (spec §9.5), before any run dir exists."""
    seen_pairs = set()
    for i, fa in enumerate(forced_adoptions):
        if fa.tech not in catalog:
            raise ValueError(f"forced adoption {i}: unknown tech {fa.tech!r}")
        tech = catalog[fa.tech]
        if not fa.members:
            raise ValueError(f"forced adoption {i}: members must be non-empty")
        if len(set(fa.members)) != len(fa.members):
            raise ValueError(f"forced adoption {i}: duplicate members {fa.members}")
        for m in fa.members:
            if m not in net.nodes:
                raise ValueError(f"forced adoption {i}: unknown node {m!r}")
            role = net.nodes[m].role
            if role not in tech.eligible_roles:
                raise ValueError(f"forced adoption {i}: {m} ({role}) is not eligible for {fa.tech}")
        if not (1 <= fa.week <= weeks):
            raise ValueError(f"forced adoption {i}: week {fa.week} is outside 1..{weeks}")
        for m in fa.members:
            pair = (m, fa.tech)
            if pair in seen_pairs:
                raise ValueError(f"forced adoption {i}: {m} already assigned {fa.tech} in another entry")
            seen_pairs.add(pair)


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
        members = []
        for m in sorted(fa.members):
            if fa.tech in s.holdings[m]:
                s.events.append({"week": week, "type": "forced_skipped", "node": m, "tech": fa.tech,
                                 "reason": "already held"})
            else:
                members.append(m)
        if not members:
            continue
        coalition = f"forced_{i}" if len(members) > 1 else None
        if s.cfg.decision.cost_split == "by_size":
            cost_of = {m: tech.cost_one_time[s.nodes[m].role] for m in members}
        else:
            share = sum(tech.cost_one_time[s.nodes[m].role] for m in members) / len(members)
            cost_of = {m: share for m in members}
        if coalition:
            s.events.append({"week": week, "type": "coalition", "id": coalition, "tech": fa.tech,
                             "members": members, "kind": coalition_kind(s.net, members)})
        for m in members:
            adopt(s, m, fa.tech, week, coalition, cost_of[m])


def coalition_kind(net, members) -> str:
    n = len(members)
    if n == len(net.order):
        return "network"
    if n == 2:
        return "dyad"
    if n == 3:
        return "triad"
    return "chain"
