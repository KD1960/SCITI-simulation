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
