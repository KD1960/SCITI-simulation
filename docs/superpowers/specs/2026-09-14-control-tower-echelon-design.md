# Control Tower Redesign — Echelon Ordering

**Project:** SCITI 1
**Date:** 2026-09-14
**Status:** Approved by Kevin. Amended 2026-09-14 after acceptance run 1 (§3.4, §3.5, §3.6).
**Replaces:** the `visibility` effect in `_forecast_and_order` (spec 2026-09-12 §5.3 step 5, §6 `control_tower`)

---

## 1. Problem

Before this change, a node with a control tower replaced the orders it receives with end-customer demand as its forecast signal:

```
obs = (1 - v) * orders_in + v * actual_end_demand
```

Its forecast error `err`, and so its safety stock, is then measured against that smooth signal, while the node still has to fill lumpy downstream orders. Measured on 10 paired seeds with the whole network adopting (after the purchase-timing fix):

| Rule | Fill rate | Profit | Main cost changes |
|---|---|---|---|
| Today (`err` vs. end demand) | −0.23 pt | −$62M | stockout +$38M |
| Tried: `err` vs. orders | +0.31 pt | −$147M | holding +$143M, scrap +$74M, supplier COGS +$185M |

Neither works, because the node loses sight of downstream replenishment needs (why orders differ from end demand). The textbook information-sharing mechanism is echelon inventory control: the node plans for all stock at and below it.

## 2. Goal and success criteria

A control tower should let a node order as if it managed everything downstream of it. With full-network adoption, in calm conditions (no disruptions), against same-seed no-tech baselines (10 seeds):

1. Bullwhip falls at DC, MFG, and CM tiers.
2. Fill rate does not fall meaningfully: the upper bound of the 95% CI of the paired change is ≥ 0.
3. System inventory value (network `costs_holding`) does not rise: the lower bound of the 95% CI of the paired change is ≤ 0.
4. The effect grows with adoption scope: Shanghai chain (5 nodes) < all DCs and stores (12) < all 48.

Profit is reported with a cost breakdown but has no pass bar (tower costs are placeholders). These are acceptance-experiment results reported to Kevin, not test thresholds. If a criterion fails, stop and report; don't tune to pass.

## 3. Design

### 3.1 Scope

- Applies to ordering nodes: DC, MFG, CM. Suppliers don't order. Retail keeps `v = 0` (it has no downstream, so its echelon equals its installation position).
- `v = params["visibility"]` is computed as today (chain share of downstream adopters × (1 + group bonus), capped at 1).
- Non-adopters (`v = 0`) order exactly as today.

### 3.2 Forecasts

- **Installation forecast (all nodes):** `obs = orders_in` always (retail: sales, as today). The `(1 - v) * orders + v * actual` blend is removed. `err` is unchanged in form.
- **Echelon forecast (new, per ordering node and item):** `fc_end[item]` and `err_end[item]`, smoothed with the same `alpha` on `D = actual[n][item]`, where `actual = propagate(net, this week's retail demand)` (already computed in `_forecast_and_order`). Initialized like `forecast`/`err`: mean first-year flow and 0.2 × mean.
- ML forecasting (`forecast_skill` w) applies to both: `blend = (1 - w) * fc + w * exp_next[n][item]`, `sigma = 1.25 * err`. (Revised 2026-09-17: the assumed `(1 - w/2)` cut was removed; `err` and `err_end` are now measured against the blended forecast for the observed week, so sigma falls only as far as the forecast really improves.)
- Early warning (`z_boost`) applies to both order calculations.

### 3.3 Echelon stock

`E(j, x)` = units of `x` at or below node `j` that `j` is responsible for (on hand or in transit), in `x`'s units. True stock values are used for downstream nodes (the tower sees system data); the ordering node's own stock uses its recorded value, as today.

| Node | Item | `E(j, x)` |
|---|---|---|
| Retail `r` | product `p` | `stock_r[p] + transit_in(r, p)` |
| DC `d` | product `p` | `stock_d[p] + transit_in(d, p) + Σ_{r ∈ down(d)} share_r[d] × E(r, p)` |
| MFG `m` | part `k` | `stock_m[k] + transit_in(m, k) + bom[k] × Σ_p ( stock_m[p] + Σ_{d ∈ down(m)} share_d[m] × E(d, p) )` |
| CM `c` | part `k` | `stock_c["RAW:k"] + transit_in(c, k) + stock_c[k] + Σ_{m ∈ down(c)} E(m, k)` |

