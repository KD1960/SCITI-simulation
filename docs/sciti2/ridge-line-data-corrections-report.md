# Ridge Line Case: Data Corrections Report

**To:** Authors of the Ridge Line case and `Master Data Set_4.xlsx`
**From:** Kevin Dooley, W. P. Carey School of Business, ASU (SCITI simulation project)
**Date:** 2026-09-14
**Files reviewed:** `Master Data Set_4.xlsx`, `RidgeLine_SupplyChain_Overview.docx`

---

## Why you are receiving this

We built an agent-based simulation of the Ridge Line supply chain (SCITI 1). It runs all 48 firms week by week for three years. To do that, we had to read every sheet of the workbook into a model, and then check the model against the data and the overview document.

That work turned up errors in the workbook, gaps where the model needed information the case does not give, and places where the document and the data disagree. This report lists them. For each, it says what we found, what we did about it, and what we suggest you change.

We found the case rich and very useful. These notes are meant to make it stronger for students and for anyone who models it.

**How to read severity:**
- **High:** you cannot model the chain correctly, or answer the case question, without a fix.
- **Medium:** we had to make an assumption or a workaround.
- **Low:** wording, naming, or cosmetic.

Cell addresses are Excel addresses. The scripts used for every number here are available on request.

## 1. Summary

| # | Issue | Severity | What we did |
|---|---|---|---|
| 1 | Supplier lookup formula only ever picks the first of three suppliers, so 20 of 30 suppliers have no transactions | High | Used the parameter table for all 30; borrowed spread and quality from the one supplier per part that has data |
| 2 | Supplier transactions re-randomize every time Excel recalculates | High | Read the saved values once and recorded the file's fingerprint |
| 3 | No supplier is actually slipping: the case question has no answer in the data | High | Nothing (it does not affect the simulation) |
| 4 | Demand formula bugs for Retailer 5 (Mumbai) and Retailer 7 (Tokyo), repeated in the document's Table 5 | High | Corrected: rebuilt each wrong column from its intended Retailer 1 product (logged) |
| 5 | Every store's demand is a multiple of Retailer 1; Retailer 1 Product C is a copy of Product A | High | Fitted each store and product separately |
| 6 | DC→store shipment rows ignore the document's DC–store assignments | High | Network links follow the document; lane statistics taken from the data by mode |
| 7 | CM→plant shipment quantities are about 338× too small for the bill of materials, and split 25% per CM | High | Ignored shipment quantities; flows come from demand × bill of materials |
| 8 | Many shipment distances do not match the cities named | Medium | Used real city-to-city distances; simple lead-time model where the data fit was poor |
| 9 | Mode mixes, lead times, and cost ranges in the document differ from the data | Medium | Used the data |
| 10 | Overlapping supplier ranges in Table 3 | Medium | Used three suppliers per part, as in the workbook |
| 11 | Plant is called both `MFG_US` and `MFG_LA` | Low–Medium | Treated as one plant, `MFG_US` |
| 12 | Information a simulation needs is missing (prices, capacities, costs, weights) | Medium | Assumptions, clearly labeled (§5) |
| 13 | CO2 formula uses 50 kg per unit for every part | Medium | Kept the formula; flagged it |
| 14 | Naming, sentiment labels, typos | Low | Mapped names to one set of IDs |

## 2. Workbook errors (please fix)

### 2.1 Supplier lookup picks only one supplier per part — High

**What the case says.** Suppliers 1–30 each have transactions (§2.2).

**What the data shows.**
- `Supplier Data!D2` picks a sub-component at random: `=VLOOKUP(RAND(),$P$2:$Q$31,2,TRUE)`.
- `F2` then finds the supplier by sub-component name: `=VLOOKUP(D2,$Q$2:$S$31,3,FALSE)`. An exact-match lookup always returns the **first** of the three suppliers for that part.
- So only Suppliers 1, 4, 7, 10, 13, 16, 19, 22, 25, and 28 appear. The other 20 have zero rows.
- The sheet's used range runs to row 500,001. Rows 2–501 are the 500 real transactions. Rows 502–250,001 hold only a column G lookup that returns `#N/A`. The rest are empty but formatted.
- The price spread is a flat $2 (`NORM.INV(RAND(), price, 2)`) whether a part costs $20 or $100.

**What we did.** Took lead time and price for all 30 suppliers from the parameter table (Q:W, rows 2–31). For the 20 suppliers with no rows, we borrowed lead-time spread and defect share from the one supplier of the same part that has data. The model lists every one of these in its validation report.

**Suggested fix.** Choose the supplier within the part's block, for example `=INDEX($S$2:$S$31, MATCH(D2,$Q$2:$Q$31,0) + RANDBETWEEN(0,2))`. Clear rows 502 onward, including formats. Make price spread proportional to price.

### 2.2 Transactions change on every recalculation — High

