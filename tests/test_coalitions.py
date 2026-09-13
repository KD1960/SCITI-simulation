import json

from sciti.config import Config, DecisionCfg
from sciti.coalitions import group_members
from sciti.runner import run
from tests.helpers import make_state


def reply(*decisions):
    return json.dumps({"decisions": list(decisions)})


def d(tech, action, partners=(), group_id=None, reason="ok"):
    out = {"tech": tech, "action": action, "partners": list(partners), "reason": reason}
    if group_id:
        out["group_id"] = group_id
    return out


def mock_cfg(baseline_path, tmp_path, script, **decision):
    return Config(name="m", seed=2, weeks=27, baseline_path=str(baseline_path), output_dir=str(tmp_path),
                  decision=DecisionCfg(policy="mock", mock_script=script, **decision))


def events(run_dir):
    return [json.loads(x) for x in (run_dir / "events.jsonl").read_text().splitlines()]


def test_group_members_chain_and_network(baseline):
    s = make_state(baseline)
    chain = group_members(s.net, s.holdings, s.catalog, "DC_Shanghai", "control_tower", ["chain"])
    assert "Retail_8" in chain and "MFG_China" in chain and "Supplier_1" in chain and "Retail_1" not in chain
    net_all = group_members(s.net, s.holdings, s.catalog, "DC_Shanghai", "wh_robotics", ["network"])
    assert net_all == ["DC_Dubai", "DC_Houston", "DC_Shanghai", "DC_Sofia"]
    pair = group_members(s.net, s.holdings, s.catalog, "CM_1", "blockchain", ["Supplier_1", "Supplier_2"])
    assert pair == ["CM_1", "Supplier_1", "Supplier_2"]


def test_solo_adopt_logged_and_applied(baseline_path, tmp_path):
    script = [{"agent": "MFG_US", "week": 14, "pass": "proposal", "replies": [reply(d("routing", "adopt"))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = [e for e in events(out) if e["type"] == "adopt"]
    assert ev == [{"week": 14, "type": "adopt", "node": "MFG_US", "tech": "routing", "coalition": None, "one_time": 400000}]
    logs = [json.loads(x) for x in (out / "decisions.jsonl").read_text().splitlines()]
    assert len([l for l in logs if l["pass"] == "proposal"]) == 48 * 3
    mine = [l for l in logs if l["agent"] == "MFG_US" and l["week"] == 14][0]
    assert mine["parsed"][0]["action"] == "adopt" and mine["fallback"] is False


def test_dyad_forms_when_partner_accepts(baseline_path, tmp_path):
    gid = "q2_CM_1_blockchain"
    script = [
        {"agent": "CM_1", "week": 14, "pass": "proposal", "replies": [reply(d("blockchain", "propose_group", ["Supplier_1"]))]},
        {"agent": "Supplier_1", "week": 14, "pass": "response",
         "replies": [reply(d("blockchain", "accept_group", group_id=gid))]},
    ]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    co = [e for e in ev if e["type"] == "coalition"]
    assert co == [{"week": 14, "type": "coalition", "id": gid, "tech": "blockchain",
                   "members": ["CM_1", "Supplier_1"], "kind": "dyad"}]
    shares = sorted(e["one_time"] for e in ev if e["type"] == "adopt")
    assert shares == [200000.0, 200000.0]  # (300k + 100k) / 2


def test_group_fails_when_partner_declines(baseline_path, tmp_path):
    script = [{"agent": "CM_1", "week": 14, "pass": "proposal",
               "replies": [reply(d("blockchain", "propose_group", ["Supplier_1"]))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    assert [e["type"] for e in ev if e["type"].startswith("coalition")] == ["coalition_failed"]
    assert not [e for e in ev if e["type"] == "adopt"]


def test_bad_reply_retry_then_fallback(baseline_path, tmp_path):
    script = [{"agent": "Retail_2", "week": 14, "pass": "proposal", "replies": ["garbage", "still garbage"]},
              {"agent": "Retail_3", "week": 14, "pass": "proposal",
               "replies": ["garbage", reply(d("rfid", "skip"))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    logs = {(l["agent"], l["week"], l["pass"]): l for l in map(json.loads, (out / "decisions.jsonl").read_text().splitlines())}
    r2, r3 = logs[("Retail_2", 14, "proposal")], logs[("Retail_3", 14, "proposal")]
    assert r2["fallback"] is True and r2["error"] and r2["retry_error"]
    assert r3["fallback"] is False and r3["error"] and r3["retry_error"] is None
    assert r3["parsed"] == [{"tech": "rfid", "action": "skip", "partners": [], "reason": "ok", "group_id": None}]


def test_over_budget_rejected(baseline_path, tmp_path):
    script = [{"agent": "Retail_6", "week": 14, "pass": "proposal", "replies": [reply(d("control_tower", "propose_group", ["network"]))]},
              {"agent": "DC_Sofia", "week": 14, "pass": "proposal", "replies": [reply(d("wh_robotics", "adopt"))]}]
    c = mock_cfg(baseline_path, tmp_path, script)
    c.assumptions.persona_budget_share = (0.0, 0.0)
    out = run(c, run_dir=tmp_path / "r")
    ev = events(out)
    assert {"week": 14, "type": "rejected", "node": "DC_Sofia", "tech": "wh_robotics", "reason": "budget"} in ev
    assert not [e for e in ev if e["type"] == "adopt"]
