# Technology Evidence Table (calibration groundwork)

**Date:** 2026-09-17
**Purpose:** replace the catalog's placeholder effect sizes and costs (`assumption: true`) with sourced ranges, and say how confident each one is.
**Method:** web research by four helpers (two technologies each), each asked for 4–8 sources per technology with the KPI, the effect as reported, the sample, and a quality flag. Findings were checked against the model's parameter definitions and the 2026-09-17 sensitivity screen. Paywalled papers were read from abstracts or snippets and are marked. **Nothing in the catalog has been changed yet.**

Quality flags: **PR** peer-reviewed · **IND** industry/analyst survey · **VND** vendor-published or vendor-funded · **ANEC** single self-reported case.

## 1. Summary

| Technology | Parameter | Placeholder | LOW | MID | HIGH | Placeholder verdict | Confidence |
|---|---|---|---|---|---|---|---|
| Blockchain traceability | `defect_mult` | 0.60 | 0.95–1.0 | **0.80–0.85** | 0.65 | **Too strong.** No study measures a defect change from blockchain; evidence is for traceability in general | Low |
| Routing / TMS | `ship_cost_mult` | 0.92 | 0.95 | **0.92** | 0.87 | Holds | Medium |
| | `co2_mult` | 0.90 | 0.97 | **0.94** | 0.90 | A bit optimistic for carrier freight | Medium |
| Item-level RFID | `record_error_sd` × | 0.20 | 0.60 | **0.25** | 0.10 | Holds for CMs/DCs; use 0.25 at stores | High |
| | `shrink_rate` × | 0.50 | 0.95–1.0 | **0.80** | 0.50 | **Too strong** (vendor claim) | Medium |
| Warehouse robotics | `handling_cost_per_unit` × | 0.80 | 0.90 | **0.80** | 0.65 | Holds | Medium |
| | `dispatch_delay_days` | −1.0 | −0.3 | **−0.6** | −1.0 | Optimistic | Medium |
| Control tower | `visibility` | 1.0 | 0.25–0.35 | **0.55–0.65** | 0.85–0.95 | **Too strong.** 1.0 matches VMI with decision transfer, not visibility alone | Medium-high (rich PR literature) |
| ML forecasting | `forecast_skill` | +0.30 | 0.10 | **0.25–0.30** | 0.45–0.50 | Top of MID; use LOW at stores, MID at DCs/factories | High (M4/M5) |
| APS | `capacity_mult` | +0.08 | +0.03 | **+0.08** | +0.15 | Holds | Low (vendor cases only) |
| Risk intelligence | `recovery_mult` | 0.60 | 0.85 | **0.70** | 0.55 | Optimistic; the effect should shrink for long outages | Low-medium |
| | `early_warning_weeks` | +2 | 0 | **+1** | +2 | +2 only for the forecastable third-to-half of events | Low-medium |

LOW = weakest defensible effect, HIGH = strongest. Where the sensitivity screen showed profit moving roughly in proportion to effect size, the MID values above imply: blockchain gain about half the placeholder result, RFID a little lower (shrink is a small part of its gain), control tower unchanged in shape but 60% of the placeholder weight, ML slightly lower at stores. Costs matter little (break-even multiples 4×–200× in the screen), so the cost columns below are for realism, not ranking.

## 2. Technology detail

### 2.1 Blockchain traceability → `defect_mult` (confidence: low)

*KPI mapping.* No source reports a defect-share change. Defects were split into counterfeit/non-conforming parts, which traceability can screen out (a small share of a 10% baseline; ERAI reports ~1,000 suspect parts a year across the industry), and process defects, which traceability affects only through supplier incentives and faster root cause. MID assumes most of the first and 10–15% of the second are removed.

