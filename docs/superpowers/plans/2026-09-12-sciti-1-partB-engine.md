# SCITI 1 — Part B: Engine (Tasks 6–10)

> Part of `2026-09-12-sciti-1.md`. Read that file's Global Constraints first. Requires Part A. Steps use checkbox (`- [ ]`) syntax.

All shell commands run from the project root: `cd "$HOME/Claude/Projects/SCITI simulation"`.

## Engine model decisions (apply to every task in this part)

- **Quantities are floats** (continuous units). Retail demand is whole units; everything downstream may be fractional.
- **Items.** Supplier stocks its sku. CM stocks `RAW:<sku>` (inputs) and `<sku>` (outputs). MFG stocks skus (inputs) and products `A`,`B`,`C`. DC and Retail stock products. Shipments carry the **seller's** item name; the receiver's stock key is `input_key(role, item)` (`RAW:` prefix at CMs).
- **Orders** become the seller's `owed[buyer][item]` backlog. Unfilled upstream orders carry over; unmet retail demand is lost.
- **Money is cash-flow.** Seller books `revenue` at ship time; buyer books `purchases` and `shipping` at arrival. Profit = revenue − (purchases + shipping + holding + stockout + handling + tech + cogs). `scrap` (shrink + caught defects, at unit value) is tracked but not subtracted, because those units were already paid for.
- **Supplier→CM lanes** use supplier lead time (days) with SD from baseline; no freight cost or CO2 (not in data; noted in validation report).
- **Road/Rail** allowed only when lane distance < 2,500 miles; mode shares renormalized.
- **Production targets:** finished-goods cover of `fg_cover_weeks` (default 2) of forecast, net of backlog owed.
- **Forecast:** exponential smoothing (α) of the observed signal. Observed = orders received (retail: demand), blended with end-customer demand by `visibility`. Forecast used for ordering = `(1−w)·ES + w·expected`, where `w = forecast_skill` and `expected` is the demand model's propagated expectation for next week. Forecast SD = `1.25 · smoothed |error| · (1 − w/2)`.
- **Ordering:** `order = max(0, f·(L+1) + z·σ·sqrt(L+1) − position)`, `z = NormalDist().inv_cdf(target_service_level) + z_boost`. Position = recorded stock (true stock × (1 + N(0, record_error_sd)), floored at 0) + in-transit to me + backlog owed to me − net backlog I owe downstream in input units (DC: owed products; MFG: max(0, owed products − finished stock) × BOM units; CM: max(0, owed sku − sku stock)). Amended 2026-09-12 after Task 6 review (Kevin approved): the DC-only rule let MFG backlog grow without limit.
- **Quality** (network, weekly) = 1 − escaped defects ÷ units received at CMs; carries forward in weeks with no CM receipts.

---

### Task 6: Engine core — state, prices, weekly operations

**Files:**
- Modify: `sciti/config.py` (add three assumptions)
- Create: `sciti/engine/state.py`, `sciti/engine/economics.py`, `sciti/engine/ops.py`
- Test: `tests/__init__.py`, `tests/helpers.py`, `tests/test_engine_units.py`, `tests/test_engine_week.py`

**Interfaces:**
- Consumes: `Config`, `make_streams`, `DemandModel`, `Network`, `PRODUCTS`, `load_catalog`, `TechHolding`, `base_params`, `effective_params` (Part A).
- Produces:
  - `sciti.engine.economics`: `price_table(net, baseline, markup) -> dict` with keys `supplier` (sid→price), `raw` (sku→mean supplier price), `cm` (sku→price), `mfg`, `dc`, `retail` (floats); `sell_price(prices, net, node_id, item) -> float`; `unit_value(prices, net, node_id, item) -> float`; `propagate(net, retail: dict[tuple[str, str], float]) -> dict[str, dict[str, float]]`
  - `sciti.engine.state`: `LEDGER_KEYS`, `PROFIT_COST_KEYS`, `COUNT_KEYS`; `Shipment` dataclass; `NodeState` dataclass with `add(item, qty)`, `remove(item, qty)`, `owed_total(item) -> float`, `reset_week()`, `profit() -> float`; `SimState` dataclass; `input_key(role, item) -> str`; `output_items(net, node_id) -> list[str]`; `lane_type(src_role) -> str`; `init_state(cfg, baseline, net, demand_model, demand, catalog, streams) -> SimState`; `StockError(Exception)`
  - `sciti.engine.ops`: `order_up_to(forecast, sigma, lead_weeks, z, position) -> float`; `ration(available, owed: dict[str, float]) -> dict[str, float]`; `build_qty(parts, bom, capacity, target) -> float`; `allowed_modes(mix: dict[str, float], miles: float) -> dict[str, float]`; `sample_lane(stats: dict, miles: float, rng) -> tuple[str, float, float, float]` (mode, lead_days, quote_days, cost_per_unit); `step_week(s: SimState, t: int) -> None`

- [ ] **Step 1: Add assumptions to `sciti/config.py`**

In `class Assumptions`, after `persona_horizon_weeks`, add:

```python
    supplier_cogs_share: float = 0.7
    fg_cover_weeks: float = 2.0
    initial_cash_weeks: float = 13.0
```

- [ ] **Step 2: Write the failing unit tests**

`tests/test_engine_units.py`:

```python
import numpy as np
import pytest

from sciti.config import Assumptions
from sciti.engine.economics import price_table, propagate, sell_price, unit_value
from sciti.engine.ops import allowed_modes, build_qty, order_up_to, ration, sample_lane
from sciti.network import build_network


def test_order_up_to():
    # f=100, L=1 → (L+1)=2: 200 + 1.645*20*sqrt(2) − 150
    assert order_up_to(100, 20, 1, 1.645, 150) == pytest.approx(200 + 1.645 * 20 * 2 ** 0.5 - 150)
    assert order_up_to(100, 20, 1, 1.645, 10_000) == 0.0


def test_ration_proportional_and_capped():
    assert ration(50, {"b": 60, "a": 40}) == {"a": 20.0, "b": 30.0}
    assert ration(500, {"a": 40}) == {"a": 40.0}
    assert ration(5, {}) == {}


def test_build_limited_by_scarcest_part():
    bom = {"x": 10, "y": 40}
    assert build_qty({"x": 1000, "y": 400}, bom, capacity=1e9, target=1e9) == 10
    assert build_qty({"x": 1000, "y": 4000}, bom, capacity=5, target=1e9) == 5
    assert build_qty({"x": 1000}, bom, capacity=5, target=1e9) == 0


def test_modes_filtered_by_distance():
    mix = {"Air": 0.5, "Ship": 0.3, "Road": 0.1, "Rail": 0.1}
    assert allowed_modes(mix, 1000) == pytest.approx(mix)
    assert allowed_modes(mix, 6000) == pytest.approx({"Air": 0.625, "Ship": 0.375})


def test_sample_lane_floor_and_quote(baseline):
    stats = baseline["lanes"]["mfg_dc"]
    mode, lead, quote, cpu = sample_lane(stats, 6000, np.random.default_rng(0))
    m = stats["modes"][mode]
    assert mode in ("Air", "Ship")
    assert quote == pytest.approx(max(1.0, m["lead_a"] + m["lead_b"] * 6000))
    assert lead >= 1.0 and cpu == m["cost_per_unit"]


def test_prices_chain_markups(baseline):
    net = build_network(baseline, Assumptions())
    pr = price_table(net, baseline, Assumptions().markup)
    assert pr["cm"]["SR_MCU"] == pytest.approx(20 * 1.2)
    assert pr["mfg"] == pytest.approx(sum(pr["cm"][k] * u for k, u in net.bom.items()) * 1.25)
    assert pr["retail"] == pytest.approx(pr["mfg"] * 1.1 * 1.4)
    assert sell_price(pr, net, "DC_Dubai", "A") == pr["dc"]
    assert unit_value(pr, net, "CM_1", "RAW:SR_MCU") == pr["raw"]["SR_MCU"]
    assert unit_value(pr, net, "Retail_1", "B") == pr["dc"]


def test_propagate_conserves_units(baseline):
    net = build_network(baseline, Assumptions())
    retail = {(f"Retail_{r}", p): 100.0 for r in range(1, 9) for p in "ABC"}
    f = propagate(net, retail)
    total_products = 2400.0
    assert sum(f[d]["A"] + f[d]["B"] + f[d]["C"] for d in net.by_role("DC")) == pytest.approx(total_products)
    assert sum(f[m]["A"] + f[m]["B"] + f[m]["C"] for m in net.by_role("MFG")) == pytest.approx(total_products)
    assert sum(f[c]["EPDM"] for c in ["CM_3"]) == pytest.approx(total_products * 40)
    assert f["Supplier_19"]["EPDM"] == pytest.approx(total_products * 40 / 3)
```

