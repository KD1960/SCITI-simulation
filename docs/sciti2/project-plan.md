# Project Plan — Making the SCITI Simulator a Standing Part of SCITI

**Owner:** Kevin Dooley, W. P. Carey School of Business, ASU
**Date:** 2026-09-14
**Starting point:** SCITI 1 MVP is built, reviewed, and merged to `main` (168 tests pass). Mumbai/Tokyo demand bug fixed. Technology parameters are placeholders. No paid LLM run yet.
**Horizon:** 2026-09-14 to 2027-05-28 (about 37 weeks)

---

## 1. Goal

Turn SCITI 1 from a working prototype into a **trusted, reusable SCITI asset** that (a) produces credible research on how technology adoption — and who adopts together — changes supply chain profit, service, and CO2, and (b) is used routinely in SCITI teaching and executive education.

## 2. Objectives

| # | Objective | Measure of success | Due |
|---|---|---|---|
| O1 | **Stable, trusted engine** | Per-shipment random draws in place; paired profit-difference SD under one third of baseline SD; the three pilot anomalies explained and closed | 2026-10-09 |
| O2 | **Correct case data** | Data corrections report sent to the Ridge Line case authors; their answers folded into `sciti prepare`; revised validation report with zero unexplained fallbacks | 2026-10-30 |
| O3 | **Teaching-ready** | 3 classroom presets, a 1-page instructor guide, the infographic, and one live demo in the Oct 2026 SCM & AI workshop (date to confirm) | Workshop date |
| O4 | **Evidence-based technology catalog** | All 8 technologies have a cited cost and effect range (source + `assumption: false` or a stated range); catalog version 2 committed | 2026-12-11 |
| O5 | **First research results** | Experiments E1–E4 complete at 30 seeds with 95% CIs; one internal results brief | 2027-02-12 |
| O6 | **LLM agents validated** | Approved-budget LLM pilot run, replayed exactly; LLM vs. rules comparison written up | 2027-01-22 |
| O7 | **Dissemination** | Working paper draft on "who innovates with whom"; replay view available to SCITI partners/students; SCITI 2 scope agreed | 2027-05-28 |

## 3. Scope

**In:** the Ridge Line network; the 8 current technologies; research batches; the replay view; teaching materials; links to other SCITI projects where they add evidence.

**Out (for now):** the other 40 Observatory technologies; new networks or industries; a hosted public web app; learning (reinforcement-learning) agents. These are candidates for SCITI 2 (Phase 5).

## 4. Phases and schedule

### Phase 1 — Stabilize (Sep 14 – Oct 9, 2026 · 4 weeks)

| Week of | Work |
|---|---|
| Sep 14 | ✓ Branch merged; ✓ Mumbai/Tokyo demand fix. Send data corrections report to case authors. |
| Sep 21 | Per-shipment random draws (test first). Rerun 10-seed paired check. |
| Sep 28 | Investigate the pilot anomalies: ML forecasting and control tower lower profit; risk intelligence recovers ~100% of a disruption; CO2 about 50 t per product. |
| Oct 5 | Fixes reviewed; STATUS.md updated. **Milestone M1: engine trusted.** |

### Phase 2 — Teach (Oct 5 – Oct 30, 2026 · 4 weeks, overlaps Phase 1)

| Week of | Work |
|---|---|
| Oct 5 | Pick 3 classroom presets: (1) calm chain, no tech; (2) Shanghai control tower + glass disruption; (3) elastomer (CM_Mexico) disruption with and without risk intelligence. |
| Oct 12 | Instructor guide (1 page): what to watch on the map, 5 discussion questions, how to read the dashboard. Dry run with a colleague. |
| Oct 19 | Live demo at the SCM & AI workshop (confirm date). Collect participant feedback. |
| Oct 26 | Fold in case-author answers; re-run `sciti prepare`. **Milestone M2: teaching-ready, data corrected.** |