| Source | Finding | Flag |
|---|---|---|
| Culot, Podrecca & Nassimbeni (2024), *IJOPM* 44(13), event study of 130 North American adopters vs matched controls. https://www.emerald.com/insight/content/doi/10.1108/ijopm-05-2023-0346/full/html | Operating cycle −3 to −4 days, ROA +0.8 to +2.0 pts, sales unchanged. **No quality metric.** Authors note blockchain "does not guarantee the veracity of data." | PR |
| Cui, Gaur & Liu (2023), *M&SOM*; EJOR (2020) traceability × recall; Zhou et al. (2024), *ITOR*. https://pubsonline.informs.org/doi/10.1287/msom.2022.1161 ; https://onlinelibrary.wiley.com/doi/abs/10.1111/itor.13295 | Traceability raises supplier quality incentives in some settings and lowers them under intense competition. Direction is contingent. | PR (theory) |
| Vu, Ghadge & Bourlakis (2025), *IJPR* 63(14). https://www.tandfonline.com/doi/full/10.1080/00207543.2024.2414375 | Inventory and lead-time gains in a calibrated model; no defect estimate. | PR (model) |
| Kamath (2018), *JBBA*, Walmart/IBM mango and pork pilots. https://jbba.scholasticahq.com/article/3712-food-traceability-on-blockchain-walmart-s-pork-and-mango-pilots-with-ibm | Trace-back 7 days → 2.2 s. Speed, not defects. | ANEC |
| Just Auto on Volvo/Circulor, Ford, Renault XCEED. https://www.just-auto.com/features/oems-look-to-blockchain-solutions-for-compliance-and-parts-performance/ | Sourcing disputes −90%, paperwork −90%; "recall cost −35%" is unsourced. | ANEC |
| ERAI 2024 report; GAO-16-236; SIA whitepaper. https://www.erai.com/erai_blog/3187/_2024_annual_report ; https://www.gao.gov/products/gao-16-236 | Counterfeit incidence base rates: small next to a 10% defect share. | IND / government |
| Gartner (2019) "90% of blockchain SC initiatives will suffer fatigue by 2023"; McKinsey (2017) "must or maybe". https://www.gartner.com/en/newsroom/press-releases/2019-05-07-gartner-predicts-90--of-blockchain-based-supply-chain | Most pilots stall; realisation risk. | IND |

*Costs.* Joining an existing network: $50–150k one-time, $10–30k/yr (small supplier). Network anchor: $0.5–1M+ one-time, $100–500k/yr. All vendor/analyst (ScienceSoft, MRFR, IBM platform pricing). Placeholders ($100k/$300k one-time; $52k/$156k per year) are inside these ranges.

### 2.2 Routing / TMS → `ship_cost_mult`, `co2_mult` (confidence: medium)

*KPI mapping.* `ship_cost_mult` = 1 − freight-spend saving. The model's shippers use carriers on multimodal lanes, so the TMS surveys are the right evidence; own-fleet last-mile routing (larger savings) is a different case. Only the mode-shift and consolidation part of TMS savings cuts CO2, so `co2_mult` should be closer to 1 than `ship_cost_mult`.

| Source | Finding | Flag |
|---|---|---|
| ARC Advisory Group TMS ROI surveys (2011–2016). https://www.arcweb.com/industry-best-practices/tms-roi-improving | Freight-spend savings ~6% → 8% → 8–10%; the TMS absorbs <10% of savings for ~60% of users. Origin of the "8%". | IND |
| Logistics Management (2014), "State of TMS". https://www.logisticsmgmt.com/article/supply_chain_technology_2014_state_of_tmscost_reductions_and_roi_continue_t | ~8%; $100M freight spend, $1–2M TMS, ~$8M/yr saved. | IND (secondary) |
| Gartner TMS ROI band, relayed by Oracle. https://www.oracle.com/scm/logistics/transportation-management/what-is-transportation-management-system/ | 5–15% total freight cost. Primary paywalled. | IND (secondary) |
| UPS ORION, INFORMS Edelman (2016). https://www.informs.org/Impact/O.R.-Analytics-Success-Stories/Optimizing-Delivery-Routes | 100M fewer miles/yr, 100 kt CO2, $300–400M/yr; ≈3–4% of package-car miles; ~$250M to build. | Case, independently verified |
| Karimipour et al. (2017), *IJESD* 8(11). https://www.ijesd.org/vol8/1056-D54.pdf | −10% distance, −11% fuel, −10% GHG on one fleet. | PR (small) |
| Cruijssen et al. (2007), *IJPDLM* 37(4). https://www.emerald.com/insight/content/doi/10.1108/09600030710752514/full/html | Joint route planning ~30%: collaborative upper bound, computational. | PR |
| Kay et al. (2022), *TRR*. https://doi.org/10.1177/03611981211041596 | Long-haul multi-stop gains are single-digit % over good heuristics. | PR |

