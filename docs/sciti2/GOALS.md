# SCITI goals and completion criteria

**Set by Kevin, 2026-09-25.** Read with STATUS.md §0.

## Goal A (now): a research paper on how informed AI agents adopt supply chain technology, alone and in groups, versus a payback rule

**The model is frozen at tag `v1.4`.** No engine, catalog, brief, prompt or rule change until the criteria below are met and the paper's results are written up. A change needs a new guesses page *and* Kevin's explicit decision to unfreeze.

Completion criteria (from the 2026-09-20 engineering review, applied to v1.4):

| # | Criterion | Status 2026-09-25 |
|---|---|---|
| A1 | Model frozen at one tag; every reported number made at that tag | `v1.4` frozen today; headline tables `*_current.csv` are on v1.4 |
| A2 | Headline results confirmed on held-out seeds | **Done for v1.4, 2026-09-25:** seeds 61–90, 15 of 15 numbers inside their intervals, ranking holds (`holdout-seeds-61-90.md`) |
| A3 | Key sources read by a human | Done: ten sources read by Kevin, 2026-09-24 |
| A4 | LLM-agent claims rest on more than one seed, at the frozen tag | Pages 1 and 5 used 5 seeds on v1.0 and v1.3; **to do: one pre-registered LLM run on v1.4** (5 seeds × calm and CM_3 hit, ~$35–40) |
| A5 | Every result the paper quotes has a results CSV stamped with the commit, and its write-up names the guesses page it came from | Mostly in place since 2026-09-20; check when the paper draft is assembled |

Done = A1–A5 all met. Then: results write-up → paper draft.

## Goal B (later): teaching — a workshop run of the replay view

Done when the view has been used once with students on a v1.4 run. Nothing to do until A is done.

## Goal C (later): companies — one scenario built for a real firm's question

Done when one company has brought a question and received a run and a write-up. The one-pager (`docs/outreach/`) is ready. Nothing to do until A is done.
