import pytest

from sciti.config import Assumptions
from sciti.network import build_network, great_circle_miles


@pytest.fixture
def net(baseline):
    return build_network(baseline, Assumptions())


def test_48_nodes_in_tier_order(net):
    assert len(net.order) == 48
    roles = [net.nodes[n].role for n in net.order]
    assert roles == sorted(roles, key=["Supplier", "CM", "MFG", "DC", "Retail"].index)
    assert net.order[:2] == ["Supplier_1", "Supplier_2"]
    assert net.order[-1] == "Retail_8"


def test_links_follow_document(net):
    assert net.downstream["Supplier_1"] == ["CM_1"]
    assert net.downstream["CM_4"] == ["MFG_China", "MFG_US"]
    assert net.downstream["MFG_US"] == ["DC_Dubai", "DC_Houston", "DC_Shanghai", "DC_Sofia"]
    assert net.upstream["Retail_3"] == ["DC_Dubai", "DC_Sofia"]
    assert net.upstream["Retail_7"] == ["DC_Shanghai"]
    assert net.downstream["DC_Houston"] == ["Retail_1", "Retail_2"]


def test_shares_sum_to_one(net):
    for buyer, shares in net.source_share.items():
        assert sum(shares.values()) == pytest.approx(1.0), buyer
    assert net.source_share["Retail_1"] == {"DC_Houston": 1.0}


def test_bom_and_sourcing(net):
    assert sum(net.bom.values()) == 160
    assert net.suppliers_of["EPDM"] == ["Supplier_19", "Supplier_20", "Supplier_21"]
    assert net.cm_of["EPDM"] == "CM_3"
    assert net.nodes["CM_3"].skus == ("PP_Resin", "Poly_F_EU", "EPDM", "NR_201")


def test_distance_la_to_shenzhen(net):
    assert net.miles("MFG_US", "MFG_China") == pytest.approx(7250, rel=0.03)
    assert great_circle_miles(0, 0, 0, 0) == 0
