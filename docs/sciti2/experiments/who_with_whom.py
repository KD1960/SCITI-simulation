"""E3 who-with-whom experiment (docs/sciti2/experiments-recommendation.md, E3).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/who_with_whom.py OUT_DIR

Same technology, same number of adopting firms (6), different structures, plus an all-firms
reference. Control tower (effect grows with the share of a firm's downstream partners that
adopt) and blockchain (works only when a linked partner also adopts). Two conditions: calm, and
CM_3 at 20% output with +14 days for 12 weeks from week 30. Policy none, seeds 1-30, 156 weeks.
Each forced-adoption entry forms its own group and gets the +25% group bonus.

Writes OUT_DIR/who_with_whom.csv: each arm minus the no-tech arm in the same condition
(mean paired difference and 95% CI).
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, Disruption, ForcedAdoption
from sciti.network import build_network
from sciti.tech.catalog import load_catalog

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
COLS = ["network_profit", "satisfaction_index", "fill_rate", "retail_on_time_rate", "quality_mean", "costs_tech",
        "costs_stockout", "costs_holding", "costs_scrap", "bullwhip_DC", "bullwhip_MFG", "bullwhip_CM"]
CONDITIONS = {"calm": [], "cm3_12w": [Disruption(target="CM_3", start_week=30, weeks=12, capacity_mult=0.2,
                                                   extra_lead_days=14.0)]}
# Each arm is a list of groups; each group is one forced-adoption entry.
ARMS = {
    "ct_scattered": ("control_tower", [["CM_1"], ["DC_Houston"], ["Retail_3"], ["Retail_8"], ["Supplier_10"],
                                       ["Supplier_20"]]),
    "ct_dyads": ("control_tower", [["DC_Houston", "Retail_1"], ["DC_Sofia", "Retail_3"], ["DC_Dubai", "Retail_4"]]),
    "ct_downstream_chain": ("control_tower", [["MFG_China", "DC_Shanghai", "Retail_5", "Retail_6", "Retail_7",
                                              "Retail_8"]]),
    "ct_upstream_chain": ("control_tower", [["CM_1", "CM_2", "CM_3", "CM_4", "MFG_China", "DC_Shanghai"]]),
    "bc_scattered": ("blockchain", [["Supplier_1"], ["Supplier_7"], ["Supplier_13"], ["Supplier_19"],
                                    ["Supplier_25"], ["Supplier_28"]]),
    "bc_dyads": ("blockchain", [["Supplier_1", "CM_1"], ["Supplier_7", "CM_2"], ["Supplier_25", "CM_4"]]),
    "bc_hub_cm3": ("blockchain", [["CM_3", "Supplier_13", "Supplier_16", "Supplier_19", "Supplier_20",
                                   "Supplier_22"]]),
    "bc_hub_cm1": ("blockchain", [["CM_1", "Supplier_1", "Supplier_2", "Supplier_3", "Supplier_4", "Supplier_5"]]),
}


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
    arms = dict(ARMS)
    for tech, short in (("control_tower", "ct"), ("blockchain", "bc")):
        arms[f"{short}_all"] = (tech, [[n for n in net.order if net.nodes[n].role in catalog[tech].eligible_roles]])
    jobs = []
    for cond, disruptions in CONDITIONS.items():
        base = Config(name=f"{cond}__none", seed=1, weeks=156, output_dir=str(out), disruptions=disruptions)
        jobs.append((base.name, base, out))
        for arm, (tech, groups) in arms.items():
            c = base.model_copy(update={"name": f"{cond}__{arm}"}, deep=True)
            c.forced_adoptions = [ForcedAdoption(week=1, tech=tech, members=g) for g in groups]
            jobs.append((c.name, c, out))
    with ProcessPoolExecutor(max_workers=7) as pool:
        dirs = dict(pool.map(_run, jobs))
    rows = []
    for cond in CONDITIONS:
        none = load(dirs[f"{cond}__none"])
        for arm, (tech, groups) in arms.items():
            diff = load(dirs[f"{cond}__{arm}"]) - none
            for c in COLS:
                half = T_975_DF29 * diff[c].std(ddof=1) / np.sqrt(len(diff))
                rows.append({"condition": cond, "arm": arm, "tech": tech, "firms": sum(len(g) for g in groups),
                             "groups": len(groups), "measure": c, "mean": diff[c].mean(),
                             "ci_low": diff[c].mean() - half, "ci_high": diff[c].mean() + half})
    table = pd.DataFrame(rows)
    table.to_csv(out / "who_with_whom.csv", index=False)
    print(f"wrote {out / 'who_with_whom.csv'}: {len(table)} rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
