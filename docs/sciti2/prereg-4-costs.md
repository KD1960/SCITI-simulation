# Guesses page 4: evidence-based technology costs

**Status:** SIGNED by Kevin 2026-09-24 ("table is fine, yes on all 6, build"). Built the same day on branch `page4-costs` (239 tests; tech golden regenerated for the new costs); scored in `prereg-4-results.md` (G1–G4 right, G5–G6 wrong); tag `v1.3`.

## 0. Why

Costs are the last `placeholder` in the catalog (STATUS §0, open data question 4). Page 3 showed the failure split bites only through costs, and the sensitivity screen found costs change the answer only for control tower, APS and ML forecasting. The evidence table (§2.x "Costs", 22 logged cost sources, all vendor or analyst) already gives ranges by firm size; this page turns them into catalog values and tests what moves.

**Firm sizes in the model** (yearly revenue, seed 1, no tech): suppliers $106–579M (median $229M); CMs $1.1–7.4B; factories $5.9–8.4B; DCs $1.2–6.6B; stores $0.5–4.6B (a "store" is a whole retail region). So every non-supplier is an enterprise buyer and suppliers are mid-market. Today's placeholder costs are 0.01–0.1% of yearly revenue; the evidence puts enterprise programmes in the same band. **Expect little to move.** The value of this page is closing the caveat, not changing results.

## 1. Proposed catalog v3 costs (one-time / per week)

| Tech | Role | Placeholder | Proposed | Evidence-table line |
|---|---|---|---|---|
| Control tower | MFG | 1.2M / 12k | 1.5M / 15k | large platform $0.5–2M/yr, implementation 1–3× |
| | DC, CM | 700k / 7k; 500k / 5k | 500k / 6k | mid-large SaaS $200–500k/yr |
| | Retail | 250k / 2.5k | 300k / 4k | same |
| | Supplier | 150k / 1.5k | **25k / 0.3k** | joining a partner's tower: onboarding $5–25k, small user seat |
| APS | MFG | 1.5M / 15k | 1.5M / 10k | enterprise multi-plant, six to seven figures; maintenance ~20% |
| | CM | 600k / 6k | 300k / 3k | mid-market licence $50–200k + services $30–100k |
| ML forecasting | MFG | 900k / 9k | 450k / 7k | enterprise licence $200–500k/yr, implementation 0.75–1.25× |
| | DC | 600k / 6k | 300k / 4k | same |
| | Retail | 400k / 4k | 300k / 3k | same |
| Risk intelligence | MFG | 500k / 5k | 100k / 5k | subscription $50–260k/yr; little one-time |
| | CM, DC | 250k / 2.5k; 300k / 3k | 50k / 2k | same |
| Routing, RFID, robotics, blockchain | all | unchanged | unchanged | placeholders already sit inside the ranges (table §2.2–2.4, 2.1) |

Rule used: MID of the enterprise range for MFG/DC/Retail/CM, small-firm range for suppliers; per-week = yearly ÷ 52. Kevin edits any cell. Every value cites its evidence-table line in the catalog `evidence` field; the catalog header drops "costs are still placeholders" for the four technologies above.

## 2. Design (free)

Rerun the calm screen, random disruptions (rate 0.2) and the E4 default point on seeds 1–30; compare with `*_current.csv` (v1.2). Plus one stress arm: **all costs ×10**, calm screen only, to find which technologies stop paying.

## 3. Guesses

**G1.** The calm ranking (routing > robotics > RFID ≈ blockchain ≈ control tower > APS > ML > risk intel) is unchanged. Counts as yes: same order, ties allowed inside overlapping intervals.
**G2.** Control tower, all firms, calm: +$35M → +$40–55M (cheaper supplier seats). Counts as yes: inside range.
**G3.** Risk intelligence calm: −$7M → −$2 to −$5M; at rate 0.2 within ±$20M of +$380M. Counts as yes: both.
**G4.** The hybrid's share of the disruption loss recovered stays 34–40%. Counts as yes: inside band.
**G5.** At costs ×10, control tower, APS, ML forecasting and risk intelligence go negative in calm; routing, robotics, RFID and blockchain stay positive. Counts as yes: all eight as stated.
**G6.** Rule agents at the E4 default form more groups than before (control tower chains are cheaper for the 30 suppliers who must accept them): 0.13 → 0.5–2 per run in calm. Counts as yes: inside range.

## 4. Not allowed

No cost tuned after seeing results; a cost Kevin wants to revisit gets a new page.

Kevin's edits to §1: none · Guesses: agrees with all six · Signed (Kevin), date: 2026-09-24
