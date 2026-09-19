# Risk intelligence: how much rests on "weeks saved", and what the evidence supports

**Date:** 2026-09-19
**Engine and catalog:** `main` at `02ff591` (catalog v2)
**Command:** `.venv/bin/python docs/sciti2/experiments/risk_intel_sensitivity.py OUT_DIR`
**Full numbers:** `docs/sciti2/experiments/risk_intel_sensitivity_results.csv`
**Follows:** `random-disruptions.md`, where risk intelligence became the best-value technology on the weakest evidence.

Quality flags: **PR** peer-reviewed · **IND** industry/analyst survey · **VND** vendor · **ANEC** single case. "[snippet]" = read from an abstract or search snippet only.

## Part 1. Sensitivity (free run)

Random disruptions at the realistic rate (0.2 per site-year), the same 30 schedules as `random-disruptions.md`. Risk intelligence's catalog entry varied; profit is `network_profit_with_inventory`, $M, paired differences.

| Risk intelligence setting | Forced on 10 eligible firms vs no tech | 95% range | Pays in | Fill | Insurance habit (hybrid vs follow) |
|---|---|---|---|---|---|
| 0 weeks saved, 40% warning | +236 | 148–324 | 80% of seeds | +0.46 pt | +223 |
| 1 week saved, 40% warning | **+536** | 374–698 | 90% | +0.93 pt | +499 |
| 2 weeks saved, 40% warning (catalog v2) | +724 | 497–952 | 90% | +1.23 pt | +666 |
| 3 weeks saved, 40% warning | +838 | 578–1,098 | 90% | +1.41 pt | +803 |
| 2 weeks saved, no advance warning | +687 | 476–897 | 90% | +1.16 pt | +674 |

1. **The conclusion is robust to the weakest number.** At one week saved, ten firms still recover +$536M for $8M of spend (74% of the catalog-v2 result, not half). Returns diminish: the first week is worth ~$300M, the second ~$190M, the third ~$115M.
2. **With zero weeks saved it still pays (+$236M).** That is the extra safety stock subscribers hold once a disruption at their site or a direct supplier is known.
3. **Advance warning is worth little (~$37M of $724M).** The share of disruptions that can be foreseen is not a parameter worth more research for this model.
4. The insurance habit tracks the same curve, so the hybrid benchmark's conclusions hold across the range.

## Part 2. Evidence search: does monitoring shorten the outage a firm experiences?

**Main finding: no peer-reviewed study compares time-to-recover for firms with and without risk monitoring.** Everything below is inferred from cases, adjacent studies, and vendor data.

### Recovery time and firm-level levers

| Source | Finding | Flag |
|---|---|---|
| Jain, Girotra & Netessine (2022), *M&SOM* 24(2):846–863, ~1,460 US firm-category import series. https://lbsresearch.london.edu/id/eprint/1525/1/RecoveringFromSourcingInterruptions_MSOM.pdf | Typical recovery to 99% of pre-interruption sourcing takes ~3 months. One SD more long-term supplier relationships: 20% faster recovery. One SD less diversification: 16% faster (diversified firms lean on smaller, slower suppliers). Does not measure monitoring, but is the best evidence that firm-level levers move recovery time *proportionally*, 15–20% per SD. | PR (full text) |
| McKinsey supply chain pulse survey (2022). https://www.mckinsey.com/capabilities/operations/our-insights/taking-the-pulse-of-shifting-supply-chains | Firms with end-to-end visibility dashboards were "twice as likely" to avoid supply chain problems in early 2022. Avoidance, not duration; self-reported. | IND [snippet] |
| McKinsey supply chain risk survey (2025). https://www.mckinsey.com/capabilities/operations/our-insights/supply-chain-risk-survey | 90% have tier-1 visibility; only 58% at tier 2 and beyond. | IND [snippet] |
| Capgemini Research Institute (2020), "Fast forward". https://www.capgemini.com/wp-content/uploads/2020/11/Fast-forward_Report.pdf | 68% took more than 3 months to recover from COVID disruption. No split by visibility. | IND [snippet] |
| Chen (2025), *Transportation Research Part E*. https://www.sciencedirect.com/science/article/abs/pii/S1366554525004697 | Visibility improves resilience; slack strengthens the effect; weak or null for firms with concentrated suppliers. Effect sizes not obtained. | PR [summary only] |
| Todo, Nakajima & Matous (2015), *J. Regional Science* 55(2). https://onlinelibrary.wiley.com/doi/abs/10.1111/jors.12119 | After Tōhoku, diversified supplier networks sped recovery on net. About network structure, not monitoring. | PR [abstract] |
| Bode & Macdonald (2017), *Decision Sciences* 48(5). https://onlinelibrary.wiley.com/doi/10.1111/deci.12245 | Models recognition, diagnosis, development, and implementation speed as drivers of disruption impact. Measures impact, not weeks. | PR [abstract] |

### First-mover cases

