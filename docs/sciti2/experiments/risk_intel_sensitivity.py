"""How much of risk intelligence's value rests on "weeks of outage saved" (STATUS.md, 2026-09-19).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/risk_intel_sensitivity.py OUT_DIR

Same random-disruption schedules as random_disruptions.py at rate 0.2, seeds 1-30. The catalog's
risk_intel entry is varied: recovery_weeks_saved 0, 1, 2 (catalog v2), 3, each with warning_prob
0.4; plus 2 weeks saved with no warning at all. Arms per level: risk intelligence forced on every
eligible firm vs no tech, and the hybrid (payback rule, suppliers follow, insurance habit) vs the
same rule without the habit. Writes OUT_DIR/risk_intel_sensitivity.csv and prints it.
"""
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from random_disruptions import FOLLOW, SEEDS, T_975_DF29, WEEKS, schedule  # noqa: E402

from sciti.batch import provenance
from sciti.config import Config, DecisionCfg, ForcedAdoption  # noqa: E402
from sciti.network import build_network  # noqa: E402
from sciti.runner import run  # noqa: E402
from sciti.tech.catalog import DEFAULT_PATH  # noqa: E402

RATE = 0.2
LEVELS = {"saved0_warn": (0.0, 0.4), "saved1_warn": (1.0, 0.4), "saved2_warn": (2.0, 0.4),
          "saved3_warn": (3.0, 0.4), "saved2_nowarn": (2.0, 0.0)}
ARMS = {"none": DecisionCfg(), "risk_intel": DecisionCfg(), "follow": DecisionCfg(**FOLLOW),
        "hybrid": DecisionCfg(**FOLLOW, insurance_techs=["risk_intel", "aps"])}


def catalog_for(out: Path, level: str) -> str:
    saved, prob = LEVELS[level]
    rows = yaml.safe_load(DEFAULT_PATH.read_text())
    for r in rows:
        if r["id"] == "risk_intel":
            for e in r["effects"]:
                e["value"] = {"recovery_weeks_saved": saved, "warning_prob": prob}.get(e["param"], e["value"])
    path = out / "catalogs" / f"{level}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(rows))
    return str(path)


def _run(job):
    level, arm, seed, sites, eligible, catalog, out = job
    cfg = Config(name=f"{level}_{arm}", seed=seed, weeks=WEEKS, output_dir=str(out), catalog_path=catalog,
                 decision=ARMS[arm], disruptions=schedule(seed, RATE, sites))
    if arm == "risk_intel":
        cfg.forced_adoptions = [ForcedAdoption(week=1, tech="risk_intel", members=eligible)]
    d = run(cfg, run_dir=out / level / arm / f"s{seed}")
    s = json.loads((d / "summary.json").read_text())
    shutil.rmtree(d)
    return {"level": level, "arm": arm, "seed": seed, "profit": s["network_profit_with_inventory"], "fill": s["fill_rate"]}


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    base = Config(name="base", seed=1)
    net = build_network(json.loads(Path(base.baseline_path).read_text()), base.assumptions)
    sites = [n for n in net.order if net.nodes[n].role != "Retail"]
    eligible = [n for n in net.order if net.nodes[n].role in ("CM", "MFG", "DC")]
    jobs = []
    for level in LEVELS:
        cat = catalog_for(out, level)
        # none and follow never hold risk intelligence, so one copy serves every level
        arms = ARMS if level == "saved2_warn" else ("risk_intel", "hybrid")
        jobs += [(level, a, s, sites, eligible, cat, out) for a in arms for s in SEEDS]
    with ProcessPoolExecutor(max_workers=7) as pool:
        runs = pd.DataFrame(list(pool.map(_run, jobs, chunksize=4)))
    ref = {a: runs[(runs.level == "saved2_warn") & (runs.arm == a)].set_index("seed") for a in ("none", "follow")}
    rows = []
    for level in LEVELS:
        for arm, against in (("risk_intel", "none"), ("hybrid", "follow")):
            d = runs[(runs.level == level) & (runs.arm == arm)].set_index("seed")
            for m in ("profit", "fill"):
                diff = d[m] - ref[against][m]
                half = T_975_DF29 * diff.std(ddof=1) / np.sqrt(len(diff))
                rows.append({"level": level, "comparison": f"{arm}_vs_{against}", "measure": m, "mean": diff.mean(),
                             "ci_low": diff.mean() - half, "ci_high": diff.mean() + half,
                             "share_positive": float((diff > 0).mean())})
    table = pd.DataFrame(rows)
    table.assign(**provenance()).to_csv(out / "risk_intel_sensitivity.csv", index=False)
    print(table.to_string(float_format=lambda x: f"{x:.4g}"))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
