"""Guesses page 8 (Kevin, 2026-09-25): tier-adjacent groups with a network switch, a protection hazard that
decays after a shock, learning from the whole network's outcomes, and two attempts per technology."""
import json

import numpy as np
import pytest

from sciti.coalitions import group_members
from sciti.config import Assumptions, Config, DecisionCfg
from sciti.decide.briefs import build_brief, make_personas
from sciti.decide.rules import RulesPolicy
from sciti.engine.adoption import AdoptionError, adopt
from sciti.runner import run
from tests.helpers import make_state
from tests.test_coalitions import d, events, mock_cfg, reply


def _brief(s, node, week=14, pass_="proposal", proposals=None):
    personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
    return build_brief(s, node, week, pass_, personas[node], [], "partners", 1, proposals=proposals)


# R1 ---------------------------------------------------------------------------------------------------------

def test_groups_span_only_the_proposer_tier_and_its_neighbours(baseline):
    s = make_state(baseline)
    chain = group_members(s.net, s.holdings, s.catalog, "CM_1", "control_tower", ["chain"])
    roles = {s.net.nodes[m].role for m in chain}
    assert roles == {"Supplier", "CM", "MFG"}
    dc = group_members(s.net, s.holdings, s.catalog, "DC_Shanghai", "control_tower", ["chain"])
    assert {s.net.nodes[m].role for m in dc} == {"MFG", "DC", "Retail"} and "Supplier_1" not in dc


def test_network_groups_are_refused_unless_switched_on(baseline_path, tmp_path):
    script = [{"agent": "MFG_US", "week": 14, "pass": "proposal",
               "replies": [reply(d("control_tower", "propose_group", ["network"]))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "off")
    failed = [e for e in events(out) if e["type"] == "coalition_failed"]
    assert failed and failed[0]["reason"] == "network groups off" and not [e for e in events(out) if e["type"] == "coalition"]
    out = run(mock_cfg(baseline_path, tmp_path, script, allow_network_groups=True), run_dir=tmp_path / "on")
    assert [e for e in events(out) if e["type"] == "coalition_failed" and e["reason"] == "network groups off"] == []


# R2 ---------------------------------------------------------------------------------------------------------

def test_briefs_report_weeks_since_the_last_shock_in_reach(baseline):
    s = make_state(baseline)
    assert _brief(s, "DC_Houston").data["shocks"] == {"weeks_since_last": None, "recent": []}
    s.events.append({"week": 10, "type": "disruption_start", "target": "CM_3", "until": 14})
    b = _brief(s, "DC_Houston", week=27)
    assert b.data["shocks"]["weeks_since_last"] == 17 and b.data["shocks"]["recent"][0]["target"] == "CM_3"
    assert _brief(s, "Supplier_1", week=27).data["shocks"]["weeks_since_last"] is None  # CM_3 is not in Supplier_1's reach


def test_protection_hazard_decays_after_a_shock():
    from sciti.decide.briefs import protection_hazard
    A = Assumptions()
    assert (A.protection_hazard_floor, A.protection_half_life_weeks) == (0.05, 26)
    assert protection_hazard(None, A) == 0.05
    assert protection_hazard(0, A) == 1.0
    assert protection_hazard(26, A) == pytest.approx(0.525)
    assert protection_hazard(0, Assumptions(protection_hazard_floor=1.0)) == 1.0


def test_insurance_habit_fires_only_when_the_draw_beats_the_hazard():
    from tests.test_rules import brief
    ri = [{"id": "risk_intel", "one_time_cost": 50000, "weekly_cost": 2000, "network_requirement": "solo", "group_bonus": 0.0}]
    def acts(hazard):
        b = brief({}, eligible=ri)
        b.data["last_quarter"]["revenue"] = 1e9
        b.data["rules"]["insurance"] = {"techs": ["risk_intel"], "revenue_share": 0.005, "hazard": hazard}
        return [x["action"] for x in json.loads(RulesPolicy(np.random.default_rng(1)).decide(b).raw)["decisions"]]
    assert acts(1.0) == ["adopt"] and acts(0.0) == []


# R3 ---------------------------------------------------------------------------------------------------------

def test_briefs_count_the_networks_outcomes_in_the_last_year(baseline):
    s = make_state(baseline)
    s.events += [{"week": 1, "type": "adopt", "node": "CM_1", "tech": "rfid", "outcome": "full", "coalition": None, "one_time": 1},
                 {"week": 5, "type": "implementation_cancelled", "node": "CM_2", "tech": "rfid"},
                 {"week": 6, "type": "implementation_failed", "node": "CM_4", "tech": "rfid"}]
    from sciti.tech.catalog import TechHolding
    s.holdings["CM_1"]["rfid"] = TechHolding("rfid", 1, 9)
    x = _brief(s, "DC_Houston", week=27).data["network_experience"]
    assert x["rfid"] == {"full": 1, "partial": 0, "cancelled": 1, "failed": 1}
    assert _brief(s, "DC_Houston", week=70).data["network_experience"]["rfid"]["failed"] == 0  # older than a year


def test_rules_agents_scale_the_expected_saving_by_network_sentiment():
    from tests.test_rules import brief
    def acts(exp):
        b = brief({"shipping": 1300000})  # routing saves ~8k/week vs 3k cost: pays back in ~60 weeks on its own
        b.data["network_experience"] = {"routing": exp}; b.data["rules"]["network_sentiment"] = 0.5
        return [x["action"] for x in json.loads(RulesPolicy(np.random.default_rng(0)).decide(b).raw)["decisions"]]
    assert acts({"full": 0, "partial": 0, "cancelled": 0, "failed": 0}) == ["adopt"]
    assert acts({"full": 0, "partial": 0, "cancelled": 20, "failed": 20}) == []


# R4 ---------------------------------------------------------------------------------------------------------

def test_two_failures_end_a_firms_attempts_at_a_technology(baseline, monkeypatch):
    import sciti.engine.adoption as adoption
    s = make_state(baseline, weeks=120); s.cfg.assumptions.implementation_risk = True
    assert Assumptions().max_attempts == 2
    monkeypatch.setattr(adoption, "implementation_draw", lambda seed, node, tech, week: 0.01)
    for w in (1, 40):
        adopt(s, "DC_Houston", "routing", w)
        s.events.append({"week": w + 26, "type": "implementation_cancelled", "node": "DC_Houston", "tech": "routing"})
        del s.holdings["DC_Houston"]["routing"]
    assert "routing" not in [e["id"] for e in _brief(s, "DC_Houston", week=79).data["eligible_technologies"]]
    with pytest.raises(AdoptionError, match="two"):
        adopt(s, "DC_Houston", "routing", 79)
    assert "DC_Houston" not in group_members(s.net, s.holdings, s.catalog, "MFG_US", "routing", ["DC_Houston"],
                                             s.events, s.cfg.assumptions.max_attempts)
