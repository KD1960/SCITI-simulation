import math

import pytest

from sciti.checks import SimulationError, check_invariants, enforce
from sciti.config import Config, Disruption
from sciti.engine.ops import step_week
from sciti.engine.state import init_state
from sciti.network import build_network
from sciti.rng import make_streams
from sciti.tech.catalog import load_catalog
from sciti.data.demand import DemandModel
from tests.helpers import make_state


def test_clean_run_has_no_violations(baseline):
    s = make_state(baseline)
    for t in range(1, 11):
        step_week(s, t)
        assert check_invariants(s, t) == []


def test_clean_run_30_weeks_with_disruption_has_no_violations(baseline):
    """Verify flow balance holds across all roles with a disruption."""
    cfg = Config(name="t", seed=1, weeks=30)
    cfg.disruptions = [Disruption(target="CM_4", start_week=3, weeks=6, capacity_mult=0.2)]
    net = build_network(baseline, cfg.assumptions)
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(1)
    demand = dm.generate(30, streams["demand"])
    s = init_state(cfg, baseline, net, dm, demand, load_catalog(), streams)
    for t in range(1, 31):
        step_week(s, t)
        assert check_invariants(s, t) == [], f"violations at week {t}: {check_invariants(s, t)}"


def test_flow_balance_catches_wrong_count(baseline):
    s = make_state(baseline)
    step_week(s, 1)
    s.nodes["DC_Dubai"].counts["shipped"] += 5.0  # corrupt counter only
    v = check_invariants(s, 1)
    assert any("DC_Dubai" in x and "flow balance" in x for x in v)


def test_nan_stock_caught(baseline):
    s = make_state(baseline)
    step_week(s, 1)
    s.nodes["Retail_2"].stock["A"] = math.nan
    v = check_invariants(s, 1)
    assert any("Retail_2" in x and "non-finite stock" in x for x in v)


def test_direct_mutation_is_caught(baseline):
    s = make_state(baseline)
    step_week(s, 1)
    s.nodes["DC_Dubai"].stock["A"] += 5.0  # bypasses add()
    v = check_invariants(s, 1)
    assert any("DC_Dubai" in x and "conservation" in x for x in v)


def test_nan_cash_caught_and_strict_raises(baseline):
    s = make_state(baseline)
    step_week(s, 1)
    s.nodes["Retail_2"].cash = math.nan
    with pytest.raises(SimulationError):
        enforce(s, 1, strict=True)
    enforce(s, 1, strict=False)
    assert s.events[-1]["type"] == "check_warning"
