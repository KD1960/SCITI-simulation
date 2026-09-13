import csv

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
