# Sensitivity Screen — Results

**Date:** 2026-09-17
**Engine:** `main` at `97c76bb` (after the 2026-09-17 audit fixes and freight-in-prices)
**Command:** `.venv/bin/python docs/sciti2/experiments/sensitivity_screen.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/sensitivity_screen_results.csv`

> **Illustrative only.** Every technology's cost and effect is a placeholder (`assumption: true`). This screen asks which placeholders matter, so the evidence search can start with those.

## What we ran

- One technology at a time, switched on in week 1 for every firm allowed to use it (so the +25% group bonus applies).
- Effect size scaled to 0.5×, 1×, and 1.5× of the catalog value.
- Two scenarios: calm, and CM_3 at 20% capacity for 12 weeks from week 30 (as in E2).
- 30 seeds per arm, 3 years, each paired with a same-seed, same-scenario no-tech run.
- Cost was not simulated at other levels. With policy `none`, technology cost is a straight deduction, so the table gives profit at cost ×0.5 and ×2 and the break-even cost multiplier by arithmetic.

## Profit vs no-tech ($M over 3 years)

| Technology | Calm 0.5× | Calm 1× | Calm 1.5× | CM_3 hit 0.5× | CM_3 hit 1× | CM_3 hit 1.5× | Tech cost | Break-even cost (1×, calm / hit) |
|---|---|---|---|---|---|---|---|---|
| Blockchain | +349 | +689 | +1,010 | +340 | +671 | +982 | 10.8 | 65× / 63× |
| Routing | +219 | +444 | +670 | +211 | +430 | +649 | 7.2 | 63× / 61× |
| RFID | +123 | +223 | +308 | +107 | +208 | +305 | 13.8 | 17× / 16× |
| Warehouse robotics | +105 | +199 | +287 | +100 | +194 | +283 | 19.4 | 11× / 11× |
| Control tower | +74 | +108 | +108 | +111 | +132 | +132 | 35.1 | 4× / 5× |
| Risk intelligence | −8 | −8 | −8 | +893 | +1,667 | +1,912 | 8.2 | never / 205× |
| APS | −16 (n.s.) | −22 (n.s.) | −24 (n.s.) | +202 | +345 | +455 | 13.8 | never / 26× |
| ML forecasting | −7 (n.s.) | −12 (n.s.) | −33 (n.s.) | −2 (n.s.) | −37 (n.s.) | −80 | 18.9 | 0.4× / never |

n.s. = the 95% range includes zero.

## Bottom line

1. **Costs almost never matter.** For six of eight technologies the placeholder cost could be 4× to 200× higher before the sign flips. Evidence work should go to effect sizes first, not costs.
2. **Effect size drives the ranking, and nearly in a straight line.** Blockchain, routing, RFID, and robotics gain about in proportion to their effect. Their order (blockchain > routing > RFID ≈ robotics) holds only if the true effects sit in similar parts of their ranges: blockchain at 0.5× falls below routing at 1×. These four effect sizes (defect cut, shipping-cost cut, shrink/record-error cut, handling-cost cut) are the top items for the evidence table.
3. **For risk intelligence and APS, the scenario matters more than any parameter.** Both lose a little in calm and gain a lot in a long CM hit. What needs evidence is how often and how long disruptions happen, plus the recovery effect for risk intelligence (its gain flattens between 1× and 1.5×).
4. **Control tower is insensitive upward.** Visibility is capped at 1, so 1.5× equals 1×. Half visibility keeps about 70% of the gain in calm.
5. **ML forecasting gets worse as its effect grows.** More forecast skill lowers profit and fill in both scenarios (significant at 1.5× in the CM hit). Better forecasts should not hurt, so this looks like a model problem (likely the same safety-stock pattern found in the old control tower rule), not a parameter question. Reproduce and check before spending evidence effort on it.
6. **APS loses more in calm as its capacity gain grows** (not significant). Worth a look alongside ML forecasting.

## Not covered

- Engine assumptions (markups, holding rate, record error, shrink, defect concentration), group bonus, and setup weeks were not varied.
- One technology at a time; no interactions.
- Forced adoption only; agent decisions (rules or LLM) may respond to costs even where network profit does not.
