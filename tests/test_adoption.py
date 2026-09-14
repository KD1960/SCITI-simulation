import pytest

from sciti.config import ForcedAdoption
from sciti.engine.adoption import AdoptionError, adopt, apply_forced, drop, validate_forced_adoptions
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


def test_validate_forced_adoptions_rejects_ineligible_member(baseline):
    s = make_state(baseline, weeks=30)
    with pytest.raises(ValueError, match="0.*not eligible"):
        validate_forced_adoptions(
            [ForcedAdoption(week=20, tech="wh_robotics", members=["Retail_1"])], s.net, s.catalog, 30)


def test_validate_forced_adoptions_rejects_empty_members(baseline):
    s = make_state(baseline, weeks=30)
    with pytest.raises(ValueError, match="0.*non-empty"):
        validate_forced_adoptions([ForcedAdoption(week=1, tech="routing", members=[])], s.net, s.catalog, 30)


def test_validate_forced_adoptions_rejects_duplicate_members(baseline):
    s = make_state(baseline, weeks=30)
    with pytest.raises(ValueError, match="0.*duplicate"):
        validate_forced_adoptions(
            [ForcedAdoption(week=1, tech="routing", members=["DC_Houston", "DC_Houston"])], s.net, s.catalog, 30)


def test_validate_forced_adoptions_rejects_node_tech_reused_across_entries(baseline):
    s = make_state(baseline, weeks=30)
    entries = [ForcedAdoption(week=1, tech="routing", members=["DC_Houston"]),
               ForcedAdoption(week=5, tech="routing", members=["DC_Houston"])]
    with pytest.raises(ValueError, match="1.*already assigned"):
        validate_forced_adoptions(entries, s.net, s.catalog, 30)


def test_validate_forced_adoptions_rejects_week_out_of_range(baseline):
    s = make_state(baseline, weeks=30)
    with pytest.raises(ValueError, match="0.*week"):
        validate_forced_adoptions([ForcedAdoption(week=0, tech="routing", members=["DC_Houston"])],
                                  s.net, s.catalog, 30)
    with pytest.raises(ValueError, match="0.*week"):
        validate_forced_adoptions([ForcedAdoption(week=31, tech="routing", members=["DC_Houston"])],
                                  s.net, s.catalog, 30)


def test_forced_skips_member_who_already_holds_tech(baseline):
    s = make_state(baseline)
    adopt(s, "DC_Shanghai", "control_tower", week=1)
    s.cfg.forced_adoptions = [ForcedAdoption(week=2, tech="control_tower",
                                             members=["DC_Shanghai", "Retail_6"])]
    apply_forced(s, 2)
    skipped = [e for e in s.events if e["type"] == "forced_skipped"]
    assert skipped == [{"week": 2, "type": "forced_skipped", "node": "DC_Shanghai",
                        "tech": "control_tower", "reason": "already held"}]
    # Only one member remains -- adopted alone, no coalition.
    assert s.holdings["Retail_6"]["control_tower"].coalition_id is None
    assert not any(e["type"] == "coalition" and e["week"] == 2 for e in s.events)