"10–30% last-mile savings" on vendor sites is marketing.

*Costs.* Enterprise TMS $1–2M one-time per $100M freight spend, ~$0.5–0.8M/yr; mid $150–500k / $50–150k per year; small $20k / $10–30k per year. Placeholders ($200–400k one-time; $104–208k per year) fit a mid-size shipper; the model's factories and DCs are larger than that.

### 2.3 Item-level RFID → `record_error_sd` ×, `shrink_rate` × (confidence: high for accuracy, medium for shrink)

*KPI mapping.* Sources report the share of SKUs with a wrong record, not the SD of the error. Auburn's own metrics note shows magnitude metrics move less than share metrics, so MID is 0.25 rather than 0.15. Shrink evidence is applied directly as a multiplier.

| Source | Finding | Flag |
|---|---|---|
| Hardgrave, Aloysius & Goyal (2013), *POMS* 22(4), Walmart, 13 stores. https://onlinelibrary.wiley.com/doi/abs/10.1111/poms.12010 | Record inaccuracy −26% vs control (case-level tags). | PR field experiment |
| Hardgrave et al. (2008/2011), *IJRFT*. https://rfid.auburn.edu/papers/documents/DoesRFIDImproveInventoryAccuracy.pdf | Understated records −13%; baseline 65% of records inaccurate (Raman, DeHoratius & Ton 2001). | PR |
| Hardgrave, Waller & Miller (2008), *MISQE* 7(4), 24 Walmart stores. https://aisel.aisnet.org/misqe/vol7/iss4/4/ | Out-of-stocks −26% (−21% net of controls). | PR |
| Auburn RFID Lab & GS1 US (2018), Project Zipper, >1M items, 8 brands, 5 retailers. https://www.supplychaindive.com/news/RFID-100-accurate-ROI-Auburn/539449/ | Shipment errors in 69% of orders → <0.01% with item-level EPC. Directly relevant to CM/DC record error. | IND (academic lab, GS1-funded) |
| Beck / ECR Retail Loss (2018), 10 retailers. https://www.rfidjournal.com/news/ecr-retail-loss-group-issues-report-on-rfid-in-retailing/191458/ | Accuracy 65–75% → 93–99%; stock −2 to −13%; one firm shrink −15%; all report ROI. | IND (sponsored, self-reported) |
| ECR Retail Loss (2025), 25 retailers. https://ecrloss.com/rfid-retail-case-studies-25-retailers/ | 60–75% → 95–99%; sales +5–8%. | IND (secondary) |
| Auburn "Inventory Accuracy" whitepaper. https://rfid.auburn.edu/papers/documents/InventoryAccuracyWhitepaper.pdf | The "65% → 95%" number depends on the metric (exact match vs magnitude). | Lab note |
| Checkpoint (2022) RF label press release; NRF 2023 shrink 1.6% of sales. https://nrf.com/media-center/press-releases/shrink-accounted-over-112-billion-industry-losses-2022-according-nrf | Shrink −50% on previously unprotected items (EAS-style). | VND |

The "65% → 95%" figure originates in University of Arkansas RFID Research Center news (2008) and Hardgrave's talks. Macy's and Zara numbers are company statements.

