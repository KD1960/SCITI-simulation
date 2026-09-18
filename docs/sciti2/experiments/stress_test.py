"""E2 stress test (docs/sciti2/experiments-recommendation.md, E2).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/stress_test.py OUT_DIR

Scenarios: demand growth multiplier (0.5, 1, 1.5) x disruption (none; CM_3, CM_4, or DC_Shanghai
for 4 or 12 weeks from week 30). A disruption cuts the site's capacity to 20% (DCs have no
capacity limit in the model, so for DC_Shanghai only the delay applies) and adds 14 days to its
outgoing shipments. Arms per scenario: no tech, risk intelligence (all eligible firms), control
tower (all 48), APS (all eligible), and agents deciding with the payback rule. Seeds 1-30, 156 weeks.

Writes OUT_DIR/stress.csv with two comparisons, as mean difference and 95% CI over paired seeds:
  scenario_vs_calm: no-tech arm in the scenario minus no-tech calm (growth 1, no disruption)
  tech_vs_none:     each tech arm minus the no-tech arm in the same scenario
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, DecisionCfg, DemandCfg, Disruption, ForcedAdoption
from sciti.network import build_network
from sciti.tech.catalog import load_catalog

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
GROWTH = (0.5, 1.0, 1.5)
SITES = ("CM_3", "CM_4", "DC_Shanghai")
LENGTHS = (4, 12)
FORCED_TECHS = ("risk_intel", "control_tower", "aps")
COLS = ["network_profit", "network_profit_with_inventory", "satisfaction_index", "fill_rate", "retail_on_time_rate", "costs_stockout",
        "costs_holding", "costs_tech", "co2_kg", "adoptions", "bullwhip_DC", "bullwhip_MFG", "bullwhip_CM"]


def scenarios():
    for g in GROWTH:
        yield f"g{g}_calm", g, []
        for site in SITES:
            for weeks in LENGTHS:
                yield f"g{g}_{site}_{weeks}w", g, [Disruption(target=site, start_week=30, weeks=weeks,
                                                               capacity_mult=0.2, extra_lead_days=14.0)]


def _run(job):
    name, cfg, out = job
    return name, run_batch(cfg, SEEDS, out / name)


def load(batch_dir: Path) -> pd.DataFrame:
    d = pd.read_csv(batch_dir / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {batch_dir}: {d.error.dropna().unique()}")
    return d.set_index("seed")[COLS]


def main(out: Path) -> None:
    probe = Config(name="probe", seed=1)
    net = build_network(json.loads(Path(probe.baseline_path).read_text()), probe.assumptions)
    catalog = load_catalog()
    members = {t: [n for n in net.order if net.nodes[n].role in catalog[t].eligible_roles] for t in FORCED_TECHS}
    jobs = []
    for scen, g, disruptions in scenarios():
        base = Config(name=f"{scen}__none", seed=1, weeks=156, output_dir=str(out),
                      demand=DemandCfg(growth_mult=g), disruptions=disruptions)
        jobs.append((base.name, base, out))
        for t in FORCED_TECHS:
            c = base.model_copy(update={"name": f"{scen}__{t}"}, deep=True)
            c.forced_adoptions = [ForcedAdoption(week=1, tech=t, members=members[t])]
            jobs.append((c.name, c, out))
        c = base.model_copy(update={"name": f"{scen}__rules", "decision": DecisionCfg(policy="rules")}, deep=True)
        jobs.append((c.name, c, out))
    with ProcessPoolExecutor(max_workers=7) as pool:
        dirs = dict(pool.map(_run, jobs))
    data = {name: load(d) for name, d in dirs.items()}
    calm = data["g1.0_calm__none"]
    rows = []

    def add(comparison, scen, arm, diff):
        g, _, rest = scen.partition("_")
        for c in COLS:
            half = T_975_DF29 * diff[c].std(ddof=1) / np.sqrt(len(diff))
            rows.append({"comparison": comparison, "scenario": scen, "growth": float(g[1:]),
                         "disruption": rest, "arm": arm, "measure": c, "mean": diff[c].mean(),
                         "ci_low": diff[c].mean() - half, "ci_high": diff[c].mean() + half})

    for scen, _, _ in scenarios():
        none = data[f"{scen}__none"]
        add("scenario_vs_calm", scen, "none", none - calm)
        for arm in FORCED_TECHS + ("rules",):
            add("tech_vs_none", scen, arm, data[f"{scen}__{arm}"] - none)
    table = pd.DataFrame(rows)
    table.to_csv(out / "stress.csv", index=False)
    print(f"wrote {out / 'stress.csv'}: {len(table)} rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