| Case | What happened | Flag |
|---|---|---|
| Nokia vs Ericsson, Philips fire, March 2000 (Norrman & Jansson 2004, *IJPDLM* 34(5); Sheffi, *The Resilient Enterprise*). https://husdal.com/2008/10/18/ericsson-versus-nokia-the-now-classic-case-of-supply-chain-disruption/ | Both firms got the same call on day 3. Nokia escalated that day and tied up alternate capacity; Ericsson grasped the seriousness ~2 weeks in and engaged senior management ~3 weeks in, when spare capacity was gone. Ericsson lost ~$400M in sales and later left handset manufacturing. **The 2–3 week gap was assessment and decision, not detection, and the penalty was far larger than 2–3 weeks** because alternate capacity went first-come. | ANEC [secondary] |
| Cisco, Tōhoku 2011 (WDI Publishing case). https://wdi-publishing.com/product/cisco-scrm-in-action-2011-tohoku-earthquake/ | Incident manager alerted within 30 minutes; all direct suppliers, sites, and parts in the zone identified within 12 hours; revenue loss "negligible". | ANEC |
| Intel, Tōhoku 2011 (Sheffi, *The Power of Resilience*). https://supplychaindigital.com/logistics/intel-supply-chain-poised-withstand-global-disasters | Every risk known within the first 10 days. A floor: even a top program needs ~1.5 weeks for the full sub-tier picture. | ANEC [snippet] |
| Toyota RESCUE database. https://global.toyota/en/detail/11373994 | Mapped ~6,800 items after 2011; avoided multi-week halts after Kumamoto 2016. Confounded with added buffers and dual sourcing. | ANEC |
| Renesas Naka fab, 2011 (IEEE Spectrum). https://spectrum.ieee.org/how-japanese-chipmaker-renesas-recovered-from-the-earthquake | Physical recovery cut by ~3 months by up to 2,500 workers a day sent by customers. The largest cut in recovery time came from supplier-side help, not sensing. | ANEC |

### Buyer-side lag vs physical recovery (triangulated; no study splits them)

| Setting | Lag without a program | With a program |
|---|---|---|
| Tier-1 supplier event | ~3 days to be told, plus 2–3 weeks to assess and decide (Ericsson) | same day to 3 days (Nokia) |
| Sub-tier or regional event | ~6 weeks (GM, 2011) | 12 hours for tier 1 (Cisco); ~10 days for the full sub-tier picture (Intel) |

Removable lag is about 1–3 weeks for tier-1 events and 3–5 weeks for sub-tier events, never zero. Physical recovery for serious events runs 6–12 weeks. So lag is about 15–35% of a serious outage and can exceed 50% of a short one.

### Evidence against monitoring alone

- Nokia and Ericsson had identical information; the difference was authority to act and available alternates (Ericsson had single-sourced on purpose).
- Chen (2025): visibility's benefit depends on slack and is weak or null with concentrated suppliers.
- Jain et al. (2022): diversification alone slows recovery; an alternate helps only when it is a long-term, qualified relationship.
- Toyota's result cannot be separated from its buffers and dual sourcing.
- No peer-reviewed study, for or against, tests whether subscribing to Resilinc, Everstream, or Interos is associated with shorter disruptions.

### Advance warning

| Source | Finding | Flag |
|---|---|---|
| DHL Resilience360 Annual Risk Report 2019. https://www.globenewswire.com/news-release/2020/02/27/1991997/0/en/Resilience360-Annual-Risk-Report-Reveals-Impacts-of-2019-Supply-Chain-Disruptions-and-Predicts-2020-Supply-Chain-Risks.html | High-impact incidents: industrial fires 27%, earthquakes 23%, theft 18%: at least 68% with no warning. | VND |
| Resilinc EventWatch 2021 and 2024. https://resilinc.ai/press-release/global-supply-chains-see-nearly-40-annual-increase-in-disruptions/ | Factory fires the top category six years running (10–17% of alerts); ~60% of alerts trigger a "WarRoom"; foreseeable categories (M&A, leadership change) rarely cause outages. No precision or false-alarm figures published. | VND |
| Everstream Analytics. https://www.everstream.ai/solutions/weather-intelligence-and-analytics/ | 14+ day forecasts; one case with 8 days' lead before Hurricane Ian. | VND |

## Part 3. Recommendation

**Weeks of experienced outage saved by monitoring** (for a firm with some alternate or buffer to act on; with none, use LOW):

| Underlying outage | LOW | MID | HIGH |
|---|---|---|---|
| 4 weeks | 0 | 1 | 2 |
| 8 weeks | 0.5 | 2 | 3.5 |
| 12 weeks | 1 | 2.5 | 5 |

- Catalog v2's fixed 2 weeks is a defensible MID for 8–12 week outages and **too generous for short ones**: it turns a 3-week outage into 1 week.
- Best-supported form: **saved = min(L, p × outage)** with L ≈ 2 weeks and p ≈ 0.25–0.30. The mechanism (lag removal) is a fixed time, the only peer-reviewed effect sizes are proportional (16–20%), and this form reproduces the table. It makes the 1-week floor unnecessary.
- **Advance warning:** probability LOW 15% / MID 30% / HIGH 45%; catalog v2's 40% is at the upper end. Lead time 2 weeks is a reasonable MID. Part 1 shows this barely matters.
- **Confidence: low to moderate.** Direction and a 1–3 week lag are well supported by consistent cases; magnitudes rest on about five famous cases chosen because they were dramatic, plus vendor data.
- **The study that would settle it:** an event study on shipment-level customs data (as in Jain et al.) comparing recovery curves of buyers exposed to the same supplier event, split by whether they subscribed to a monitoring service at the time, controlling for inventory and dual sourcing.

## What this means for SCITI

1. Risk intelligence's top ranking under realistic disruptions survives the whole defensible range (+$236M to +$838M for $8M).
2. Switching to min(2, 0.25 × outage) would cut the saving on 1–7 week outages (most events) and leave 8+ week outages unchanged. Since short outages mostly sit inside the buffer, expect a result between the 1-week and 2-week rows (+$536M to +$724M). **Kevin approved the change on 2026-09-19;** the rerun gave +$564M (see `random-disruptions.md`, Rerun section).
3. The evidence says monitoring pays only when there is something to act on. In the model, the benefit is unconditional. A later refinement could tie it to the subscriber's safety stock or to a second source.
4. First-mover scarcity (Nokia/Ericsson) is not modelled: every subscriber gets the same saving however many share the disrupted supplier. This biases the model *against* risk intelligence in shared-supplier events.
