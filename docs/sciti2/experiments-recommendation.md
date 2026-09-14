# SCITI 1 — Recommended Initial Experiments

**For:** Kevin Dooley
**Date:** 2026-09-14 (thread "SCITI sim 2")
**Basis:** README, STATUS, design spec, and a pilot I ran today on the `sciti-mvp` branch (no code changed, no API calls, outputs kept in the session scratchpad only).

---

## 1. Bottom line

Run experiments in this order:

1. **E0 — Make the comparisons trustworthy** (fix lane noise, fix the Mumbai/Tokyo demand bug, check three odd results). Small job, and everything later depends on it.
2. **E1 — One-technology screen** at 30 seeds. Gives a clean effect table for each technology.
3. **E2 — Stress scenarios.** The baseline chain is almost too healthy to improve, so service effects need disruptions and demand shocks to show up.
4. **E3 — "Who with whom."** The core research question: same technology, same number of adopters, different group structures.
5. **E4 — Agent decision rules** (rules policy sweeps), then **E5 — a small paid LLM pilot** with your approval.

Do not present any result as a real-world estimate until the technology costs and effects are replaced with cited values (they are all `assumption: true` today).

## 2. What the pilot showed

### 2.1 Agents using the payback rule vs. no technology (10 seeds, paired)

| Measure | No-tech baseline | Rules policy | Paired difference (mean ± SD) |
|---|---|---|---|
| Adoptions / coalitions | 0 / 0 | 52.2 / 3.8 | — |
| Network profit (3 yrs) | $31.39B | $31.32B | −$67M ± $220M |
| Satisfaction index | 0.9627 | 0.9626 | −0.0001 ± 0.0019 |
| Fill rate | 0.986 | 0.986 | +0.0003 ± 0.003 |
| Bullwhip, DC / MFG / CM | 8.9 / 25.4 / 104.7 | 5.8 / 13.5 / 48.5 | large drops at every tier |

Three lessons:

- **The pairing is not doing its job.** The SD of the paired profit difference ($220M) is *bigger* than the seed-to-seed SD of the baseline alone ($162M). Pairing should shrink it a lot. This is the lane-noise problem already noted in the README: lead-time and mode draws fall out of step once one run ships differently. With this noise, a $67M effect needs roughly 80+ seeds to detect.
- **There is a ceiling.** Baseline fill rate is 98.6% and the satisfaction index is 0.963. Technology has almost no room to raise service in calm conditions.
- **Agents cut bullwhip a lot but do not make money from it.** That may be real (tech cost outweighs savings with the placeholder numbers) or a model effect worth checking (see E0).

### 2.2 One technology forced on every eligible firm in week 1 (5 seeds, vs. same-seed baseline)

| Technology | Firms | Profit change (± SE) | Satisfaction change | What moved |
|---|---|---|---|---|
| Routing optimization | 10 | **+$403M** (± $1M) | 0 | Shipping −$410M; CO2 about −13% |
| Blockchain traceability | 36 | **+$571M** (± $55M) | +0.0017 | Scrap −$966M; quality +1.0 pt |
| RFID | 18 | +$80M (± $76M) | −0.0013 | Scrap −$248M |
| Warehouse robotics | 4 | +$53M (± $64M) | **+0.0093** (largest) | On-time +0.7 pt |
| APS | 6 | +$8M (± $79M) | +0.0006 | Small |
| Risk intelligence | 10 | −$8M (its cost) | 0 | Nothing — no disruption to respond to |
| Control tower | 48 | **−$199M** (± $100M) | −0.0026 | CM bullwhip 105 → 3; fill −0.4 pt; stockout cost +$59M |
| ML forecasting | 14 | **−$358M** (± $109M) | 0 | CM bullwhip −69; tech cost only $19M |

### 2.3 Risk intelligence under a disruption (5 seeds)

A made-up shock: CM_Mexico (CM_3) at 20% capacity with +10 days delay for 8 weeks from week 30.

- The disruption alone costs **−$410M** and **−1.1 pts** of fill rate.
- Risk intelligence on the 10 eligible firms wins back **+$400M** and **+1.2 pts** of fill. That is almost the whole loss, for $8M.

## 3. Three results to check before trusting anything

These are not proven bugs. They are results that look too strong or point the wrong way. Reproduce each one with a small test first, as the project rules say.

1. **ML forecasting and control tower lower profit while cutting bullwhip.** The lost profit ($358M) is about 19 times the tech cost. Better information should not usually make a chain worse. Trace one seed week by week: is lower upstream stock starving factories, or is the order-up-to target reacting badly to a smoother signal?
2. **Risk intelligence recovers nearly 100% of a disruption.** A 2-week early warning plus 40% faster recovery may be too generous, or pre-building may not be limited by capacity.
3. **CO2 is about 207 million tonnes over three years** for a chain selling about 1.3 million products a year (2024 store demand). That is roughly 50 tonnes of CO2 per product sold, which looks far too high. The data report covers the workbook's CO2 formula; check the units in the engine too.