- [ ] **Step 3: Write the failing week test**

`tests/__init__.py`: empty file (lets tests import shared helpers).

`tests/helpers.py` (shared; not a test module, so pytest does not collect it twice):

```python
from sciti.config import Config
from sciti.data.demand import DemandModel
from sciti.engine.state import init_state
from sciti.network import build_network
from sciti.rng import make_streams
from sciti.tech.catalog import load_catalog


def make_state(baseline, weeks=30, seed=1):
    cfg = Config(name="t", seed=seed, weeks=weeks)
    net = build_network(baseline, cfg.assumptions)
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(seed)
    demand = dm.generate(weeks, streams["demand"])
    return init_state(cfg, baseline, net, dm, demand, load_catalog(), streams)
```

`tests/test_engine_week.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_engine_units.py tests/test_engine_week.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.engine.economics'`

- [ ] **Step 5: Implement `sciti/engine/economics.py`**

```python
"""Prices, unit values, and demand propagation through the network (spec §5.4)."""
from __future__ import annotations

import numpy as np

from sciti.network import PRODUCTS


def price_table(net, baseline, markup) -> dict:
    sup = {sid: float(v["price"]) for sid, v in baseline["suppliers"].items()}
    raw = {sku: float(np.mean([sup[s] for s in net.suppliers_of[sku]])) for sku in net.skus}
    cm = {sku: raw[sku] * (1 + markup["CM"]) for sku in net.skus}
    mfg = sum(cm[sku] * u for sku, u in net.bom.items()) * (1 + markup["MFG"])
    dc = mfg * (1 + markup["DC"])
    return {"supplier": sup, "raw": raw, "cm": cm, "mfg": mfg, "dc": dc,
            "retail": dc * (1 + markup["Retail"])}


def sell_price(prices, net, node_id, item) -> float:
    role = net.nodes[node_id].role
    if role == "Supplier":
        return prices["supplier"][node_id]
    if role == "CM":
        return prices["cm"][item]
    return prices[{"MFG": "mfg", "DC": "dc", "Retail": "retail"}[role]]


def unit_value(prices, net, node_id, item) -> float:
    role = net.nodes[node_id].role
    if role == "Supplier":
        return prices["supplier"][node_id]
    if role == "CM":
        return prices["raw"][item[4:]] if item.startswith("RAW:") else prices["cm"][item]
    if role == "MFG":
        return prices["mfg"] if item in PRODUCTS else prices["cm"][item]
    return prices["mfg"] if role == "DC" else prices["dc"]


def propagate(net, retail: dict[tuple[str, str], float]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {n: {} for n in net.order}
    for r in net.by_role("Retail"):
        out[r] = {p: float(retail.get((r, p), 0.0)) for p in PRODUCTS}
    for d in net.by_role("DC"):
        out[d] = {p: sum(net.source_share[r].get(d, 0.0) * out[r][p] for r in net.downstream[d]) for p in PRODUCTS}
    for m in net.by_role("MFG"):
        prod = {p: sum(net.source_share[d].get(m, 0.0) * out[d][p] for d in net.downstream[m]) for p in PRODUCTS}
        total = sum(prod.values())
        out[m] = {**prod, **{sku: total * u for sku, u in net.bom.items()}}
    for c in net.by_role("CM"):
        out[c] = {sku: sum(out[m][sku] for m in net.by_role("MFG")) for sku in net.nodes[c].skus}
    for s in net.by_role("Supplier"):
        sku = net.nodes[s].skus[0]
        out[s] = {sku: out[net.cm_of[sku]][sku] / len(net.suppliers_of[sku])}
    return out
```

- [ ] **Step 6: Implement `sciti/engine/state.py`**