- `share_b[s]` is `net.source_share[b][s]` (the share of buyer `b`'s orders placed on seller `s`). Each part has one CM, so a CM's share of an MFG's part stock is 1.
- `transit_in(j, x)` is the sum of in-transit shipment units to `j` for `x` (the existing `pipe` dict).
- Nothing is subtracted for backlog owed downstream: those units are still inside the echelon.

**Echelon position:** `IP_E(n, i) = E(n, i) + owed_to_n(i)` (ordered from sources, not yet shipped — the same `owed_to_me` used today).

### 3.4 Echelon lead time

Static, computed once in `init_state` from `lead_weeks` and mean first-year flows (`mean`):

- Retail `r`, `p`: `LE = L(r, p)`
- DC `d`, `p`: `LE = L(d, p) + 1 + Σ_r a_r × LE(r, p)`, with `a_r ∝ share_r[d] × mean[r][p]`, normalized to sum to 1
- MFG `m`, part `k`: `LE = L(m, k) + 1 + Σ_{d,p} b_{d,p} × LE(d, p)`, with `b_{d,p} ∝ share_d[m] × mean[d][p]`, normalized
- CM `c`, part `k`: `LE = L(c, k) + 1 + Σ_m g_m × LE(m, k)`, with `g_m ∝ mean[m][k]`, normalized

The `+ 1` is the node's own one-week review period. Every stage in the echelon keeps one (the installation rule covers `L + 1`), so the echelon horizon `LE + 1` equals the sum of `L + 1` over the node and the stages below it.

Stored as `s.echelon_lead_weeks[(n, item)]`. Disruption extra lead days are ignored here, as they are for `lead_weeks` today.

### 3.5 Order quantity

```
q_inst = order_up_to(fc, sigma, L, z, IP)                       # today's rule, unchanged
H      = LE + 1                                                  # echelon horizon
safety = max(z * sigma_end * sqrt(H), SS_floor(n, item))
q_ech  = max(0, fc_end * H + safety - IP_E)
q      = (1 - v) * q_inst + v * q_ech
```

`SS_floor(n, item)` is the sum of the installation safety stocks at and below `n`, in `n`'s input units, all at `n`'s `z`:

| Node | `SS_floor` |
|---|---|
| Retail `r`, `p` | `z × sigma_r(p) × sqrt(L(r, p) + 1)` |
| DC `d`, `p` | own term + `Σ_{r ∈ down(d)} share_r[d] × SS_floor(r, p)` |
| MFG `m`, part `k` | own term + `bom[k] × Σ_{d ∈ down(m)} Σ_p share_d[m] × SS_floor(d, p)` |
| CM `c`, part `k` | own term + `Σ_{m ∈ down(c)} SS_floor(m, k)` |

"Own term" is `z × sigma × sqrt(L + 1)` with the node's installation `sigma` from `_needs` (so ML forecasting applies). `q_inst` floors at 0 via `order_up_to`; `q_ech` floors at 0 explicitly. `q` is split across sources by `source_share` exactly as today. When `v = 0`, `q_ech` is not computed.

### 3.6 Why the amendment (acceptance run 1)

The first build used `LE` without the per-stage `+ 1` and the pooled safety stock `z × sigma_end × sqrt(LE + 1)` only. Whole-network adoption cut fill by 12.2 pt (stockout +$2.0B); DC_Shanghai's average stock fell from 8,085 to 1,249 units. Two gaps: (1) the echelon target missed one review week per downstream stage, so a tower DC ran about one week short; (2) the pooled echelon safety stock was smaller than the safety stocks the downstream nodes still keep under their own installation rules, so the tower node squeezed its own stock to fund them. A scratch test fixing only (1) brought whole-network fill to −1.2 pt. The floor fixes (2): the echelon never plans for less safety stock than the stages below it actually hold.

## 4. Units and files

| File | Change |
|---|---|
| `sciti/engine/state.py` | `NodeState.fc_end`, `err_end`; `SimState.echelon_lead_weeks`; initialize both in `init_state` |
| `sciti/engine/echelon.py` | `echelon_stock(s, n, item, pipe)` and `echelon_lead_weeks(net, lead_weeks, mean)` |
| `sciti/engine/ops.py` | `obs = orders_in`; update `fc_end`/`err_end`; new `_echelon_signal` and `_echelon_safety_floor`; blend orders by `v` |
| `sciti/tech/catalog.yaml` | No change (effect stays `visibility +1.0`) |
| `tests/test_engine_week.py` (or new `tests/test_echelon.py`) | Tests in §5 |
| `tests/golden/none_seed7_summary.json` | Regenerated (the golden config forces a control tower) |
| Spec 2026-09-12 §5.3, §6; README; STATUS | Describe the new effect |

`echelon_stock` is a pure function of state (no randomness), so replay and paired runs are unaffected.

## 5. Tests (written before the code)

1. **No tower, no change:** with no technology, a 30-week state's orders match the pre-change code exactly; a `none` run's `summary.json` matches the pre-change output for the same seed.
2. **DC echelon stock:** hand-built state; a DC serving two stores, one split 50/50 with another DC, returns the hand-calculated `E`.
3. **MFG echelon stock:** converts DC and own product stock to parts (× BOM units) and applies `share_d[m]`.
4. **CM echelon stock:** includes RAW and finished part stock plus both MFGs' part echelons.
5. **Echelon lead time:** matches a hand calculation for one DC and one MFG.
6. **Blend:** at `v = 0.5` the order equals the mean of the installation and echelon orders; at `v = 1` it equals the echelon order.
7. **Invariants and replay:** a 156-week run with the whole network forcing `control_tower` passes strict checks, and a rules run with a tower replays exactly.

## 6. Acceptance experiment

Paired batches, seeds 1–10, policy `none`, weeks 156, each vs. a same-seed no-tech run:

| Arm | Forced `control_tower` members |
|---|---|
| Shanghai chain | DC_Shanghai, Retail_5, Retail_6, Retail_7, Retail_8 |
| Downstream | All 4 DCs + all 8 stores |
| Whole network | All 48 nodes |

Report per arm: bullwhip by tier, fill rate, satisfaction index, `costs_holding`, profit and cost breakdown, each as mean paired difference ± 95% CI. Compare with the pre-change whole-network numbers in §1.

## 7. Out of scope

- Agent briefs and prompts (the catalog text is unchanged).
- Sharing forecasts or production plans (beyond stock and demand).
- Capacity-aware echelon targets.
- Re-running the full E1 technology screen (a separate step after this lands).
