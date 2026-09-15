# E3 Who With Whom — Results

**Date:** 2026-09-15
**Engine:** `main` at `6ba2678`
**Command:** `.venv/bin/python docs/sciti2/experiments/who_with_whom.py OUT_DIR` (660 runs)
**Full numbers:** `docs/sciti2/experiments/who_with_whom_results.csv`

> **Illustrative only.** Technology costs and effects are placeholders. These results show how the model behaves, not real-world impact.

## The question

If the same number of firms adopt the same technology, does it matter **who** adopts, and **with whom**?

## What we ran

- **Two technologies that depend on partners:**
  - **Control tower:** a firm's benefit grows with the share of its direct customers (the next tier down) that also have it.
  - **Blockchain:** a firm benefits only if a linked partner also has it. The benefit is fewer defects in supplier shipments.
- **Six adopting firms in every structured arm**, arranged differently. Each linked group gets the +25% group bonus.
- **Reference arm:** every eligible firm adopts (48 for control tower, 36 for blockchain).
- **Two conditions:** calm, and a 12-week hit at Mexico (CM_3: 20% output, +14 days).
- 30 seeds, 3 years, each compared with the same seed and no technology.

| Arm | The 6 firms | Linked? |
|---|---|---|
| **Control tower, scattered** | CM_1, DC_Houston, Retail_3, Retail_8, Supplier_10, Supplier_20 | No two are partners |
| **Control tower, 3 pairs** | DC_Houston + Retail_1; DC_Sofia + Retail_3; DC_Dubai + Retail_4 | Each DC with one of its stores |
| **Control tower, downstream chain** | MFG_China, DC_Shanghai, Retail_5–8 | Factory → DC → all its stores |
| **Control tower, upstream chain** | CM_1–4, MFG_China, DC_Shanghai | Component makers → factory → DC |
| **Blockchain, scattered** | Suppliers 1, 7, 13, 19, 25, 28 | No supplier's CM adopts |
| **Blockchain, 3 pairs** | Supplier_1 + CM_1; Supplier_7 + CM_2; Supplier_25 + CM_4 | Each supplier with its CM |
| **Blockchain, hub at CM_1** | CM_1 + Suppliers 1–5 | One CM with 5 suppliers (low-volume parts) |
| **Blockchain, hub at CM_3** | CM_3 + Suppliers 13, 16, 19, 20, 22 | One CM with 5 suppliers (high-volume parts) |

## Bottom line

1. **Scattered adoption is wasted money.** With no partner, both technologies do nothing. The firms just pay the cost (control tower −$5M, blockchain −$2M).
2. **For control tower, chains beat pairs, and the best chain depends on conditions.**
   - **In calm conditions,** the **upstream chain** pays best (+$29M). It calms ordering at the component makers, where stock is most expensive.
   - **In a long disruption,** the **downstream chain** pays best (+$61M, up from +$3M in calm). It protects the stores' fill rate.
   - **Three separate pairs** gain little in either condition (+$6–8M, not clearly above zero).
3. **For blockchain, what matters is how much volume the linked suppliers carry, not the shape of the group.** Profit rises almost in step with the parts volume passing through linked suppliers: three pairs +$33M, a small-volume hub +$65M, a high-volume hub +$224M. The hub shape doesn't add anything beyond linking more volume. It is cheaper, though, because one CM serves five suppliers.
4. **Blockchain gains don't depend on disruptions; control tower gains grow with them.** Blockchain is about the same calm or disrupted. Control tower chains gain much more in a disruption.

## Control tower

Profit in $M over 3 years; fill rate and satisfaction changes. * = the 95% range excludes zero.

| Arm | Firms | Tech cost | Profit, calm | Profit, 12-week hit | Fill, calm | Fill, 12-week hit | Bullwhip at CMs, calm |
|---|---|---|---|---|---|---|---|
| Scattered | 6 | 5 | −5* | −5* | 0 | 0 | 0 |
| 3 pairs | 6 | 7 | +6 | +8 | +0.06 pt* | +0.06 pt* | −21* |
| Downstream chain | 6 | 7 | +3 | **+61*** | +0.05 pt* | **+0.18 pt*** | −25* |
| Upstream chain | 6 | 10 | **+29*** | +44* | +0.05 pt* | +0.17 pt* | **−51*** |
| All firms (reference) | 48 | 35 | +99* | +120* | +0.08 pt* | +0.23 pt* | −78* |

**Why the shapes differ:**
- **Pairs:** each DC has only one of its stores, so its tower works at partial strength. In a disruption, the DCs in the pairs aren't the ones feeding the hardest-hit stores.
- **Downstream chain:** DC_Shanghai has all of its stores, so it plans for their whole stock. In a disruption that cuts stockouts by $29M. In calm conditions, the extra holding cost (+$6M) and scrap cost (+$4M) cancel the savings.
- **Upstream chain:** the component makers see half of their factories adopt, so their towers work at more than half strength. That cuts their bullwhip in half and lowers holding cost (−$9M) in calm conditions. In a disruption they hold more stock (+$28M holding), but stockouts fall by $29M.

The 6-firm downstream chain captures about half of the whole-network gain in a disruption (+$61M of +$120M) for a fifth of the cost.

## Blockchain

| Arm | Firms | Suppliers with a linked CM | Their parts per product | Tech cost | Profit, calm | Profit, 12-week hit | Quality |
|---|---|---|---|---|---|---|---|
| Scattered | 6 | 0 | 0 | 2 | −2* | −2* | 0 |
| 3 pairs | 6 | 3 | 8.3 | 3 | +33* | +32* | +0.05 pt* |
| Hub at CM_1 | 6 | 5 | 16.7 | 2 | +65* | +63* | +0.12 pt* |
| Hub at CM_3 | 6 | 5 | 50.0 | 2 | **+224*** | **+219*** | +0.40 pt* |
| All firms (reference) | 36 | 30 | 160 | 13 | +686* | +663* | +1.05 pt* |

"Parts per product" is the share of each product's 160 parts that the linked suppliers provide (each part type has three suppliers). Profit per part covered is about $4M for every arm (33/8.3, 65/16.7, 224/50, 686/160), so volume explains the results. The hub shape itself adds nothing.

## What this means

- **Research finding (with placeholder values):** for a technology that needs *partners* (blockchain), any link works, and value follows the volume linked. For a technology that needs *chain coverage* (control tower), the shape matters. Chains beat pairs, and where the chain sits decides whether it saves money every day (upstream) or protects customers in a crisis (downstream).
- **Teaching:** the scattered arms make a sharp classroom point. Six firms, same spend, zero benefit.
- **For agents (E4/E5):** in E2 (calm, normal growth), the payback-rule agents adopted control tower about 14 times per run, always inside groups, mostly stores (7.1) and DCs (3.3), with few component makers (1.2). That is a downstream-leaning pattern, which E3 suggests pays least in calm conditions. A good next question is whether different decision rules, or LLM agents, form upstream chains when that pays more.
- **Caveats:**
  - The arms differ in which firms are in them, not only in shape. For example, the downstream chain includes the biggest-volume DC, and pairs cover different DCs.
  - The group bonus and all effect sizes are placeholders.
  - Only six-firm structures were tested.

## Settings

- Seeds 1–30; 156 weeks; policy none (forced adoption only); normal demand growth.
- Disruption: CM_3, weeks 30–41, 20% output, +14 days.
- 95% ranges use t = 2.045 for 30 paired seeds.