### Phase 3 — Evidence (Oct 26 – Dec 11, 2026 · 7 weeks)

| Week of | Work |
|---|---|
| Oct 26 | Run E1 (one-technology screen, 30 seeds). |
| Nov 2 | Literature and practitioner evidence for costs and effects of the 8 technologies; start from the SC Innovation Observatory lexicon entries they came from. |
| Nov 16 | Catalog v2 with cited ranges; mark any value still assumed. |
| Nov 30 | Re-run E1 on catalog v2; compare with v1. Sensitivity: low / mid / high effect per technology. |
| Dec 7 | **Milestone M3: catalog v2 committed.** |

### Phase 4 — Research (Dec 7, 2026 – Feb 12, 2027 · 10 weeks, winter break included)

| Week of | Work |
|---|---|
| Dec 7 | E2 stress scenarios (half-fraction first). |
| Jan 4 | E3 "who with whom" structures for control tower and blockchain. |
| Jan 11 | E5 LLM pilot: set prices, estimate, **get approval**, run 1 seed, replay exactly. **Milestone M4.** |
| Jan 18 | E4 decision-rule sweeps; LLM vs. rules comparison on 5 seeds (with approval). |
| Feb 8 | Internal results brief. **Milestone M5: first results.** |

### Phase 5 — Share and plan SCITI 2 (Feb 15 – May 28, 2027 · 15 weeks)

| Week of | Work |
|---|---|
| Feb 15 | Working paper outline; figures from E1–E4. |
| Mar 15 | Draft paper; replication package (configs, seeds, `results.csv`, replay logs). |
| Apr 12 | Package the replay view for SCITI partners and students (static bundle of chosen runs). |
| May 3 | SCITI 2 scoping: more technologies, a second network, calibration of adoption to disclosed-adoption data. |
| May 24 | **Milestone M6: paper draft + SCITI 2 scope agreed.** |

## 5. How it connects to the rest of SCITI

| SCITI project | Link |
|---|---|
| SC Innovation Observatory | Source of the technology lexicon. Its Disclosed Adoption Index could later calibrate how fast agents adopt each technology (E4). |
| SCDAI (disruption attention) | Real disruption types and timing could seed the disruption scenarios in E2. |
| SCM & AI workshop / exec ed | Uses the Ridge Line case already; the simulator gives it a live, visual "what if" layer. |

These are proposed links, not commitments. Each needs its own check that the data fit.

## 6. Resources and budget

- **People:** Kevin (lead, ~3–4 hrs/week); Claude Code for build and analysis sessions; optional student RA in Phase 3 for the evidence review.
- **Compute:** a laptop is enough. A 30-seed batch takes about 90 seconds.
- **LLM spend:** pilot capped at the config limit (`max_spend_usd`, now $10); total for the plan suggested under $100, each run approved in advance.
- **Other:** none required.

## 7. Risks

| Risk | Effect | Response |
|---|---|---|
| Case authors slow to reply | Data stays uncertain | Keep the current documented fixes; label them in outputs |
| No good evidence for some effect sizes | Catalog stays partly assumed | Use ranges and sensitivity runs; say so plainly |
| Pilot anomalies are real model problems | Results delayed | Phase 1 is sized for this; do not skip M1 |
| LLM agents behave oddly or cost more | Weak E5 | Rules fallback, spend caps, exact replay; keep LLM as a comparison, not the only engine |
| Classroom view too detailed for novices | Weak teaching use | Presets + instructor guide; test with a colleague first |

## 8. Governance

- `STATUS.md` stays the single handoff file; update at each milestone.
- Standing rules still apply: stage files by name, tests never call the API, ask before paid runs or downloads, don't loosen test thresholds without Kevin.
- Milestone review with Kevin at M1–M6.

## 9. Decisions needed from Kevin now

1. Confirm the October workshop date for the demo.
2. Approve sending the data corrections report to the case authors (and who they are).
