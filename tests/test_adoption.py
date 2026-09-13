import pytest

from sciti.config import ForcedAdoption
from sciti.engine.adoption import AdoptionError, adopt, apply_forced, drop
from sciti.engine.ops import step_week
from tests.helpers import make_state


def test_adopt_creates_holding_and_charges(baseline):
    s = make_state(baseline)
    ev = adopt(s, "DC_Houston", "wh_robotics", week=1)
    h = s.holdings["DC_Houston"]["wh_robotics"]
    assert (h.adopted_week, h.active_week) == (1, 17)
    assert s.nodes["DC_Houston"].pending_tech_cost == 2_500_000
    assert ev["type"] == "adopt" and s.events[-1] == ev
    step_week(s, 1)
    assert s.nodes["DC_Houston"].ledger["tech"] == 2_500_000 + 15_000


def test_ineligible_or_duplicate_rejected(baseline):
    s = make_state(baseline)
    with pytest.raises(AdoptionError):
        adopt(s, "Retail_1", "wh_robotics", 1)
    adopt(s, "DC_Houston", "routing", 1)
    with pytest.raises(AdoptionError):
        adopt(s, "DC_Houston", "routing", 2)


def test_drop_stops_running_cost(baseline):
    s = make_state(baseline)
    adopt(s, "DC_Houston", "routing", 1)
    drop(s, "DC_Houston", "routing", 1)
    step_week(s, 1)
    assert s.nodes["DC_Houston"].ledger["tech"] == 300_000


def test_forced_coalition_splits_cost(baseline):
    s = make_state(baseline)
    s.cfg.forced_adoptions = [ForcedAdoption(week=1, tech="control_tower",
                                             members=["DC_Shanghai", "Retail_6"])]
    apply_forced(s, 1)
    assert s.holdings["Retail_6"]["control_tower"].coalition_id == "forced_0"
    assert s.nodes["Retail_6"].pending_tech_cost == pytest.approx((700_000 + 250_000) / 2)
