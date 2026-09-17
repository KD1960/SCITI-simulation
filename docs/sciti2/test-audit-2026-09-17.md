# Test Adequacy Audit — 2026-09-17

**Engine:** `main` at `e49a116` · 185 tests pass · read-only audit (probe scripts kept in the session scratchpad only)

## Verdict: partly

The plumbing is well tested: rationing, order-up-to, BOM assembly, mode choice, prices, demand propagation, echelon stock/lead/safety floor, purchase-timing identity, CO2 weights, conservation/flow checks, exact replay, batch pairing, and the LLM validation/fallback/spend-cap paths all have hand-computed or exact-identity tests.

The part that produces research findings is weakly tested:
- **Technology effects:** for 5 of 8 technologies (ML forecasting, RFID, APS, warehouse robotics, blockchain) no test checks that the effect actually changes operations.
- **Outcome measures:** on-time, quality, satisfaction index, and profit by role have no value tests; bullwhip is checked only for being finite.
- **Costs:** holding, stockout, shrink, inspection/scrap, and handling have no value tests; backlog netting has none.
- Much of the rest is covered only by golden snapshots or "runs clean" tests, which catch change but not wrongness.

## Confirmed defects (probed)

1. **Blockchain does nothing when a CM or factory adopts.** `defect_mult` is read only in the supplier branch of `make_shipment` (`sciti/engine/ops.py:256`). A factory that adopts pays for no effect.
2. **Routing savings go to the customer, not the adopter.** The sender's `ship_cost_mult` applies (`ops.py:265`) but the receiver pays shipping (`ops.py:83`). Network totals are right; profit by tier and the adopter's incentive are not.
3. **Forced coalitions ignore `cost_split`.** `apply_forced` always splits equally (`sciti/engine/adoption.py:80`).
4. **Quality has no randomness** (spec §5.3 step 8 says it should). Defects are `q × defect_share` with no draw; the `quality` stream is unused, so `quality_mean` is a constant 0.98 without tech.
5. **Early warning switches off once the disruption starts** (`sciti/disruptions.py:32`), and a fractional warning (2.5 weeks with the group bonus) has no extra effect.
6. **The summary cost list includes scrap, which profit excludes** (`sciti/metrics.py:66`). Revenue minus summed `costs_*` columns does not equal network profit. Profit itself is correct.

## Suspected (read, not probed)

- On-time rates barely respond to supply problems: upstream shortages never make a shipment late, so the 0.3 weight in the satisfaction index is mostly lane noise.
- "Quality" is the rate of defects escaping CM inspection, not something customers see.
- Factory finished goods are valued at selling price for holding cost (`sciti/engine/economics.py:35`).
- CO2 counts only arrived shipments and excludes supplier→CM lanes.
- RFID's record error is fresh noise each week, which likely understates RFID's value.
- ML forecasting blends toward the demand model's true expectation (`ops.py:200`), so it is partly an oracle.

## Highest-value missing tests

1. Blockchain wiring: supplier+CM pair gives `defective = q × share × 0.6`; factory alone changes nothing (decide intended behaviour).
2. RFID: record-error SD 0.05 × 0.2 = 0.01; weekly shrink = stock × 0.002 × 0.5.
3. Warehouse robotics: handling 0.5 × 0.8 per unit; DC shipment lead −1 day, quote unchanged.
4. APS: CM build = min(capacity × 1.08, raw stock, target) with capacity binding.
5. ML forecast in `_needs`: w = 0.3 → fc = 0.7·F + 0.3·E, sigma = 1.25·err·0.85.
6. Order position in a hand-built state: recorded stock + pipeline + owed-to-me − backlog (factory backlog = max(0, owed − stock) × BOM).
7. Arrival and costs: 100 units, 10 defective, catch 0.8 → 92 into stock, scrap = 8 × unit price; holding = stock × value × 0.25/52; stockout = lost × (retail − DC price + 5).
8. Metrics on a synthetic state: on-time from arrive vs due weeks; satisfaction = 0.5·fill + 0.3·retail on-time + 0.2·quality; bullwhip from given series (weeks 14+, ÷160).
9. Coalitions: chain forms at exactly 60% acceptance and fails just below; `by_size` charges each member its own role cost; forced adoptions follow `cost_split`.
10. Additive group bonus (ML forecast in a group = 0.375), visibility cap at 1, and `extra_lead_days` = 14 moves arrival by 2 weeks.

## Calibration and validation gaps

- `tests/test_calibration.py` compares the engine against its own fitted models; the only real-data check is transit time per mode (±25%, Ship at 0.76).
- No demand holdout test (fit 2020–23, predict 2024).
- No targets for inventory turns, days of stock, on-time rate, or cost shares.
- No stylized-fact checks (bullwhip grows upstream; information sharing cuts bullwhip; losses rise steeply with disruption length) — the properties E1–E5 rely on.
- All technology effect sizes and costs are placeholders; no sensitivity analysis shows which conclusions survive plausible ranges.
- On-time and quality as defined barely move, so satisfaction findings sit near a 0.96 ceiling for structural reasons.

## Consequences for results already reported

- **E4 split incentives:** the routing case is partly an artifact of defect 2 (who books the saving). The blockchain case is partly defect 1 (CM/factory adoption does nothing). The general split-incentive finding still stands for stockout-based technologies, but the routing and blockchain rows need rework.
- **E1 blockchain one-tier arm:** "factories add nothing" is defect 1, not a real-world claim.
- **Satisfaction-index findings (E1–E5):** read with the on-time/quality caveat above.
