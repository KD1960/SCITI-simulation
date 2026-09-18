import json

import numpy as np

from sciti.config import Config, DecisionCfg
from sciti.decide.interface import Brief, validate_reply, parse_reply
from sciti.decide.rules import RulesPolicy
from sciti.runner import run


def brief(costs, budget=1e9, horizon=104, risk="balanced", eligible=None, pass_="proposal", proposals=()):
    eligible = eligible or [{"id": "routing", "one_time_cost": 300000, "weekly_cost": 3000,
                             "network_requirement": "solo", "group_bonus": 0.25}]
    return Brief("DC_Houston", "DC", 14, 2, pass_, {
        "you": {"persona": {"risk": risk, "budget_share": 0.05, "horizon_weeks": horizon}},
        "last_quarter": {"costs": costs}, "budget_available": budget,
        "eligible_technologies": eligible, "held": [], "partners": [{"id": "MFG_US", "role": "MFG"}],
        "proposals": list(proposals), "rules": {"max_new_adoptions": 1}})


def test_adopts_when_payback_short():
    b = brief({"shipping": 13 * 200000})  # saves ~16k/week vs 3k cost → payback ~23 weeks
    ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(0)).decide(b).raw), b, 1)
    assert [(d.tech, d.action) for d in ds] == [("routing", "adopt")]


def test_skips_when_no_saving_or_no_budget():
    p = RulesPolicy(np.random.default_rng(0))
    assert json.loads(p.decide(brief({"shipping": 0})).raw) == {"decisions": []}
    assert json.loads(p.decide(brief({"shipping": 13 * 200000}, budget=10)).raw) == {"decisions": []}


def test_response_accepts_affordable_share():
    prop = {"group_id": "g1", "tech": "routing", "from": "MFG_US", "members": ["DC_Houston", "MFG_US"],
            "your_cost_share": 350000}
    b = brief({"shipping": 13 * 200000}, pass_="response", proposals=[prop])
    ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(1)).decide(b).raw), b, 1)
    assert ds[0].action == "accept_group" and ds[0].group_id == "g1"


def test_rules_run_is_deterministic_and_adopts(baseline_path, tmp_path):
    c = Config(name="r", seed=5, weeks=52, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    a = run(c, run_dir=tmp_path / "a")
    b = run(c, run_dir=tmp_path / "b")
    assert (a / "events.jsonl").read_bytes() == (b / "events.jsonl").read_bytes()
    summary = json.loads((a / "summary.json").read_text())
    assert summary["adoptions"] > 0


def test_rules_run_forms_coalitions(baseline_path, tmp_path):
    c = Config(name="r", seed=5, weeks=52, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    out = run(c, run_dir=tmp_path / "a")
    summary = json.loads((out / "summary.json").read_text())
    assert summary["coalitions"] > 0


def test_response_declines_unknown_tech_without_raising():
    prop = {"group_id": "g1", "tech": "custom_x", "from": "MFG_US", "members": ["DC_Houston", "MFG_US"],
            "your_cost_share": 350000}
    b = brief({"shipping": 13 * 200000}, pass_="response", proposals=[prop])
    ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(1)).decide(b).raw), b, 1)
    assert ds[0].action == "decline_group" and ds[0].group_id == "g1"


