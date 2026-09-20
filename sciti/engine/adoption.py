"""Technology adoption bookkeeping (spec §6, §7.3)."""
from __future__ import annotations

from sciti.rng import implementation_draw
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


def learning_multiplier(s, node_id: str, tech_id: str, week: int) -> float:
    """What experience does to the odds of failure: own failed attempts at this technology, technologies the
    firm already runs, and direct partners already running this one. Failing or not-yet-live projects teach nothing."""
    A = s.cfg.assumptions
    live = lambda h: h.fails_week is None and week >= h.active_week
    failures = sum(e["type"] == "implementation_failed" and e["node"] == node_id and e["tech"] == tech_id for e in s.events)
    retry = A.retry_failure_odds[min(failures, len(A.retry_failure_odds)) - 1] if failures else 1.0
    own = sum(live(h) for t, h in s.holdings[node_id].items() if t != tech_id)
    partners = sum(tech_id in s.holdings[p] and live(s.holdings[p][tech_id]) for p in s.net.partners(node_id))
    return (retry * max(A.own_success_floor, A.own_success_failure_odds ** own)
            * max(A.partner_success_floor, A.partner_success_failure_odds ** partners))


def implementation_odds(tech, role: str, assumptions, learning: float = 1.0, joiner: bool = False) -> tuple[float, float]:
    """(p_fail, p_partial) for this role; suppliers, the small firms, do worse, and experience helps.
    A joiner is a member of a group's project: the project's own draw decides failure for everyone, so the
    member only risks a shallow onboarding (p_fail 0; the catalog's odds of partial among survivors, scaled the same way)."""
    if not assumptions.implementation_risk:
        return 0.0, 0.0
    if joiner:
        shallow = tech.p_partial / (1 - tech.p_fail) if tech.p_fail < 1 else 0.0
        if 0 < shallow < 1:
            odds = shallow / (1 - shallow) * learning * (assumptions.small_firm_failure_odds if role == "Supplier" else 1.0)
            shallow = odds / (1 + odds)
        return 0.0, shallow
    p_fail, p_partial = tech.p_fail, tech.p_partial
    mult = learning * (assumptions.small_firm_failure_odds if role == "Supplier" else 1.0)
    if mult != 1.0 and 0 < p_fail < 1:
        odds = p_fail / (1 - p_fail) * mult
        p_partial *= (1 - odds / (1 + odds)) / (1 - p_fail)
        p_fail = odds / (1 + odds)
    return p_fail, p_partial


def implementation_outcome(u: float, tech, role: str, assumptions, learning: float = 1.0,
                           joiner: bool = False) -> tuple[str, float]:
    """Map a draw u to ("fail" | "partial" | "full", share of the effect delivered)."""
    p_fail, p_partial = implementation_odds(tech, role, assumptions, learning, joiner)
    if u < p_fail:
        return "fail", 0.0
    if u < p_fail + p_partial:
        return "partial", tech.partial_fraction
    return "full", 1.0


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
    A = s.cfg.assumptions
    project = coalition_id is not None and tech.network_requirement != "solo" and A.group_project_draw
    outcome, fraction = implementation_outcome(implementation_draw(s.cfg.seed, node_id, tech_id, week), tech, ns.role,
                                               A, learning_multiplier(s, node_id, tech_id, week), joiner=project)
    if project:  # the group's project has one outcome for everyone; "MFG" = no small-firm scaling for the project
        p_outcome, p_fraction = implementation_outcome(implementation_draw(s.cfg.seed, coalition_id, tech_id, week),
                                                       tech, "MFG", A)
        fraction = min(fraction, p_fraction)
        outcome = "fail" if "fail" in (outcome, p_outcome) else ("full" if fraction == 1.0 else "partial")
    fails_week = week + (tech.fail_after_weeks or tech.setup_weeks) if outcome == "fail" else None
    s.holdings[node_id][tech_id] = TechHolding(tech_id, week, week + tech.setup_weeks, coalition_id,
                                               fraction=fraction if outcome != "fail" else 1.0, fails_week=fails_week)
    ns.pending_tech_cost += cost
    ev = {"week": week, "type": "adopt", "node": node_id, "tech": tech_id,
          "coalition": coalition_id, "one_time": cost, "outcome": outcome}  # the outcome is for analysts; agents never see it
    s.events.append(ev)
    return ev


def drop(s, node_id: str, tech_id: str, week: int) -> dict:
    if tech_id not in s.holdings[node_id]:
        raise AdoptionError(f"{node_id} does not hold {tech_id}")
    del s.holdings[node_id][tech_id]
    ev = {"week": week, "type": "drop", "node": node_id, "tech": tech_id}
    s.events.append(ev)
    return ev


def abandon_failed(s, week: int) -> None:
    """Failing implementations are given up in their fails_week: running cost stops and the firm may try again."""
    for n in s.net.order:
        for tech_id in sorted(s.holdings[n]):
            if s.holdings[n][tech_id].fails_week == week:
                del s.holdings[n][tech_id]
                s.events.append({"week": week, "type": "implementation_failed", "node": n, "tech": tech_id})


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
