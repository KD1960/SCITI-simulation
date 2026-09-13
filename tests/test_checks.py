import math

import pytest

from sciti.checks import SimulationError, check_invariants, enforce
from sciti.engine.ops import step_week
from tests.helpers import make_state


def test_clean_run_has_no_violations(baseline):
    s = make_state(baseline)
    for t in range(1, 11):
        step_week(s, t)
        assert check_invariants(s, t) == []


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
