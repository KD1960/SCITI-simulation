# Implementation failure rates — evidence by technology

**Date:** 2026-09-19
**Purpose:** in SCITI every adoption succeeds. Kevin asked for technology-specific data on how often implementations fail, so failure can be modelled.
**Method:** two research helpers (four technologies each), asked for outright-failure, partial-success, firm-size, multi-party, time-to-failure, and sunk-cost evidence, and to trace the widely repeated numbers to their origins. Many items were read from abstracts or search snippets ([S]); several publisher and consultancy pages blocked fetching. **Nothing in the engine or catalog has been changed.**

Quality flags: **PR** peer-reviewed · **IND** industry/analyst survey · **VND** vendor · **ANEC** single case.

## 1. Summary

Probabilities are per adoption attempt, resolved within about three years. "Benefit fraction" is the share of the planned effect a partial success delivers. MID values; ranges in section 3.

| Technology | P(fail) | P(partial) | Benefit fraction if partial | P(full) | Sunk share on failure | When failures happen | Confidence |
|---|---|---|---|---|---|---|---|
| Blockchain traceability | **0.65** (0.50–0.85) | 0.25 | 0.30–0.50 | 0.10 | 0.9–1.0 | pilots 6–18 months; consortia 4–5.5 years, all members at once | Medium (measured) |
| ML demand forecasting | **0.45** (0.30–0.60) | 0.35 | 0.5 | 0.20 | 0.25–0.4 at pilot; ~1.0 after go-live | 6–12 months (pilot gate) | Medium at the pilot gate |
| Risk intelligence service | 0.30 (0.15–0.45) | 0.45 | 0.35 | 0.25 | low (fees paid) | renewals at 12/24/36 months | Low (all proxies) |
| Control tower / visibility | 0.25 (0.15–0.40) | 0.50 | 0.4 | 0.25 | integration + 1–2 years of fees | 12–24 months | Low |
| Item-level RFID (voluntary) | 0.20 (0.10–0.35) | 0.40 | 0.5–0.7 | 0.40 | 0.7–0.85 | 12–24 months | Low–medium |
| APS | 0.15 (0.05–0.25) | 0.50 | 0.45 | 0.35 | 0.7–1.0 | 12–30 months | Medium (several surveys converge) |
| Warehouse robotics (fixed) | 0.15 (0.08–0.30) | 0.55 | 0.5–0.7 | 0.30 | 0.7–0.9 | 2–4.5 years *after* go-live | Low–medium |
| Routing / TMS | 0.15 (0.08–0.25) | 0.50 | 0.5–0.7 | 0.35 | 0.3–0.5 | 12–36 months (renewal) | Low (borrowed) |

**Headlines**

1. **Only blockchain has measured failure data, and it is bad:** 5–14% of enterprise blockchain projects reach production; 3% run at scale. Every large shared platform died within 4–5.5 years.
2. **For the mature technologies, partial success is the normal outcome,** not failure: about half of adopters get roughly half the planned benefit. Full success is a minority (25–40%).
3. **ML forecasting fails mostly at the pilot gate** (~46% of AI pilots never reach production), and the ones that go live are eroded by planners overriding the forecasts.
4. **Multi-party technologies carry a second, correlated risk:** when a consortium or mandate collapses, every member loses at once.
5. **Firm-size evidence is thin.** Direction (small and low-maturity firms fail more) is supported; magnitudes are judgment.

## 2. General anchors (and what not to cite)

