"""Free same-seed arms for the pre-registered paid LLM run (docs/sciti2/prereg-llm-run-implementation-risk.md).

Seeds 1-5, calm and the CM_3 12-week hit: no tech; payback rule with suppliers following at
collaboration 0.25 / 0.5 / 0.75; hybrid (insurance habit: risk intelligence, APS) at 0.5.
One row per run, so the paid runs can be compared seed by seed.

    .venv/bin/python docs/sciti2/experiments/prereg_free_arms.py OUT_DIR
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from sciti.batch import provenance, run_batch
from sciti.config import Assumptions, Config, DecisionCfg, Disruption

SEEDS = [1, 2, 3, 4, 5]
SCENARIOS = {"calm": [], "cm3_12w": [Disruption(target="CM_3", start_week=30, weeks=12, capacity_mult=0.2)]}
FOLLOW = dict(policy="rules", rules_roles=["Supplier"])
ARMS = {"none": (DecisionCfg(), 0.5),
        "follow_c0.25": (DecisionCfg(**FOLLOW), 0.25),
        "follow_c0.5": (DecisionCfg(**FOLLOW), 0.5),
        "follow_c0.75": (DecisionCfg(**FOLLOW), 0.75),
        "hybrid_c0.5": (DecisionCfg(**FOLLOW, insurance_techs=["risk_intel", "aps"]), 0.5)}
COLS = ["network_profit_with_inventory", "fill_rate", "satisfaction_index", "costs_stockout", "costs_tech",
        "adoptions", "coalitions"]


def main(out: Path) -> None:
    rows = []
    for scen, disruptions in SCENARIOS.items():
        for arm, (decision, collaboration) in ARMS.items():
            cfg = Config(name=f"{scen}__{arm}", seed=1, weeks=156, output_dir=str(out), decision=decision,
                         disruptions=disruptions, assumptions=Assumptions(collaboration=collaboration))
            d = pd.read_csv(run_batch(cfg, SEEDS, out / cfg.name, keep_runs=False) / "results.csv")
            if not (d.status == "ok").all():
                raise SystemExit(f"failed runs in {cfg.name}: {d.error.dropna().unique()}")
            rows.append(d[["seed"] + COLS].assign(scenario=scen, arm=arm))
    runs = pd.concat(rows, ignore_index=True)
    base = runs[runs.arm == "none"].set_index(["scenario", "seed"]).network_profit_with_inventory
    runs["gain_musd"] = (runs.network_profit_with_inventory
                         - base.reindex(list(zip(runs.scenario, runs.seed))).to_numpy()) / 1e6
    runs.assign(**provenance()).to_csv(out / "prereg_free_arms.csv", index=False)
    print(runs.pivot_table(index=["scenario", "arm"], values=["gain_musd", "coalitions", "adoptions"]).round(1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
