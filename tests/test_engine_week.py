import pytest

from sciti.engine.ops import step_week
from sciti.engine.state import StockError
from tests.helpers import make_state


def test_init_state_has_stock_and_cash(baseline):
    s = make_state(baseline)
    assert s.nodes["Retail_1"].stock["A"] > 0
    assert s.nodes["CM_3"].stock["RAW:EPDM"] > 0
    assert s.nodes["MFG_US"].capacity["BUILD"] > 0
    assert all(ns.cash > 0 for ns in s.nodes.values())
    assert len(s.flows) == 31


def test_retail_sales_never_exceed_stock_or_demand(baseline):
    s = make_state(baseline)
    for t in range(1, 21):
        step_week(s, t)
        for r in s.net.by_role("Retail"):
            c = s.nodes[r].counts
            assert c["sales"] <= c["demand"] + 1e-9
            assert c["sales"] + c["lost"] == pytest.approx(c["demand"])


def test_shipments_arrive_exactly_once_and_stock_nonnegative(baseline):
    s = make_state(baseline)
    for t in range(1, 21):
        step_week(s, t)
        assert all(sh.arrive_week > t for sh in s.in_transit)
        for ns in s.nodes.values():
            assert all(v >= 0 for v in ns.stock.values())
    ids = [sh.id for sh in s.arrived]
    assert len(ids) == len(set(ids)) > 0
    assert not set(ids) & {sh.id for sh in s.in_transit}


def test_mfg_consumes_bom_exactly(baseline):
    s = make_state(baseline)
    for t in range(1, 11):
        step_week(s, t)
        for m in s.net.by_role("MFG"):
            ns = s.nodes[m]
            for sku, u in s.net.bom.items():
                assert ns.consumed[sku] == pytest.approx(ns.counts["built"] * u)


def test_same_seed_same_result(baseline):
    a, b = make_state(baseline, seed=4), make_state(baseline, seed=4)
    for t in range(1, 16):
        step_week(a, t)
        step_week(b, t)
    assert [n.cash for n in a.nodes.values()] == [n.cash for n in b.nodes.values()]


def test_remove_more_than_stock_raises(baseline):
    s = make_state(baseline)
    ns = s.nodes["Retail_1"]
    with pytest.raises(StockError):
        ns.remove("A", ns.stock["A"] + 10)


def test_owed_fifo_matches_owed_totals(baseline):
    s = make_state(baseline)
    for t in range(1, 6):
        step_week(s, t)
        for ns in s.nodes.values():
            for b, items in ns.owed.items():
                for item, qty in items.items():
                    fifo_total = sum(e[1] for e in ns.owed_fifo.get(b, {}).get(item, []))
                    assert fifo_total == pytest.approx(qty, abs=1e-6)


def test_fill_rate_holds_over_three_years(baseline):
    from sciti.network import PRODUCTS

    s = make_state(baseline, weeks=156, seed=1)
    sales = lost = 0.0
    for t in range(1, 157):
        step_week(s, t)
        if 105 <= t <= 156:
            for r in s.net.by_role("Retail"):
                c = s.nodes[r].counts
                sales += c["sales"]
                lost += c["lost"]
    fill = sales / (sales + lost)
    assert fill >= 0.95
    for m in s.net.by_role("MFG"):
        ns = s.nodes[m]
        backlog = sum(ns.owed_total(p) for p in PRODUCTS)
        mean_forecast = sum(ns.forecast[p] for p in PRODUCTS)
        assert backlog < 4 * mean_forecast


def test_shipment_draws_do_not_depend_on_earlier_shipments(baseline):
    # Paired runs must see the same lead time and mode on a lane-week even if their shipment histories differ.
    from sciti.engine.ops import make_shipment
    s1, s2 = make_state(baseline), make_state(baseline)
    for t in (1, 2, 3):
        make_shipment(s2, "MFG_China", "DC_Shanghai", "A", 50, t)
        make_shipment(s2, "Supplier_1", "CM_1", "SR_MCU", 50, t)
    for src, dst, item in (("MFG_China", "DC_Shanghai", "A"), ("Supplier_1", "CM_1", "SR_MCU")):
        a, b = make_shipment(s1, src, dst, item, 100, 5), make_shipment(s2, src, dst, item, 100, 5)
        assert (a.mode, a.lead_days) == (b.mode, b.lead_days)
    leads = {make_shipment(s1, "MFG_China", "DC_Shanghai", "A", 100, t).lead_days for t in range(1, 21)}
    assert len(leads) > 1


def test_internal_sales_and_purchases_book_in_the_same_week(baseline):
    # Every internal sale is a purchase for its buyer, so the two must match each week;
    # otherwise goods in transit at the horizon end show up as network profit.
    s = make_state(baseline)
    for t in range(1, 21):
        step_week(s, t)
        sales = sum(ns.ledger["revenue"] for ns in s.nodes.values() if ns.role != "Retail")
        purchases = sum(ns.ledger["purchases"] for ns in s.nodes.values())
        assert purchases == pytest.approx(sales)
