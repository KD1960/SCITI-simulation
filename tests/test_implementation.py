"""Implementation risk: an adoption can fail, partly work, or fully work (docs/sciti2/implementation-failure-evidence.md)."""
import pytest

from sciti.config import Assumptions
from sciti.engine.adoption import adopt, implementation_outcome
from sciti.engine.ops import step_week
from sciti.tech.catalog import TechHolding, load_catalog
from sciti.tech.effects import effective_params
from tests.helpers import make_state


def test_outcome_thresholds_and_small_firm_odds():
    """Blockchain: p_fail 0.65, p_partial 0.25 (fraction 0.4), so a CM fails below 0.65, is partial
    below 0.90, and full above. Suppliers are the small firms: failure odds x1.75, i.e.
    0.65/0.35 * 1.75 = 3.25 -> p_fail 3.25/4.25 = 0.7647; partial keeps its share of the rest:
    0.25 * (1 - 0.7647) / 0.35 = 0.1681."""
    bc, A = load_catalog()["blockchain"], Assumptions()
    assert (bc.p_fail, bc.p_partial, bc.partial_fraction) == (0.65, 0.25, 0.4)
    assert implementation_outcome(0.64, bc, "CM", A) == ("fail", 0.0)
    assert implementation_outcome(0.66, bc, "CM", A) == ("partial", 0.4)
    assert implementation_outcome(0.91, bc, "CM", A) == ("full", 1.0)
    assert implementation_outcome(0.76, bc, "Supplier", A) == ("fail", 0.0)
    assert implementation_outcome(0.77, bc, "Supplier", A) == ("partial", 0.4)
    assert implementation_outcome(0.7647 + 0.1681 + 0.001, bc, "Supplier", A) == ("full", 1.0)
    off = Assumptions(implementation_risk=False)
    assert implementation_outcome(0.01, bc, "Supplier", off) == ("full", 1.0)


def test_partial_success_scales_the_effect(baseline):
    """A partial blockchain pair at fraction 0.4 cuts defects by 0.4 x 18%: 1 - 0.18 * 0.4 = 0.928.
    In a coalition the 25% bonus applies to the scaled effect: 1 - 0.072 * 1.25 = 0.91."""
    s = make_state(baseline)
    h = {"Supplier_1": {"blockchain": TechHolding("blockchain", 1, 1, fraction=0.4)},
         "CM_1": {"blockchain": TechHolding("blockchain", 1, 1)}}
    p = effective_params("Supplier_1", 2, h, s.catalog, s.net, s.base["Supplier_1"])
    assert p["defect_mult"] == pytest.approx(0.928)
    h["Supplier_1"]["blockchain"] = TechHolding("blockchain", 1, 1, "g1", fraction=0.4)
    assert effective_params("Supplier_1", 2, h, s.catalog, s.net, s.base["Supplier_1"])["defect_mult"] == pytest.approx(0.91)


def test_failed_implementation_costs_money_and_never_switches_on(baseline, monkeypatch):
    """A failing routing project at a DC: the one-time cost is spent, the weekly cost runs until the
    project is abandoned (fail_after_weeks = 104), it never changes the DC's parameters or counts as
    an active partner, and afterwards the DC may try again."""
    import sciti.engine.adoption as adoption
    s = make_state(baseline, weeks=120)
    s.cfg.assumptions.implementation_risk = True
    monkeypatch.setattr(adoption, "implementation_draw", lambda seed, node, tech, week: 0.01)
    ev = adopt(s, "DC_Houston", "routing", 1)
    assert ev["outcome"] == "fail" and ev["one_time"] == 300000
    h = s.holdings["DC_Houston"]["routing"]
    assert h.fails_week == 1 + 104
    tech_cost = 0.0
    for t in range(1, 108):
        step_week(s, t)
        assert s.nodes["DC_Houston"].params["ship_cost_mult"] == 1.0
        tech_cost += s.nodes["DC_Houston"].ledger["tech"]
    assert "routing" not in s.holdings["DC_Houston"]
    assert tech_cost == pytest.approx(300000 + 104 * 3000)
    assert [e for e in s.events if e["type"] == "implementation_failed"] == \
        [{"week": 105, "type": "implementation_failed", "node": "DC_Houston", "tech": "routing"}]
    monkeypatch.setattr(adoption, "implementation_draw", lambda seed, node, tech, week: 0.99)
    assert adopt(s, "DC_Houston", "routing", 108)["outcome"] == "full"


def test_draws_are_keyed_so_runs_replay(baseline):
    from sciti.rng import implementation_draw
    a = implementation_draw(1, "DC_Houston", "routing", 14)
    assert a == implementation_draw(1, "DC_Houston", "routing", 14) and 0 <= a < 1
    assert len({a, implementation_draw(2, "DC_Houston", "routing", 14), implementation_draw(1, "DC_Sofia", "routing", 14),
                implementation_draw(1, "DC_Houston", "rfid", 14), implementation_draw(1, "DC_Houston", "routing", 27)}) == 5


