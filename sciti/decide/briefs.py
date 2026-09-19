"""What an agent may see at a quarterly decision (spec §7.2)."""
from __future__ import annotations

from sciti.engine.adoption import implementation_odds, learning_multiplier
from sciti.decide.interface import Brief, PROPOSAL_ACTIONS, RESPONSE_ACTIONS, MAX_REASON_WORDS
from sciti.engine.state import PROFIT_COST_KEYS

RISKS = ("cautious", "balanced", "bold")


def make_personas(net, assumptions, rng) -> dict[str, dict]:
    lo, hi = assumptions.persona_budget_share
    hlo, hhi = assumptions.persona_horizon_weeks
    out = {}
    for n in net.order:
        out[n] = {"risk": RISKS[int(rng.integers(0, 3))],
                  "budget_share": round(float(rng.uniform(lo, hi)), 4),
                  "horizon_weeks": int(rng.integers(hlo, hhi + 1))}
    return out


def budget_available(s, node_id: str, persona: dict, recent: list[dict]) -> float:
    ns = s.nodes[node_id]
    rev = sum(r["revenue"] for r in recent)
    if not recent:
        rev = ns.cash / s.cfg.assumptions.initial_cash_weeks * 13
    return max(0.0, min(ns.cash, persona["budget_share"] * rev))


def _odds(s, tech, node_id, role, week) -> dict:
    """What an agent may know before adopting: the odds given its own experience, never the outcome."""
    p_fail, p_partial = implementation_odds(tech, role, s.cfg.assumptions,
                                            learning_multiplier(s, node_id, tech.id, week))
    if p_fail == 0 and p_partial == 0:
        return {}
    expected = (1 - p_fail - p_partial) + p_partial * tech.partial_fraction
    return {"implementation_odds": {"fail": round(p_fail, 3), "partial": round(p_partial, 3),
                                    "partial_benefit": tech.partial_fraction, "expected_benefit": round(expected, 3)}}


def _effects_text(tech, role) -> str:
    return "; ".join(f"{e.param} {'x' if e.op == 'mul' else '+'}{(e.by_role or {}).get(role, e.value)}"
                     for e in tech.effects)


def build_brief(s, node_id, week, pass_, persona, recent, visibility, max_new, proposals=None) -> Brief:
    net, ns = s.net, s.nodes[node_id]
    node = net.nodes[node_id]
    held = sorted(s.holdings[node_id])
    ships = [sh for sh in s.arrived if sh.src == node_id and sh.ship_week > week - 14]
    sent_ships = [sh for sh in s.arrived + s.in_transit if sh.src == node_id and sh.ship_week > week - 14]
    data = {
        "you": {"id": node_id, "role": node.role, "city": node.city, "persona": persona},
        "last_quarter": {
            "revenue": round(sum(r["revenue"] for r in recent), 2),
            "profit": round(sum(r["profit"] for r in recent), 2),
            "cash": round(ns.cash, 2),
            "costs": {k: round(sum(r[k] for r in recent), 2) for k in PROFIT_COST_KEYS + ("scrap",)},
            "lost_sales": round(sum(r["lost"] for r in recent), 2),
            "shipped_units": round(sum(r["shipped"] for r in recent), 2),
            "on_time_outbound": round(sum(sh.arrive_week <= sh.due_week for sh in ships) / len(ships), 4) if ships else None,
            "co2_kg": round(sum(sh.co2 for sh in sent_ships), 2),
        },
        "budget_available": round(budget_available(s, node_id, persona, recent), 2),
        "your_technologies": [{"tech": t, "since_week": h.adopted_week, "active": week >= h.active_week,
                               "coalition": h.coalition_id} for t, h in sorted(s.holdings[node_id].items())],
        "held": held,
        "partners": [{"id": p, "role": net.nodes[p].role, "technologies": sorted(s.holdings[p])}
                     for p in net.partners(node_id)],
        "eligible_technologies": [
            {"id": t.id, "name": t.name, "one_time_cost": t.cost_one_time[node.role],
             "weekly_cost": t.cost_per_week[node.role], "setup_weeks": t.setup_weeks,
             "network_requirement": t.network_requirement, "group_bonus": t.group_bonus,
             "effects": _effects_text(t, node.role), **_odds(s, t, node_id, node.role, week)}
            for t in sorted(s.catalog.values(), key=lambda x: x.id)
            if node.role in t.eligible_roles and t.id not in held],
        "rules": {"pass": pass_, "allowed_actions": list(PROPOSAL_ACTIONS if pass_ == "proposal" else RESPONSE_ACTIONS),
                  "max_new_adoptions": max_new, "max_reason_words": MAX_REASON_WORDS},
    }
    if s.cfg.decision.insurance_techs:
        data["rules"]["insurance"] = {"techs": list(s.cfg.decision.insurance_techs),
                                      "revenue_share": s.cfg.decision.insurance_revenue_share}
    if node.role in s.cfg.decision.rules_roles:
        data["rules"]["follow_revenue_share"] = s.cfg.decision.follow_revenue_share
    if visibility == "network":
        counts = {}
        for n in net.order:
            for t in s.holdings[n]:
                counts[t] = counts.get(t, 0) + 1
        data["network_adoption_counts"] = dict(sorted(counts.items()))
    if pass_ == "response":
        data["proposals"] = proposals or []
    return Brief(node_id, node.role, week, (week - 1) // 13 + 1, pass_, data)