*Baseline flag.* The model's shrink baseline is 0.2%/week (~10%/yr); retail shrink is ~1.6%/yr (NRF). The multiplier still applies, but the baseline is high.

*Costs.* Tags $0.05–0.18 per item; handheld $300–1.5k, portal $1.5–3k; small site $10–25k one-time, $10–20k/yr; enterprise $100k–1M+ one-time, $15–50k per store rollout. Tag spend dominates running cost (10M units/yr × $0.06 ≈ $600k/yr). Placeholder running costs ($104–260k per year) are low for a DC or factory tagging millions of units.

### 2.4 Warehouse robotics → `handling_cost_per_unit` ×, `dispatch_delay_days` (confidence: medium)

*KPI mapping.* Pick-rate gains were converted to labour cost per unit (∝ 1/pick rate), scaled by picking's ~55% share of DC handling cost, then robot running cost added back. Dispatch: robotics compresses the in-DC pick/pack part of order-to-dispatch (Amazon 60–75 min → 15 min), which is typically 0.5–1.0 day of a 2-day baseline.

| Source | Finding | Flag |
|---|---|---|
| Amazon/Kiva via Deutsche Bank (2016). https://finance.yahoo.com/news/amazons-775-million-deal-robotics-200246489.html | ~20% lower operating cost per fulfilment centre; click-to-ship 60–75 min → 15 min. Origin of "20%". | ANEC (company + analyst) |
| Azadeh, de Koster & Roy (2019), *Transportation Science* 53(4). https://doi.org/10.1287/trsc.2018.0873 | Robotic mobile fulfilment 2–3× picker productivity; picking ~55% of warehouse opex. | PR review |
| Boysen, de Koster & Weidinger (2019), *EJOR* 277(2). | Same 2–3× figure. | PR review |
| DHL + Locus (2024, 2026). https://group.dhl.com/en/media-relations/press-releases/2024/dhl-supply-chain-passes-unprecedented-500-million-picks-milestone-using-locus-robotics-autonomous-mobile-robots.html | Units per hour +30% to +180%; one site 78 → 150. | VND (large base) |
| McKinsey (2023), "Getting warehouse automation right". https://www.mckinsey.com/capabilities/operations/our-insights/getting-warehouse-automation-right | Operating cost up to −30%, labour up to −35%. | IND |
| Kardex (2024), AutoStore cost. https://www.kardex.com/en-us/blog/how-much-does-autostore-cost | $1M–$50M+, typical $3–6M, payback 2–3 years. | VND |
| RaaS pricing guides (2026). https://robotomated.com/learn/cost/warehouse-robot-cost-guide | AMR $25–50k each or $2–4k/robot/month; GTP $2–10M for 20k SKUs; payback 18–36 months. | VND (secondary) |

*Costs.* Small DC $0.5M one-time / $0.3M per year; mid $4M / $0.5M; large $20M / $2M. Placeholder ($2.5M one-time; $780k per year) fits a mid-size DC.

### 2.5 Control tower / visibility → `visibility` (confidence: medium-high)

*KPI mapping.* `visibility` is the weight on echelon ordering (end demand plus downstream positions) versus local orders. Peer-reviewed work says information sharing alone removes only the demand-signal-processing cause of bullwhip, captures a small share of cost, and in human experiments closes only 1–8% of the gap to zero bullwhip even though upstream order variance falls 37–52%. The large inventory cuts (50–70%) appear only when sharing is bundled with decision transfer (VMI/CRP) and shorter lead times. So read `visibility` as the share of the theoretical echelon benefit actually realised.

