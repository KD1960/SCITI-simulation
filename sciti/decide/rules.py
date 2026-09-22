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

    def _saving(self, data, tech_id, noise, bonus=0.0, group=False) -> float:
        costs = data["last_quarter"]["costs"]
        persona = data["you"]["persona"]
        base = sum(costs.get(k, 0.0) * f for k, f in TECH_SAVINGS.get(tech_id, {}).items()) / 13
        together = 2 * persona["collaboration"] if group else 1.0  # assumptions.collaboration; 0.5 is neutral
        return base * noise * RISK[persona["risk"]] * (1 + bonus) * together

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        data = brief.data
        persona = data["you"]["persona"]
        out = []
        if brief.pass_ == "proposal":
            cands = []
            for e in sorted(data["eligible_technologies"], key=lambda e: e["id"]):
                noise = float(self.rng.lognormal(0, 0.3))
                expected = e.get("implementation_odds", {}).get("expected_benefit", 1.0)  # projects can fail or fall short
                net = self._saving(data, e["id"], noise, group=e["network_requirement"] != "solo") * expected \
                    - e["weekly_cost"]
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
            ins = data["rules"].get("insurance")
            if ins:  # cheap protection that last quarter's costs cannot justify (decision.insurance_techs)
                revenue = data["last_quarter"].get("revenue") or data["budget_available"] / persona["budget_share"]
                listed = {e["id"]: e for e in data["eligible_technologies"] if e["id"] in ins["techs"]}
                for e in [listed[t] for t in ins["techs"] if t in listed]:  # in the order listed: first is most wanted
                    if len(out) >= data["rules"]["max_new_adoptions"]:
                        break
                    first_year = e["one_time_cost"] + 52 * e["weekly_cost"]
                    if e["network_requirement"] == "solo" \
                            and e["id"] not in [o["tech"] for o in out] \
                            and e["one_time_cost"] <= data["budget_available"] \
                            and first_year <= ins["revenue_share"] * 4 * revenue:
                        out.append({"tech": e["id"], "action": "adopt", "partners": [],
                                    "reason": "cheap protection; no payback needed"})
        else:
            for p in sorted(data.get("proposals", []), key=lambda p: p["group_id"]):
                if p["tech"] not in TECH_WEEKLY:
                    out.append({"tech": p["tech"], "action": "decline_group", "partners": [],
                                "reason": "unknown tech", "group_id": p["group_id"]})
                    continue
                noise = float(self.rng.lognormal(0, 0.3))
                weekly = TECH_WEEKLY[p["tech"]].get(brief.role, 0.0)
                net = self._saving(data, p["tech"], noise, TECH_BONUS[p["tech"]], group=True) - weekly
                share = p["your_cost_share"]
                ok = net > 0 and share / net <= persona["horizon_weeks"] and share <= data["budget_available"]
                reason = "worth it" if ok else "not worth it"
                follow = data["rules"].get("follow_revenue_share")
                if not ok and follow and share <= data["budget_available"] and \
                        share + 52 * weekly <= follow * 4 * data["last_quarter"].get("revenue", 0.0):
                    ok, reason = True, "small cost; going along with partners"
                out.append({"tech": p["tech"], "action": "accept_group" if ok else "decline_group",
                            "partners": [], "reason": reason, "group_id": p["group_id"]})
        return Reply(brief.agent, json.dumps({"decisions": out}))
