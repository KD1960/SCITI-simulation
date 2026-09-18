import pytest

from sciti.config import Disruption
from sciti.disruptions import apply_disruptions, validate_disruptions
from sciti.engine.ops import step_week
from sciti.rng import warning_draw
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
    # catalog v2: 2 weeks of warning, but only if this disruption is one that can be seen coming (p = 0.4)
    ahead = 1.0 if warning_draw(s.cfg.seed, 0) < 0.4 else 0.0
    assert boosts == {1: 0.0, 2: 0.0, 3: ahead, 4: ahead}
    step_week(s, 5)
    assert s.nodes["MFG_US"].z_boost == 1.0  # once it has started, every subscriber knows
    assert s.disruption_end[0] == 5 + 3  # 5 weeks minus 2 weeks of buyer-side lag saved


def test_recovery_weeks_saved_is_a_fixed_cut_with_a_one_week_floor(baseline):
    """Risk intelligence saves a fixed number of weeks (detection and response lag), so a long
    outage shrinks proportionally less than a short one; an outage never drops below 1 week."""
    for weeks, until in ((12, 10 + 10), (4, 10 + 2), (2, 10 + 1)):
        s = make_state(baseline, weeks=30)
        s.cfg.disruptions = [Disruption(target="CM_3", start_week=10, weeks=weeks, capacity_mult=0.2)]
        s.nodes["CM_3"].params["recovery_weeks_saved"] = 2.0
        apply_disruptions(s, 10)
        assert s.disruption_end[0] == until


def test_warning_only_reaches_subscribers_whose_probability_beats_the_event_draw(baseline):
    """Each disruption has one keyed draw u in [0,1); a subscriber is warned ahead of time only
    if its warning_prob > u. After the start, every subscriber holds extra safety stock."""
    s = make_state(baseline, weeks=30)
    s.cfg.disruptions = [Disruption(target="CM_3", start_week=10, weeks=4, capacity_mult=0.2)]
    u = warning_draw(s.cfg.seed, 0)
    assert 0.0 <= u < 1.0 and u == warning_draw(s.cfg.seed, 0) and u != warning_draw(s.cfg.seed, 1)
    for prob, warned in ((0.0, False), (u / 2, False), ((1 + u) / 2, True), (1.0, True)):
        s.nodes["MFG_US"].params.update(early_warning_weeks=2.0, warning_prob=prob)
        apply_disruptions(s, 9)
        assert (s.nodes["MFG_US"].z_boost == 1.0) == warned
    s.nodes["MFG_US"].params.update(early_warning_weeks=2.0, warning_prob=0.0)
    apply_disruptions(s, 10)
    assert s.nodes["MFG_US"].z_boost == 1.0
