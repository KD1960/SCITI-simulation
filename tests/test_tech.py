import pytest

from sciti.config import Assumptions
from sciti.network import build_network
from sciti.tech.catalog import load_catalog, TechHolding, catalog_hash
from sciti.tech.effects import base_params, effective_params


@pytest.fixture
def world(baseline):
    return build_network(baseline, Assumptions()), load_catalog()


def H(tech, week=1, coalition=None):
    return TechHolding(tech=tech, adopted_week=week, active_week=week, coalition_id=coalition)


def test_catalog_has_the_8_mvp_techs():
    cat = load_catalog()
    assert sorted(cat) == sorted(["ml_forecast", "control_tower", "rfid", "aps", "routing",
                                  "wh_robotics", "blockchain", "risk_intel"])
    # catalog v2: only the technologies with no measured effect stay flagged as assumptions
    assert sorted(k for k, t in cat.items() if t.assumption) == ["aps", "blockchain", "risk_intel"]
    assert cat["wh_robotics"].eligible_roles == ("DC",)
    assert len(catalog_hash()) == 64


def test_bad_catalog_param_rejected(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("- {id: x, name: X, observatory_name: X, eligible_roles: [DC], cost_one_time: {DC: 1},"
                 " cost_per_week: {DC: 1}, setup_weeks: 1, network_requirement: solo, group_bonus: 0,"
                 " effects: [{param: nope, op: mul, value: 0.5}], evidence: e, assumption: true}\n")
    with pytest.raises(ValueError):
        load_catalog(p)


def test_solo_effect_applies_after_setup(world):
    net, cat = world
    base = base_params("Retail", Assumptions())
    holdings = {"Retail_1": {"ml_forecast": TechHolding("ml_forecast", 1, 5)}}
    assert effective_params("Retail_1", 4, holdings, cat, net, base)["forecast_skill"] == 0.0
    assert effective_params("Retail_1", 5, holdings, cat, net, base)["forecast_skill"] == pytest.approx(0.03)


def test_pair_needs_partner(world):
    net, cat = world
    base = base_params("Supplier", Assumptions())
    alone = {"Supplier_1": {"blockchain": H("blockchain")}}
    assert effective_params("Supplier_1", 2, alone, cat, net, base)["defect_mult"] == 1.0
    both = {"Supplier_1": {"blockchain": H("blockchain")}, "CM_1": {"blockchain": H("blockchain")}}
    assert effective_params("Supplier_1", 2, both, cat, net, base)["defect_mult"] == pytest.approx(0.82)


def test_chain_scales_by_downstream_share(world):
    net, cat = world
    base = base_params("DC", Assumptions())
    h = {"DC_Houston": {"control_tower": H("control_tower")}, "Retail_1": {"control_tower": H("control_tower")}}
    assert effective_params("DC_Houston", 2, h, cat, net, base)["visibility"] == pytest.approx(0.5 * 0.6)


def test_group_bonus(world):
    net, cat = world
    base = base_params("DC", Assumptions())
    h = {"DC_Houston": {"routing": H("routing", coalition="c1")}}
    # routing ship_cost_mult 0.92, bonus 0.25 → 1 - 0.08*1.25 = 0.90
    assert effective_params("DC_Houston", 2, h, cat, net, base)["ship_cost_mult"] == pytest.approx(0.90)