```python
"""Simulation state (spec §5.3)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist

import numpy as np

from sciti.engine.economics import price_table, propagate, sell_price
from sciti.network import PRODUCTS
from sciti.tech.effects import base_params

LEDGER_KEYS = ("revenue", "purchases", "shipping", "holding", "stockout", "handling", "tech", "cogs", "scrap")
PROFIT_COST_KEYS = ("purchases", "shipping", "holding", "stockout", "handling", "tech", "cogs")
COUNT_KEYS = ("demand", "sales", "lost", "orders_placed", "shipped", "received", "built", "shrink",
              "defects_caught", "defects_escaped")
LANE_OF = {"CM": "cm_mfg", "MFG": "mfg_dc", "DC": "dc_retail"}


class StockError(Exception):
    pass


def input_key(role: str, item: str) -> str:
    return f"RAW:{item}" if role == "CM" else item


def output_items(net, node_id: str) -> list[str]:
    node = net.nodes[node_id]
    return list(node.skus) if node.role in ("Supplier", "CM") else list(PRODUCTS)


def lane_type(src_role: str) -> str:
    return LANE_OF[src_role]


@dataclass
class Shipment:
    id: int
    src: str
    dst: str
    item: str
    units: float
    mode: str
    ship_week: int
    due_week: int
    arrive_week: int
    lead_days: float
    miles: float
    cost: float
    co2: float
    value: float
    defective: float = 0.0


@dataclass
class NodeState:
    id: str
    role: str
    stock: dict[str, float] = field(default_factory=dict)
    owed: dict[str, dict[str, float]] = field(default_factory=dict)
    forecast: dict[str, float] = field(default_factory=dict)
    err: dict[str, float] = field(default_factory=dict)
    orders_in: dict[str, float] = field(default_factory=dict)
    capacity: dict[str, float] = field(default_factory=dict)
    cash: float = 0.0
    params: dict[str, float] = field(default_factory=dict)
    capacity_factor: float = 1.0
    extra_lead_days: float = 0.0
    z_boost: float = 0.0
    pending_tech_cost: float = 0.0
    ledger: dict[str, float] = field(default_factory=dict)
    counts: dict[str, float] = field(default_factory=dict)
    consumed: dict[str, float] = field(default_factory=dict)
    opening: dict[str, float] = field(default_factory=dict)
    delta: dict[str, float] = field(default_factory=dict)

    def add(self, item: str, qty: float) -> None:
        if qty < -1e-9:
            raise StockError(f"{self.id}: negative add {qty} of {item}")
        self.stock[item] = self.stock.get(item, 0.0) + qty
        self.delta[item] = self.delta.get(item, 0.0) + qty

    def remove(self, item: str, qty: float) -> None:
        have = self.stock.get(item, 0.0)
        if qty < -1e-9 or qty > have + 1e-6 * max(1.0, have):
            raise StockError(f"{self.id}: cannot remove {qty} of {item}, have {have}")
        self.stock[item] = max(0.0, have - qty)
        self.delta[item] = self.delta.get(item, 0.0) - (have - self.stock[item])

    def owed_total(self, item: str) -> float:
        return sum(b.get(item, 0.0) for b in self.owed.values())

    def reset_week(self) -> None:
        self.ledger = {k: 0.0 for k in LEDGER_KEYS}
        self.ledger["tech"] = self.pending_tech_cost
        self.pending_tech_cost = 0.0
        self.counts = {k: 0.0 for k in COUNT_KEYS}
        self.orders_in = {k: 0.0 for k in self.forecast}
        self.consumed = {}
        self.opening = dict(self.stock)
        self.delta = {}

    def profit(self) -> float:
        return self.ledger["revenue"] - sum(self.ledger[k] for k in PROFIT_COST_KEYS)


@dataclass
class SimState:
    cfg: object
    baseline: dict
    net: object
    catalog: dict
    streams: dict
    demand: dict
    demand_model: object
    flows: list[dict]
    prices: dict
    base: dict[str, dict[str, float]]
    nodes: dict[str, NodeState]
    lead_weeks: dict[tuple[str, str], int]
    z: float
    holdings: dict = field(default_factory=dict)
    in_transit: list[Shipment] = field(default_factory=list)
    arrived: list[Shipment] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    quality: list[float] = field(default_factory=list)
    disruption_end: dict[int, int] = field(default_factory=dict)
    next_id: int = 1
    week: int = 0


def _expected_quote_days(baseline, net, src, dst) -> float:
    role = net.nodes[src].role
    if role == "Supplier":
        return baseline["suppliers"][src]["lead_days"]
    from sciti.engine.ops import allowed_modes
    stats = baseline["lanes"][lane_type(role)]
    miles = net.miles(src, dst)
    mix = allowed_modes(stats["mode_mix"], miles)
    return sum(share * max(1.0, stats["modes"][m]["lead_a"] + stats["modes"][m]["lead_b"] * miles)
               for m, share in mix.items())


def init_state(cfg, baseline, net, demand_model, demand, catalog, streams) -> SimState:
    A = cfg.assumptions
    weeks = cfg.weeks
    flows = [propagate(net, {k: demand_model.expected(*k, w) for k in demand_model.keys})
             for w in range(1, weeks + 2)]
    yr = min(52, weeks)
    mean = {n: {i: float(np.mean([flows[w][n][i] for w in range(yr)])) for i in flows[0][n]} for n in net.order}
    prices = price_table(net, baseline, A.markup)
    base = {n: base_params(net.nodes[n].role, A) for n in net.order}
    lead_weeks: dict[tuple[str, str], int] = {}
    nodes: dict[str, NodeState] = {}
    for n in net.order:
        role = net.nodes[n].role
        ns = NodeState(id=n, role=role, params=dict(base[n]))
        outs = output_items(net, n)
        for item in outs:
            ns.forecast[item] = mean[n][item]
            ns.err[item] = 0.2 * mean[n][item]
            ns.stock[item] = A.fg_cover_weeks * mean[n][item] if role in ("Supplier", "CM", "MFG") else 0.0
        cap = A.capacity_mult
        if role == "Supplier":
            ns.capacity = {outs[0]: cap["Supplier"] * mean[n][outs[0]]}
        elif role == "CM":
            ns.capacity = {sku: cap["CM"] * mean[n][sku] for sku in outs}
        elif role == "MFG":
            ns.capacity = {"BUILD": cap["MFG"] * sum(mean[n][p] for p in PRODUCTS)}
        if role != "Supplier":
            needs = list(net.bom) if role == "MFG" else outs
            for item in needs:
                srcs = [net.cm_of[item]] if role == "MFG" else (net.suppliers_of[item] if role == "CM" else net.upstream[n])
                days = float(np.mean([_expected_quote_days(baseline, net, s_, n) +
                                      base[s_]["dispatch_delay_days"] for s_ in srcs]))
                L = max(1, math.ceil(days / 7))
                lead_weeks[(n, item)] = L
                ns.stock[input_key(role, item)] = ns.stock.get(input_key(role, item), 0.0) + (L + 2) * mean[n][item]
        weekly_rev = sum(mean[n][i] * sell_price(prices, net, n, i) for i in outs)
        ns.cash = A.initial_cash_weeks * weekly_rev
        ns.reset_week()
        nodes[n] = ns
    z = NormalDist().inv_cdf(A.target_service_level)
    catch = A.inspection_catch
    q0 = 1 - float(np.mean([s["defect_share"] for s in baseline["suppliers"].values()])) * (1 - catch)
    return SimState(cfg=cfg, baseline=baseline, net=net, catalog=catalog, streams=streams, demand=demand,
                    demand_model=demand_model, flows=flows, prices=prices, base=base, nodes=nodes,
                    lead_weeks=lead_weeks, z=z, holdings={n: {} for n in net.order}, quality=[q0])
```

- [ ] **Step 7: Implement `sciti/engine/ops.py`**

