"""Random-disruption experiment (STATUS.md, 2026-09-18, Kevin's option A).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/random_disruptions.py OUT_DIR

Each seed gets its own random disruption schedule, shared by every arm, built from the working
rule in docs/sciti2/evidence-table.md section 3 (assembled from BCI, MGI 2020, and Resilinc; not
a single primary source):
  - every supplier, CM, factory, and DC draws Poisson(RATE x 3 years) disruptions; RATE is the
    chance of a disruption per site-year, run at 0.2 and 0.4;
  - length: 65% 1-3 weeks, 27% 4-12 weeks, 8% 13-26 weeks (uniform inside each band);
  - start week uniform over the 156-week horizon;
  - severity as in E2: capacity to 20% and +14 days on outgoing shipments (DCs have no capacity
    limit in the model, so only the delay applies to them).
Arms: no tech; risk intelligence, APS, or control tower forced on every eligible firm in week 1;
payback-rule agents with suppliers following; the same plus the insurance habit (risk intel, APS);
the same plus robotics. Seeds 1-30, 156 weeks. Writes OUT_DIR/random_disruptions.csv
(paired mean difference vs the no-tech arm and 95% CI) and OUT_DIR/schedules.csv.
"""
import json
import sys
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.config import Config, DecisionCfg, Disruption, ForcedAdoption
from sciti.network import build_network
from sciti.runner import run
from sciti.tech.catalog import load_catalog

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
RATES = (0.2, 0.4)
YEARS, WEEKS = 3, 156
BANDS = ((0.65, 1, 3), (0.27, 4, 12), (0.08, 13, 26))
FORCED = ("risk_intel", "aps", "control_tower")
FOLLOW = dict(policy="rules", rules_roles=["Supplier"])
POLICIES = {"follow": DecisionCfg(**FOLLOW),
            "hybrid": DecisionCfg(**FOLLOW, insurance_techs=["risk_intel", "aps"]),
            "hybrid_robot": DecisionCfg(**FOLLOW, insurance_techs=["risk_intel", "aps", "wh_robotics"])}
MEASURES = ["network_profit_with_inventory", "fill_rate", "satisfaction_index", "retail_on_time_rate",
            "costs_stockout", "costs_tech", "adoptions"]


def schedule(seed: int, rate: float, sites: list[str]) -> list[Disruption]:
    rng = np.random.default_rng([seed, zlib.crc32(b"disruption-schedule"), int(rate * 1000)])
    out = []
    for site in sites:
        for _ in range(rng.poisson(rate * YEARS)):
            _, lo, hi = BANDS[rng.choice(len(BANDS), p=[b[0] for b in BANDS])]
            out.append(Disruption(target=site, start_week=int(rng.integers(1, WEEKS + 1)),
                                  weeks=int(rng.integers(lo, hi + 1)), capacity_mult=0.2, extra_lead_days=14.0))
    return out


def _run(job):
    rate, arm, seed, members, out = job
    cfg = Config(name=f"r{rate}_{arm}", seed=seed, weeks=WEEKS, output_dir=str(out),
                 decision=POLICIES.get(arm, DecisionCfg()), disruptions=schedule(seed, rate, members["sites"]))
    if arm in FORCED:
        cfg.forced_adoptions = [ForcedAdoption(week=1, tech=arm, members=members[arm])]
    s = json.loads((run(cfg, run_dir=out / f"r{rate}" / arm / f"s{seed}") / "summary.json").read_text())
    row = {m: s[m] for m in MEASURES if m in s}
    row.update(costs_stockout=s["costs"]["stockout"], costs_tech=s["costs"]["tech"], rate=rate, arm=arm, seed=seed)
    return row


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    base = Config(name="base", seed=1)
    net = build_network(json.loads(Path(base.baseline_path).read_text()), base.assumptions)
    members = {"sites": [n for n in net.order if net.nodes[n].role != "Retail"]}
    for tid in FORCED:
        members[tid] = [n for n in net.order if net.nodes[n].role in load_catalog()[tid].eligible_roles]
    sched = [{"rate": r, "seed": s, "target": d.target, "start_week": d.start_week, "weeks": d.weeks}
             for r in RATES for s in SEEDS for d in schedule(s, r, members["sites"])]
    pd.DataFrame(sched).to_csv(out / "schedules.csv", index=False)
    arms = ["none", *FORCED, *POLICIES]
    jobs = [(r, a, s, members, out) for r in (0.0, *RATES) for a in arms for s in SEEDS]
    with ProcessPoolExecutor(max_workers=7) as pool:
        runs = pd.DataFrame(list(pool.map(_run, jobs, chunksize=4)))
    runs.to_csv(out / "runs.csv", index=False)
    rows = []
    for r in (0.0, *RATES):
        none = runs[(runs.rate == r) & (runs.arm == "none")].set_index("seed")[MEASURES]
        calm = runs[(runs.rate == 0.0) & (runs.arm == "none")].set_index("seed")[MEASURES]
        for a in arms:
            d = runs[(runs.rate == r) & (runs.arm == a)].set_index("seed")[MEASURES] - (calm if a == "none" else none)
            for m in MEASURES:
                half = T_975_DF29 * d[m].std(ddof=1) / np.sqrt(len(d))
                rows.append({"rate": r, "arm": "none_vs_calm" if a == "none" else a, "measure": m, "mean": d[m].mean(),
                             "ci_low": d[m].mean() - half, "ci_high": d[m].mean() + half})
    table = pd.DataFrame(rows)
    table.to_csv(out / "random_disruptions.csv", index=False)
    print(table[table.measure == "network_profit_with_inventory"].to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
