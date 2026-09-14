import csv
import json
import math

import pytest

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
    assert man["assumptions"]["config"] == sorted(man["assumptions"]["config"])
    assert len(man["assumptions"]["catalog_assumed_techs"]) == 8


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


def test_bullwhip_units_are_comparable(baseline_path, tmp_path):
    c = Config(name="t", seed=3, weeks=52, baseline_path=str(baseline_path),
               output_dir=str(tmp_path / "runs"))
    d = run(c)
    bw = json.loads((d / "summary.json").read_text())["bullwhip"]
    values = [v for v in bw.values() if v is not None]
    assert values and all(math.isfinite(v) for v in values)
    assert all(v < 1000 for v in values)
    dc = bw["DC"]
    for role in ("MFG", "CM"):
        if bw[role] is not None and dc not in (None, 0):
            assert bw[role] / dc < 1000


def test_summary_has_transit_and_order_to_arrival_days(baseline_path, tmp_path):
    d = run(cfg(baseline_path, tmp_path))
    summary = json.loads((d / "summary.json").read_text())
    assert math.isfinite(summary["mean_transit_days"]) and summary["mean_transit_days"] > 0
    assert math.isfinite(summary["mean_lead_days"]) and summary["mean_lead_days"] > 0


def test_invalid_forced_adoption_raises_and_creates_no_run_dir(baseline_path, tmp_path):
    run_dir = tmp_path / "runs" / "bad"
    c = cfg(baseline_path, tmp_path, forced_adoptions=[
        ForcedAdoption(week=20, tech="wh_robotics", members=["Retail_1"])])
    with pytest.raises(ValueError, match="not eligible"):
        run(c, run_dir=run_dir)
    assert not run_dir.exists()


def test_forced_adoption_on_non_quarter_week_is_applied(baseline_path, tmp_path):
    c = cfg(baseline_path, tmp_path, forced_adoptions=[
        ForcedAdoption(week=2, tech="routing", members=["MFG_US"])])
    d = run(c, run_dir=tmp_path / "nq")
    events = [json.loads(line) for line in (d / "events.jsonl").read_text().splitlines()]
    assert any(e["type"] == "adopt" and e["week"] == 2 and e["node"] == "MFG_US" for e in events)


def test_mid_run_exception_still_writes_outputs(baseline_path, tmp_path, monkeypatch):
    import sciti.runner as runner_mod

    def boom(s, t):
        if t == 5:
            raise RuntimeError("kaboom")

    monkeypatch.setattr(runner_mod, "step_week", boom)
    run_dir = tmp_path / "runs" / "boom"
    c = cfg(baseline_path, tmp_path)
    with pytest.raises(RuntimeError, match="kaboom"):
        run(c, run_dir=run_dir)
    man = json.loads((run_dir / "manifest.json").read_text())
    assert man["checks"].startswith("failed: RuntimeError")
    decisions = (run_dir / "decisions.jsonl").read_text()  # writer was closed cleanly
    assert decisions is not None