**What the data shows.** About 3,000 cells in `Supplier Data` (columns B, C, D, H, I, K; rows 2–501) use `RAND()` or `RANDBETWEEN()`. Any edit or recalculation creates a new set of 500 transactions. The other sheets are stable.

**Why it matters.** Two students, or a student and the instructor, will see different numbers. The case is about building an analysis that can be repeated.

**What we did.** Read the saved values once and recorded the file's SHA-256 fingerprint in every simulation run.

**Suggested fix.** Paste as values before distributing. Keep a formula version for authors only.

### 2.3 The data cannot answer the case question — High (for teaching)

**What the case says.** "Which suppliers are performing well — and which ones are slipping?"

**What the data shows.**
- Lead time is the nominal value plus random noise (SD 2 days) for every supplier. No supplier is systematically late: differences between the 10 suppliers are not significant (permutation ANOVA, p = 0.47).
- Negative sentiment rates range from 1.6% to 18% by supplier, but that is also noise (χ², p = 0.25). All suppliers draw feedback from the same table (`Z2:AA15`).
- There is no promised date, ship date, or receipt date, so "on track vs. slipping" cannot be defined against a contract.

**Suggested fix.** Add promised and actual lead-time (or date) columns. Build in two or three truly weak suppliers whose lateness and negative sentiment rise together, so careful analysis is rewarded.

### 2.4 Demand formula bugs for Mumbai and Tokyo — High

**What the case says.** Mumbai (Retailer 5) is "balanced across all three products" at about 71,414 each. Tokyo (Retailer 7) is A 0.8×, B 0.5×, C 0.4× of Retailer 1, "reflecting Japanese consumer preferences."

**What the data shows** (we checked these cells directly; the same pattern runs through rows 5–264):

| Store | Cell | Formula now | Should be |
|---|---|---|---|
| Retailer 5 | P5 (A) | `=P$2*E5` | `=P$2*D5` |
| Retailer 5 | Q5 (B) | `=Q$2*E5` | `=Q$2*E5` (correct) |
| Retailer 5 | R5 (C) | `=R$2*E5` | `=R$2*F5` |
| Retailer 7 | V5 (A) | `=V$2*F5` | `=V$2*D5` |
| Retailer 7 | W5 (B) | `=W$2*F5` | `=W$2*E5` |
| Retailer 7 | X5 (C) | `=X$2*F5` | `=X$2*F5` (correct) |

- All three Mumbai products copy Retailer 1's Product B. All three Tokyo products copy Retailer 1's Product C.
- As a result, Tokyo's Product A **falls** from 69,784 (2020) to 51,483 (2024), because it follows Product C's decline.
- The document's Table 5 figures for Mumbai and Tokyo exactly match these buggy sums. The "balanced Mumbai" and "Japanese preference" stories explain a spreadsheet error.
- Corrected 2024 totals would be about: Mumbai 103,391 / 71,414 / 51,483; Tokyo 103,391 / 44,634 / 25,742.
- The bug also flows into supplier order quantities, because `AE11` (total demand) feeds `Supplier Data!Y2`.

**What we did.** Our loader now detects a store column that scales the wrong Retailer 1 product and rebuilds it as scale × the intended product. It fixed exactly four columns (Mumbai A and C, Tokyo A and B) and lists each in the validation report.

**Suggested fix.** Correct columns P, R, V, W. Regenerate Table 5. Either rewrite the Mumbai and Tokyo text, or build the intended patterns on purpose.

### 2.5 All stores share one demand pattern — High

**What the data shows.**
- Only Retailer 1 (columns D–F) holds typed values. Every other store is a fixed multiple of Retailer 1. Their week-to-week variation is therefore identical (for example, the Product A coefficient of variation is 0.1218 for Retailers 1, 2, 6, and 8).
- Retailer 1 Product C equals Product A times a constant for each year: 1.000 in 2020 (e.g., D5 = F5 = 1,235), then 0.909, 0.744, 0.609, 0.498. Only Product B is independent.
- Scaled stores get fractional demand (e.g., Singapore minimum 86.4 units).
- So Table 5's different "Demand Pattern" labels ("stable," "moderate seasonal peaks," "consistent") cannot all be true.

**What we did.** Fitted trend, seasonality, and noise to each of the 24 store × product series separately. This gives stores independent noise that the data does not have.

**Suggested fix.** Generate each store and product with its own seasonality, noise, and trend, and round to whole units.

### 2.6 DC→store shipments ignore the document's lanes — High

**What the case says.** Ten DC–store links: Houston → Columbus, São Paulo; Dubai → Barcelona, Nairobi, Mumbai; Sofia → Barcelona; Shanghai → Mumbai, Singapore, Tokyo, Melbourne. Shanghai is "the highest-volume DC."

