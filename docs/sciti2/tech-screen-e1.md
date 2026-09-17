# E1 Technology Screen — Results

> **Engine changed 2026-09-17** (audit fixes: freight paid by the shipper,
> blockchain eligibility, random defects, early warning, and expected freight
> now built into selling prices). Numbers below come from the earlier
> engine; rows for routing and blockchain, and anything that depends on who
> pays freight or on selling prices, should be rerun before citing.

**Date:** 2026-09-15
**Engine:** `main` at `de0e9df` (after the demand fix, per-shipment random draws, purchase timing, part weight, and control tower redesign)
**Command:** `.venv/bin/python docs/sciti2/experiments/tech_screen.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/tech_screen_results.csv`

> **Illustrative only.** Every technology's cost and effect is a placeholder (`assumption: true`). These results show what the model does with those placeholders. They are not estimates of real-world impact.

## What we ran

- Each of the 8 technologies was switched on in week 1 for:
  - **All:** every firm allowed to use it.
  - **One tier:** only the tier where it should matter most (7 technologies; warehouse robotics only fits DCs, so it has one arm).
- 30 seeds per arm, 3 years each, no other technology, no disruptions.
- Each run is compared with the same seed and no technology. Numbers are the average difference, with a 95% range.
- Firms switched on together count as a group, so they get the +25% group bonus.
- No-tech baseline (average): profit $32.4B, fill rate 98.4%, satisfaction 0.962, CO2 3.0 Mt.

## Bottom line

1. **Four technologies pay for themselves in calm conditions, all by cutting costs:** blockchain, routing, RFID, and warehouse robotics.
2. **Information technologies mostly calm the chain, not the bank account.** ML forecasting and control tower cut bullwhip by more than half at component makers. Control tower now makes money when the whole chain joins (+$99M). ML forecasting loses a little (−$43M).
3. **Only warehouse robotics clearly improves what customers feel** (satisfaction +0.010, on-time +2.8 pts). Everything else moves satisfaction by less than 0.003, because service is already near its ceiling.
4. **APS and risk intelligence lose money when nothing goes wrong.** They are insurance. Their value needs the stress test (E2).

## Results: whole-network ("all") arms

Profit and costs in $M over 3 years. Fill rate in percentage points. Bullwhip is the change in the component-maker ratio (baseline 107).

| Technology | Firms | Profit | Tech cost | Satisfaction | Fill rate | CO2 (kt) | Bullwhip at CMs | Where the money comes from |
|---|---|---|---|---|---|---|---|---|
| Blockchain traceability | 36 | **+686** | 13 | +0.0021 | 0.00 | 0 | 0 | Scrap −$1,060M; quality +1.1 pts |
| Routing optimization | 10 | **+439** | 7 | 0 | 0 | **−370** | 0 | Shipping −$447M |
| Item-level RFID | 18 | **+220** | 14 | 0.000 | 0.00 | −15 | −2 (not significant) | Scrap/shrink −$267M |
| Warehouse robotics | 4 | **+154** | 19 | **+0.0103** | +0.36 | +10 | 0 | Stockout −$59M, handling −$0.5M; on-time +2.8 pts |
| Control tower | 48 | +99 | 35 | +0.0005 | +0.08 | 0 | **−78** | Holding −$33M, scrap −$20M, stockout −$13M |
| Risk intelligence | 10 | −8 | 8 | 0 | 0 | 0 | 0 | No effect without disruptions |
| APS (planning) | 6 | −32 | 14 | +0.0008 | +0.16 | +10 | −10 | Stockout −$27M, but holding +$45M, scrap +$28M |
| ML forecasting | 14 | −43 | 19 | 0.000 | −0.01 | −2 | **−63** | Holding −$8M; not enough to cover its cost |

Values in bold have 95% ranges that clearly exclude zero and are large relative to the others.

## Results: one-tier arms

| Technology | Tier | Firms | Profit | Tech cost | What changed vs. "all" |
|---|---|---|---|---|---|
| Blockchain | Suppliers + CMs | 34 | +688 | 11 | Same benefit, less cost: factories add nothing because defects enter at suppliers |
| RFID | Stores | 8 | +86 | 4 | About 40% of the full benefit |
| Control tower | DCs + stores | 12 | +8 (range −10 to +26) | 12 | Half the bullwhip cut, no clear profit; holding cost rises $17M |
| ML forecasting | Stores | 8 | −20 (range −42 to +2) | 8 | Smaller loss, still about 60% of the bullwhip cut |
| APS | Factories | 2 | −26 | 8 | Most of the loss, about 70% of the fill gain |
| Routing | DCs | 4 | +0.3 | 3 | CO2 −96 kt, but DC→store shipping is cheap, so almost no money |
| Risk intelligence | CMs | 4 | −3 | 3 | Pure cost, as expected |

## What this means for the next experiments

- **E2 (stress scenarios) is next.** APS and risk intelligence can only show value under disruptions or demand swings. Service measures also need stress to move off the ceiling.
- **E3 (who with whom):** the control tower gains mostly come from full-chain adoption (+$99M with all 48 firms vs. about +$8M with DCs and stores). Blockchain shows the opposite pattern: joining at one link (suppliers + CMs) captures everything. These make good contrasting cases.
- **Placeholder sizes drive the ranking.** Blockchain's lead comes from a −40% defect effect (−50% with the group bonus) applied to a 10% defect rate taken from sentiment scores. Routing's comes from −8% (−10% with the bonus) on a $4.5B shipping bill. Citing real effect sizes could reorder the list.

## Changes from the September 14 pilot

The pilot (5 seeds, old engine) had ML forecasting at −$358M and control tower at −$199M. Those came from the purchase-timing bug and the old control tower rule, both since fixed. Blockchain, routing, and RFID kept their order and roughly their size.
