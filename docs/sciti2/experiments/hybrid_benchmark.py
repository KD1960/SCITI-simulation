"""Hybrid benchmark: payback rule plus an insurance habit (STATUS.md, 2026-09-18, Kevin's option C).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/hybrid_benchmark.py OUT_DIR

Arms (all agents on the payback rule; suppliers follow partners in every arm but the first):
  rules          plain payback rule
  follow         rules_roles = [Supplier]
  hybrid         follow + insurance_techs = [risk_intel, aps]
  hybrid_robot   follow + insurance_techs = [risk_intel, aps, wh_robotics]
Scenarios: calm, and CM_3 at 20% capacity for 12 weeks from week 30. Seeds 1-30, 156 weeks, each
paired with a same-seed, same-scenario no-tech run. Writes OUT_DIR/hybrid.csv and prints it.
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, DecisionCfg, Disruption

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
SCENARIOS = {"calm": [], "cm3_12w": [Disruption(target="CM_3", start_week=30, weeks=12, capacity_mult=0.2)]}
ARMS = {"none": DecisionCfg(),
        "rules": DecisionCfg(policy="rules"),
        "follow": DecisionCfg(policy="rules", rules_roles=["Supplier"]),
        "hybrid": DecisionCfg(policy="rules", rules_roles=["Supplier"], insurance_techs=["risk_intel", "aps"]),
        "hybrid_robot": DecisionCfg(policy="rules", rules_roles=["Supplier"],
                                    insurance_techs=["risk_intel", "aps", "wh_robotics"])}
COLS = ["network_profit_with_inventory", "satisfaction_index", "fill_rate", "retail_on_time_rate", "costs_stockout",
        "costs_tech", "adoptions", "coalitions"]


def _run(args):
    name, scen, arm, out = args
    cfg = Config(name=name, seed=1, weeks=156, output_dir=str(out), decision=ARMS[arm], disruptions=SCENARIOS[scen])
    d = pd.read_csv(run_batch(cfg, SEEDS, out / name) / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {name}: {d.error.dropna().unique()}")
    return name, d.set_index("seed")[COLS]


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(f"{scen}__{arm}", scen, arm, out) for scen in SCENARIOS for arm in ARMS]
    with ProcessPoolExecutor(max_workers=7) as pool:
        res = dict(pool.map(_run, jobs))
    rows = []
    for scen in SCENARIOS:
        for arm in ARMS:
            if arm == "none":
                continue
            diff = res[f"{scen}__{arm}"] - res[f"{scen}__none"]
            for c in COLS:
                half = T_975_DF29 * diff[c].std(ddof=1) / np.sqrt(len(diff))
                rows.append({"scenario": scen, "arm": arm, "measure": c, "mean": diff[c].mean(),
                             "ci_low": diff[c].mean() - half, "ci_high": diff[c].mean() + half})
    table = pd.DataFrame(rows)
    table.to_csv(out / "hybrid.csv", index=False)
    print(table.to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