**What the data shows** (Shipments sheet, columns AE:AR).
- All 32 possible DC–store pairs have 15–16 rows each.
- Only 155 of 500 rows (34% of units) use one of the document's ten links. Examples: Houston → Singapore, Shanghai → São Paulo.
- Columbus gets more from Dubai (82,296 units) and Sofia (76,987) than from Houston (67,564).
- The four DCs ship almost the same volume. Shanghai is the lowest, not the highest.
- Store totals do match Table 5 within about ±1%.

**What we did.** Network links follow the document. Lead time, mode mix, and cost come from the data, pooled by mode.

**Suggested fix.** Generate DC→store shipments only on the ten links, with a stated split for stores served by two DCs (Barcelona, Mumbai).

### 2.7 CM→plant quantities do not fit the bill of materials — High

**What the data shows.**
- CM→plant rows are 1,200–1,500 units each. Totals: 674,464 units, split almost exactly 25% per CM.
- The plants ship 1,426,403 finished products to DCs. At 160 parts each, they need about 228 million parts — **338 times** what the CMs ship.
- By the bill of materials, CM_Mexico should supply 110 of every 160 parts (69%). The document calls it "the highest-volume" CM.
- The unit of "Quantity" is not defined, and freight is quoted per part ($2.5–9.4) even though 160 parts go into each product.

**What we did.** Ignored shipment quantities. Flows in the model come from store demand × bill of materials.

**Suggested fix.** Define the shipment unit (part, case, pallet), and scale quantities to production and to each CM's share.

### 2.8 Shipment distances do not match the cities — Medium

**What the data shows.** Some lanes are shorter than the straight-line distance, which is impossible:

| Lane | Data (miles) | Straight-line |
|---|---|---|
| Shanghai → Singapore, ship | 1,488–1,513 | 2,365 |
| Guadalajara → Shenzhen, ship | 7,196–7,526 | 8,529 |
| Taipei → Los Angeles, ship | 6,327–6,674 | 6,777 |
| Shanghai → Nairobi, air | 4,756–5,025 | 5,949 |

Others are much too long: Dubai → Mumbai air 1,914–1,987 vs. 1,202; Houston → Columbus air 1,515–1,594 vs. 992. In some modes lead time or cost goes **down** as distance goes up.

**What we did.** Placed every node at its document city and used real great-circle distances. Where a mode had fewer than 50 rows or a negative distance slope, we used a flat average lead time. Our sea transit times come out about 24% below the data's own averages, likely because of these distances.

**Suggested fix.** Compute distances from city coordinates, then derive lead time and cost from distance and mode.

### 2.9 Other formula and field issues — Low–Medium

- **Lead times of zero or less:** `SA_0_273` (row 274) is −1; `SA_0_49`, `SA_0_191`, `SA_0_242` are 0.
- **Order quantity** is one constant per supplier (308k, 154k, 463k, or 1,234k), not a real order size.
- **Region field:** 99 rows say "SA", which is not in the document's list. The region "NA" is read as *missing* by common tools (e.g., pandas), silently dropping 120 rows. Region is random with respect to supplier.
- **Sentiment is a lookup, not NLP.** Some labels contradict the text: "Box was crushed but the product works great" = 1; "Well made product, packaging cracked but item safe" = 3; "Feels flimsy, does the job" = 1 (the document quotes it as a negative example).
- **Dates:** supplier and shipment dates are all 2024; demand covers 2020–2024. `Ship_Date` is stored as text.

## 3. Where the document and the data disagree

| Topic | Document | Data | We used |
|---|---|---|---|
| Suppliers for SR_MCU | "Suppliers 1–6" (Table 3), overlapping SR_MOS_KIT "4–6" | 1–3 and 4–6 | Data (3 per part) |
| US plant name | `MFG_US` | `MFG_US` in CM→plant rows; `MFG_LA` in all 249 plant→DC rows and Glossary A40 | One node, `MFG_US` |
| DC→store air share | ~55% air, ~35% sea | 65% air, 33% sea, 1.4% rail, 0.4% road | Data |
| Plant→DC modes | Air and sea only | Also 12% road and rail | Data |
| CM_Taiwan | Ships "via air"; 1–13 days | 43% by sea; 1–28 days | Data |
| CM_India | Ships to Shenzhen | Ships to LA and Shenzhen equally; 39% sea | Document links, data lanes |
| CM_Mexico → LA | Road, ~1 day | Road 3–6 days; also air and rail; also ships to Shenzhen | Data |
| CM_Germany → LA | "Air, 19 days" (§3.1) and "sea, ~19 days" (§4.1) | Air 2–4 days; sea 18–27 days | Data |
| Taiwan → LA | 6,893 mi, ~4 days | That is one row; lane averages 2.9 days | Data |
| Germany → Shenzhen | 8,564 mi, 38 days | 38 is the maximum; mean 31.6 | Data |
| Longest lead time | 38 days (glass) | Plant→DC up to 41; DC→store up to 44 | Data |
| Houston inbound | Road and rail from MFG_US | Also air, and 63 rows from Shenzhen | Document links |
| São Paulo | "Predominantly air" | From Houston: 6 air, 9 sea | Data |
| Melbourne | "Primarily sea" | 64% air | Data |
| Cost ranges (Table 4) | e.g., MFG→DC $1.80–18.00 | $0.81–17.97; 5–14% of rows outside the ranges | Data (Glossary ranges do match) |
| Plant ships 10–15% more than DC→store | — | +11.1% ✓ | — |
| Demand growth | — | Retailer 1: A +10.8%, B +0.3%, C −6.7% per year ✓ | Data |
| End-of-quarter peaks | — | Supported (weeks 12–13 of each quarter index 1.12) ✓ | Data |