```python
"""Weekly operations in the fixed order of spec §5.3."""
from __future__ import annotations

import math

import numpy as np

from sciti.engine.economics import propagate, sell_price, unit_value
from sciti.engine.state import Shipment, SimState, input_key, lane_type, output_items
from sciti.network import PRODUCTS
from sciti.tech.effects import effective_params

SHORT_HAUL_MILES = 2500


def order_up_to(forecast: float, sigma: float, lead_weeks: float, z: float, position: float) -> float:
    L = lead_weeks + 1
    return max(0.0, forecast * L + z * sigma * math.sqrt(L) - position)


def ration(available: float, owed: dict[str, float]) -> dict[str, float]:
    total = sum(owed.values())
    if total <= 0:
        return {b: 0.0 for b in sorted(owed)}
    f = min(1.0, available / total)
    return {b: owed[b] * f for b in sorted(owed)}


def build_qty(parts: dict[str, float], bom: dict[str, int], capacity: float, target: float) -> float:
    feasible = min(parts.get(sku, 0.0) / u for sku, u in bom.items())
    return max(0.0, min(feasible, capacity, target))


def allowed_modes(mix: dict[str, float], miles: float) -> dict[str, float]:
    ok = {m: w for m, w in mix.items() if m not in ("Road", "Rail") or miles < SHORT_HAUL_MILES}
    if not ok:
        return {"Air": 1.0}
    total = sum(ok.values())
    return {m: ok[m] / total for m in sorted(ok)}


def sample_lane(stats: dict, miles: float, rng) -> tuple[str, float, float, float]:
    mix = allowed_modes(stats["mode_mix"], miles)
    names = sorted(mix)
    mode = names[int(rng.choice(len(names), p=[mix[m] for m in names]))]
    m = stats["modes"][mode]
    quote = max(1.0, m["lead_a"] + m["lead_b"] * miles)
    lead = max(1.0, quote + m["lead_resid_sd"] * float(rng.standard_normal()))
    return mode, lead, quote, m["cost_per_unit"]


def step_week(s: SimState, t: int) -> None:
    s.week = t
    for n in s.net.order:
        ns = s.nodes[n]
        ns.reset_week()
        ns.params = effective_params(n, t, s.holdings, s.catalog, s.net, s.base[n])
    _arrivals(s, t)
    _retail_sales(s, t)
    _production(s)
    _forecast_and_order(s, t)
    _shipping(s, t)
    _close_week(s)


def _arrivals(s: SimState, t: int) -> None:
    catch = s.cfg.assumptions.inspection_catch
    keep = []
    for sh in s.in_transit:
        if sh.arrive_week != t:
            keep.append(sh)
            continue
        dst = s.nodes[sh.dst]
        caught = sh.defective * catch
        dst.add(input_key(dst.role, sh.item), sh.units - caught)
        dst.counts["received"] += sh.units
        dst.counts["defects_caught"] += caught
        dst.counts["defects_escaped"] += sh.defective - caught
        dst.ledger["purchases"] += sh.value
        dst.ledger["shipping"] += sh.cost
        dst.ledger["scrap"] += caught * (sh.value / sh.units if sh.units else 0.0)
        s.arrived.append(sh)
    s.in_transit = keep


def _retail_sales(s: SimState, t: int) -> None:
    A, pr = s.cfg.assumptions, s.prices
    for r in s.net.by_role("Retail"):
        ns = s.nodes[r]
        for p in PRODUCTS:
            d = float(s.demand[(r, p)][t - 1])
            sold = min(ns.stock[p], d)
            ns.remove(p, sold)
            ns.orders_in[p] = d
            ns.counts["demand"] += d
            ns.counts["sales"] += sold
            ns.counts["lost"] += d - sold
            ns.ledger["revenue"] += sold * pr["retail"]
            ns.ledger["stockout"] += (d - sold) * (pr["retail"] - pr["dc"] + A.goodwill_penalty_per_unit)


def _fg_target(ns, item, cover) -> float:
    return max(0.0, ns.forecast[item] * cover - (ns.stock[item] - ns.owed_total(item)))


def _production(s: SimState) -> None:
    A, net = s.cfg.assumptions, s.net
    for n in net.order:
        ns = s.nodes[n]
        cf = ns.capacity_factor * ns.params["capacity_mult"]
        if ns.role == "Supplier":
            sku = net.nodes[n].skus[0]
            q = min(ns.capacity[sku] * cf, _fg_target(ns, sku, A.fg_cover_weeks))
            ns.add(sku, q)
            ns.counts["built"] += q
            ns.ledger["cogs"] += q * s.prices["supplier"][n] * A.supplier_cogs_share
        elif ns.role == "CM":
            for sku in net.nodes[n].skus:
                q = min(ns.capacity[sku] * cf, ns.stock[f"RAW:{sku}"], _fg_target(ns, sku, A.fg_cover_weeks))
                ns.remove(f"RAW:{sku}", q)
                ns.add(sku, q)
                ns.counts["built"] += q
        elif ns.role == "MFG":
            targets = {p: _fg_target(ns, p, A.fg_cover_weeks) for p in PRODUCTS}
            tt = sum(targets.values())
            total = build_qty({k: ns.stock[k] for k in net.bom}, net.bom, ns.capacity["BUILD"] * cf, tt)
            for sku, u in net.bom.items():
                ns.remove(sku, total * u)
                ns.consumed[sku] = total * u
            if total > 0:
                for p in PRODUCTS:
                    ns.add(p, total * targets[p] / tt)
            ns.counts["built"] += total


def _needs(s: SimState, n: str, exp_next: dict) -> list[tuple[str, list[tuple[str, float]], float, float]]:
    """(item to order, [(source, share)], forecast, sigma) for one buyer."""
    net, ns = s.net, s.nodes[n]
    w = ns.params["forecast_skill"]
    blend = lambda item: (1 - w) * ns.forecast[item] + w * exp_next[n][item]
    sig = lambda e: 1.25 * e * (1 - w / 2)
    if ns.role in ("Retail", "DC"):
        srcs = sorted(net.source_share[n].items())
        return [(p, srcs, blend(p), sig(ns.err[p])) for p in PRODUCTS]
    if ns.role == "MFG":
        f_prod = sum(blend(p) for p in PRODUCTS)
        e_prod = math.sqrt(sum(ns.err[p] ** 2 for p in PRODUCTS))
        return [(sku, [(net.cm_of[sku], 1.0)], f_prod * u, sig(e_prod) * u) for sku, u in net.bom.items()]
    out = []
    for sku in net.nodes[n].skus:
        sups = net.suppliers_of[sku]
        out.append((sku, [(x, 1.0 / len(sups)) for x in sups], blend(sku), sig(ns.err[sku])))
    return out


def _forecast_and_order(s: SimState, t: int) -> None:
    net, A = s.net, s.cfg.assumptions
    alpha = A.smoothing_alpha
    actual = propagate(net, {k: float(s.demand[k][t - 1]) for k in sorted(s.demand)})
    exp_next = s.flows[t]
    rng = s.streams["ops"]
    pipe: dict[tuple[str, str], float] = {}
    for sh in s.in_transit:
        pipe[(sh.dst, sh.item)] = pipe.get((sh.dst, sh.item), 0.0) + sh.units
    for n in reversed(net.order):
        ns = s.nodes[n]
        v = 0.0 if ns.role == "Retail" else ns.params["visibility"]
        for item in sorted(ns.forecast):
            obs = (1 - v) * ns.orders_in[item] + v * actual[n][item]
            prev = ns.forecast[item]
            ns.err[item] = alpha * abs(obs - prev) + (1 - alpha) * ns.err[item]
            ns.forecast[item] = alpha * obs + (1 - alpha) * prev
        if ns.role == "Supplier":
            continue
        z = s.z + ns.z_boost
        for item, srcs, fc, sigma in _needs(s, n, exp_next):
            key = input_key(ns.role, item)
            recorded = max(0.0, ns.stock.get(key, 0.0) * (1 + ns.params["record_error_sd"] * float(rng.standard_normal())))
            owed_to_me = sum(s.nodes[src].owed.get(n, {}).get(item, 0.0) for src, _ in srcs)
            owed_by_me = ns.owed_total(item) if ns.role == "DC" else 0.0
            position = recorded + pipe.get((n, item), 0.0) + owed_to_me - owed_by_me
            q = order_up_to(fc, sigma, s.lead_weeks[(n, item)], z, position)
            if q <= 0:
                continue
            for src, share in srcs:
                seller = s.nodes[src]
                seller.owed.setdefault(n, {})
                seller.owed[n][item] = seller.owed[n].get(item, 0.0) + q * share
                seller.orders_in[item] += q * share
            ns.counts["orders_placed"] += q


def make_shipment(s: SimState, src: str, dst: str, item: str, q: float, t: int) -> Shipment:
    sn = s.nodes[src]
    P = sn.params
    miles = s.net.miles(src, dst)
    rng = s.streams["lead"]
    defective = 0.0
    if sn.role == "Supplier":
        sup = s.baseline["suppliers"][src]
        quote = sup["lead_days"]
        lead = max(1.0, quote + sup["lead_sd_days"] * float(rng.standard_normal()))
        mode, cpu, co2 = "Supplier", 0.0, 0.0
        defective = q * min(1.0, sup["defect_share"] * P["defect_mult"])
    else:
        mode, lead, quote, cpu = sample_lane(s.baseline["lanes"][lane_type(sn.role)], miles, rng)
        co2 = q * s.baseline["co2_ton_per_unit"] * miles * s.baseline["co2_factors"][mode] * P["co2_mult"]
    lead += P["dispatch_delay_days"] + sn.extra_lead_days
    quote += s.base[src]["dispatch_delay_days"]
    sh = Shipment(id=s.next_id, src=src, dst=dst, item=item, units=q, mode=mode, ship_week=t,
                  due_week=t + max(1, math.ceil(quote / 7)), arrive_week=t + max(1, math.ceil(lead / 7)),
                  lead_days=lead, miles=miles, cost=q * cpu * P["ship_cost_mult"], co2=co2,
                  value=q * sell_price(s.prices, s.net, src, item), defective=defective)
    s.next_id += 1
    return sh


def _shipping(s: SimState, t: int) -> None:
    for n in s.net.order:
        ns = s.nodes[n]
        if ns.role == "Retail":
            continue
        for item in output_items(s.net, n):
            owed = {b: ns.owed[b].get(item, 0.0) for b in sorted(ns.owed) if ns.owed[b].get(item, 0.0) > 0}
            if not owed:
                continue
            for b, q in ration(ns.stock[item], owed).items():
                if q <= 1e-9:
                    continue
                ns.remove(item, q)
                ns.owed[b][item] -= q
                sh = make_shipment(s, n, b, item, q, t)
                s.in_transit.append(sh)
                ns.counts["shipped"] += q
                ns.ledger["revenue"] += sh.value
                ns.ledger["handling"] += q * ns.params["handling_cost_per_unit"]


def _close_week(s: SimState) -> None:
    rate = s.cfg.assumptions.holding_rate_annual / 52
    received = escaped = 0.0
    for n in s.net.order:
        ns = s.nodes[n]
        for item in sorted(ns.stock):
            lost = ns.stock[item] * ns.params["shrink_rate"]
            val = unit_value(s.prices, s.net, n, item)
            ns.remove(item, lost)
            ns.counts["shrink"] += lost
            ns.ledger["scrap"] += lost * val
            ns.ledger["holding"] += ns.stock[item] * val * rate
        for tech_id in sorted(s.holdings.get(n, {})):
            ns.ledger["tech"] += s.catalog[tech_id].cost_per_week[ns.role]
        ns.cash += ns.profit()
        if ns.role == "CM":
            received += ns.counts["received"]
            escaped += ns.counts["defects_escaped"]
    s.quality.append(1 - escaped / received if received > 0 else s.quality[-1])
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_engine_units.py tests/test_engine_week.py -v`
Expected: 13 passed. If a test fails, use superpowers:systematic-debugging; do not loosen assertions.