| Source | Finding | Flag |
|---|---|---|
| Cachon & Fisher (2000), *Mgmt Sci* 46(8). | Full information sharing cuts supply chain cost 2.2% on average, max 12%; halving lead time or batch size saves ~21–22%. LOW anchor. | PR |
| Chen, Drezner, Ryan & Simchi-Levi (2000), *Mgmt Sci* 46(3). | With shared demand, bullwhip grows additively across stages instead of multiplicatively: "reduced but not eliminated". | PR |
| Lee, Padmanabhan & Whang (1997), *Mgmt Sci* 43(4). | Sharing removes one of four bullwhip causes. | PR |
| Lee, So & Tang (2000), *Mgmt Sci* 46(5). | Value high when demand is autocorrelated and lead times long (true for this model's 9 of 24 autocorrelated series). | PR |
| Croson & Donohue (2006), *Mgmt Sci* 52(3). https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/[34].pdf | Sharing inventory positions: order variance distributor −52%, manufacturer −37% (significant), retailer −6%, wholesaler −9%. MID anchor; larger upstream. | PR lab experiment |
| Steckel, Gupta & Banerji (2004), *Mgmt Sci* 50(4). https://pubsonline.informs.org/doi/10.1287/mnsc.1030.0169 | POS sharing can hurt with S-shaped demand. | PR |
| Trapero, Kourentzes & Fildes (2012), *Omega* 40(6). | Supplier forecast accuracy improves with retailer POS data. | PR |
| Sheffi (2002), "The value of CPFR", MIT. https://web.mit.edu/sheffi/www/documents/genMedia.theValueOfCPFR.pdf | Pilots: forecast accuracy +21–40%, DC stock −13%, inventory −10–40%. | IND (optimistic) |
| Cachon & Fisher (1997), *POM* 6(3), Campbell CRP. | Retailer inventory −66% with fill held: decision transfer, not sharing alone. HIGH anchor. | PR case |
| Dong, Dresner & Yao (2014), *POM* 23(5). | VMI reduces inventory, stockouts, variability. | PR |
| McKinsey (2023/24) supply chain surveys. https://www.mckinsey.com/capabilities/operations/our-insights/supply-chain-risk-survey-2024 | Control tower cases: inventory −10%, turns +15–20%. | IND |
| Gartner (2018) "Don't believe the control tower hype". | Vendor claims outrun evidence. | IND |

*Costs.* SaaS $10–25k/yr (1 user) to $200–500k+/yr (100 users); large platforms $0.5–2M/yr; implementation 1–3× licence, enterprise programs $0.5–3M one-time; partner onboarding ~$5–25k each (unsourced); support 15–25% of licence plus 1–3 FTE. Placeholders are in range for a per-site share.

### 2.6 ML demand forecasting → `forecast_skill` (confidence: high)

*KPI mapping.* The model blends the firm's smoothing forecast with the true expected demand. Since error is now measured in the model, `forecast_skill` should be set so the measured error SD falls by the target percentage; w is a little above that percentage when irreducible noise is large. The strongest finding is the level effect: ML gains are ~3% at store-SKU level and 20–40% at DC or national level.

| Source | Finding | Flag |
|---|---|---|
| Makridakis, Spiliotis & Assimakopoulos (2022), *IJF* 38(4), M5. https://www.sciencedirect.com/science/article/pii/S0169207021001874 | Winner 22.4% better than exponential smoothing; only 7.5% of 5,507 teams beat ES at all; by level ~40% at total, ~23% mid, ~3% product-store. | PR (verified) |
| Makridakis et al. (2020), *IJF* 36(1), M4. | Hybrid ES-RNN ~10% better than Comb; pure ML mostly below simple stats. | PR |
| Makridakis et al. (2018), *PLoS ONE* 13(3). https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0194889 | Eight ML methods dominated by ETS/ARIMA/Theta on 1,045 series. Counter-evidence. | PR |
| Salinas et al. (2020), *IJF* 36(3), DeepAR. https://www.sciencedirect.com/science/article/pii/S0169207019301888 | ~15% over state of the art incl. Amazon demand. | PR (vendor-authored) |
| Theodorou, Spiliotis & Assimakopoulos (2025), *EJOR* 322(2). https://www.sciencedirect.com/science/article/abs/pii/S0377221724009755 | The accuracy → inventory-performance link is "often weak". Matches this model's finding. | PR |
| Fildes, Ma & Kolassa (2022), *IJF* 38(4), retail review. https://eprints.lancs.ac.uk/id/eprint/161956/1/PostScipt_2109127_final_v2.pdf | ML wins when promotions/prices/weather are available; ETS competitive in stable conditions. | PR review |
| Caro & Gallien (2010), *Interfaces* 40(1), Zara. https://web.mit.edu/jgallien/www/ZaraInterfacesPaperDraftFeb23.pdf | Forecast + optimisation: sales +3–4% in a controlled pilot. | PR field experiment |
| McKinsey (2017), "Smartening up with AI". https://www.mckinsey.com/industries/semiconductors/our-insights/smartening-up-with-artificial-intelligence | Errors −20–50%, lost sales −65%. Origin of the widely repeated number; no sample. Upper bound. | IND |

*Costs.* Enterprise $200–500k+/yr licence, large $0.5–2M/yr; mid-market $50–150k/yr; SMB $5–10k/yr; implementation 0.75–1.25× licence, 3–18 months. Placeholders ($400–900k one-time; $208–468k per year) fit.

### 2.7 APS → `capacity_mult` (confidence: low)

*KPI mapping.* Utilisation or OEE point gains map ~1:1 to effective output at a capacity-constrained plant. Vendor cases (14–20%) are selected winners moving off manual scheduling; BCG's +3 OEE points on an instrumented line is the sober end. Peer-reviewed work gives direction (inventory, on-time delivery) but no size.

| Source | Finding | Flag |
|---|---|---|
| Siemens Drives, Congleton (Opcenter APS). https://resources.sw.siemens.com/en-US/case-study-siemens-drives/ | Utilisation +14%; WIP −60% in one cell; FG inventory −20%. | VND / ANEC |
| Narayan Powertech (Opcenter APS). https://resources.sw.siemens.com/en-US/case-study-narayan-powertech/ | Capacity utilisation +15–20%; lead time 4 → 2.5 weeks. | VND / ANEC |
| AQ Electric (Opcenter APS). https://resources.sw.siemens.com/en-US/case-study-aq-electric-opcenter/ | Changeover −15%; OTIF to 98%. | VND / ANEC |
| BCG AI scheduling, via SCW.ai / Manufacturing Digital (2024–25). https://manufacturingdigital.com/news/unlocking-factory-capacity-with-ai-driven-efficiency | OEE +3 points; planner effort −50%. Primary BCG note not located. | IND (secondary) |
| McKinsey / WEF Global Lighthouse Network. https://www.mckinsey.com/capabilities/operations/our-insights/the-continuing-evolution-of-the-global-lighthouse-network | 20–60% KPI gains, bundled with many levers; strong selection bias. | IND |
| Kjellsdotter Ivert & Jonsson (2010), *IMDS* 110(5); Jonsson, Kjellsdotter & Rudberg (2007), *IJPDLM*. https://www.emerald.com/insight/content/doi/10.1108/02635571011044713/full/html | APS benefits are mostly lower inventory and better OTD; no throughput %. | PR (qualitative) |
| Wiers (2002), *PPC* 13(6); Chen et al. (2011), *JSSSE*. | APS schedules beat manual expert schedules on due-date and utilisation measures (sizes paywalled). | PR |
| Aberdeen benchmarks via SDCExec. | Best-in-class OTD 95–98% vs 80–85% average; correlational. | IND |

"10–25% throughput", "15–30% efficiency", "hidden capacity 10–20%" on vendor blogs could not be traced to any primary study.

*Costs.* Mid-market licence $50–200k one-time, services $30–100k; SaaS $50–240k/yr; mid-size full deployment can exceed $500k; enterprise multi-plant high six to seven figures, 6–12+ months; maintenance ~20% of licence. Placeholders ($600k/$1.5M one-time; $312k/$780k per year) fit mid-to-large plants.

### 2.8 Risk intelligence → `recovery_mult`, `early_warning_weeks` (confidence: low-medium)

> **Update 2026-09-19:** a deeper search and a sensitivity run are in `risk-intel-evidence-and-sensitivity.md`. No peer-reviewed study measures monitoring's effect on outage length; best-supported form is saved = min(2 weeks, 0.25–0.30 × outage); warning probability MID 30%.

*KPI mapping.* Monitoring does not shorten the supplier's physical recovery (Renesas still took ~3 months after Tōhoku; Resilinc's 19–25 week natural-disaster recovery is measured at its own subscribers). It compresses the buyer's side: detection (GM: 6 weeks in 2011 → 6 hours in 2016), impact assessment (weeks → days), and time to trigger alternates. So `recovery_mult` is the multiplier on the subscriber's *experienced* outage. Cutting a ~3-week buyer lag to ≤1 week gives 0.85 for a 12-week outage and 0.55 for a 4-week one; a constant multiplier overstates the benefit for long outages. Early warning exists only for forecastable event classes (weather ≤14 days, labour, regulatory, financial distress): roughly a third to a half of alerts. Expected value ≈ 0.4 × 2 weeks ≈ +1 week; better modelled as P(warning) ≈ 0.35–0.5 with a 1–3 week lead.