| Source | Finding | Flag |
|---|---|---|
| Standish Group CHAOS 2020; CHAOS 2015 by project size. https://opencommons.org/CHAOS_Report_on_IT_Project_Outcomes | 31% success / 50% challenged / 19% failed. By project size: small 61/32/7 … grand 6/51/43. Criticised as biased and non-replicable (Eveleens & Verhoef, *IEEE Software* 2010): use the shape, not the levels. | IND |
| Flyvbjerg & Budzier (2011), *HBR* 89(9), 1,471 IT projects. https://hbr.org/2011/09/why-your-it-project-may-be-riskier-than-you-think | Mean cost overrun 27%; 1 in 6 is a "black swan" with ~+200% cost and ~+70% schedule. Overruns are fat-tailed. | PR-adjacent |
| Bloch, Blumberg & Laartz (McKinsey–Oxford, 2012), 5,400+ projects over $15M. https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/delivering-large-scale-it-projects-on-time-on-budget-and-on-value | 45% over budget, 7% over time, **56% less value than predicted**; 17% go badly enough to threaten the company. | IND/PR hybrid |
| BCG (2020), "Flipping the Odds", ~900 transformations. https://www.bcg.com/publications/2020/increasing-odds-of-success-in-digital-transformation | **30% met targets / 44% some value / 26% under half of target.** The only real origin of any "70%" figure, and it means 70% fell short, not failed. | IND |
| Gartner (Aug 2024), n=306 logistics leaders at $500M+ firms. https://www.gartner.com/en/newsroom/press-releases/2024-08-01-gartner-says-76-percent-of-logistics-transformations-fail-to-meet-critical-performance-metrics | 76% of logistics transformations miss at least one of budget, timeline, or KPI targets (= challenged + failed). | IND |
| Gartner (Oct 2024). https://www.gartner.com/en/newsroom/press-releases/2024-10-22-gartner-survey-reveals-that-only-48-percent-of-digital-initiatives-meet-or-exceed-their-business-outcome-targets | 48% of digital initiatives meet or exceed outcome targets. | IND [S] |
| Panorama Consulting ERP reports. https://www.panorama-consulting.com/resource-center/erp-report-archives/ | Mid-2010s: ~55–58% over budget, ~65% late, 53% under half the expected benefits. 2026 (n=170): about a quarter over budget or late. Quote the old figures only with their date. | VND/IND |
| Cisco (2017), n=1,845. https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2017/m05/cisco-survey-reveals-close-to-three-fourths-of-iot-projects-are-failing.html | 60% of IoT initiatives stall at proof of concept; 26% complete success. Stand-in for RFID and sensing. | VND |

**Do not cite** (traced, no real source or misread):
- "70% of digital transformations fail": lineage runs through McKinsey and Kotter to Hammer & Champy's informal estimate; Hughes (2011, *J. Change Management*) found no empirical basis.
- "85% of AI projects fail (Gartner)": a 2018 *prediction* about erroneous outputs, not a failure rate.
- "87% of data science projects never reach production": a conference remark relayed by VentureBeat; no study.
- "95% of GenAI pilots fail (MIT NANDA 2025)": means "no measured P&L impact yet", about GenAI, not peer-reviewed.
- "87% of enterprise blockchain pilots fail (Gartner 2023)", "up to 50% of automation projects fail (McKinsey)", "75% of European TMS implementations over budget": not traceable.
- Gartner's "90% blockchain fatigue by 2023": a forecast.

## 3. By technology

### 3.1 Blockchain traceability (P(fail) 0.50 / **0.65** / 0.85)

| Source | Finding | Flag |
|---|---|---|
| Gartner (A. Litan) survey of blockchain service providers, via CoinDesk 2021. https://www.coindesk.com/markets/2021/05/25/consensus-2021-6-questions-for-gartners-avivah-litan | **14% of enterprise blockchain projects moved into production in 2020, up from 5% in 2019.** Best measured pilot-to-production rate. | IND [S] |
| Capgemini Research Institute (2018), n≈450. https://www.capgemini.com/in-en/wp-content/uploads/sites/18/2022/05/Digital-Blockchain-in-Supply-Chain-Report-4.pdf | Supply chain blockchain deployments: **3% at scale, 10% pilot, 87% proof of concept.** | IND |
| Vadgama & Tasca (2021), *Frontiers in Blockchain*; 271 supply chain projects 2010–2020. https://arxiv.org/abs/2010.00092 | 9.6% identified as failed, 23.2% in production, 45.4% pilot, 21.8% development. Understates failure: data stop before the 2022–23 consortium collapses. | PR [S] |
| Kamilaris et al. (2019), *Trends in Food Science & Technology*. https://arxiv.org/pdf/1908.07391 | 7 of 29 agri-food initiatives possibly inactive within ~2 years. | PR [S] |
| Deloitte (2017), GitHub analysis, ~86,000 repositories. https://www.deloitte.com/us/en/insights/industry/financial-services/evolution-of-blockchain-github-platform.html | 8% active; organisation-backed 15% vs 7%; mean life ~1 year; highest mortality in the first 6 months. Code repositories, not deployments. | IND |
| Sternberg, Hofmann & Roeck (2021), *J. Business Logistics* 42(1). https://onlinelibrary.wiley.com/doi/10.1111/jbl.12240 | Benefits need a critical mass of partners; inter-firm tensions block adoption. | PR [abstract] |
| TradeLens (Maersk–IBM) 2018–2023; we.trade 2017–2022; Marco Polo 2017–2023; HSBC Serai closed 2022. https://www.supplychaindive.com/news/Maersk-IBM-shut-down-TradeLens/637580/ ; https://www.gtreview.com/news/top-stories/marco-polo-brings-in-liquidators-as-funds-run-dry/ | Shared platforms went live and still died at **4–5.5 years**; every member lost its integration spend at once. TradeLens: rivals distrusted a platform part-owned by a competitor. | ANEC |

