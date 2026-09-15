"""E1 technology screen (docs/sciti2/experiments-recommendation.md, E1).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/tech_screen.py OUT_DIR

For each technology, forces adoption in week 1 on (a) every eligible firm and (b) one tier,
with policy none, seeds 1-30, 156 weeks, on data/baseline.json. Each arm is paired with a
same-seed no-tech run. Writes OUT_DIR/screen.csv (paired mean difference and 95% CI per
arm and measure) and prints it. Multi-member forced adoptions form a group, so members get
the technology's group bonus (+25%).
"""
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Config, ForcedAdoption
from sciti.network import build_network
from sciti.tech.catalog import load_catalog

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
COLS = ["network_profit", "satisfaction_index", "fill_rate", "retail_on_time_rate", "quality_mean", "co2_kg",
        "costs_tech", "costs_holding", "costs_shipping", "costs_stockout", "costs_scrap", "costs_handling",
        "bullwhip_DC", "bullwhip_MFG", "bullwhip_CM"]
# One-tier arm per technology: the tier where its effect is most direct.
TIER = {"ml_forecast": ["Retail"], "control_tower": ["DC", "Retail"], "rfid": ["Retail"], "aps": ["MFG"],
        "routing": ["DC"], "blockchain": ["Supplier", "CM"], "risk_intel": ["CM"]}


def _run(args):
    name, members_by_tech, out = args
    cfg = Config(name=name, seed=1, weeks=156, output_dir=str(out))
    cfg.forced_adoptions = [ForcedAdoption(week=1, tech=t, members=m) for t, m in members_by_tech.items()]
    return name, run_batch(cfg, SEEDS, out / name)


def load(batch_dir: Path) -> pd.DataFrame:
    d = pd.read_csv(batch_dir / "results.csv")
    if not (d.status == "ok").all():
        raise SystemExit(f"failed runs in {batch_dir}: {d.error.dropna().unique()}")
    return d.set_index("seed")[COLS]


def main(out: Path) -> None:
    base_cfg = Config(name="base", seed=1, weeks=156, output_dir=str(out))
    net = build_network(json.loads(Path(base_cfg.baseline_path).read_text()), base_cfg.assumptions)
    catalog = load_catalog()
    jobs = [("base", {}, out)]
    for tid, tech in catalog.items():
        jobs.append((f"{tid}__all", {tid: [n for n in net.order if net.nodes[n].role in tech.eligible_roles]}, out))
        if tid in TIER:
            jobs.append((f"{tid}__tier", {tid: [n for n in net.order if net.nodes[n].role in TIER[tid]]}, out))
    with ProcessPoolExecutor(max_workers=7) as pool:
        dirs = dict(pool.map(_run, jobs))
    base = load(dirs.pop("base"))
    rows = []
    for name, d in sorted(dirs.items()):
        tid, scope = name.split("__")
        diff = load(d) - base
        n_members = len(next(j for j in jobs if j[0] == name)[1][tid])
        for c in COLS:
            half = T_975_DF29 * diff[c].std(ddof=1) / np.sqrt(len(diff))
            rows.append({"tech": tid, "scope": scope, "firms": n_members, "measure": c, "mean": diff[c].mean(),
                         "ci_low": diff[c].mean() - half, "ci_high": diff[c].mean() + half,
                         "base_mean": base[c].mean()})
    table = pd.DataFrame(rows)
    table.to_csv(out / "screen.csv", index=False)
    print(table.to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