## 4. Recommended experiments

### E0 — Make the comparisons trustworthy (do first)

- **Change:** give each shipment its own random draws (for example, seeded from lane + ship week + order index) so a tech run and its baseline see the same lead times and modes. This was the final reviewer's first research recommendation.
- **Check:** rerun the 10-seed rules batch. Success = paired profit SD falls well below the $162M baseline SD (aim for under a third of it).
- **Fix demand data:** the workbook has formula bugs for Mumbai (Retailer 5) and Tokyo (Retailer 7). The model uses the buggy series today (Mumbai A = B = C; Tokyo Product A shrinks 7% a year). Correct them in `sciti prepare` (see the data corrections report, §2.4), rebuild `baseline.json`, and rerun the golden and calibration tests. The pilot numbers above will shift a little.
- **Also:** the three checks in §3. Record each answer in STATUS.md.
- **Then:** pick the seed count. Use the new paired SD to size batches (for example, n ≈ (2.8 × SD / smallest effect you care about)²).

### E1 — One-technology screen (30 seeds each)

- **Design:** for each of the 8 technologies, force adoption on all eligible firms in week 1, policy `none`, paired with baseline. Add a second arm per technology that adopts at only one tier (for example, stores only for ML forecasting) to see where the effect lives.
- **Outputs:** an "effect ledger" table: profit, cost by type, satisfaction, fill, on-time, quality, CO2, bullwhip, with 95% CIs on paired differences.
- **Cost:** 16 arms × 30 seeds × 2 runs ≈ 1,000 runs ≈ 25 minutes. No API spend.
- **Use:** sanity check the placeholder parameters, and a teaching slide on "which tech pays for itself, and why."

### E2 — Stress scenarios (create room to improve)

- **Factors:** demand growth (`demand.growth_mult` 0.5 / 1 / 1.5); disruption site (none / CM_3 elastomers, 80 of 160 parts / CM_4 glass, 38-day sea lane / DC_Shanghai, biggest DC); disruption length (4 / 12 weeks).
- **Crossed with:** no tech, risk intelligence, control tower, APS, and the rules policy.
- **Question:** which technologies are insurance (pay only under stress) and which pay every week?
- **Cost:** about 3 × 7 × 5 arms × 30 seeds ≈ 6,300 runs ≈ 2.5 hours. Start with a half-fraction if you want it faster.

### E3 — Who with whom (the core research question)

Hold the technology and the number of adopting firms fixed; change the structure.

| Arm | Control tower adopters (example: 5 firms) |
|---|---|
| Scattered | 5 firms from different tiers and regions, not linked |
| Dyads | Linked pairs (e.g., DC + its store) |
| One chain | DC_Shanghai + its 4 stores (the classroom preset) |
| Upstream chain | MFG_China + 4 CMs |
| Whole network | All 48 (reference arm) |

Repeat for blockchain (a `pair` technology) using supplier–CM pairs vs. scattered suppliers.

- **Question:** does the same spend create more value when it is concentrated along a chain? Where in the chain should the first adopters sit?
- **Tie-in:** this is the experiment that makes SCITI different from a normal inventory simulator.

### E4 — How agents decide (rules policy)

- **Factors:** budget share range, planning horizon, `chain_accept_share` (0.4 / 0.6 / 0.8), `cost_split` (equal / by size), `visibility` (partners / network), `max_new_adoptions_per_quarter` (1 / 2).
- **Outputs:** adoption curves over time, coalition count and type, profit and satisfaction.
- **Question:** which rules of the game produce diffusion that looks like real adoption? (A good future link to the Observatory's Disclosed Adoption Index.)
- **Design:** a fractional factorial or Latin hypercube, 30 seeds per point.

### E5 — First LLM pilot (needs your approval)

- **Steps:** set current model prices in `configs/mvp_llm.yaml`; run `sciti estimate`; approve the spend; run 1 seed at 156 weeks; run `sciti replay` and confirm `replication: exact` (this also closes spec success criterion 3).
- **Compare:** LLM vs. rules on the same seed — who adopts, when, how many coalitions, and read the reasons.
- **Only after that:** 5 seeds, and a small prompt test (persona wording) before any larger batch.

## 5. Ground rules for every experiment

- One config file per arm, committed; one `results.csv` per batch; note the git commit and catalog hash.
- Report paired differences with 95% confidence intervals, not single runs.
- Decide the main measures before running (suggest: network profit, satisfaction index, fill rate, CO2).
- Keep the "illustrative parameters" label on every chart until the catalog has cited values.
- Ask before any paid LLM run (standing rule).

## 6. Suggested first two weeks

| Days | Task |
|---|---|
| 1–3 | E0 lane-draw fix (test first), rerun paired variance check |
| 4–6 | The three checks in §3 |
| 7–8 | E1 screen at 30 seeds; effect ledger |
| 9–10 | E2 half-fraction; pick the scenarios worth a full run |
