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
