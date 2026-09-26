# Acting on visible risk: how AI agents adopt supply chain technology, alone and together, compared with a payback rule

**Working paper draft 1 — 2026-09-26.** Kevin Dooley (W. P. Carey School of Business, Arizona State University). Model, code and every result table: github.com/KD1960/SCITI-simulation, tag `v1.5`. All numbers in this draft come from `docs/sciti2/results-writeup-v1.5.md`, which names the stamped CSV behind each one.

## Abstract

Firms are being asked to let AI systems make supply chain decisions, but there is little evidence about what AI decision-makers actually do when the choice is whether, when and with whom to adopt supply chain technology. We build an agent-based simulation of a 48-firm global supply chain in which every firm is an agent that may adopt one of eight technologies each quarter, alone or in a group with partners, under implementation risk calibrated to a 245-source evidence base. We compare three decision policies on identical random draws: large-language-model agents (Claude Sonnet 5) that read a briefing and reply with logged, exactly replayable decisions; a transparent payback rule; and a hybrid rule that adds an insurance habit. In pre-registered runs on the frozen model, LLM agents out-earn both rules by about $100M over three years (of a ~$34B network) in calm conditions and in a twelve-week component-maker outage, ahead in nine of ten seed-scenario pairs, with higher fill rates. The mechanism is not cleverness about any single technology but a difference in stance: LLM agents act on visible risk (they buy protection in the first quarter, form tier-adjacent groups, and keep adopting through cancelled pilots), whereas the rules wait for a shock or a payback that never arrives. The same runs show what informed agents give up: about a fifth of their attempts are cancelled pilots. We discuss what this implies for firms deciding how much to let AI decide, and release the simulator as a sandbox for that question.

## 1. Introduction

The question a supply chain executive asks about AI is rarely "can it forecast better?" It is "what will it decide, and would I have decided the same?" Technology adoption is the sharpest version of that question: it is lumpy, uncertain, often joint with partners, and its returns depend on events (disruptions) that may not happen during the payback period. Rules of thumb such as payback thresholds handle the easy cases and systematically miss protective technologies whose value is an option on a bad year.

We ask how AI agents choose in this setting when they are given the same information a manager would have, including the odds that a project fails, and we compare them with explicit rules on the same randomness. Our thesis is that **informed AI agents out-adopt and out-protect a payback rule, and the edge comes from acting on visible risk rather than waiting for it.** The contribution is threefold: a calibrated simulator in which every decision is logged and every run replays exactly; a pre-registered comparison of LLM agents with two rule benchmarks; and a set of structural results about who should adopt with whom.

## 2. The simulator

**Network.** The Ridge Line case supply chain: 30 suppliers, 4 component makers (CMs) in Taipei, Bangalore, Guadalajara and Munich, factories in Los Angeles and Shenzhen, distribution centres in Houston, Dubai, Sofia and Shanghai, and eight retail regions from Columbus to Melbourne. Demand for three products is drawn from the case's five-year history with growth and autocorrelated noise; lanes carry multimodal lead-time and cost draws; supplier shipments carry random defect shares. The engine steps weekly for 156 weeks and tracks stock, cash, orders, fill rate, on-time delivery, quality, bullwhip and CO₂ for every firm. Network profit is measured with inventory valued at a single network-wide cost basis, so that technologies that move stock between firms are not rewarded for the move.

**Technologies.** Eight from a 48-item technology lexicon: ML demand forecasting, control towers, item-level RFID, advanced planning (APS), routing/TMS, warehouse robotics, blockchain traceability and risk intelligence. Each acts on a named engine parameter (forecast skill, visibility weight, record-error and shrink multipliers, capacity, freight cost, handling cost and dispatch delay, defect share, weeks of outage saved). Effect sizes are the MID values of an evidence table built from 96 effect-size sources; three (APS, blockchain, risk intelligence) have no measured effect and are flagged as assumptions. Costs are evidence-based for the four technologies where cost changes any answer and placeholders inside their ranges for the rest; every cost is 0.01–0.1% of a firm's revenue, which is why costs do not rank technologies here.

**Implementation risk.** An adoption attempt draws one of four outcomes with technology-specific odds: cancelled in pilot (the firm pays 40% of the one-time cost and may retry after 26 weeks), failed after deployment (full cost, running cost until abandoned), partial (a share of the effect), or full. Blockchain's odds are measured (about 55% cancelled, 10% deployed-then-failed); the others rest on failure evidence for AI pilots, ERP-class systems and automation. Group projects draw once for all members, and their odds of getting nothing rise ×1.4 per doubling of members, so a 48-firm consortium project gets nothing about 60% of the time where a pair gets nothing 25% of the time. Groups span only a tier and its neighbours. A firm gets two attempts at any technology. Firms learn: retries, technologies already running, partners already running the technology, and the network's visible record of outcomes all move the odds or the expected saving.

