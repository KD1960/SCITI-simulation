# Citation log

`citations.csv` is the running log of every source found while calibrating SCITI's parameters. It exists so that any parameter value can be traced to its evidence, and so a later reader can see how strong that evidence is. Open it in Excel.

**Rule (Kevin, 2026-09-19): whenever research turns up a source that bears on a parameter, add a row here in the same piece of work, whether or not the parameter is changed.**

## Columns

| Column | Meaning |
|---|---|
| `id` | C001, C002, … Never reuse or renumber; append new rows at the end. |
| `date_added` | When the source entered the log. |
| `technology` | Catalog id (`blockchain`, `routing`, `rfid`, `wh_robotics`, `control_tower`, `ml_forecast`, `aps`, `risk_intel`), `all` for general anchors, `disruptions` for base rates. |
| `topic` | `effect size`, `implementation failure`, `disruption base rates`, `cost` (none logged yet). |
| `parameter` | The model parameter(s) the source bears on. |
| `citation`, `year`, `url` | The source. |
| `finding` | What it measured and the number, in one or two sentences. |
| `quality_flag` | PR peer-reviewed · IND industry/analyst survey · VND vendor · ANEC single case (with qualifiers). |
| `read_level` | `page or full text`, `snippet/abstract`, or `not recorded` (the 2026-09-17 round did not record this consistently). Check the full text before citing a `snippet/abstract` or `not recorded` row in a paper. |
| `role` | How it was used: LOW / MID / HIGH anchor, form of the effect, base rate, general prior, or `context`. |
| `informs_value` | The parameter value or range the evidence for this technology led to (the same for every row of a technology and topic). |
| `source_doc` | The write-up that discusses it. |

## What is and is not here

- Backfilled on 2026-09-19 from `evidence-table.md`, `risk-intel-evidence-and-sensitivity.md`, and `implementation-failure-evidence.md` by `build_backfill.py` (a one-off; do not rerun it over an edited CSV).
- **Not yet logged:** the cost evidence in `evidence-table.md` (it is in prose there), and sources the research helpers reported that did not make it into the write-ups.
- Numbers traced and found to have **no real source** are listed in `implementation-failure-evidence.md` §2 ("Do not cite"); they are deliberately not in the log.
