"""What an agent may see at a quarterly decision (spec §7.2)."""
from __future__ import annotations

from sciti.engine.adoption import attempts_used_up, group_size_multiplier, implementation_odds, learning_multiplier, reach
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
                  "horizon_weeks": int(rng.integers(hlo, hhi + 1)),
                  "collaboration": assumptions.collaboration}
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
    nothing = tech.p_cancel + tech.p_fail
    cancel = round(p_fail * tech.p_cancel / nothing, 3) if nothing else 0.0
    return {"implementation_odds": {"fail": round(p_fail, 3), "cancelled_in_pilot": cancel,
                                    "pilot_cost_share": s.cfg.assumptions.pilot_cost_share, "partial": round(p_partial, 3),
                                    "partial_benefit": tech.partial_fraction, "expected_benefit": round(expected, 3)}}


def _project_odds(s, tech, members: int) -> dict:
    """What a group project of this size faces: one draw for everyone, and bigger projects fail more."""
    p_fail, p_partial = implementation_odds(tech, "MFG", s.cfg.assumptions, group_size_multiplier(members, s.cfg.assumptions))
    expected = (1 - p_fail - p_partial) + p_partial * tech.partial_fraction
    return {"members": members, "fail": round(p_fail, 3), "partial": round(p_partial, 3), "expected_benefit": round(expected, 3)}


def protection_hazard(weeks_since: int | None, assumptions) -> float:
    """Kevin's rule R2: the chance a rule agent buys protection this quarter, high right after a shock and decaying."""
    floor = assumptions.protection_hazard_floor
    if weeks_since is None:
        return floor
    return floor + (1 - floor) * 0.5 ** (weeks_since / assumptions.protection_half_life_weeks)


def _shocks(s, node_id: str, week: int) -> dict:
    """Disruptions so far at any site upstream or downstream of this firm, and how long ago the last one began."""
    near = reach(s.net, node_id, s.net.upstream) | reach(s.net, node_id, s.net.downstream) | {node_id}
    seen = [e for e in s.events if e["type"] == "disruption_start" and e["target"] in near and e["week"] <= week]
    recent = [{"target": e["target"], "start_week": e["week"], "weeks": e["until"] - e["week"], "active": week < e["until"]}
              for e in seen[-5:]]
    return {"weeks_since_last": week - seen[-1]["week"] if seen else None, "recent": recent}


def _network_experience(s, week: int) -> dict:
    """Kevin's rule R3: what every firm can see of the network's outcomes with each technology in the last 52 weeks."""
    out = {t: {"full": 0, "partial": 0, "cancelled": 0, "failed": 0} for t in s.catalog}
    for e in s.events:
        if e["week"] < week - 52 or e["week"] > week or e.get("tech") not in out:
            continue
        if e["type"] == "implementation_failed":
            out[e["tech"]]["failed"] += 1
        elif e["type"] == "implementation_cancelled":
            out[e["tech"]]["cancelled"] += 1
        elif e["type"] == "adopt" and e["outcome"] in ("full", "partial"):
            h = s.holdings.get(e["node"], {}).get(e["tech"])
            if h is not None and h.adopted_week == e["week"] and week >= h.active_week:  # live, so the outcome is public
                out[e["tech"]][e["outcome"]] += 1
    return out


def _effects_text(tech, role) -> str:
    return "; ".join(f"{e.param} {'x' if e.op == 'mul' else '+'}{(e.by_role or {}).get(role, e.value)}"
                     for e in tech.effects)


def build_brief(s, node_id, week, pass_, persona, recent, visibility, max_new, proposals=None) -> Brief:
    D = s.cfg.decision
    show_odds = D.show_implementation_odds or s.net.nodes[node_id].role in D.rules_roles
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
             "effects": _effects_text(t, node.role),
             **(_odds(s, t, node_id, node.role, week) if show_odds else {}),
             **({"project_odds_by_members": {str(n): _project_odds(s, t, n) for n in (2, 4, 8, 16, 48)}}
                if show_odds and t.network_requirement != "solo" and s.cfg.assumptions.implementation_risk else {})}
            for t in sorted(s.catalog.values(), key=lambda x: x.id)
            if node.role in t.eligible_roles and t.id not in held
            and not attempts_used_up(s.events, node_id, t.id, s.cfg.assumptions.max_attempts)],
        "shocks": _shocks(s, node_id, week),
        "network_experience": _network_experience(s, week),
        "rules": {"pass": pass_, "allowed_actions": list(PROPOSAL_ACTIONS if pass_ == "proposal" else RESPONSE_ACTIONS),
                  "max_new_adoptions": max_new, "max_reason_words": MAX_REASON_WORDS},
    }
    if s.cfg.decision.insurance_techs:
        data["rules"]["insurance"] = {"techs": list(s.cfg.decision.insurance_techs),
                                      "revenue_share": s.cfg.decision.insurance_revenue_share,
                                      "hazard": round(protection_hazard(data["shocks"]["weeks_since_last"], s.cfg.assumptions), 4)}
    data["rules"]["network_sentiment"] = s.cfg.assumptions.network_sentiment
    data["rules"]["group_scope"] = "your tier and the tiers next to it" + ("" if D.allow_network_groups else "; whole-network groups are off")
    if node.role in s.cfg.decision.rules_roles:
        data["rules"]["follow_revenue_share"] = s.cfg.decision.follow_revenue_share
    if visibility == "network":
        counts = {}
        for n in net.order:
            for t in s.holdings[n]:
                counts[t] = counts.get(t, 0) + 1
        data["network_adoption_counts"] = dict(sorted(counts.items()))
    if pass_ == "response":
        data["proposals"] = [
            {**p, **({"project_odds": _project_odds(s, s.catalog[p["tech"]], len(p["members"]))}
                     if show_odds and p["tech"] in s.catalog and s.catalog[p["tech"]].network_requirement != "solo"
                     and s.cfg.assumptions.implementation_risk else {})}
            for p in (proposals or [])]
    return Brief(node_id, node.role, week, (week - 1) // 13 + 1, pass_, data)
