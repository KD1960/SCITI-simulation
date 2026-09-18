"""Sensitivity screen for the placeholder technology parameters (STATUS.md next step, 2026-09-17).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/sensitivity_screen.py OUT_DIR

For each technology, forces adoption in week 1 on every eligible firm with its effect sizes
scaled by k = 0.5, 1, 1.5 (mul effects: 1 - (1 - value) * k; add effects: value * k), one
technology at a time, policy none, seeds 1-30, 156 weeks. Two scenarios: calm, and CM_3 at 20%
capacity for 12 weeks from week 30 (as in E2). Each arm is paired with a same-seed,
same-scenario no-tech run. Writes OUT_DIR/sensitivity.csv and prints it.

Costs are not simulated at other levels: with policy none, technology cost is a straight
deduction, so profit at cost multiplier c is profit + (1 - c) * costs_tech. The table gives
profit at c = 0.5 and 2, and the break-even multiplier (profit gain is zero at that c).
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from sciti.batch import run_batch
from sciti.config import Config, Disruption, ForcedAdoption
from sciti.network import build_network
from sciti.tech.catalog import DEFAULT_PATH, load_catalog

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
SCALES = [0.5, 1.0, 1.5]
SCENARIOS = {"calm": [], "cm3_12w": [Disruption(target="CM_3", start_week=30, weeks=12, capacity_mult=0.2)]}
COLS = ["network_profit", "network_profit_with_inventory", "satisfaction_index", "fill_rate", "costs_tech"]


def scaled_catalog(out: Path, tid: str, k: float) -> str:
    rows = yaml.safe_load(DEFAULT_PATH.read_text())
    for r in rows:
        if r["id"] == tid:
            for e in r["effects"]:
                e["value"] = 1 - (1 - e["value"]) * k if e["op"] == "mul" else e["value"] * k
    path = out / "catalogs" / f"{tid}_k{k}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(rows))
    return str(path)


def _run(args):
    name, scen, tid, members, catalog_path, out = args
    cfg = Config(name=name, seed=1, weeks=156, output_dir=str(out), catalog_path=catalog_path,
                 disruptions=SCENARIOS[scen])
    if tid:
        cfg.forced_adoptions = [ForcedAdoption(week=1, tech=tid, members=members)]
    return name, run_batch(cfg, SEEDS, out / name)


def load(batch_dir: Path) -> pd.DataFrame:
    d = pd.read_csv(batch_dir / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {batch_dir}: {d.error.dropna().unique()}")
    return d.set_index("seed")[COLS]


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    base_cfg = Config(name="base", seed=1, weeks=156, output_dir=str(out))
    net = build_network(json.loads(Path(base_cfg.baseline_path).read_text()), base_cfg.assumptions)
    jobs = []
    for scen in SCENARIOS:
        jobs.append((f"{scen}__base__k0", scen, None, [], None, out))
        for tid, tech in load_catalog().items():
            members = [n for n in net.order if net.nodes[n].role in tech.eligible_roles]
            for k in SCALES:
                jobs.append((f"{scen}__{tid}__k{k}", scen, tid, members, scaled_catalog(out, tid, k), out))
    with ProcessPoolExecutor(max_workers=7) as pool:
        dirs = dict(pool.map(_run, jobs))
    rows = []
    for name, d in sorted(dirs.items()):
        scen, tid, k = name.split("__")
        if tid == "base":
            continue
        diff = load(d) - load(dirs[f"{scen}__base__k0"])
        profit, cost = diff["network_profit"], diff["costs_tech"].mean()
        half = T_975_DF29 * profit.std(ddof=1) / np.sqrt(len(profit))
        rows.append({"scenario": scen, "tech": tid, "effect_scale": float(k[1:]),
                     "profit_with_inventory": diff["network_profit_with_inventory"].mean(), "profit": profit.mean(), "ci_low": profit.mean() - half, "ci_high": profit.mean() + half,
                     "satisfaction": diff["satisfaction_index"].mean(), "fill_rate": diff["fill_rate"].mean(),
                     "costs_tech": cost, "profit_cost_x0.5": profit.mean() + 0.5 * cost,
                     "profit_cost_x2": profit.mean() - cost, "breakeven_cost_mult": 1 + profit.mean() / cost})
    table = pd.DataFrame(rows)
    table.to_csv(out / "sensitivity.csv", index=False)
    print(table.to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
