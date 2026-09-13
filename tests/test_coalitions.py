import json

from sciti.config import Config, DecisionCfg
from sciti.coalitions import DecisionContext, group_members, run_decision_round
from sciti.decide.briefs import make_personas
from sciti.decide.interface import Reply
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


def test_proposer_limited_to_one_new_adoption_per_quarter(baseline_path, tmp_path):
    gid1 = "q2_CM_1_blockchain"
    gid2 = "q2_Supplier_1_control_tower"
    script = [
        {"agent": "CM_1", "week": 14, "pass": "proposal", "replies": [reply(d("blockchain", "propose_group", ["Supplier_1"]))]},
        {"agent": "Supplier_1", "week": 14, "pass": "proposal", "replies": [reply(d("control_tower", "propose_group", ["CM_1"]))]},
        {"agent": "CM_1", "week": 14, "pass": "response", "replies": [reply(d("control_tower", "accept_group", group_id=gid2))]},
        {"agent": "Supplier_1", "week": 14, "pass": "response", "replies": [reply(d("blockchain", "accept_group", group_id=gid1))]},
    ]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    adopts = [e for e in ev if e["type"] == "adopt" and e["week"] == 14]
    assert len([e for e in adopts if e["node"] == "CM_1"]) <= 1
    assert len([e for e in adopts if e["node"] == "Supplier_1"]) <= 1


def test_proposer_can_join_another_group(baseline_path, tmp_path):
    gid_a = "q2_Supplier_1_blockchain"  # Supplier_1 -> CM_1
    gid_b = "q2_CM_1_blockchain"        # CM_1 -> Supplier_1, Supplier_2
    script = [
        {"agent": "Supplier_1", "week": 14, "pass": "proposal", "replies": [reply(d("blockchain", "propose_group", ["CM_1"]))]},
        {"agent": "CM_1", "week": 14, "pass": "proposal",
         "replies": [reply(d("blockchain", "propose_group", ["Supplier_1", "Supplier_2"]))]},
        {"agent": "CM_1", "week": 14, "pass": "response", "replies": [reply(d("blockchain", "accept_group", group_id=gid_a))]},
        {"agent": "Supplier_1", "week": 14, "pass": "response", "replies": [reply(d("blockchain", "accept_group", group_id=gid_b))]},
        {"agent": "Supplier_2", "week": 14, "pass": "response", "replies": [reply(d("blockchain", "decline_group", group_id=gid_b))]},
    ]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    co = [e for e in ev if e["type"] == "coalition" and e["tech"] == "blockchain"]
    assert len(co) == 1
    assert sorted(co[0]["members"]) == ["CM_1", "Supplier_1"]
    adopts = [e for e in ev if e["type"] == "adopt" and e["week"] == 14]
    assert len([e for e in adopts if e["node"] == "CM_1"]) == 1
    assert len([e for e in adopts if e["node"] == "Supplier_1"]) == 1
    failed = [e for e in ev if e["type"] == "coalition_failed"]
    assert len(failed) == 1
    assert failed[0]["reason"] in ("quota", "held", "acceptance")


def test_formation_never_exceeds_budget(baseline, baseline_path, tmp_path, monkeypatch):
    import sciti.coalitions as coalitions
    s = make_state(baseline)
    tech = s.catalog["control_tower"]
    members = s.net.order
    total = sum(tech.cost_one_time[s.net.nodes[m].role] for m in members)
    unfiltered_share = total / len(members)
    zero_budget_nodes = {"Supplier_1", "Supplier_2", "Supplier_3"}
    big_budget = unfiltered_share + 1.0

    def fake_budget(state, node_id, persona, recent):
        return 0.0 if node_id in zero_budget_nodes else big_budget

    monkeypatch.setattr(coalitions, "budget_available", fake_budget)

    gid = "q2_MFG_US_control_tower"
    script = [{"agent": "MFG_US", "week": 14, "pass": "proposal",
               "replies": [reply(d("control_tower", "propose_group", ["network"]))]}]
    for n in members:
        if n == "MFG_US":
            continue
        script.append({"agent": n, "week": 14, "pass": "response",
                       "replies": [reply(d("control_tower", "accept_group", group_id=gid))]})
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    for e in [e for e in ev if e["type"] == "adopt"]:
        assert e["one_time"] <= big_budget + 1e-6
    rejected_zero = [e for e in ev if e["type"] == "rejected" and e["node"] in zero_budget_nodes]
    assert len(rejected_zero) == len(zero_budget_nodes)


def test_invalid_fallback_reply_does_not_crash(baseline):
    class StubWriter:
        def __init__(self):
            self.records = []

        def log_decision(self, record):
            self.records.append(record)

    class BadPolicy:
        name = "bad"

        def decide(self, brief, feedback=None):
            return Reply(brief.agent, "not json at all")

    class BadFallback:
        name = "badfallback"

        def decide(self, brief, feedback=None):
            return Reply(brief.agent, "still not json")

    s = make_state(baseline)
    personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
    writer = StubWriter()
    ctx = DecisionContext(policy=BadPolicy(), fallback=BadFallback(), writer=writer, personas=personas, recent={})
    run_decision_round(s, 14, ctx)
    rec = next(r for r in writer.records if r["pass"] == "proposal")
    assert rec["fallback"] is True
    assert rec["fallback_error"]
    assert rec["parsed"] == []


def test_retry_fallback_reply_is_logged_as_fallback(baseline):
    """When the retry itself comes from the fallback policy (e.g. spend cap hit mid-round),
    the record must show fallback=True and carry the fallback's error -- not look like a
    normal LLM answer (review finding #3, 2026-09-13)."""
    class StubWriter:
        def __init__(self):
            self.records = []

        def log_decision(self, record):
            self.records.append(record)

    class RetryFallbackPolicy:
        name = "retryfallback"

        def decide(self, brief, feedback=None):
            if feedback is None:
                return Reply(brief.agent, "not json at all")
            return Reply(brief.agent, '{"decisions": []}', fallback=True, error="spend cap reached")

    class UnusedFallback:
        name = "unused"

        def decide(self, brief, feedback=None):
            raise AssertionError("ctx.fallback must not be called when the retry already validated")

    s = make_state(baseline)
    personas = make_personas(s.net, s.cfg.assumptions, s.streams["personas"])
    writer = StubWriter()
    ctx = DecisionContext(policy=RetryFallbackPolicy(), fallback=UnusedFallback(), writer=writer,
                          personas=personas, recent={})
    run_decision_round(s, 14, ctx)
    rec = next(r for r in writer.records if r["pass"] == "proposal")
    assert rec["fallback"] is True
    assert rec["retry_error"] == "spend cap reached"
