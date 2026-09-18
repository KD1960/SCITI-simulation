# E4 How Agents Decide — Results

> **Engine changed 2026-09-17** (audit fixes: freight paid by the shipper,
> blockchain eligibility, random defects, early warning, and expected freight
> now built into selling prices). Numbers below come from the earlier
> engine; rows for routing and blockchain, and anything that depends on who
> pays freight or on selling prices, should be rerun before citing.
> **Rerun 2026-09-18:** see `e2-e4-rerun-v2.md`; use that one.

**Date:** 2026-09-15
**Engine:** `main` at `5b3687b`
**Command:** `.venv/bin/python docs/sciti2/experiments/decision_rules.py OUT_DIR` (1,980 runs)
**Full numbers:** `docs/sciti2/experiments/decision_rules_main_effects.csv` (factor effects) and `decision_rules_points.csv` (each combination)

> **Illustrative only.** Technology costs and effects are placeholders, and so are the payback rule's own beliefs about savings.

## The question

When firms decide for themselves with the payback rule, which rules of the game change what they adopt, who they team up with, and how much the network gains?

## What we ran

Every combination of high and low levels for the five settings the payback rule uses (32 combinations), plus today's defaults. Two conditions: calm, and a 12-week hit at Mexico (CM_3). 30 seeds each, each compared with the same seed and no technology.

| Setting | Low | High | Default |
|---|---|---|---|
| **Budget:** share of revenue a firm may spend on tech | 1–4% | 5–20% | 2–10% |
| **Planning horizon:** longest payback a firm accepts | 13–52 weeks | 52–156 weeks | 26–104 weeks |
| **Group acceptance:** share of invited partners who must say yes | 40% | 80% | 60% |
| **Cost split** in a group | equal | by firm size | equal |
| **New technologies** a firm may take per quarter | 1 | 2 | 1 |

(The "visibility" setting was left out: the payback rule doesn't use it.)

## Bottom line

1. **Agents always gain, but capture only a small part of what's possible.** Across all settings, the network gains +$145M to +$348M. For comparison, in E1 the four cost-cutting technologies made about +$1.5B when every eligible firm adopted them.
2. **Two settings matter most: how many technologies a firm may take per quarter, and how long a payback it accepts.**
   - Allowing 2 per quarter: **+$81M** calm, **+$105M** in the disruption. Firms also adopt about 11 weeks sooner.
   - A long planning horizon: **+$65M** calm, **+$70M** in the disruption. Firms adopt about 15 more technologies.
3. **Budget doesn't matter at all.** Results are identical at 1–4% and 5–20% of revenue. Even the smallest budget (a supplier's, about $257k) is bigger than any one-time cost that firm could face. The placeholder tech costs are tiny next to these firms' revenue.
4. **Stricter group acceptance usually hurts, but helps in the best settings.** Requiring 80% of partners to agree causes about 52 more failed groups and 10 fewer control tower adoptions, and costs $14–23M on average. In the best combination, though (long horizon, 2 per quarter, cost split by size), strict acceptance gains $11–19M more than lenient acceptance. It filters out weak chains.
5. **Splitting group costs by size helps a little** (+$19M calm; about +2 adoptions).
6. **No setting makes agents buy the technologies that matter most for customers or for disruptions.** In all 1,980 runs, agents never adopted risk intelligence, APS, or warehouse robotics.

## Settings' effects

Effect of moving each setting from low to high, averaged over the other settings. Profit in $M over 3 years. * = the 95% range excludes zero.

| Setting (low → high) | Profit, calm | Profit, 12-week hit | Adoptions per run | Failed groups | Mean adoption week |
|---|---|---|---|---|---|
| New tech per quarter (1 → 2) | **+81*** | **+105*** | +8.4* | 0 | **−11.4*** |
| Planning horizon (short → long) | **+65*** | **+70*** | **+15.4*** | +13* | +1.5* |
| Cost split (equal → by size) | +19* | +14 | +2.1* | 0 | 0 |
| Group acceptance (40% → 80%) | −14* | −23* | **−10.6*** | **+52*** | 0 |
| Budget (1–4% → 5–20%) | 0 | 0 | 0 | 0 | 0 |

## Best and worst combinations

| Combination | Profit, calm | Profit, 12-week hit | Adoptions | Control tower | Blockchain | Routing |
|---|---|---|---|---|---|---|
| **Best:** long horizon, 80% acceptance, split by size, 2 per quarter | **+335** | **+348** | 61 | 16 | 9.9 | 3.6 |
| Same, but 40% acceptance | +316 | +337 | 68 | 23 | 9.4 | 3.7 |
| Today's defaults | +190 | +180 | 53 | 14 | 6.7 | 2.8 |
| **Worst:** short horizon, 80% acceptance, equal split, 1 per quarter | +160 | +145 | 36 | 0 | 6.3 | 2.0 |

The worst combination forms no control tower groups at all: short paybacks plus strict acceptance kill every chain proposal.

## Why agents skip the most valuable technologies

The payback rule counts only savings on the **adopting firm's own** costs. But in the model many costs sit with someone else:

| Technology | Who can adopt | Where its benefit lands | What the rule sees |
|---|---|---|---|
| **Routing** (cuts shipping cost) | Sellers: CMs, factories, DCs | Shipping is charged to the **buyer** | Only the seller's own inbound shipping, so little saving. Adopted by 2–4 of 10 firms, yet worth +$439M network-wide in E1 |
| **Blockchain** (fewer defects) | Suppliers, CMs, factories | Defect scrap is charged to the **receiving CM** | Suppliers see little saving. Adopted by 5–10 of 36 firms, yet worth +$686M in E1 |
| **Risk intelligence, APS** (fewer stockouts) | CMs, factories, DCs | Only **stores** record stockout costs | Zero saving. Never adopted |
| **Warehouse robotics** | DCs | Mostly faster dispatch and fewer store stockouts | Only a small handling saving. Never adopted |

This is a classic **split-incentive** problem: the firm that pays for the technology is not the firm that saves. No budget, horizon, or group rule fixes it, because the rule never sees the partner's savings.

## What this means

- **For research:** "who with whom" depends as much on *who captures the benefit* as on the rules for forming groups. A natural follow-up is to test decision rules that see partners' savings (shared-savings contracts), or that value insurance against disruptions.
- **For the LLM pilot (E5):** the key question is now concrete. Do LLM agents, reading the same brief, recognize split incentives (for example, propose routing or blockchain deals that pay the partner) or buy insurance? The payback rule gives a clear baseline: +$190M with today's defaults, never buys insurance.
- **For calibration:** tech costs are so small next to firm revenue that budgets never bind. Real cost figures should be checked against firm size when the catalog is updated.
- **For teaching:** the split-incentive table is a ready-made discussion case.

## Settings

- Seeds 1–30; 156 weeks; normal demand growth; no forced adoption.
- Disruption: CM_3, weeks 30–41, 20% output, +14 days.
- Effects are seed-paired differences between the 16 combinations at the high level and the 16 at the low level. 95% ranges use t = 2.045.