**Decision policies.** Every quarter each firm receives a briefing (its persona, budget, last quarter's costs, partners and their technologies, eligible technologies with costs, effects and odds, proposals from partners, recent shocks, and the network's outcome record) and returns decisions: adopt, propose a group, accept or decline an invitation, drop. Three policies: (i) **LLM agents**, one API call per firm-quarter to Claude Sonnet 5 with a structured-output schema; the 30 suppliers use the payback rule and follow partners into cheap groups, so 18 firms are LLM-driven; (ii) the **payback rule**, which adopts when expected savings (discounted by the odds shown) repay the one-time cost within the persona's horizon; (iii) the **hybrid rule**, the payback rule plus an insurance habit that buys risk intelligence and APS after a shock with a hazard that decays over 26-week half-lives. Every LLM reply is logged with its briefing hash; a replay re-runs the simulation from the log and must reproduce every output byte for byte, which it has done in all 34 paid runs.

**Method discipline.** The model changed in eight pre-registered steps from its first version; each step had a "guesses page" signed by the author before the run, with pass/fail lines, and a scorecard after (25 of 46 guesses were right). The final model was frozen at tag v1.5; its headline tables were confirmed on thirty held-out seeds (15 of 15 numbers inside their intervals). Every results table carries the commit that made it.

## 3. Results

### 3.1 What each technology is worth on its own

Table 1 (write-up §2): with every eligible firm forced to adopt, routing is the one large calm-conditions gain (+$299M over three years, and a 148,000-tonne CO₂ cut); warehouse robotics is the only clear service gain (+0.14 fill points); RFID earns +$50M. The information technologies (control tower, ML forecasting) cut upstream bullwhip by a quarter but earn little in calm; risk intelligence is pure cost until something goes wrong. With realistic random disruptions (Table 2, write-up §3; no-tech loss −$2.4B), protection pays: risk intelligence on ten firms recovers 16% of the loss for $8M, and the hybrid rule recovers a quarter.

### 3.2 Who should adopt with whom

Table 6 (write-up §7): scattered adopters of a network technology earn nothing (−$4M); a six-firm downstream control tower chain recovers +$47M in a twelve-week CM outage, as much as all 48 firms adopting together, because the whole-network project usually fails; blockchain's value follows the volume of parts covered, and the best hub is the site that gets hit. Structure matters most in disruptions and hardly at all in calm.

### 3.3 What the rules do

The payback rule's gain is scenario-blind: about +$260–280M whether or not a hit occurs, because it never buys protection (write-up §4, §5). Its outcome is moved by how many adoptions it may make per quarter and by its horizon, not by its budget. The hybrid rule fixes protection only where shocks repeat: it recovers a quarter of the random-disruption loss but has no edge in a single mid-horizon hit, because its habit waits for a shock.

### 3.4 LLM agents against the rules

Table 5 (write-up §6), five seeds, pre-registered: LLM agents earn +$315M in calm and +$315M in the CM_3 outage, against +$212M / +$208M for the payback rule with followers and +$221M / +$203M for the hybrid; ahead of the rule in 4 of 5 calm seeds and 5 of 5 hit seeds, with fill rates 0.02–0.30 points above no-tech. What they did differently: they bought risk intelligence in the first quarter in 8 of 10 runs, while the rules waited; they formed 10–17 groups per run, all tier-adjacent, the biggest 13 members, and never proposed a whole-network project once the model refused them; they adopted 76–102 times among 18 firms across every technology and kept adopting through cancelled pilots (14–28% of their attempts) and deployed failures (0–9%).

### 3.5 Where the edge comes from, and what it cost to learn that

Across model versions the LLM agents' behaviour was stable — buy protection early, join groups, adopt broadly — while their edge over the rules moved with the rules' assumptions: when a supplier's seat in a control tower was priced at $150k the rules formed no chains and the agents' edge was chains; when the price fell to $25k the rules joined chains too and the calm edge vanished; when protection habits were made to wait for shocks the edge returned in both scenarios. One pre-registered arm (page 2) showed that hiding the failure odds from the agents moved their protection purchase from week 66 back to week 1 at the old prices; at evidence-based prices they buy in week 1 with the odds shown. The consistent reading is that the agents act on visible risk at almost any price the evidence supports, and the rules act on realised losses.

## 4. Discussion

**For managers.** An AI agent given a manager's briefing does not behave like a payback rule with better arithmetic; it behaves like a cautious owner who buys insurance early and tries things. On these seeds that stance earned about $100M more over three years on a $34B network, and better service. It also wasted about a fifth of its projects. Whether that trade is right for a given firm depends on how often its chain is hit and how it accounts for cancelled pilots — both are inputs this sandbox lets a firm set.

**For research.** Three findings do not depend on the agents at all and hold across every model version: scattered adoption of network technologies is worthless; connected chains earn most, and mostly in disruptions; protection technologies are options whose value is set by the disruption rate, so calm-conditions screens undervalue them. The agent finding — that the edge lies in stance, not in technology selection — is the one most worth replicating with other models and prompts.

**Limits.** One supply chain; five seeds for the paid arm; one model family; effect sizes with uneven evidence (three technologies rest on assumptions; the depth exponent, the group-size multiplier and every learning magnitude are judgment, flagged); no strategic behaviour by the disruption; agents cannot renegotiate cost splits or leave groups; the "store" is a whole retail region. The LLM agents saw odds and costs the real world only approximates.

## 5. Next

Teaching use of the replay view; a company-supplied scenario; a second model family on the same pre-registered design.

## References

To be assembled from `docs/sciti2/citations/citations.csv` (245 rows) and the evidence documents listed in STATUS §0.