- [ ] **Step 9: Commit**

```bash
git add sciti/config.py sciti/engine/state.py sciti/engine/economics.py sciti/engine/ops.py tests/__init__.py tests/helpers.py tests/test_engine_units.py tests/test_engine_week.py
git commit -m "feat: engine core - state, prices, weekly receive/sell/build/order/ship

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Disruptions

**Files:**
- Create: `sciti/disruptions.py`
- Modify: `sciti/engine/ops.py` (call `apply_disruptions` in `step_week`)
- Test: `tests/test_disruptions.py`

**Interfaces:**
- Consumes: `SimState`, `Config.disruptions` (list of `Disruption`), node `params["recovery_mult"]`, `params["early_warning_weeks"]`.
- Produces:
  - `validate_disruptions(disruptions, net) -> None` (raises `ValueError` for unknown target or non-positive weeks)
  - `apply_disruptions(s: SimState, t: int) -> None`: resets every node's `capacity_factor=1`, `extra_lead_days=0`, `z_boost=0`; on `t == start_week` fixes end week `start + ceil(weeks · recovery_mult(target at t))` in `s.disruption_end[index]` and appends event `{"week", "type": "disruption_start", "target", "until"}`; while `start ≤ t < end` multiplies target `capacity_factor` and adds `extra_lead_days`; sets `z_boost = 1.0` for any node whose `early_warning_weeks > 0` and where a disruption on itself or an upstream partner starts within `(t, t + early_warning_weeks]`.

- [ ] **Step 1: Write the failing test**

`tests/test_disruptions.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_disruptions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.disruptions'`

- [ ] **Step 3: Implement `sciti/disruptions.py`**

```python
"""Scheduled capacity and lead-time shocks (spec §5.3 step 1, §6 risk_intel)."""
from __future__ import annotations

import math


def validate_disruptions(disruptions, net) -> None:
    for i, d in enumerate(disruptions):
        if d.target not in net.nodes:
            raise ValueError(f"disruption {i}: unknown target {d.target!r}")
        if d.weeks <= 0 or d.start_week < 1:
            raise ValueError(f"disruption {i}: start_week must be >= 1 and weeks > 0")


def apply_disruptions(s, t: int) -> None:
    for ns in s.nodes.values():
        ns.capacity_factor, ns.extra_lead_days, ns.z_boost = 1.0, 0.0, 0.0
    for i, d in enumerate(s.cfg.disruptions):
        if t == d.start_week:
            mult = s.nodes[d.target].params["recovery_mult"]
            s.disruption_end[i] = d.start_week + math.ceil(d.weeks * mult)
            s.events.append({"week": t, "type": "disruption_start", "target": d.target,
                             "until": s.disruption_end[i]})
        if i in s.disruption_end and d.start_week <= t < s.disruption_end[i]:
            s.nodes[d.target].capacity_factor *= d.capacity_mult
            s.nodes[d.target].extra_lead_days += d.extra_lead_days
    for n in s.net.order:
        ew = s.nodes[n].params["early_warning_weeks"]
        if ew <= 0:
            continue
        watch = set(s.net.upstream[n]) | {n}
        if any(d.target in watch and t < d.start_week <= t + ew for d in s.cfg.disruptions):
            s.nodes[n].z_boost = 1.0
```

- [ ] **Step 4: Call it from `step_week` in `sciti/engine/ops.py`**

Add the import at the top:

```python
from sciti.disruptions import apply_disruptions
```

In `step_week`, insert the call after the params loop and before `_arrivals`:

```python
    for n in s.net.order:
        ns = s.nodes[n]
        ns.reset_week()
        ns.params = effective_params(n, t, s.holdings, s.catalog, s.net, s.base[n])
    apply_disruptions(s, t)
    _arrivals(s, t)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_disruptions.py tests/test_engine_week.py -v`
Expected: all pass (early warning for MFG_US: disruption at week 5, ew=2 → boosted at t=3 and t=4).

- [ ] **Step 6: Commit**

```bash
git add sciti/disruptions.py sciti/engine/ops.py tests/test_disruptions.py
git commit -m "feat: scheduled disruptions with risk-intel recovery and early warning

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Invariant checks

**Files:**
- Create: `sciti/checks.py`
- Test: `tests/test_checks.py`

**Interfaces:**
- Consumes: `SimState` after `step_week`.
- Produces:
  - `SimulationError(Exception)`
  - `check_invariants(s: SimState, t: int) -> list[str]` — returns human-readable violations (empty list = clean). Checks: (1) no negative stock; (2) per node per item `stock == opening + delta` (tolerance `1e-6 · max(1, |stock|)`); (3) MFG `consumed[sku] == built · bom[sku]`; (4) shipment ids unique across `arrived` ∪ `in_transit`, every in-transit `arrive_week > t`; (5) all ledger values and cash finite, `|cash| < 1e15`.
  - `enforce(s: SimState, t: int, strict: bool) -> None` — strict: raise `SimulationError` with all violations; non-strict: append `{"week", "type": "check_warning", "detail"}` events.

- [ ] **Step 1: Write the failing test**

`tests/test_checks.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_checks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.checks'`

- [ ] **Step 3: Implement `sciti/checks.py`**