| Source | Finding | Flag |
|---|---|---|
| Banker, Forbes (2016), GM and Resilinc. https://www.forbes.com/sites/stevebanker/2016/05/31/general-motors-embraces-supply-chain-resiliency/ | Detection 6 weeks (2011) → 6 hours (2016). | ANEC (vendor-adjacent) |
| Resilinc case studies; SDCExec on Flextronics. https://resilinc.ai/learning-center/case-studies/ | At-risk parts identified in 4 days (Hurricane Maria); an OEM later cut buffers 15%. | VND / ANEC |
| Resilinc EventWatch 2018 and 2024; factory-fires report. https://www.globenewswire.com/news-release/2025/01/21/3012562/0/en/Global-Supply-Chains-See-Nearly-40-Annual-Increase-in-Disruptions.html | 22,522 alerts in 2024 (+38%); 2,299 factory fires, 9% with >4 weeks downtime; natural-disaster site recovery 19–25 weeks. | VND (only large-N dataset) |
| BCI Supply Chain Resilience Report 2024 and 10-year trend (2009–2018). https://www.thebci.org/resource/bci-supply-chain-resilience-report-2024.html | ~80% of firms had ≥1 disruption in 2024; 1–5 per year for 40–55% of firms; 80% lose <€1M/yr, 6% lose >€11M/yr. | IND |
| McKinsey Global Institute (2020), "Risk, resilience, and rebalancing". https://www.mckinsey.com/capabilities/operations/our-insights/risk-resilience-and-rebalancing-in-global-value-chains | A ≥1-month disruption every 3.7 years; ~2-week ones every ~2 years; shocks cost ~45% of a year's EBITDA per decade. Modelled, not observed. | IND |
| Hendricks & Singhal (2005), *Mgmt Sci* 51(5); (2005) *POM* 14(1); (2003) *JOM*. https://pubsonline.informs.org/doi/10.1287/mnsc.1040.0353 | Per glitch: operating income −107%, sales −7%, costs +11%; ~−40% shareholder value over 3 years. Loss anchor; no monitoring counterfactual. | PR |
| Simchi-Levi, Schmidt & Wei (2014), *HBR*; Simchi-Levi et al. (2015), *Interfaces* 45(5), Ford. https://hbr.org/2014/01/from-superstorms-to-factory-fires-managing-unpredictable-supply-chain-disruptions | Time-to-recover is a property of the supplier site (2–8 weeks typical at Ford); risk = sites where TTR > time-to-survive. | PR |
| Matsuo (2015), *IJPE* 161; IEEE Spectrum on Renesas. https://www.sciencedirect.com/science/article/abs/pii/S0925527314002278 | Renesas fab ~3 months to restart; Toyota ~3 months to regain output. | PR / press |
| Macdonald & Corsi (2013), *JBL* 34(4). https://onlinelibrary.wiley.com/doi/abs/10.1111/jbl.12026 | Firms discover disruptions by phone calls and news; discovery method drives response speed. | PR (qualitative) |
| Everstream FAQ and Schaeffler case. https://www.everstream.ai/platform/global-monitoring/ | Weather/route risk forecast up to 14 days ahead; "seven-figure cost avoidance" claims. | VND |
| Interos / Vanson Bourne (2021). | Large firms average $184M/yr disruption cost. | VND-funded survey |
| Transportation Research Part E (2025), 526 Chinese manufacturers. https://www.sciencedirect.com/science/article/pii/S1366554525004697 | Visibility improves resilience (direction only). | PR |

