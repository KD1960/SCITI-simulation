import pytest

from sciti.config import Disruption
from sciti.disruptions import apply_disruptions, validate_disruptions
from sciti.engine.ops import step_week
from sciti.tech.catalog import TechHolding
from tests.helpers import make_state


def test_unknown_target_rejected(baseline):
    s = make_state(baseline)
    with pytest.raises(ValueError):
        validate_disruptions([Disruption(target="CM_9", start_week=2, weeks=3)], s.net)


def test_capacity_drops_during_window_only(baseline):
    s = make_state(baseline)
    s.cfg.disruptions = [Disruption(target="CM_4", start_week=3, weeks=2, capacity_mult=0.0)]
    seen = {}
    for t in range(1, 7):
        step_week(s, t)
        seen[t] = s.nodes["CM_4"].capacity_factor
    assert seen == {1: 1.0, 2: 1.0, 3: 0.0, 4: 0.0, 5: 1.0, 6: 1.0}
    assert [e for e in s.events if e["type"] == "disruption_start"] == \
        [{"week": 3, "type": "disruption_start", "target": "CM_4", "until": 5}]


def test_shipments_track_order_to_arrival_wait_during_shortage(baseline):
    s = make_state(baseline, weeks=30)
    s.cfg.disruptions = [Disruption(target="CM_4", start_week=2, weeks=9, capacity_mult=0.0)]
    for t in range(1, 31):
        step_week(s, t)
    assert all(sh.order_week <= sh.ship_week + 1e-6 for sh in s.arrived)
    downstream = [sh for sh in s.arrived if s.nodes[sh.dst].role in ("DC", "Retail")]
    assert any(sh.ship_week - sh.order_week >= 1 for sh in downstream)


def test_risk_intel_shortens_and_warns(baseline):
    s = make_state(baseline)
    s.cfg.disruptions = [Disruption(target="CM_4", start_week=5, weeks=5, capacity_mult=0.5)]
    s.holdings["CM_4"]["risk_intel"] = TechHolding("risk_intel", 1, 1)
    s.holdings["MFG_US"]["risk_intel"] = TechHolding("risk_intel", 1, 1)
    boosts = {}
    for t in range(1, 5):
        step_week(s, t)
        boosts[t] = s.nodes["MFG_US"].z_boost
    assert boosts == {1: 0.0, 2: 0.0, 3: 1.0, 4: 1.0}
    step_week(s, 5)
    assert s.disruption_end[0] == 5 + 3  # ceil(5 * 0.6)