```python
"""Weekly invariants (spec §9.4)."""
from __future__ import annotations

import math


class SimulationError(Exception):
    pass


def check_invariants(s, t: int) -> list[str]:
    out = []
    for n in s.net.order:
        ns = s.nodes[n]
        for item in sorted(set(ns.stock) | set(ns.opening)):
            now = ns.stock.get(item, 0.0)
            if now < 0:
                out.append(f"week {t} {n} {item}: negative stock {now}")
            expect = ns.opening.get(item, 0.0) + ns.delta.get(item, 0.0)
            if abs(now - expect) > 1e-6 * max(1.0, abs(now)):
                out.append(f"week {t} {n} {item}: conservation broken, stock {now} vs expected {expect}")
        if ns.role == "MFG":
            for sku, u in s.net.bom.items():
                if abs(ns.consumed.get(sku, 0.0) - ns.counts["built"] * u) > 1e-6 * max(1.0, ns.counts["built"] * u):
                    out.append(f"week {t} {n} {sku}: BOM consumption {ns.consumed.get(sku)} != built*{u}")
        values = list(ns.ledger.values()) + [ns.cash]
        if not all(math.isfinite(v) for v in values) or abs(ns.cash) >= 1e15:
            out.append(f"week {t} {n}: non-finite or out-of-range money (cash {ns.cash})")
    ids = [sh.id for sh in s.arrived] + [sh.id for sh in s.in_transit]
    if len(ids) != len(set(ids)):
        out.append(f"week {t}: duplicate shipment ids")
    late = [sh.id for sh in s.in_transit if sh.arrive_week <= t]
    if late:
        out.append(f"week {t}: shipments past arrival still in transit: {late[:5]}")
    return out


def enforce(s, t: int, strict: bool) -> None:
    violations = check_invariants(s, t)
    if not violations:
        return
    if strict:
        raise SimulationError("\n".join(violations))
    for v in violations:
        s.events.append({"week": t, "type": "check_warning", "detail": v})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_checks.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add sciti/checks.py tests/test_checks.py
git commit -m "feat: weekly invariant checks with strict and warning modes

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Adoption, outputs, metrics, runner, CLI `prepare` and `run`

**Files:**
- Create: `sciti/engine/adoption.py`, `sciti/metrics.py`, `sciti/outputs.py`, `sciti/runner.py`, `sciti/cli.py`, `configs/baseline.yaml`
- Test: `tests/test_adoption.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `sciti.engine.adoption`: `AdoptionError(Exception)`; `adopt(s, node_id, tech_id, week, coalition_id=None, one_time=None) -> dict` (checks eligibility and not already held; creates `TechHolding(tech, week, week + setup_weeks, coalition_id)`; adds `one_time` (default `tech.cost_one_time[role]`) to `ns.pending_tech_cost`; appends and returns event `{"week", "type": "adopt", "node", "tech", "coalition", "one_time"}`); `drop(s, node_id, tech_id, week) -> dict` (event type `"drop"`); `apply_forced(s, week) -> None` (for each `cfg.forced_adoptions` with this week: coalition id `forced_<index>` if >1 member; one-time cost = sum of members' role costs ÷ member count)
  - `sciti.metrics`: `week_rows(s, t) -> list[dict]` (one row per node, columns `WEEK_COLUMNS`); `WEEK_COLUMNS: list[str]`; `summarize(s, rows: list[dict]) -> dict`
  - `sciti.outputs`: `scrub(text: str) -> str` (replaces `sk-ant-…` key-like strings with `[REDACTED]`); `RunWriter(run_dir: Path)` with `.log_decision(record: dict)`, `.finish(s, rows, summary, manifest)`, `.close()`; `build_manifest(cfg, run_id, started, finished, extra: dict) -> dict`; `DETERMINISTIC_FILES = ("weekly_nodes.csv", "shipments.csv", "events.jsonl", "summary.json")`
  - `sciti.runner`: `run(cfg: Config, run_dir: Path | None = None, policy=None) -> Path`; `quarter_start(t: int) -> bool` (`(t − 1) % 13 == 0`)
  - `sciti.cli.main(argv: list[str] | None = None) -> int` with subcommands `prepare [--xlsx PATH] [--out DIR]` and `run CONFIG [--run-dir DIR]`

`summary.json` keys (spec §5.5): `network_profit`, `costs` (dict by `PROFIT_COST_KEYS` plus `scrap`), `revenue`, `fill_rate`, `on_time_rate`, `retail_on_time_rate`, `mean_lead_days`, `p95_lead_days`, `quality_mean`, `satisfaction_index`, `co2_kg`, `bullwhip` (dict role → ratio, weeks > 13), `adoptions`, `coalitions`, `tech_spend`, `profit_by_role`, `weeks`.

- [ ] **Step 1: Write the failing tests**

`tests/test_adoption.py`:

```python
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
```

`tests/test_runner.py`:

```python
import csv
import json

from sciti.config import Config, Disruption, ForcedAdoption
from sciti.outputs import DETERMINISTIC_FILES, scrub
from sciti.runner import run


def cfg(baseline_path, tmp_path, **kw):
    return Config(name="t", seed=3, weeks=26, baseline_path=str(baseline_path),
                  output_dir=str(tmp_path / "runs"), **kw)


def test_run_writes_all_outputs(baseline_path, tmp_path):
    d = run(cfg(baseline_path, tmp_path))
    for f in DETERMINISTIC_FILES + ("manifest.json", "decisions.jsonl", "network.json"):
        assert (d / f).exists(), f
    rows = list(csv.DictReader(open(d / "weekly_nodes.csv")))
    assert len(rows) == 26 * 48
    summary = json.loads((d / "summary.json").read_text())
    assert 0 <= summary["fill_rate"] <= 1
    assert 0 <= summary["satisfaction_index"] <= 1
    man = json.loads((d / "manifest.json").read_text())
    assert man["seed"] == 3 and man["decision_policy"] == "none"
    assert len(man["config_hash"]) == 64 and "git_commit" in man
    assert man["checks"] == "passed"


def test_same_seed_outputs_identical(baseline_path, tmp_path):
    c = cfg(baseline_path, tmp_path, forced_adoptions=[ForcedAdoption(week=1, tech="routing", members=["MFG_US"])],
            disruptions=[Disruption(target="CM_4", start_week=4, weeks=3, capacity_mult=0.2)])
    a = run(c, run_dir=tmp_path / "a")
    b = run(c, run_dir=tmp_path / "b")
    for f in DETERMINISTIC_FILES:
        assert (a / f).read_bytes() == (b / f).read_bytes(), f


def test_forced_tech_changes_outcome(baseline_path, tmp_path):
    base = run(cfg(baseline_path, tmp_path), run_dir=tmp_path / "base")
    tech = run(cfg(baseline_path, tmp_path, forced_adoptions=[
        ForcedAdoption(week=1, tech="routing", members=["MFG_US", "MFG_China"])]), run_dir=tmp_path / "tech")
    s0 = json.loads((base / "summary.json").read_text())
    s1 = json.loads((tech / "summary.json").read_text())
    assert s1["costs"]["shipping"] < s0["costs"]["shipping"]
    assert s1["adoptions"] == 2 and s1["coalitions"] == 1


def test_scrub_removes_keys():
    assert scrub("key sk-ant-api03-abcDEF123_xyz-987654 end") == "key [REDACTED] end"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_adoption.py tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.engine.adoption'`

- [ ] **Step 3: Implement `sciti/engine/adoption.py`**

```python
"""Technology adoption bookkeeping (spec §6, §7.3)."""
from __future__ import annotations

from sciti.tech.catalog import TechHolding


class AdoptionError(Exception):
    pass


def adopt(s, node_id: str, tech_id: str, week: int, coalition_id: str | None = None,
          one_time: float | None = None) -> dict:
    if tech_id not in s.catalog:
        raise AdoptionError(f"unknown tech {tech_id!r}")
    tech = s.catalog[tech_id]
    ns = s.nodes[node_id]
    if ns.role not in tech.eligible_roles:
        raise AdoptionError(f"{node_id} ({ns.role}) is not eligible for {tech_id}")
    if tech_id in s.holdings[node_id]:
        raise AdoptionError(f"{node_id} already holds {tech_id}")
    cost = tech.cost_one_time[ns.role] if one_time is None else one_time
    s.holdings[node_id][tech_id] = TechHolding(tech_id, week, week + tech.setup_weeks, coalition_id)
    ns.pending_tech_cost += cost
    ev = {"week": week, "type": "adopt", "node": node_id, "tech": tech_id,
          "coalition": coalition_id, "one_time": cost}
    s.events.append(ev)
    return ev


def drop(s, node_id: str, tech_id: str, week: int) -> dict:
    if tech_id not in s.holdings[node_id]:
        raise AdoptionError(f"{node_id} does not hold {tech_id}")
    del s.holdings[node_id][tech_id]
    ev = {"week": week, "type": "drop", "node": node_id, "tech": tech_id}
    s.events.append(ev)
    return ev


def apply_forced(s, week: int) -> None:
    for i, fa in enumerate(s.cfg.forced_adoptions):
        if fa.week != week:
            continue
        tech = s.catalog[fa.tech]
        coalition = f"forced_{i}" if len(fa.members) > 1 else None
        share = sum(tech.cost_one_time[s.nodes[m].role] for m in fa.members) / len(fa.members)
        if coalition:
            s.events.append({"week": week, "type": "coalition", "id": coalition, "tech": fa.tech,
                             "members": sorted(fa.members), "kind": coalition_kind(s.net, fa.members)})
        for m in sorted(fa.members):
            adopt(s, m, fa.tech, week, coalition, share)


def coalition_kind(net, members) -> str:
    n = len(members)
    if n == len(net.order):
        return "network"
    if n == 2:
        return "dyad"
    if n == 3:
        return "triad"
    return "chain"
```

- [ ] **Step 4: Implement `sciti/metrics.py`**

```python
"""Per-week rows and run summary (spec §5.5)."""
from __future__ import annotations

import numpy as np

from sciti.engine.state import COUNT_KEYS, LEDGER_KEYS, PROFIT_COST_KEYS

WEEK_COLUMNS = (["week", "node", "role", "stock_units", "cash", "profit", "capacity_factor", "techs"]
                + list(COUNT_KEYS) + list(LEDGER_KEYS))


def week_rows(s, t: int) -> list[dict]:
    rows = []
    for n in s.net.order:
        ns = s.nodes[n]
        row = {"week": t, "node": n, "role": ns.role, "stock_units": round(sum(ns.stock.values()), 4),
               "cash": round(ns.cash, 2), "profit": round(ns.profit(), 2),
               "capacity_factor": ns.capacity_factor,
               "techs": ";".join(sorted(k for k, h in s.holdings[n].items() if t >= h.active_week))}
        row.update({k: round(ns.counts[k], 4) for k in COUNT_KEYS})
        row.update({k: round(ns.ledger[k], 2) for k in LEDGER_KEYS})
        rows.append(row)
    return rows


def _series(rows, role, key, weeks):
    agg = np.zeros(weeks)
    for r in rows:
        if r["role"] == role:
            agg[r["week"] - 1] += r[key]
    return agg


def summarize(s, rows: list[dict]) -> dict:
    A = s.cfg.assumptions
    weeks = s.cfg.weeks
    tot = lambda key: float(sum(r[key] for r in rows))
    retail = [r for r in rows if r["role"] == "Retail"]
    demand = sum(r["demand"] for r in retail)
    fill = sum(r["sales"] for r in retail) / demand if demand else 1.0
    arrived = s.arrived
    on_time = float(np.mean([sh.arrive_week <= sh.due_week for sh in arrived])) if arrived else 1.0
    r_in = [sh for sh in arrived if s.nodes[sh.dst].role == "Retail"]
    r_on_time = float(np.mean([sh.arrive_week <= sh.due_week for sh in r_in])) if r_in else 1.0
    leads = np.array([sh.lead_days for sh in arrived]) if arrived else np.array([0.0])
    quality = float(np.mean(s.quality[1:])) if len(s.quality) > 1 else s.quality[0]
    w = A.satisfaction_weights
    csi = w["fill_rate"] * fill + w["on_time"] * r_on_time + w["quality"] * quality
    dem = _series(rows, "Retail", "demand", weeks)[13:]
    bullwhip = {}
    for role in ("Retail", "DC", "MFG", "CM"):
        orders = _series(rows, role, "orders_placed", weeks)[13:]
        bullwhip[role] = float(np.var(orders) / np.var(dem)) if len(dem) > 1 and np.var(dem) > 0 else None
    adopt_ev = [e for e in s.events if e["type"] == "adopt"]
    profit_by_role = {}
    for r in rows:
        profit_by_role[r["role"]] = profit_by_role.get(r["role"], 0.0) + r["profit"]
    return {
        "weeks": weeks,
        "revenue": tot("revenue"),
        "costs": {k: tot(k) for k in PROFIT_COST_KEYS + ("scrap",)},
        "network_profit": tot("profit"),
        "profit_by_role": {k: round(v, 2) for k, v in sorted(profit_by_role.items())},
        "fill_rate": fill,
        "on_time_rate": on_time,
        "retail_on_time_rate": r_on_time,
        "mean_lead_days": float(leads.mean()),
        "p95_lead_days": float(np.percentile(leads, 95)),
        "quality_mean": quality,
        "satisfaction_index": csi,
        "co2_kg": float(sum(sh.co2 for sh in arrived)),
        "bullwhip": bullwhip,
        "adoptions": len(adopt_ev),
        "coalitions": len([e for e in s.events if e["type"] == "coalition"]),
        "tech_spend": tot("tech"),
    }
```

- [ ] **Step 5: Implement `sciti/outputs.py`**

```python
"""Run output files and manifest (spec §8, §9.1, §9.6)."""
from __future__ import annotations

import csv
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata as md
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path

from sciti.config import config_hash
from sciti.engine.state import Shipment
from sciti.metrics import WEEK_COLUMNS

DETERMINISTIC_FILES = ("weekly_nodes.csv", "shipments.csv", "events.jsonl", "summary.json")
KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHIPMENT_COLUMNS = [f.name for f in dataclasses.fields(Shipment)]


def scrub(text: str) -> str:
    return KEY_PATTERN.sub("[REDACTED]", text)


def _dumps(obj) -> str:
    return scrub(json.dumps(obj, sort_keys=True, default=str))


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _git() -> dict:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "sciti", "configs"],
                                    cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip())
        return {"git_commit": commit, "git_dirty": dirty}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"git_commit": None, "git_dirty": None}


def build_manifest(cfg, run_id: str, started: str, finished: str, extra: dict) -> dict:
    versions = {}
    for pkg in ("numpy", "pandas", "pydantic", "pyyaml", "anthropic"):
        try:
            versions[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            versions[pkg] = None
    return {"run_id": run_id, "name": cfg.name, "seed": cfg.seed, "started": started, "finished": finished,
            "config": cfg.model_dump(mode="json"), "config_hash": config_hash(cfg),
            "python": platform.python_version(), "packages": versions,
            "baseline_sha256": _sha256(Path(cfg.baseline_path)),
            "decision_policy": cfg.decision.policy, "model": cfg.decision.model, **_git(), **extra}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class RunWriter:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._decisions = open(self.run_dir / "decisions.jsonl", "w")

    def log_decision(self, record: dict) -> None:
        self._decisions.write(_dumps(record) + "\n")
        self._decisions.flush()

    def finish(self, s, rows: list[dict], summary: dict, manifest: dict) -> None:
        with open(self.run_dir / "weekly_nodes.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=WEEK_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        ships = sorted(s.arrived + s.in_transit, key=lambda sh: sh.id)
        with open(self.run_dir / "shipments.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SHIPMENT_COLUMNS)
            w.writeheader()
            for sh in ships:
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in dataclasses.asdict(sh).items()})
        (self.run_dir / "events.jsonl").write_text("".join(_dumps(e) + "\n" for e in s.events))
        (self.run_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
        net = {"nodes": [{"id": n, "role": s.net.nodes[n].role, "city": s.net.nodes[n].city,
                          "lat": s.net.nodes[n].lat, "lon": s.net.nodes[n].lon} for n in s.net.order],
               "links": [[a, b] for a in s.net.order for b in s.net.downstream[a]],
               "techs": {t.id: t.name for t in s.catalog.values()}}
        (self.run_dir / "network.json").write_text(json.dumps(net, indent=1))
        (self.run_dir / "manifest.json").write_text(scrub(json.dumps(manifest, indent=1, sort_keys=True, default=str)))
        report = Path(s.cfg.baseline_path).with_name("validation_report.md")
        if report.exists():
            shutil.copy(report, self.run_dir / "validation_report.md")

    def close(self) -> None:
        self._decisions.close()
```

- [ ] **Step 6: Implement `sciti/runner.py`**

```python
"""One simulation run (spec §4, §8)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from sciti.checks import SimulationError, enforce
from sciti.data.demand import DemandModel
from sciti.disruptions import validate_disruptions
from sciti.engine.adoption import apply_forced
from sciti.engine.ops import step_week
from sciti.engine.state import init_state
from sciti.metrics import summarize, week_rows
from sciti.network import build_network
from sciti.outputs import RunWriter, build_manifest, now
from sciti.rng import make_streams
from sciti.tech.catalog import catalog_hash, load_catalog


def quarter_start(t: int) -> bool:
    return (t - 1) % 13 == 0


def run(cfg, run_dir: Path | None = None, policy=None) -> Path:
    started = now()
    baseline_file = Path(cfg.baseline_path)
    if not baseline_file.exists():
        raise FileNotFoundError(f"{baseline_file} not found; run `sciti prepare` first")
    baseline = json.loads(baseline_file.read_text())
    net = build_network(baseline, cfg.assumptions)
    validate_disruptions(cfg.disruptions, net)
    catalog = load_catalog(cfg.catalog_path)
    for fa in cfg.forced_adoptions:
        if fa.tech not in catalog or any(m not in net.nodes for m in fa.members):
            raise ValueError(f"forced adoption refers to unknown tech or node: {fa}")
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(cfg.seed)
    demand = dm.generate(cfg.weeks, streams["demand"])
    s = init_state(cfg, baseline, net, dm, demand, catalog, streams)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{cfg.name}_s{cfg.seed}_{stamp}"
    run_dir = Path(run_dir) if run_dir else Path(cfg.output_dir) / run_id
    writer = RunWriter(run_dir)
    rows: list[dict] = []
    checks = "passed" if cfg.checks.strict else "warnings-allowed"
    extra = {"catalog_sha256": catalog_hash(cfg.catalog_path), "xlsx_sha256": baseline["source"]["xlsx_sha256"]}
    try:
        for t in range(1, cfg.weeks + 1):
            if quarter_start(t):
                apply_forced(s, t)
            step_week(s, t)
            enforce(s, t, cfg.checks.strict)
            rows.extend(week_rows(s, t))
    except SimulationError as e:
        checks = f"failed: {e}"
        writer.finish(s, rows, {"error": str(e)}, build_manifest(cfg, run_id, started, now(), {**extra, "checks": checks}))
        writer.close()
        raise
    summary = summarize(s, rows)
    writer.finish(s, rows, summary, build_manifest(cfg, run_id, started, now(), {**extra, "checks": checks}))
    writer.close()
    return run_dir
```

- [ ] **Step 7: Implement `sciti/cli.py` and `configs/baseline.yaml`**

`sciti/cli.py`:

```python
"""`sciti` command line (spec §4.1)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_XLSX = Path.home() / "Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sciti")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="read the workbook once into data/baseline.json")
    p.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    p.add_argument("--out", default="data")
    r = sub.add_parser("run", help="run one simulation")
    r.add_argument("config")
    r.add_argument("--run-dir", default=None)
    args = ap.parse_args(argv)

    if args.cmd == "prepare":
        from sciti.data.loader import prepare
        prepare(Path(args.xlsx), Path(args.out))
        print(f"wrote {args.out}/baseline.json and {args.out}/validation_report.md")
        return 0
    if args.cmd == "run":
        from sciti.config import load_config
        from sciti.runner import run
        out = run(load_config(args.config), run_dir=Path(args.run_dir) if args.run_dir else None)
        print(out)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

`configs/baseline.yaml`:

```yaml
# No-innovation baseline (spec §4.2 policy `none`).
name: baseline
seed: 1
weeks: 156
decision:
  policy: none
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_adoption.py tests/test_runner.py -v`
Expected: 8 passed

- [ ] **Step 9: Run on the real workbook**

```bash
.venv/bin/sciti prepare
.venv/bin/sciti run configs/baseline.yaml
```

Expected: `data/baseline.json` and `data/validation_report.md` written; the run prints a `runs/baseline_s1_<stamp>` path in under a minute. Open `summary.json` and `validation_report.md` and paste both into the task report. A `SimulationError` here is a bug: use superpowers:systematic-debugging.

- [ ] **Step 10: Commit**

```bash
git add sciti/engine/adoption.py sciti/metrics.py sciti/outputs.py sciti/runner.py sciti/cli.py configs/baseline.yaml tests/test_adoption.py tests/test_runner.py
git commit -m "feat: runner with adoption, outputs, manifest, summary, and CLI prepare/run

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Golden run and calibration tests

**Files:**
- Create: `tests/test_golden.py`, `tests/golden/none_seed7_summary.json` (generated in Step 2), `tests/test_calibration.py`

**Interfaces:**
- Consumes: `run`, `Config`, `DemandModel`, synthetic `baseline_path` fixture.
- Produces: regression guard files only.

- [ ] **Step 1: Write the golden test**

`tests/test_golden.py`:

```python
import json
import os
from pathlib import Path

import pytest

from sciti.config import Config, Disruption, ForcedAdoption
from sciti.runner import run

GOLDEN = Path(__file__).parent / "golden" / "none_seed7_summary.json"


def golden_cfg(baseline_path, tmp_path):
    return Config(name="golden", seed=7, weeks=52, baseline_path=str(baseline_path),
                  output_dir=str(tmp_path),
                  forced_adoptions=[ForcedAdoption(week=1, tech="control_tower",
                                                   members=["DC_Shanghai", "Retail_5", "Retail_6", "Retail_7", "Retail_8"])],
                  disruptions=[Disruption(target="CM_4", start_week=10, weeks=4, capacity_mult=0.3)])


def test_golden_summary(baseline_path, tmp_path):
    d = run(golden_cfg(baseline_path, tmp_path), run_dir=tmp_path / "g")
    got = json.loads((d / "summary.json").read_text())
    if os.environ.get("SCITI_UPDATE_GOLDEN") == "1":
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True))
        pytest.skip("golden file updated")
    assert got == json.loads(GOLDEN.read_text())


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_full_horizon_invariants(baseline_path, tmp_path, seed):
    c = Config(name="inv", seed=seed, weeks=156, baseline_path=str(baseline_path), output_dir=str(tmp_path))
    run(c, run_dir=tmp_path / f"s{seed}")  # strict checks raise on any violation
```

- [ ] **Step 2: Generate the golden file and verify the test**

```bash
SCITI_UPDATE_GOLDEN=1 .venv/bin/pytest tests/test_golden.py::test_golden_summary -v
.venv/bin/pytest tests/test_golden.py -v
```

Expected: first command SKIPPED ("golden file updated"); second: 6 passed. Inspect `tests/golden/none_seed7_summary.json` — fill rate, CSI and quality in [0, 1], `adoptions` = 5, `coalitions` = 1. Only regenerate the golden file on purpose and say why in the commit message.

- [ ] **Step 3: Write the calibration test**

`tests/test_calibration.py`:

```python
import csv
import json
from pathlib import Path

import numpy as np
import pytest

from sciti.config import Config
from sciti.data.demand import DemandModel
from sciti.runner import run

REAL_BASELINE = Path(__file__).resolve().parents[1] / "data" / "baseline.json"


def _check(baseline_file: Path, tmp_path):
    base = json.loads(baseline_file.read_text())
    dm = DemandModel.from_baseline(base, 0.15, 1.0)
    fill, sims, lead_ratio = [], [], []
    expected = sum(dm.expected(r, p, w) for r, p in dm.keys for w in range(1, 53))
    for seed in range(10):
        d = run(Config(name="cal", seed=seed, weeks=52, baseline_path=str(baseline_file), output_dir=str(tmp_path)),
                run_dir=tmp_path / f"c{seed}")
        rows = [r for r in csv.DictReader(open(d / "weekly_nodes.csv")) if r["role"] == "Retail"]
        sims.append(sum(float(r["demand"]) for r in rows))
        fill.append(json.loads((d / "summary.json").read_text())["fill_rate"])
        ships = [r for r in csv.DictReader(open(d / "shipments.csv")) if r["mode"] != "Supplier"]
        for mode in sorted({r["mode"] for r in ships}):
            m = base["lanes"]["mfg_dc"]["modes"].get(mode)
            sub = [r for r in ships if r["mode"] == mode and r["src"].startswith("MFG")]
            if m and sub:
                predicted = np.mean([max(1.0, m["lead_a"] + m["lead_b"] * float(r["miles"])) for r in sub])
                actual = np.mean([float(r["lead_days"]) for r in sub])
                lead_ratio.append(actual / predicted)
    print(f"\nfill rate mean {np.mean(fill):.3f}; demand sim/expected {np.mean(sims) / expected:.3f}; "
          f"lead actual/predicted {np.mean(lead_ratio):.3f}")
    assert np.mean(sims) == pytest.approx(expected, rel=0.05)
    assert np.mean(lead_ratio) == pytest.approx(1.0, rel=0.15)
    assert np.mean(fill) > 0.80


def test_calibration_synthetic(baseline_path, tmp_path):
    _check(baseline_path, tmp_path)


@pytest.mark.realdata
@pytest.mark.skipif(not REAL_BASELINE.exists(), reason="run `sciti prepare` first")
def test_calibration_real(tmp_path):
    _check(REAL_BASELINE, tmp_path)
```

Note: MFG→DC `lead_days` includes the MFG's dispatch delay (0 at MFGs), so actual/predicted ≈ 1 plus the effect of the `max(1, …)` floor.

- [ ] **Step 4: Run calibration**

Run: `.venv/bin/pytest tests/test_calibration.py -v -s`
Expected: 2 passed, printed ratios near 1.0 and fill rate above 0.80. If the fill-rate assertion fails, it means the baseline inventory policy is mis-tuned: use superpowers:systematic-debugging, report the numbers, and do not lower the threshold without the user's agreement.

- [ ] **Step 5: Full suite and commit**

Run: `.venv/bin/pytest -v`
Expected: all tests pass.

```bash
git add tests/test_golden.py tests/golden/none_seed7_summary.json tests/test_calibration.py
git commit -m "test: golden run, full-horizon invariants, demand and lead-time calibration

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
