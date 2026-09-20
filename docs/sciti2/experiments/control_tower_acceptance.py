"""Control tower acceptance experiment (spec 2026-09-14 §2, §6).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/control_tower_acceptance.py OUT_DIR

Runs a no-tech batch and three forced-control-tower arms (seeds 1-10, 156 weeks, policy none)
on data/baseline.json and prints paired differences (arm - same-seed no-tech) as
mean +/- 95% CI half-width, plus the four acceptance checks.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, ForcedAdoption
from sciti.network import build_network

SEEDS = list(range(1, 11))
T_975_DF9 = 2.262  # two-sided 95% t critical value for 10 paired seeds
COLS = ["bullwhip_DC", "bullwhip_MFG", "bullwhip_CM", "fill_rate", "satisfaction_index", "costs_holding",
        "network_profit", "revenue", "costs_purchases", "costs_cogs", "costs_shipping", "costs_stockout",
        "scrap_value", "costs_tech"]


def load(batch_dir: Path) -> pd.DataFrame:
    d = pd.read_csv(batch_dir / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {batch_dir}: {d.error.dropna().unique()}")
    return d.set_index("seed")[COLS]


def main(out: Path) -> None:
    base_cfg = Config(name="ct_base", seed=1, weeks=156, output_dir=str(out))
    net = build_network(json.loads(Path(base_cfg.baseline_path).read_text()), base_cfg.assumptions)
    arms = {
        "shanghai_chain": ["DC_Shanghai", "Retail_5", "Retail_6", "Retail_7", "Retail_8"],
        "downstream": net.by_role("DC") + net.by_role("Retail"),
        "whole_network": list(net.order),
    }
    base = load(run_batch(base_cfg, SEEDS, out / "base"))
    rows, diffs = [], {}
    for arm, members in arms.items():
        cfg = base_cfg.model_copy(update={"name": f"ct_{arm}"}, deep=True)
        cfg.forced_adoptions = [ForcedAdoption(week=1, tech="control_tower", members=members)]
        d = load(run_batch(cfg, SEEDS, out / arm, keep_runs=False)) - base
        diffs[arm] = d
        for c in COLS:
            half = T_975_DF9 * d[c].std(ddof=1) / np.sqrt(len(d))
            rows.append({"arm": arm, "measure": c, "mean": d[c].mean(), "ci_low": d[c].mean() - half,
                         "ci_high": d[c].mean() + half, "base_mean": base[c].mean()})
    table = pd.DataFrame(rows)
    print(table.to_string(float_format=lambda x: f"{x:.4g}"))

    w = table[table.arm == "whole_network"].set_index("measure")
    bullwhip_sum = {a: (diffs[a][["bullwhip_DC", "bullwhip_MFG", "bullwhip_CM"]].sum(axis=1)).mean() for a in arms}
    checks = {
        "1 bullwhip falls at DC, MFG, CM (whole network)":
            all(w.loc[c, "mean"] < 0 for c in ("bullwhip_DC", "bullwhip_MFG", "bullwhip_CM")),
        "2 fill rate CI upper bound >= 0 (whole network)": w.loc["fill_rate", "ci_high"] >= 0,
        "3 holding cost CI lower bound <= 0 (whole network)": w.loc["costs_holding", "ci_low"] <= 0,
        "4 bullwhip reduction grows: shanghai < downstream < whole":
            bullwhip_sum["shanghai_chain"] > bullwhip_sum["downstream"] > bullwhip_sum["whole_network"],
    }
    print()
    print("| Check | Result |\n|---|---|")
    for name, ok in checks.items():
        print(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    print()
    print("Mean change in DC+MFG+CM bullwhip by arm:", {a: round(v, 2) for a, v in bullwhip_sum.items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]))