Suggested platform-death hazard for a blockchain consortium: 0.4–0.6 cumulative over 5 years (judgment from the cases).

### 3.2 ML demand forecasting (0.30 / **0.45** / 0.60)

| Source | Finding | Flag |
|---|---|---|
| Gartner "AI in Organizations" surveys, 2019 and 2022. https://www.gartner.com/en/newsroom/press-releases/2022-08-22-gartner-survey-reveals-80-percent-of-executives-think-automation-can-be-applied-to-any-business-decision | **53–54% of AI prototypes reach production** (so ~46% do not). Mostly large, AI-active firms. | IND [S] |
| S&P Global Market Intelligence (2025), n=1,006. https://www.spglobal.com/market-intelligence/en/news-insights/research/ai-experiences-rapid-adoption-but-with-mixed-outcomes-highlights-from-vote-ai-machine-learning | 46% of proofs of concept scrapped before production; firms abandoning most AI initiatives rose 17% → 42% in a year. | IND [S] |
| BCG (Oct 2024), n=1,000. https://www.bcg.com/press/24october2024-ai-adoption-in-2024-74-of-companies-struggle-to-achieve-and-scale-value | 74% have yet to show tangible value; 4% generate value consistently. | IND |
| RAND (2024), Ryseff, De Bruhl & Newberry, 65 interviews. https://www.rand.org/pubs/research_reports/RRA2680-1.html | Root causes: leadership misalignment, data quality, deployment infrastructure. Its ">80%" is second-hand. | IND [S] |
| Fildes, Goodwin, Lawrence & Nikolopoulos (2009), *IJF* 25(1), 60,000+ forecasts at 4 companies. https://www.sciencedirect.com/science/article/abs/pii/S0169207008001362 | Planners adjusted up to 90%+ of system forecasts; small and upward adjustments typically reduced accuracy. **Partial use is the main failure mode after go-live.** | PR [S] |
| Morlidge (2013/14), *Foresight*; 8 companies. https://forecasters.org/wp-content/uploads/FVA_A-Reality-Check_Foresight29.pdf | ~52% of item-level forecasts were worse than a naive forecast. | IND [S] |
| Supply Chain Insights (2014). | Demand planning: 82% satisfied; more often on time and on budget than supply planning. | IND [S] |

Forecasting is a mature AI use and probably fails less than GenAI pilots; the MID leans on the pilot-gate figures.

### 3.3 Supply chain risk intelligence (0.15 / **0.30** / 0.45; all proxies)

| Source | Finding | Flag |
|---|---|---|
| McKinsey supply chain pulse surveys 2021–2025. https://www.mckinsey.com/capabilities/operations/our-insights/supply-chain-risk-survey-2024 | Visibility beyond tier 1 *fell* in 2023–24 from its 2022 peak: capability lapses once a crisis passes. | IND [S] |
| Choi, Rogers & Vakil (2020), *HBR*; Resilinc survey n=300. https://hbr.org/2020/03/coronavirus-is-a-wake-up-call-for-supply-chain-management | 70% were still identifying affected suppliers by hand at COVID onset; one firm needed 100 people for over a year to map sub-tiers after 2011. | ANEC + VND |
| Conflict-minerals SEC filings (supplier survey response rates). | ~50–70% per tier; compounding gives ~36% coverage at tier 2 and ~22% at tier 3. | ANEC [S] |
| SaaS churn norms (KeyBanc/Bessemer via secondary sources). | Enterprise logo churn ~5–7% a year, mid-market ~10–12%, SMB 20%+: 15–50% over three years. No vendor-specific data. | IND/VND [S, low quality] |