def test_briefs_show_the_odds_and_the_payback_rule_discounts_by_them(baseline):
    """Agents never see an outcome in advance, but they see the odds. Routing at a DC: fail 0.15,
    partial 0.50 at 0.6, so the expected share of the benefit is 0.35 + 0.50 * 0.6 = 0.65. The payback
    rule multiplies its expected saving by that share: a saving of 16,000/week becomes 10,400, so the
    payback on 300,000 at 3,000/week running cost goes from ~23 weeks to ~41 weeks."""
    import json

    import numpy as np

    from sciti.decide.briefs import build_brief, make_personas
    from sciti.decide.rules import RulesPolicy
    from tests.test_rules import brief
    s = make_state(baseline)
    s.cfg.assumptions.implementation_risk = True
    personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
    b = build_brief(s, "DC_Houston", 14, "proposal", personas["DC_Houston"], [], "partners", 1)
    routing = next(e for e in b.data["eligible_technologies"] if e["id"] == "routing")
    assert routing["implementation_odds"] == {"fail": 0.15, "partial": 0.5, "partial_benefit": 0.6, "expected_benefit": 0.65}
    s.cfg.assumptions.implementation_risk = False
    b = build_brief(s, "DC_Houston", 14, "proposal", personas["DC_Houston"], [], "partners", 1)
    assert all("implementation_odds" not in e for e in b.data["eligible_technologies"])

    def weeks(odds, horizon):
        e = {"id": "routing", "one_time_cost": 300000, "weekly_cost": 3000, "network_requirement": "solo", "group_bonus": 0.25}
        if odds:
            e["implementation_odds"] = routing["implementation_odds"]
        class NoNoise:
            def lognormal(self, *a):
                return 1.0
        return json.loads(RulesPolicy(NoNoise()).decide(brief({"shipping": 13 * 200000}, horizon=horizon, eligible=[e])).raw)["decisions"]
    assert weeks(False, 30) and not weeks(True, 30)   # 23 weeks passes a 30-week horizon; 41 does not
    assert weeks(True, 45)[0]["reason"] == "payback about 41 weeks"


def test_learning_cuts_the_odds_of_failure(baseline):
    """Learning multiplies the ODDS of failure (docs/sciti2/learning-evidence.md, MID values):
    x0.75 after one failed attempt at the same technology, x0.60 after two or more; x0.87 per
    technology the firm already runs successfully (floor 0.50); x0.88 per direct partner already
    running this technology successfully (floor 0.60). Failing or not-yet-live holdings teach nothing.
    Routing at a DC (p_fail 0.15, odds 0.1765): one earlier failure, two live technologies, and one
    live partner give 0.75 * 0.87^2 * 0.88 = 0.4996 -> odds 0.0882 -> p_fail 0.0810."""
    from sciti.engine.adoption import implementation_odds, learning_multiplier
    s = make_state(baseline)
    s.cfg.assumptions.implementation_risk = True
    assert learning_multiplier(s, "DC_Houston", "routing", 20) == 1.0
    s.events.append({"week": 5, "type": "implementation_failed", "node": "DC_Houston", "tech": "routing"})
    assert learning_multiplier(s, "DC_Houston", "routing", 20) == pytest.approx(0.75)
    s.holdings["DC_Houston"]["rfid"] = TechHolding("rfid", 1, 7)
    s.holdings["DC_Houston"]["risk_intel"] = TechHolding("risk_intel", 1, 5, fraction=0.35)   # partial still teaches
    s.holdings["DC_Houston"]["wh_robotics"] = TechHolding("wh_robotics", 1, 17, fails_week=105)  # failing: no lesson yet
    s.holdings["DC_Houston"]["aps_like"] = TechHolding("ml_forecast", 15, 23)                  # not live until week 23
    s.holdings["MFG_US"]["routing"] = TechHolding("routing", 1, 5)
    s.holdings["Retail_1"]["routing"] = TechHolding("routing", 1, 5, fails_week=105)
    m = learning_multiplier(s, "DC_Houston", "routing", 20)
    assert m == pytest.approx(0.75 * 0.87 ** 2 * 0.88)
    p_fail, p_partial = implementation_odds(s.catalog["routing"], "DC", s.cfg.assumptions, m)
    assert p_fail == pytest.approx(0.0810, abs=2e-4)
    assert p_partial == pytest.approx(0.50 * (1 - p_fail) / 0.85)   # partial and full share what failure gives up
    s.events.append({"week": 9, "type": "implementation_failed", "node": "DC_Houston", "tech": "routing"})
    s.events.append({"week": 12, "type": "implementation_failed", "node": "DC_Houston", "tech": "routing"})
    assert learning_multiplier(s, "DC_Houston", "routing", 20) == pytest.approx(0.60 * 0.87 ** 2 * 0.88)
    for i in range(8):   # floors: many live technologies and partners cannot push below 0.50 and 0.60
        s.holdings["DC_Houston"][f"x{i}"] = TechHolding("rfid", 1, 2)
    for r in s.net.partners("DC_Houston"):
        s.holdings[r]["routing"] = TechHolding("routing", 1, 2)
    assert learning_multiplier(s, "DC_Houston", "routing", 20) == pytest.approx(0.60 * 0.50 * 0.60)


