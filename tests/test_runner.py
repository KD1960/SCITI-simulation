import csv
import json

from sciti.config import Config, Disruption, ForcedAdoption
from sciti.outputs import DETERMINISTIC_FILES, scrub
from sciti.runner import run


def cfg(baseline_path, tmp_path, **kw):
    return Config(name="t", seed=3, weeks=26, baseline_path=str(baseline_path),
                  output_dir=str(tmp_path / "runs"), **kw)


def test_run_writes_all_outputs(baseline_path, tmp_path):
    d = run(cfg(baseline_path, tmp_path))
    for f in DETERMINISTIC_FILES + ("manifest.json", "decisions.jsonl", "network.json"):
        assert (d / f).exists(), f
    rows = list(csv.DictReader(open(d / "weekly_nodes.csv")))
    assert len(rows) == 26 * 48
    summary = json.loads((d / "summary.json").read_text())
    assert 0 <= summary["fill_rate"] <= 1
    assert 0 <= summary["satisfaction_index"] <= 1
    man = json.loads((d / "manifest.json").read_text())
    assert man["seed"] == 3 and man["decision_policy"] == "none"
    assert len(man["config_hash"]) == 64 and "git_commit" in man
    assert man["checks"] == "passed"


def test_same_seed_outputs_identical(baseline_path, tmp_path):
    c = cfg(baseline_path, tmp_path, forced_adoptions=[ForcedAdoption(week=1, tech="routing", members=["MFG_US"])],
            disruptions=[Disruption(target="CM_4", start_week=4, weeks=3, capacity_mult=0.2)])
    a = run(c, run_dir=tmp_path / "a")
    b = run(c, run_dir=tmp_path / "b")
    for f in DETERMINISTIC_FILES:
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_forced_tech_changes_outcome(baseline_path, tmp_path):
    base = run(cfg(baseline_path, tmp_path), run_dir=tmp_path / "base")
    tech = run(cfg(baseline_path, tmp_path, forced_adoptions=[
        ForcedAdoption(week=1, tech="routing", members=["MFG_US", "MFG_China"])]), run_dir=tmp_path / "tech")
    s0 = json.loads((base / "summary.json").read_text())
    s1 = json.loads((tech / "summary.json").read_text())
    assert s1["costs"]["shipping"] < s0["costs"]["shipping"]
    assert s1["adoptions"] == 2 and s1["coalitions"] == 1


def test_scrub_removes_keys():
    assert scrub("key sk-ant-api03-abcDEF123_xyz-987654 end") == "key [REDACTED] end"