Suggested dynamic: the lapse hazard rises with time since the last disruption and resets after one.

### 3.4 Control tower / visibility (0.15 / **0.25** / 0.40)

| Source | Finding | Flag |
|---|---|---|
| Gartner (2018), "Don't believe the control tower hype". | Qualitative warning; no failure statistics. | IND |
| Gartner (Sept 2023), n=600. https://www.gartner.com/en/newsroom/press-releases/2023-09-27-gartner-says-80-percent-of-supply-chain-not-accounted-for-in-current-digital-decision-models | Digital decision models made no meaningful difference to decision quality; over half felt they would have decided better without them. | IND [S] |
| Småros (2007), *J. Operations Management* 25. https://www.sciencedirect.com/science/article/abs/pii/S0272696306000751 | Ten years after CPFR's launch, large-scale implementations were still scarce despite many pilots; four collaborations with one grocer all struggled to scale. | PR [S] |
| AMR Research via Computerworld (~2002); META Group (n=105). https://www.computerworld.com/article/1326011/cpfr-clamor-persists-but-adoption-remains-slow.html | CPFR pilots far more plentiful than scaled programs. Inference: under ~20–30% of pilot pairs scaled. | IND [S] |
| FourKites citing Gartner and MIT CTL. | A disruption still takes 34+ manual updates across 6 systems: visibility without action. | VND |

Multi-party lever: realised benefit should follow the partner coverage actually achieved; per-partner join probability ~0.5–0.7 a year; coverage decays without upkeep.

### 3.5 Item-level RFID (voluntary 0.10 / **0.20** / 0.35)

| Source | Finding | Flag |
|---|---|---|
| Walmart mandate 2003–09. https://spectrum.ieee.org/suppliers-resist-rfid-push | About half of the top 100 suppliers tagging by Jan 2005; most did "slap-and-ship" with no benefit of their own; narrowed in 2007; penalty cut from $2–3 to $0.12 per pallet in Jan 2009. Collapse over 4–6 years. | ANEC |
| JCPenney 2012–13. https://www.rfidjournal.com/news/j-c-penney-defers-its-rfid-dreams/83724/ | Chain-wide item tagging cut back to a few categories within ~12 months (company distress, not the technology). | ANEC |
| Accenture RFID in Retail studies (2018; 2020–21). https://www.accenture.com/in-en/insights/retail/new-era-rfid | Pilot-only retailers 48% → 8%; full adoption 28% → 47%; 25% of pilots take over a year. No abandonment rate. | IND [S] |

For a mandated supplier: ~0.25 discontinue once the mandate weakens; 0.60 comply minimally and get 10–30% of their own planned benefit. No published RFID abandonment rate exists.

### 3.6 APS (0.05 / **0.15** / 0.25)

| Source | Finding | Flag |
|---|---|---|
| McKinsey, "Decoding success: how leaders get value from advanced planning systems". https://www.mckinsey.com/capabilities/operations/our-insights/decoding-success-how-leaders-get-value-from-advanced-planning-systems | "Around 65% of APS programs fail to achieve their expected ROI"; over 60% of planning-IT transformations miss outcomes and overrun. Undisclosed sample. | IND [S] |
| McKinsey Global Supply Chain Leader Survey 2024; Risk Pulse 2025. https://www.mckinsey.com/capabilities/operations/our-insights/supply-chain-risk-survey | **15% say their APS implementation has not met business objectives; 2% failed and must be restarted.** | IND [S] |
| Gartner via SCMR. | 44% of planners say transformation initiatives achieved half or fewer of targeted benefits. | IND [S] |
| Supply Chain Insights (2014). | Supply planning projects: 42% on time, 55% over budget, 59% satisfied; ~65% of firms still planning in Excel. | IND |
| de Man & Strandhagen (2018), *IFAC-PapersOnLine* 51(11); Ivert & Jonsson (2011), *IJPDLM* 41(4). https://www.sciencedirect.com/science/article/pii/S2405896318315507 | Spreadsheets stay the planners' main tool despite APS; parallel systems, under-use, consultant dependency. | PR (cases) |
| Nike–i2 (2000–01); Hershey (1999). https://www.cio.com/article/264637/enterprise-resource-planning-nike-rebounds-how-nike-recovered-from-its-supply-chain-disaster.html | ~$100M and ~$150M of lost sales (about 1% and 3% of revenue). Both firms kept the systems. **The tail risk is operational disruption, larger than the software cost.** | ANEC |

