import json

import numpy as np
import pytest

from sciti.config import Assumptions
from sciti.decide.briefs import build_brief, make_personas
from sciti.decide.interface import Brief, ReplyError, parse_reply, validate_reply
from sciti.decide.mock import MockPolicy
from sciti.engine.adoption import adopt
from sciti.engine.ops import step_week
from tests.helpers import make_state


def brief(pass_="proposal", eligible=("routing", "rfid", "control_tower"), held=(), partners=("MFG_US", "MFG_China"),
          proposals=()):
    return Brief("DC_Houston", "DC", 14, 2, pass_, {
        "eligible_technologies": [{"id": t} for t in eligible], "held": list(held),
        "partners": [{"id": p} for p in partners], "proposals": [{"group_id": g, "tech": "routing"} for g in proposals]})


def test_parse_reply_extracts_json_from_prose():
    assert parse_reply('Sure! {"decisions": []} done') == {"decisions": []}
    with pytest.raises(ReplyError):
        parse_reply("no json here")


def test_valid_proposal_reply():
    obj = {"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "cuts freight"},
                         {"tech": "control_tower", "action": "propose_group", "partners": ["chain"], "reason": "x"}]}
    ds = validate_reply(obj, brief(), max_new=2)
    assert [d.action for d in ds] == ["adopt", "propose_group"]


@pytest.mark.parametrize("obj,msg", [
    ({"nope": []}, "decisions"),
    ({"decisions": [{"tech": "wh_robotics", "action": "adopt", "partners": [], "reason": "x"}]}, "not eligible"),
    ({"decisions": [{"tech": "routing", "action": "fly", "partners": [], "reason": "x"}]}, "action"),
    ({"decisions": [{"tech": "routing", "action": "propose_group", "partners": ["Retail_8"], "reason": "x"}]}, "partner"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "word " * 41}]}, "words"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "a"},
                    {"tech": "rfid", "action": "adopt", "partners": [], "reason": "b"}]}, "at most"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "a"},
                    {"tech": "routing", "action": "skip", "partners": [], "reason": "b"}]}, "twice"),
    ({"decisions": [{"tech": "routing", "action": "drop", "partners": [], "reason": "a"}]}, "not held"),
    ({"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "a"}]}, "action"),
    ({"decisions": [{"tech": ["routing"], "action": "adopt", "partners": [], "reason": "x"}]}, "tech"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": {"dict": "bad"}}]}, "reason"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "x", "group_id": ["bad"]}]}, "group"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": None}]}, "reason"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": 0}]}, "reason"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": False}]}, "reason"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": []}]}, "reason"),
])
def test_invalid_replies_rejected(obj, msg):
    with pytest.raises(ReplyError, match=msg):
        validate_reply(obj, brief(), max_new=1)


def test_decision_without_reason_key_is_valid():
    obj = {"decisions": [{"tech": "routing", "action": "adopt", "partners": []}]}
    ds = validate_reply(obj, brief(), max_new=1)
    assert ds[0].reason == ""


def test_response_pass_needs_known_group():
    b = brief(pass_="response", proposals=["q2_MFG_US_routing"])
    ok = {"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "y",
                         "group_id": "q2_MFG_US_routing"}]}
    assert validate_reply(ok, b, max_new=1)[0].group_id == "q2_MFG_US_routing"
    bad = {"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "y",
                          "group_id": "q9_other"}]}
    with pytest.raises(ReplyError, match="group"):
        validate_reply(bad, b, max_new=1)


def test_response_pass_tech_must_match_proposal():
    b = brief(pass_="response", proposals=["q2_MFG_US_routing"])
    mismatched = {"decisions": [{"tech": "rfid", "action": "accept_group", "partners": [], "reason": "y",
                                 "group_id": "q2_MFG_US_routing"}]}
    with pytest.raises(ReplyError, match="tech"):
        validate_reply(mismatched, b, max_new=1)


def test_personas_seeded(baseline):
    s = make_state(baseline)
    a = make_personas(s.net, Assumptions(), np.random.default_rng(3))
    b = make_personas(s.net, Assumptions(), np.random.default_rng(3))
    assert a == b and len(a) == 48
    assert a["Retail_1"]["risk"] in ("cautious", "balanced", "bold")


def test_brief_contents(baseline):
    s = make_state(baseline)
    for t in range(1, 14):
        step_week(s, t)
    adopt(s, "DC_Houston", "routing", 13)
    personas = make_personas(s.net, s.cfg.assumptions, np.random.default_rng(0))
    b = build_brief(s, "DC_Houston", 14, "proposal", personas["DC_Houston"], recent=[], visibility="partners", max_new=1)
    ids = [e["id"] for e in b.data["eligible_technologies"]]
    assert "routing" not in ids and "wh_robotics" in ids and "blockchain" not in ids
    assert b.data["held"] == ["routing"]
    assert [p["id"] for p in b.data["partners"]] == ["MFG_China", "MFG_US", "Retail_1", "Retail_2"]
    assert "network_adoption_counts" not in b.data
    assert "co2_kg" in b.data["last_quarter"] and b.data["last_quarter"]["co2_kg"] > 0
    json.dumps(b.data)  # must be JSON-serializable


def test_mock_policy_script_sequence():
    m = MockPolicy([{"agent": "DC_Houston", "week": 14, "pass": "proposal", "replies": ["bad", '{"decisions": []}']}])
    b = brief()
    assert m.decide(b).raw == "bad"
    assert m.decide(b, feedback="err").raw == '{"decisions": []}'
    assert m.decide(Brief("Retail_1", "Retail", 14, 2, "proposal", {})).raw == '{"decisions": []}'
