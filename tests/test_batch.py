import csv
from unittest.mock import patch

import pytest

from sciti.batch import SpendConfirmationRequired, estimate, flatten, parse_seeds, run_batch
from sciti.config import Config, DecisionCfg


def test_parse_seeds():
    assert parse_seeds("1-3,7") == [1, 2, 3, 7]


def test_flatten():
    assert flatten({"a": 1, "b": {"c": 2, "d": None}}) == {"a": 1, "b_c": 2, "b_d": None}


def test_estimate_llm_and_rules():
    llm = Config(name="e", seed=1, decision=DecisionCfg(policy="llm", model="m", price_per_mtok_in=1, price_per_mtok_out=5))
    e = estimate(llm)
    assert e["rounds"] == 12 and e["calls_expected"] == round(48 * 12 * 1.3)
    assert e["usd_max"] == pytest.approx(e["calls_max"] * (3000 * 1 + 400 * 5) / 1e6)
    assert estimate(Config(name="e", seed=1))["calls_max"] == 0
    assert "price" in estimate(Config(name="e", seed=1, decision=DecisionCfg(policy="llm", model="m")))["note"]


def test_batch_writes_results_with_baseline(baseline_path, tmp_path):
    c = Config(name="b", seed=0, weeks=26, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    out = run_batch(c, [1, 2], tmp_path / "batch", with_baseline=True)
    rows = list(csv.DictReader(open(out / "results.csv")))
    assert [(r["policy"], r["seed"]) for r in rows] == [("rules", "1"), ("none", "1"), ("rules", "2"), ("none", "2")]
    assert "costs_shipping" in rows[0] and "bullwhip_DC" in rows[0]


def test_batch_llm_requires_spend_confirmation(baseline_path, tmp_path):
    c = Config(name="b", seed=0, weeks=26, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="llm", model="m", price_per_mtok_in=100, price_per_mtok_out=100,
                                    confirm_spend_threshold_usd=0.01))
    with pytest.raises(SpendConfirmationRequired):
        run_batch(c, [1], tmp_path / "batch")


def test_parse_seeds_validation():
    with pytest.raises(ValueError):
        parse_seeds("3-1")
    with pytest.raises(ValueError):
        parse_seeds("")
    with pytest.raises(ValueError):
        parse_seeds("a")
    with pytest.raises(ValueError):
        parse_seeds("1-2,x")
    assert parse_seeds(" 1 - 3 , 2 ") == [1, 2, 3]


def test_batch_continues_after_run_failure(baseline_path, tmp_path, monkeypatch):
    c = Config(name="b", seed=0, weeks=13, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    call_count = [0]
    original_run = __import__("sciti.batch", fromlist=["run"]).run

    def mock_run(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("boom")
        return original_run(*args, **kwargs)

    monkeypatch.setattr("sciti.batch.run", mock_run)
    out = run_batch(c, [1, 2, 3], tmp_path / "batch")
    rows = list(csv.DictReader(open(out / "results.csv")))
    assert len(rows) == 3
    assert [r["status"] for r in rows] == ["ok", "failed", "ok"]
    assert "RuntimeError: boom" in rows[1]["error"]


def test_batch_config_factors(baseline_path, tmp_path):
    from sciti.config import ForcedAdoption, Disruption
    c = Config(name="b", seed=0, weeks=13, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules", visibility="network", cost_split="by_size",
                                    chain_accept_share=0.7, max_new_adoptions_per_quarter=2),
               forced_adoptions=[ForcedAdoption(week=1, tech="control_tower", members=["DC_Shanghai", "Retail_5"])],
               disruptions=[Disruption(target="CM_4", start_week=20, weeks=6, capacity_mult=0.25, extra_lead_days=7)])
    out = run_batch(c, [1], tmp_path / "batch", with_baseline=False)
    rows = list(csv.DictReader(open(out / "results.csv")))
    assert rows[0]["name"] == "b"
    assert rows[0]["weeks"] == "13"
    assert rows[0]["decision_model"] == "rules"
    assert rows[0]["decision_visibility"] == "network"
    assert rows[0]["decision_cost_split"] == "by_size"
    assert rows[0]["decision_chain_accept_share"] == "0.7"
    assert rows[0]["decision_max_new_adoptions_per_quarter"] == "2"
    assert rows[0]["forced_adoptions"] == "w1:control_tower:DC_Shanghai|Retail_5"
    assert rows[0]["disruptions"] == "CM_4@20+6x0.25+7d"


def test_batch_baseline_has_no_forced_adoptions(baseline_path, tmp_path):
    from sciti.config import ForcedAdoption
    c = Config(name="b", seed=0, weeks=13, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"),
               forced_adoptions=[ForcedAdoption(week=1, tech="routing", members=["MFG_US"])])
    out = run_batch(c, [1], tmp_path / "batch", with_baseline=True)
    rows = list(csv.DictReader(open(out / "results.csv")))
    assert len(rows) == 2
    primary = rows[0]
    baseline = rows[1]
    assert primary["policy"] == "rules" and baseline["policy"] == "none"
    assert primary["baseline_for"] == "" and baseline["baseline_for"] == "rules"
    assert baseline["adoptions"] == "0"
    assert baseline["forced_adoptions"] == ""
    assert baseline["disruptions"] == primary["disruptions"]


def test_estimate_reports_a_with_retries_figure():
    # E5: the pilot needed 2.6 calls per agent-quarter once truncated replies were retried, not 1.3.
    from sciti.batch import EST_CALLS_PER_AGENT_ROUND_RETRIES
    llm = Config(name="e", seed=1, decision=DecisionCfg(policy="llm", model="m", price_per_mtok_in=1,
                                                        price_per_mtok_out=5))
    e = estimate(llm)
    assert e["calls_with_retries"] == round(48 * 12 * EST_CALLS_PER_AGENT_ROUND_RETRIES)
    assert e["usd_with_retries"] > e["usd_expected"]
    assert e["calls_with_retries"] <= e["calls_max"]


def test_estimate_excludes_rules_roles_agents():
    """Suppliers on the payback rule make no API calls: 30 of the 48 agents drop out of the estimate."""
    base = dict(policy="llm", model="m", price_per_mtok_in=1, price_per_mtok_out=5)
    e = estimate(Config(name="e", seed=1, decision=DecisionCfg(**base, rules_roles=["Supplier"])))
    assert e["calls_expected"] == round(18 * 12 * 1.3)
    assert e["calls_max"] == 18 * 12 * 2 * 2