"41% take a week to identify impacted materials" and "83% can't respond in 24 hours" are vendor webinar polls.

*Costs.* Resilinc from ~$17k/yr per module, realistic starter $50–100k/yr; Sphera/riskmethods actual spend: SMB $35k/yr, enterprise $261k/yr (Vendr); enterprise platforms six to seven figures; multi-tier mapping 3–9 months (inferred). Placeholders ($250–500k one-time; $130–260k per year) are high on the one-time side (subscriptions have little upfront cost) and fine on the running side.

## 3. Disruption base rates (for weighting calm vs disrupted scenarios in E2 and the LLM runs)

| Quantity | Value | Source |
|---|---|---|
| Firms with ≥1 supply disruption per year | 56–80% | BCI |
| Disruptions per firm per year, among the disrupted | 1–5 for ~40–55% of firms; 6–10 for ~8–16%; 11–20 for ~2–4% | BCI 2010–2018 |
| A ≥1-month disruption at a given company | once per ~3.7 years | MGI 2020 (modelled) |
| ~2-week disruptions | roughly every 2 years | MGI 2020 (verify in the PDF) |
| Factory fires with >4 weeks downtime | 9% of fires; fires ≈10% of alerts | Resilinc |
| Natural-disaster supplier-site recovery | 19–25 weeks average | Resilinc 2018 |
| Severe single-site event (fab) | ~13 weeks to restart | Matsuo 2015; Renesas |

