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
