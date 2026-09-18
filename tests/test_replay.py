import json

import pytest

from sciti.cli import main
from sciti.config import Config, DecisionCfg
from sciti.decide.interface import Brief
from sciti.decide.replay import ReplayError, ReplayPolicy
from sciti.runner import replay_run, run


def rules_run(baseline_path, tmp_path):
    c = Config(name="rp", seed=9, weeks=40, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    return run(c, run_dir=tmp_path / "orig")


def test_replay_of_none_run_keeps_none_policy(baseline_path, tmp_path):
    c = Config(name="none", seed=2, weeks=13, baseline_path=str(baseline_path), output_dir=str(tmp_path))
    orig = run(c, run_dir=tmp_path / "orig")
    man = json.loads((orig / "manifest.json").read_text())
    assert man["decision_policy"] == "none"
    assert replay_run(orig, tmp_path / "again") == []


def test_llm_run_replays_exactly(baseline_path, tmp_path, monkeypatch):
    from tests.test_llm import FAKE_KEY, FakeClient
    from tests.test_llm import cfg as llm_cfg
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    valid = json.dumps({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "ok"}]})
    invalid_json = "not json at all"
    ineligible = json.dumps({"decisions": [{"tech": "wh_robotics", "action": "adopt", "partners": [], "reason": "x"}]})
    texts = ([valid, invalid_json, ineligible, valid, invalid_json] * 20)
    c = Config(name="llmreplay", seed=5, weeks=27, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=llm_cfg(max_spend_usd=0.003))
    orig = run(c, run_dir=tmp_path / "orig", client=FakeClient(texts, errors=2))
    assert replay_run(orig, tmp_path / "again") == []
    records = [json.loads(line) for line in (orig / "decisions.jsonl").read_text().splitlines()]
    assert any(r["fallback"] for r in records)


def test_replay_reproduces_exactly(baseline_path, tmp_path):
    orig = rules_run(baseline_path, tmp_path)
    assert json.loads((orig / "summary.json").read_text())["adoptions"] > 0
    assert replay_run(orig, tmp_path / "again") == []


def test_replay_detects_divergence(baseline_path, tmp_path):
    orig = rules_run(baseline_path, tmp_path)
    p = ReplayPolicy(orig / "decisions.jsonl")
    with pytest.raises(ReplayError):
        p.decide(Brief("Retail_1", "Retail", 999, 77, "proposal", {}))


def test_cli_replay(baseline_path, tmp_path, capsys):
    orig = rules_run(baseline_path, tmp_path)
    assert main(["replay", str(orig), "--out", str(tmp_path / "cli")]) == 0
    assert "replication: exact" in capsys.readouterr().out


def test_rules_roles_use_the_rules_policy_and_replay_exactly(baseline_path, tmp_path, monkeypatch):
    """decision.rules_roles: agents in those roles use the payback rule instead of the main policy
    (their log records say policy "rules", not fallback); the run still replays exactly."""
    from tests.test_llm import FAKE_KEY, FakeClient
    from tests.test_llm import cfg as llm_cfg
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    valid = json.dumps({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "ok"}]})
    c = Config(name="rr", seed=5, weeks=27, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=llm_cfg(rules_roles=["Supplier"]))
    client = FakeClient([valid] * 100)
    orig = run(c, run_dir=tmp_path / "orig", client=client)
    records = [json.loads(line) for line in (orig / "decisions.jsonl").read_text().splitlines()]
    sup = [r for r in records if r["agent"].startswith("Supplier_")]
    assert sup and all(r["policy"] == "rules" and not r["fallback"] for r in sup)
    assert all(r["policy"] == "llm" for r in records if not r["agent"].startswith("Supplier_"))
    assert len([r for r in records if r["policy"] == "llm"]) == len(records) - len(sup)
    assert replay_run(orig, tmp_path / "again") == []