Reconciled: ~10–20% outright failure, 45–55% partial, 30–40% full. Tail: a 1–3% chance of a go-live disruption costing a multiple of the project.

### 3.7 Warehouse robotics (fixed 0.08 / **0.15** / 0.30; leased mobile robots ~0.20 with a 0.2–0.4 sunk share)

| Source | Finding | Flag |
|---|---|---|
| McKinsey (Dec 2023), "Getting warehouse automation right". https://www.mckinsey.com/capabilities/operations/our-insights/getting-warehouse-automation-right | "Too many projects are not delivering"; no percentage; a $150M automated DC left largely unused. | IND |
| Mordor Intelligence via Total Retail. | Integration overruns budgets by ~30% and timelines by up to a year. | IND [S] |
| Kroger–Ocado. https://www.grocerydive.com/news/kroger-canceling-charlotte-cfc-closing-nashville-spoke-ecommerce-ocado/807167/ | 3 of 8 automated fulfilment centres closing Jan 2026; $2.6B in charges; 2.5–4.5 years after go-live. | ANEC |
| Walmart–Bossa Nova 2017–2020; Adidas Speedfactory 2016–2020. https://techcrunch.com/2020/11/02/walmart-reportedly-ends-contract-with-inventory-robotics-startup-bossa-nova/ | Scaled to ~500 stores, then ended; factories closed after ~3 years. | ANEC |

Fixed automation rarely fails before go-live (capital is committed). It fails 2–5 years later as under-use or closure when demand forecasts prove wrong. No sourced base rate exists.

### 3.8 Routing / TMS (0.08 / **0.15** / 0.25; borrowed)

No TMS-specific failure data exists. ARC's user surveys (63% say freight would cost 5%+ more without their TMS) cover survivors only. Routing software is often overridden by drivers and dispatchers ("shelfware"; vendor and trade sources, no percentages). Parameters borrow from Standish's moderate-size rows, Panorama 2026, BCG's 30/44/26, and Gartner's 76%.

## 4. Scaling rules (suggested; low–medium confidence)

- **Firm size and maturity.** Evidence is about project size relative to capability (Standish: outright failure 7% for small projects to 43% for grand ones). Suggest multiplying the *odds* of failure by ~1.5–2.0 for small or low-maturity adopters and ~0.6–0.7 for large, mature ones. Magnitudes are judgment.
- **Multi-party adoption.** Member benefit × share of relevant partners that actually succeed. Add a platform-level hazard: if the hub or consortium dies, all members fail together and lose ~100% of platform-specific spend.
- **Mandated followers** comply minimally and keep a low benefit fraction of their own.
- **Overruns are fat-tailed** (mean +27%; ~1 in 6 at +200%).

## 5. What this would mean in SCITI (proposal; needs Kevin's ruling)

1. **One keyed draw per (firm, technology) at adoption** decides fail / partial / full, so runs still replay exactly.
   - *Fail:* the one-time cost is spent (sunk share), running cost stops at the failure week, and the technology never switches on; the firm can try again later.
   - *Partial:* it switches on at the benefit fraction (e.g., 0.5 × the catalog effect).
   - *Full:* as today.
2. **Catalog fields** per technology: `p_fail`, `p_partial`, `partial_fraction`, `fail_after_weeks` (from the table above), marked as evidence-based or borrowed.
3. **Small-firm scaling:** suppliers (the small firms in Ridge Line) get the 1.5–2× odds; factories and DCs the baseline.
4. **Group adoptions:** each member draws separately, and chain/pair effects already scale with the share of partners *active*, so failed members automatically weaken the group. A **platform-death draw** for blockchain groups (0.4–0.6 over 5 years) would be a second step.
5. **Agents do not know the outcome in advance,** but briefs could show each technology's failure odds, so LLM agents can weigh them; the payback rule could discount expected savings by the success odds.
6. **Expected effect on results:** blockchain's +$321M would fall to roughly a quarter to a third of that (10% full + 25% at 0.4); risk intelligence +$564M → roughly 40%; routing, RFID, robotics, APS to ~55–65%; ML forecasting barely matters (already ~0). Routing would stay on top, and risk intelligence would stay the best value per dollar. These are arithmetic guesses; the screen would need rerunning.