def test_information_technologies_are_concave_in_depth(baseline):
    """depth_exponent 0.5 for control tower and risk intelligence (Gavirneni et al. 1999: partial
    information captures most of the value): a 0.4-deep control tower with its one downstream partner
    live gives visibility 0.6 * 0.4^0.5 = 0.379, not 0.6 * 0.4 = 0.24. Physical technologies stay
    linear: a 0.6-deep routing project cuts shipping cost by 8% * 0.6."""
    s = make_state(baseline)
    cat = s.catalog
    assert (cat["control_tower"].depth_exponent, cat["risk_intel"].depth_exponent, cat["routing"].depth_exponent) == (0.5, 0.5, 1.0)
    store = s.net.downstream["DC_Houston"][0]
    h = {n: {} for n in s.net.order}
    for r in s.net.downstream["DC_Houston"]:
        h[r]["control_tower"] = TechHolding("control_tower", 1, 1)
    h["DC_Houston"]["control_tower"] = TechHolding("control_tower", 1, 1, fraction=0.4)
    h["DC_Houston"]["routing"] = TechHolding("routing", 1, 1, fraction=0.6)
    p = effective_params("DC_Houston", 2, h, cat, s.net, s.base["DC_Houston"])
    assert p["visibility"] == pytest.approx(0.6 * 0.4 ** 0.5)
    assert p["ship_cost_mult"] == pytest.approx(1 - 0.08 * 0.6)
    assert store in h


def test_a_group_adopting_a_multi_party_technology_is_one_project(baseline, monkeypatch):
    """The measured failure rates are per project. A blockchain pair or control tower chain adopted
    as a group gets ONE project draw at the catalog odds (blockchain 0.65 fail / 0.25 partial at 0.4),
    keyed by the group id: the members fail or go live together. The project draw replaces the
    members' own failure draws (no double count); each member only draws how deep its own onboarding
    goes: shallow with the catalog's odds of partial among survivors, 0.25 / 0.35 = 0.714 for a CM
    (suppliers' odds x1.75 -> 0.814), and its depth is the lesser of the project's and its own.
    Solo technologies adopted in a group, and firms adopting alone, draw as before."""
    import sciti.engine.adoption as adoption
    draws = {}
    monkeypatch.setattr(adoption, "implementation_draw", lambda seed, key, tech, week: draws[key])

    def outcomes(project_u, members):
        s = make_state(baseline)
        s.cfg.assumptions.implementation_risk = True
        draws.clear()
        draws.update({"g1": project_u, **members})
        return {m: (adopt(s, m, "blockchain", 1, "g1")["outcome"], s.holdings[m]["blockchain"].fraction,
                    s.holdings[m]["blockchain"].fails_week) for m in members}

    dead = outcomes(0.64, {"CM_1": 0.99, "Supplier_1": 0.99})           # the platform fails: everyone fails
    assert {m: o[0] for m, o in dead.items()} == {"CM_1": "fail", "Supplier_1": "fail"}
    assert dead["CM_1"][2] == 1 + 52
    full = outcomes(0.95, {"CM_1": 0.01, "CM_2": 0.70, "CM_3": 0.72, "Supplier_1": 0.80, "Supplier_2": 0.82})
    assert {m: o[0] for m, o in full.items()} == {"CM_1": "partial", "CM_2": "partial", "CM_3": "full",
                                                   "Supplier_1": "partial", "Supplier_2": "full"}   # nobody fails alone
    assert full["CM_2"][1] == 0.4 and full["CM_3"][1] == 1.0
    shallow = outcomes(0.70, {"CM_3": 0.99})                             # a shallow platform caps a full member at 0.4
    assert shallow["CM_3"][:2] == ("partial", 0.4)

    s = make_state(baseline)
    s.cfg.assumptions.implementation_risk = True
    draws.clear()
    draws.update({"DC_Houston": 0.22, "CM_1": 0.66})
    assert adopt(s, "DC_Houston", "rfid", 1, "g2")["outcome"] == "partial"   # solo tech in a group: own odds (0.20 fail)
    assert adopt(s, "CM_1", "blockchain", 1)["outcome"] == "partial"         # adopting alone: catalog odds (0.65 fail)
    s.cfg.assumptions.group_project_draw = False
    draws.update({"CM_2": 0.64})
    assert adopt(s, "CM_2", "blockchain", 1, "g3")["outcome"] == "fail"      # switch off: per-member catalog odds again