def test_follower_accepts_a_group_invite_when_the_first_year_cost_is_small():
    """An agent put on rules by decision.rules_roles goes along with a partner's group when the
    first-year cost (its one-time share + 52 weeks of running cost) is at most
    follow_revenue_share (1%) of its yearly revenue (4 x last quarter) and the share fits its
    budget, even with no payback. Control tower at a DC runs 7,000/week: 250,000 + 364,000 =
    614,000 against 1% of 4 x 20M = 800,000 -> accept; against 4 x 15M = 600,000 -> decline.
    Without the follower flag the payback rule alone decides (no savings here -> decline)."""
    prop = {"group_id": "g1", "tech": "control_tower", "from": "MFG_US", "members": ["DC_Houston", "MFG_US"],
            "your_cost_share": 250000}
    def answer(revenue, follows, budget=1e9):
        b = brief({}, budget=budget, pass_="response", proposals=[prop])
        b.data["last_quarter"]["revenue"] = revenue
        if follows:
            b.data["rules"]["follow_revenue_share"] = 0.01
        return validate_reply(parse_reply(RulesPolicy(np.random.default_rng(1)).decide(b).raw), b, 1)[0].action
    assert answer(20e6, follows=True) == "accept_group"
    assert answer(15e6, follows=True) == "decline_group"
    assert answer(20e6, follows=True, budget=100000) == "decline_group"
    assert answer(20e6, follows=False) == "decline_group"


def test_rules_roles_briefs_carry_the_follow_share_and_others_do_not(baseline):
    from sciti.decide.briefs import build_brief, make_personas
    from tests.helpers import make_state
    s = make_state(baseline)
    s.cfg.decision.rules_roles = ["Supplier"]
    personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
    sup = build_brief(s, "Supplier_1", 14, "response", personas["Supplier_1"], [], "partners", 1, proposals=[])
    dc = build_brief(s, "DC_Houston", 14, "response", personas["DC_Houston"], [], "partners", 1, proposals=[])
    assert sup.data["rules"]["follow_revenue_share"] == 0.005
    assert "follow_revenue_share" not in dc.data["rules"]


def test_insurance_habit_buys_cheap_protection_after_the_payback_picks():
    """decision.insurance_techs: a rules agent also buys a listed technology that shows no payback
    when its first-year cost (one-time + 52 weeks) is at most insurance_revenue_share of yearly
    revenue and the one-time cost fits the budget. Payback picks come first and share the
    quarterly limit. Risk intel at a DC: 300,000 + 52 x 3,000 = 456,000; 0.5% of 4 x 25M =
    500,000 -> buy; of 4 x 20M = 400,000 -> skip."""
    ri = {"id": "risk_intel", "one_time_cost": 300000, "weekly_cost": 3000, "network_requirement": "solo",
          "group_bonus": 0.25}
    routing = {"id": "routing", "one_time_cost": 300000, "weekly_cost": 3000, "network_requirement": "solo",
               "group_bonus": 0.25}
    def picks(revenue, costs, eligible, max_new=1, habit=True, budget=1e9):
        b = brief(costs, budget=budget, eligible=eligible)
        b.data["last_quarter"]["revenue"] = revenue
        b.data["rules"]["max_new_adoptions"] = max_new
        if habit:
            b.data["rules"]["insurance"] = {"techs": ["risk_intel"], "revenue_share": 0.005}
        ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(0)).decide(b).raw), b, max_new)
        return [(d.tech, d.action) for d in ds]
    assert picks(25e6, {}, [ri]) == [("risk_intel", "adopt")]
    assert picks(20e6, {}, [ri]) == []
    assert picks(25e6, {}, [ri], budget=100000) == []
    assert picks(25e6, {}, [ri], habit=False) == []
    ship = {"shipping": 13 * 200000}
    assert picks(25e6, ship, [ri, routing]) == [("routing", "adopt")]  # payback pick takes the only slot
    assert picks(25e6, ship, [ri, routing], max_new=2) == [("routing", "adopt"), ("risk_intel", "adopt")]
    # with one slot and two affordable protections, the one listed first wins (not alphabetical order)
    aps = dict(ri, id="aps")
    b = brief({}, eligible=[aps, ri])
    b.data["last_quarter"]["revenue"] = 25e6
    b.data["rules"]["insurance"] = {"techs": ["risk_intel", "aps"], "revenue_share": 0.005}
    assert [d["tech"] for d in json.loads(RulesPolicy(np.random.default_rng(0)).decide(b).raw)["decisions"]] == ["risk_intel"]
