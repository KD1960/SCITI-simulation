"""Quarterly decision round: proposals, responses, coalitions (spec §7.4)."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from sciti.decide.briefs import budget_available, build_brief
from sciti.decide.interface import ReplyError, brief_hash, parse_reply, validate_reply
from sciti.engine.adoption import adopt, coalition_kind, drop


@dataclass
class DecisionContext:
    policy: object
    fallback: object
    writer: object
    personas: dict
    recent: dict


def _reach(net, start, edges):
    seen, stack = set(), [start]
    while stack:
        for nxt in edges[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def group_members(net, holdings, catalog, proposer, tech_id, partners) -> list[str]:
    tech = catalog[tech_id]
    if partners == ["network"]:
        pool = set(net.order)
    elif partners == ["chain"]:
        pool = _reach(net, proposer, net.upstream) | _reach(net, proposer, net.downstream)
    else:
        pool = set(partners)
    pool.add(proposer)
    return sorted(n for n in pool if net.nodes[n].role in tech.eligible_roles
                  and (n == proposer or tech_id not in holdings[n]))


def _ask(s, t, ctx, brief, max_new):
    """Policy reply → validate → one retry → rules fallback. Returns decisions and writes the log."""
    rec = {"week": t, "quarter": brief.quarter, "pass": brief.pass_, "agent": brief.agent,
           "policy": ctx.policy.name, "brief": brief.data, "brief_hash": brief_hash(brief),
           "raw": None, "error": None, "retry_raw": None, "retry_error": None, "fallback": False,
           "fallback_raw": None, "fallback_error": None,
           "tokens_in": 0, "tokens_out": 0, "latency_s": 0.0}
    reply = ctx.policy.decide(brief)
    rec.update(raw=reply.raw, fallback=reply.fallback, tokens_in=reply.tokens_in,
               tokens_out=reply.tokens_out, latency_s=reply.latency_s)
    if reply.fallback:
        rec["error"] = reply.error
    try:
        decisions = validate_reply(parse_reply(reply.raw), brief, max_new)
    except ReplyError as e:
        rec["error"] = str(e)
        retry = ctx.policy.decide(brief, feedback=str(e))
        rec.update(retry_raw=retry.raw, tokens_in=rec["tokens_in"] + retry.tokens_in,
                   tokens_out=rec["tokens_out"] + retry.tokens_out)
        try:
            decisions = validate_reply(parse_reply(retry.raw), brief, max_new)
        except ReplyError as e2:
            rec["retry_error"] = str(e2)
            rec["fallback"] = True
            fb = ctx.fallback.decide(brief)
            rec["fallback_raw"] = fb.raw
            try:
                decisions = validate_reply(parse_reply(fb.raw), brief, max_new)
            except ReplyError as e3:
                rec["fallback_error"] = str(e3)
                decisions = []
    rec["parsed"] = [dataclasses.asdict(d) for d in decisions]
    ctx.writer.log_decision(rec)
    return decisions, rec


def run_decision_round(s, t: int, ctx: DecisionContext) -> dict:
    D = s.cfg.decision
    net = s.net
    stats = {"calls": 0, "fallbacks": 0, "errors": 0}
    budget = {n: budget_available(s, n, ctx.personas[n], ctx.recent.get(n, [])) for n in net.order}
    new_count = {n: 0 for n in net.order}
    groups: dict[str, dict] = {}

    def charge(node, tech_id, cost):
        if cost > budget[node] + 1e-9:
            s.events.append({"week": t, "type": "rejected", "node": node, "tech": tech_id, "reason": "budget"})
            return False
        budget[node] -= cost
        return True

    for n in net.order:
        brief = build_brief(s, n, t, "proposal", ctx.personas[n], ctx.recent.get(n, []), D.visibility,
                            D.max_new_adoptions_per_quarter)
        decisions, rec = _ask(s, t, ctx, brief, D.max_new_adoptions_per_quarter)
        stats["calls"] += 1
        stats["fallbacks"] += rec["fallback"]
        stats["errors"] += rec["error"] is not None
        for dcs in decisions:
            role = net.nodes[n].role
            if dcs.action == "drop":
                drop(s, n, dcs.tech, t)
            elif dcs.action == "adopt":
                if charge(n, dcs.tech, s.catalog[dcs.tech].cost_one_time[role]):
                    adopt(s, n, dcs.tech, t)
                    new_count[n] += 1
            elif dcs.action == "propose_group":
                members = group_members(net, s.holdings, s.catalog, n, dcs.tech, dcs.partners)
                invited = [m for m in members if m != n]
                if not invited:
                    s.events.append({"week": t, "type": "coalition_failed", "id": None, "tech": dcs.tech,
                                     "proposer": n, "accepted": [], "reason": "no eligible partners"})
                    continue
                gid = f"q{brief.quarter}_{n}_{dcs.tech}"
                strict = dcs.partners not in (["chain"], ["network"]) or s.catalog[dcs.tech].network_requirement == "pair"
                groups[gid] = {"id": gid, "tech": dcs.tech, "proposer": n, "invited": invited,
                               "members": members, "strict": strict, "accepted": []}

    inbox: dict[str, list[dict]] = {}
    for g in groups.values():
        for m in g["invited"]:
            inbox.setdefault(m, []).append(g)
    for n in [x for x in net.order if x in inbox]:
        props = []
        for g in sorted(inbox[n], key=lambda g: g["id"]):
            props.append({"group_id": g["id"], "tech": g["tech"], "from": g["proposer"], "members": g["members"],
                          "your_cost_share": _share(s, g["tech"], g["members"], n)})
        brief = build_brief(s, n, t, "response", ctx.personas[n], ctx.recent.get(n, []), D.visibility,
                            D.max_new_adoptions_per_quarter, proposals=props)
        decisions, rec = _ask(s, t, ctx, brief, len(props))
        stats["calls"] += 1
        stats["fallbacks"] += rec["fallback"]
        stats["errors"] += rec["error"] is not None
        for dcs in sorted(decisions, key=lambda x: x.group_id):
            if dcs.action == "accept_group" and new_count[n] < D.max_new_adoptions_per_quarter:
                g = groups[dcs.group_id]
                if g["tech"] not in s.holdings[n]:
                    g["accepted"].append(n)

    # The one-new-adoption cap counts only what actually happens: solo adopts (above) and
    # groups that form (below). Proposing and accepting don't consume it on their own.
    joined = dict(new_count)
    for gid in sorted(groups):
        g = groups[gid]
        tech, proposer = g["tech"], g["proposer"]
        if tech in s.holdings[proposer]:
            s.events.append({"week": t, "type": "coalition_failed", "id": gid, "tech": tech,
                             "proposer": proposer, "accepted": [], "reason": "held"})
            continue
        if joined[proposer] >= D.max_new_adoptions_per_quarter:
            s.events.append({"week": t, "type": "coalition_failed", "id": gid, "tech": tech,
                             "proposer": proposer, "accepted": [], "reason": "quota"})
            continue
        accepted = sorted(m for m in g["accepted"] if tech not in s.holdings[m]
                          and joined[m] < D.max_new_adoptions_per_quarter)
        final = sorted([proposer] + accepted)
        ok = len(final) >= 2 and (
            len(accepted) == len(g["invited"]) if g["strict"] else len(accepted) / len(g["invited"]) >= D.chain_accept_share)
        if not ok:
            s.events.append({"week": t, "type": "coalition_failed", "id": gid, "tech": tech,
                             "proposer": proposer, "accepted": accepted, "reason": "acceptance"})
            continue
        rejected_once: set[str] = set()
        while len(final) >= 2:
            over = [m for m in final if _share(s, tech, final, m) > budget[m] + 1e-9]
            if not over:
                break
            for m in over:
                if m not in rejected_once:
                    s.events.append({"week": t, "type": "rejected", "node": m, "tech": tech, "reason": "budget"})
                    rejected_once.add(m)
            final = sorted(set(final) - set(over))
            accepted = [m for m in accepted if m in final]
        ok = proposer in final and len(final) >= 2 and (
            len(accepted) == len(g["invited"]) if g["strict"] else len(accepted) / len(g["invited"]) >= D.chain_accept_share)
        if not ok:
            s.events.append({"week": t, "type": "coalition_failed", "id": gid, "tech": tech,
                             "proposer": proposer, "accepted": accepted, "reason": "budget"})
            continue
        s.events.append({"week": t, "type": "coalition", "id": gid, "tech": tech, "members": final,
                         "kind": coalition_kind(net, final)})
        for m in final:
            cost = _share(s, tech, final, m)
            budget[m] -= cost
            adopt(s, m, tech, t, gid, cost)
            joined[m] += 1
    return stats


def _share(s, tech_id, members, node) -> float:
    tech = s.catalog[tech_id]
    if s.cfg.decision.cost_split == "by_size":
        return float(tech.cost_one_time[s.nodes[node].role])
    return sum(tech.cost_one_time[s.nodes[m].role] for m in members) / len(members)
