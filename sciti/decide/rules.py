"""Transparent payback rule; also the fallback for every other policy (spec §4.2, §9.2)."""
from __future__ import annotations

import json

from sciti.decide.interface import Brief, Reply
from sciti.tech.catalog import load_catalog

TECH_SAVINGS = {
    "ml_forecast": {"stockout": 0.20, "holding": 0.10},
    "control_tower": {"stockout": 0.10, "holding": 0.10},
    "rfid": {"stockout": 0.05, "scrap": 0.50},
    "aps": {"stockout": 0.10},
    "routing": {"shipping": 0.08},
    "wh_robotics": {"handling": 0.20},
    "blockchain": {"scrap": 0.40, "purchases": 0.002},
    "risk_intel": {"stockout": 0.05},
}
RISK = {"cautious": 0.7, "balanced": 1.0, "bold": 1.3}
_CAT = load_catalog()
TECH_ROLES = {t.id: t.eligible_roles for t in _CAT.values()}
TECH_BONUS = {t.id: t.group_bonus for t in _CAT.values()}
TECH_WEEKLY = {t.id: t.cost_per_week for t in _CAT.values()}


class RulesPolicy:
    name = "rules"

    def __init__(self, rng):
        self.rng = rng

    def _saving(self, data, tech_id, noise, bonus=0.0) -> float:
        costs = data["last_quarter"]["costs"]
        risk = RISK[data["you"]["persona"]["risk"]]
        base = sum(costs.get(k, 0.0) * f for k, f in TECH_SAVINGS.get(tech_id, {}).items()) / 13
        return base * noise * risk * (1 + bonus)

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        data = brief.data
        persona = data["you"]["persona"]
        out = []
        if brief.pass_ == "proposal":
            cands = []
            for e in sorted(data["eligible_technologies"], key=lambda e: e["id"]):
                noise = float(self.rng.lognormal(0, 0.3))
                net = self._saving(data, e["id"], noise) - e["weekly_cost"]
                if net <= 0 or e["one_time_cost"] > data["budget_available"]:
                    continue
                payback = e["one_time_cost"] / net
                if payback <= persona["horizon_weeks"]:
                    cands.append((payback, e))
            for payback, e in sorted(cands, key=lambda x: (x[0], x[1]["id"]))[: data["rules"]["max_new_adoptions"]]:
                reason = f"payback about {payback:.0f} weeks"
                if e["network_requirement"] == "solo":
                    out.append({"tech": e["id"], "action": "adopt", "partners": [], "reason": reason})
                elif e["network_requirement"] == "chain":
                    out.append({"tech": e["id"], "action": "propose_group", "partners": ["chain"], "reason": reason})
                else:
                    ps = sorted(p["id"] for p in data["partners"] if p["role"] in TECH_ROLES[e["id"]])
                    if ps:
                        out.append({"tech": e["id"], "action": "propose_group", "partners": ps, "reason": reason})
        else:
            for p in sorted(data.get("proposals", []), key=lambda p: p["group_id"]):
                noise = float(self.rng.lognormal(0, 0.3))
                weekly = TECH_WEEKLY[p["tech"]].get(brief.role, 0.0)
                net = self._saving(data, p["tech"], noise, TECH_BONUS[p["tech"]]) - weekly
                share = p["your_cost_share"]
                ok = net > 0 and share / net <= persona["horizon_weeks"] and share <= data["budget_available"]
                out.append({"tech": p["tech"], "action": "accept_group" if ok else "decline_group",
                            "partners": [], "reason": "worth it" if ok else "not worth it", "group_id": p["group_id"]})
        return Reply(brief.agent, json.dumps({"decisions": out}))
