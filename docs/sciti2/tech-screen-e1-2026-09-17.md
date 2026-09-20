# E1 Technology Screen — Rerun on the corrected engine

> **Status (2026-09-20):** catalog v1 placeholders, every adoption succeeding. Current numbers: `multi-party-combination-proposal.md` §6 and `implementation-risk-results.md`; catalog v2 "works" case: `catalog-v2-results.md`.

**Date:** 2026-09-17
**Engine:** `main` at `14b0a08` (after the audit fixes, freight in prices, the ML forecasting sigma fix, and inventory-adjusted profit)
**Command:** `.venv/bin/python docs/sciti2/experiments/tech_screen.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/tech_screen_results_2026-09-17.csv`
**Replaces:** `tech-screen-e1.md` (2026-09-15, old engine)

> **Illustrative only.** Every technology's cost and effect is a placeholder (`assumption: true`). These results show what the model does with those placeholders. They are not estimates of real-world impact.

## What we ran

Same design as the 2026-09-15 screen: each technology switched on in week 1 for every eligible firm ("all") and, where it makes sense, for one tier; 30 paired seeds, 3 years, calm conditions, no other technology. Firms switched on together form a group and get the +25% bonus.

New in this rerun: **profit with inventory** (`network_profit_with_inventory`) values opening and closing stock on one network-wide cost basis (supplier cost plus freight paid), so a technology that shifts stock between firms or across the horizon is not mis-scored. Use it for comparisons; cash-basis profit is shown for reference.

No-tech baseline (average): cash profit $42.1B, profit with inventory $41.4B, fill rate 98.4%, satisfaction 0.961, CO2 3.0 Mt, CM bullwhip 107.

## Results: whole-network ("all") arms

$M over 3 years. Fill rate in percentage points. (ns) = 95% range includes zero.

| Technology | Firms | Profit with inventory | Cash profit | Tech cost | Satisfaction | Fill rate | CO2 (kt) | CM bullwhip | Where the money comes from |
|---|---|---|---|---|---|---|---|---|---|
| Blockchain traceability | 34 | **+706** | +689 | 11 | +0.0021 | 0.00 | 0 | 0 | Scrap −$1,055M; quality +1.1 pts |
| Routing optimization | 10 | **+444** | +444 | 7 | 0 | 0 | **−370** | 0 | Shipping −$452M |
| Warehouse robotics | 4 | **+198** | +199 | 19 | **+0.0103** | +0.36 | +10 | 0 | Stockout −$69M; on-time +2.85 pts |
| Item-level RFID | 18 | **+185** | +223 | 14 | 0 | 0 | −15 | 0 | Scrap/shrink −$302M; shipping −$30M |
| Control tower | 48 | **+65** | +108 | 35 | +0.0005 | +0.08 | 0 | **−78** | Holding −$31M, scrap −$19M, stockout −$16M |
| APS (planning) | 6 | +20 (ns) | −22 (ns) | 14 | +0.0008 | +0.16 | +10 | −11 | Stockout −$31M, but holding +$55M, scrap +$31M |
| Risk intelligence | 10 | −8 | −8 | 8 | 0 | 0 | 0 | 0 | No effect without disruptions |
| ML forecasting | 14 | **−35** | −53 | 19 | 0 | 0.00 | 0 | **−64** | Stockout −$27M; holding +$11M; not enough to cover its cost |

## Results: one-tier arms

| Technology | Tier | Firms | Profit with inventory | Tech cost | What changed vs. "all" |
|---|---|---|---|---|---|
| RFID | Stores | 8 | +56 | 4 | About 30% of the full benefit |
| Control tower | DCs + stores | 12 | +23 | 12 | Half the bullwhip cut, a third of the profit; now clearly positive (was ns) |
| APS | Factories | 2 | +22 | 8 | All of the gain, about 70% of the fill gain |
| Routing | DCs | 4 | 0 | 3 | CO2 −96 kt, but DC→store shipping is cheap |
| Risk intelligence | CMs | 4 | −3 | 3 | Pure cost, as expected |
| ML forecasting | Stores | 8 | −35 | 8 | Same loss with less cost: stores' own holding rises |

Blockchain has no one-tier arm any more: after the audit fix it is eligible for suppliers and CMs only, so "all" is that arm (34 firms).

## What changed since 2026-09-15

1. **The ranking held.** Blockchain > routing > robotics ≈ RFID > control tower > APS ≈ risk intel > ML forecasting. Routing is unchanged; blockchain, robotics, and RFID are within noise of the old numbers.
2. **Profit with inventory moves four results.** Control tower's gain falls from +$108M cash to +$65M (it builds stock upstream, where cash profit over-credited it). RFID falls from +$223M to +$185M. APS flips from −$22M to +$20M (it ends with more stock, which cash profit ignored); both APS figures are within noise. ML forecasting improves from −$53M to −$35M.
3. **ML forecasting is still a net loss at the placeholder effect size**, but a smaller one: it now cuts stockouts (−$27M) without hurting fill, and the sensitivity screen shows the loss is about the tech cost plus $15M. Its bullwhip cut (−64 at CMs) is real but earns nothing under these placeholders.
4. **Control tower at DCs + stores is now clearly positive** (+$23M; it was +$8M and not significant).

## Placeholders drive this

Per the same-day sensitivity screen, the four money-makers gain roughly in proportion to their effect size, and costs almost never change the sign. The evidence table should start with: blockchain's defect cut, routing's shipping-cost cut, RFID's shrink/record-error cut, and robotics' handling and dispatch effects.