## 4. CO2 — Medium

The CO2 columns follow the Glossary formula exactly (quantity × 0.05 t × miles × factor; all 1,500 rows check out, in kg). Three concerns:
- The same 50 kg per unit is applied to microcontrollers, resin, and finished products. A microcontroller does not weigh 50 kg.
- The formula uses the faulty distances in §2.8.
- The Glossary does not say short or metric tons. The air factor (2.1 kg/ton-mile) is at the high end of published values and worth a source note.

**What we did.** Kept the formula on real distances and flagged the result. In our model, total CO2 works out to roughly 50 tonnes per product sold, which is far too high.

**Suggested fix.** Give a weight per part and per finished product, and cite the emission factors.

## 5. Information a simulation needs that the case does not give

We filled these gaps with assumptions. Each is labeled as an assumption in every simulation output. If the case can supply real values, we will use them.

| Needed | Our assumption |
|---|---|
| Transfer and retail prices | Cost plus markup: CM +20%, plant +25%, DC +10%, store +40% (gives about $5,642 in parts → $13,032 retail per product) |
| Capacity | Suppliers 1.5×, CMs 1.3×, plants 1.3× of average flow |
| Holding cost | 25% of unit value per year |
| Stockout penalty | Lost margin + $5 goodwill per unit |
| Handling cost and dispatch delay | $0.50 per unit; 2 days |
| Inventory record error, shrink | 5%; 0.2% per week |
| Quality inspection | 80% of defects caught; defect rate = share of sentiment 1 |
| Ordering policy | 95% service target; exponential smoothing α = 0.3 |
| Split for stores with two DCs | Barcelona and Mumbai 50/50 |
| Which plant supplies each DC | Houston 80/20 US/China; Sofia 60/40; Dubai 40/60; Shanghai 10/90 |
| Supplier locations | Placed near their CM (illustrative) |
| Supplier → CM freight | Not modeled (no cost or CO2 data) |
| Supplier cost of goods | 70% of price |
| Raw material → part conversion | 1 : 1 |
| Starting stock and cash | 2 weeks of finished goods; lead time + 2 weeks of inputs; 13 weeks of revenue as cash |
| Road and rail | Not allowed on lanes of 2,500 miles or more |
| Weight per unit | 0.05 t for everything (from the Glossary) |

## 6. Naming and wording — Low

- **Company name:** the narrative uses "Silicon Ridge Systems" (5 times), described as a chip maker selling through distributors. The overview uses "Ridge Line Inc.", which owns its stores.
- **IDs:** stores appear as `Retail_1` (Glossary), `Ret_01` (shipments), and "Retailer 1" (demand). Shipment IDs use three formats (`CM_M_001`, `S0001`, `DR_001`). "Plastic" vs. "Plastics."
- **Structure wording:** "four material families" vs. "five component groups." Semiconductors are called the "highest-unit-count" component, but elastomers have 40 units each. Suppliers are called raw-material providers but sell finished part SKUs. Table 1 mentions PCBs, which are not in the bill of materials.
- **Typos:** "Sao Paolo" (Glossary C27); stray characters at the end of the CM_4 address (Glossary E19); "Emmisions" (A66); "Its recalculate" (A78); missing or misplaced quotation marks in the narrative ("Well, that was…", "Yeah, he said.", "And then, she said,").

## 7. Suggested priority for a revised release

1. Paste supplier transactions as values; fix the supplier lookup (§2.1, §2.2).
2. Fix the Mumbai and Tokyo formulas and Table 5 (§2.4).
3. Build a real supplier-performance signal with promised vs. actual dates (§2.3).
4. Make DC→store shipments follow the document's links (§2.6).
5. Make distances, quantities, and weights consistent (§2.7, §2.8, §4).
6. Reconcile the document's mode, lead-time, and cost statements with the data (§3).
7. If possible, add prices, capacities, and costs (§5).

We are glad to share the scripts behind these checks, test a revised workbook, and send the simulation's validation report for it.