Working rule for one supplier site in the model: P(any disruption in a year) ≈ 0.3–0.5 per site-year; given a disruption, ~60–70% last <4 weeks, ~20–30% 4–12 weeks, ~5–10% >12 weeks. No single primary source gives this distribution; it is assembled from the rows above and should be labelled as such. E2 showed 4-week hits sit inside the buffer and 12-week CM hits cost ~$1.5B, so the 4–12 week band is where risk intelligence and APS earn their keep.

## 4. What to do with this (for Kevin's ruling)

1. **Catalog v2 candidates** (MID values): blockchain `defect_mult` 0.6 → 0.82; RFID `shrink_rate` ×0.5 → ×0.8; control tower `visibility` 1.0 → 0.6; routing `co2_mult` 0.90 → 0.94; robotics `dispatch_delay_days` −1.0 → −0.6; risk intel `recovery_mult` 0.6 → 0.7 and `early_warning_weeks` 2 → 1; keep routing cost, RFID record error, robotics handling, ML skill, APS capacity. Keep `assumption: true` on blockchain, APS, and risk intelligence (no measured effect), and change the `evidence` field to cite the anchors above.
2. **Two model changes the evidence suggests**, beyond a number: (a) `forecast_skill` by role (LOW at stores, MID at DCs/factories: M5's level effect); (b) risk intelligence's recovery benefit as a fixed number of weeks saved (buyer lag) rather than a multiplier, and early warning as a probability with a lead time rather than a flat +2 weeks.
3. **Baseline flags to check:** shrink 0.2%/week is ~6× retail shrink; placeholder one-time costs for risk intelligence are high for a subscription service; RFID running cost is low for high-volume sites.
4. **Rerun E1 and the sensitivity screen on catalog v2** and compare with v1 (project plan, Nov 30 item).
