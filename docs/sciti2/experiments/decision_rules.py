"""E4 decision-rule sweep (docs/sciti2/experiments-recommendation.md, E4).

Run from the project root:
    .venv/bin/python docs/sciti2/experiments/decision_rules.py OUT_DIR

Agents decide with the payback rule. Full 2^5 factorial over the settings that rule uses, plus the
default point, in two conditions (calm; CM_3 at 20% output and +14 days for 12 weeks from week 30).
Seeds 1-30, 156 weeks. Each point is paired with a same-seed no-tech run in the same condition.
(`decision.visibility` is not varied: the payback rule does not read it.)

Writes:
  OUT_DIR/runs.csv         one row per run: point, condition, seed, outcome differences vs no-tech,
                           adoption counts by technology, groups formed/failed
  OUT_DIR/main_effects.csv high-level minus low-level effect per factor, condition, and measure,
                           as a seed-paired mean and 95% CI (averaged over the other factors)
"""
import itertools
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sciti.batch import run_batch
from sciti.config import Assumptions, Config, DecisionCfg, Disruption

SEEDS = list(range(1, 31))
T_975_DF29 = 2.045  # two-sided 95% t critical value for 30 paired seeds
TECHS = ("ml_forecast", "control_tower", "rfid", "aps", "routing", "wh_robotics", "blockchain", "risk_intel")
CONDITIONS = {"calm": [], "cm3_12w": [Disruption(target="CM_3", start_week=30, weeks=12, capacity_mult=0.2,
                                                   extra_lead_days=14.0)]}
# factor: (low, high, default)
FACTORS = {
    "budget_share": ((0.01, 0.04), (0.05, 0.20), (0.02, 0.10)),
    "horizon_weeks": ((13, 52), (52, 156), (26, 104)),
    "chain_accept_share": (0.4, 0.8, 0.6),
    "cost_split": ("equal", "by_size", "equal"),
    "max_new_per_quarter": (1, 2, 1),
}
OUTCOMES = ["network_profit", "network_profit_with_inventory", "satisfaction_index", "fill_rate", "costs_tech", "adoptions", "coalitions"]


def point_config(name, levels, disruptions, out):
    return Config(name=name, seed=1, weeks=156, output_dir=str(out), disruptions=disruptions,
                  assumptions=Assumptions(persona_budget_share=levels["budget_share"],
                                          persona_horizon_weeks=levels["horizon_weeks"]),
                  decision=DecisionCfg(policy="rules", chain_accept_share=levels["chain_accept_share"],
                                       cost_split=levels["cost_split"],
                                       max_new_adoptions_per_quarter=levels["max_new_per_quarter"]))


def points():
    names = list(FACTORS)
    yield "default", {f: FACTORS[f][2] for f in names}, None
    for bits in itertools.product((0, 1), repeat=len(names)):
        yield "p" + "".join(map(str, bits)), {f: FACTORS[f][b] for f, b in zip(names, bits)}, dict(zip(names, bits))


def _run(job):
    name, cfg, out = job
    batch = run_batch(cfg, SEEDS, out / name)
    d = pd.read_csv(batch / "results.csv")
    if not (d.status == "ok").all():
        raise RuntimeError(f"failed runs in {batch}: {d.error.dropna().unique()}")
    rows = []
    for _, r in d.iterrows():
        row = {"seed": r.seed, **{c: r[c] for c in OUTCOMES}}
        if cfg.decision.policy == "rules":
            adopts, kinds, failed, weeks = Counter(), Counter(), Counter(), []
            for line in open(Path(r.run_dir) / "events.jsonl"):
                e = json.loads(line)
                if e["type"] == "adopt":
                    adopts[e["tech"]] += 1
                    weeks.append(e["week"])
                elif e["type"] == "coalition":
                    kinds[e["kind"]] += 1
                elif e["type"] == "coalition_failed":
                    failed[e["reason"]] += 1
            row.update({f"adopt_{t}": adopts[t] for t in TECHS})
            row.update({f"formed_{k}": kinds[k] for k in ("dyad", "triad", "chain", "network")})
            row.update({f"failed_{k.replace(' ', '_')}": failed[k]
                        for k in ("acceptance", "budget", "held", "quota", "no eligible partners")})
            row["mean_adopt_week"] = float(np.mean(weeks)) if weeks else np.nan
        rows.append(row)
    return name, pd.DataFrame(rows).set_index("seed")


def main(out: Path) -> None:
    jobs, meta = [], {}
    for cond, disruptions in CONDITIONS.items():
        none = Config(name=f"{cond}__none", seed=1, weeks=156, output_dir=str(out), disruptions=disruptions)
        jobs.append((none.name, none, out))
        for pname, levels, bits in points():
            name = f"{cond}__{pname}"
            jobs.append((name, point_config(name, levels, disruptions, out), out))
            meta[name] = (cond, pname, levels, bits)
    with ProcessPoolExecutor(max_workers=7) as pool:
        res = dict(pool.map(_run, jobs))

    runs = []
    for name, (cond, pname, levels, bits) in meta.items():
        d = res[name].copy()
        for c in ("network_profit", "network_profit_with_inventory", "satisfaction_index", "fill_rate"):
            d[f"d_{c}"] = d[c] - res[f"{cond}__none"][c]
        d["condition"], d["point"] = cond, pname
        for f in FACTORS:
            d[f] = str(levels[f])
            d[f"{f}_high"] = np.nan if bits is None else bits[f]
        runs.append(d.reset_index())
    runs = pd.concat(runs, ignore_index=True)
    runs.to_csv(out / "runs.csv", index=False)

    measures = ["d_network_profit", "d_network_profit_with_inventory", "d_satisfaction_index", "d_fill_rate", "costs_tech", "adoptions", "coalitions",
                "mean_adopt_week"] + [f"adopt_{t}" for t in TECHS] + ["formed_dyad", "formed_triad", "formed_chain",
                                                                      "formed_network", "failed_acceptance",
                                                                      "failed_budget"]
    fac = runs[runs.point != "default"]
    eff = []
    for cond in CONDITIONS:
        c = fac[fac.condition == cond]
        for f in FACTORS:
            hi = c[c[f"{f}_high"] == 1].groupby("seed")[measures].mean()
            lo = c[c[f"{f}_high"] == 0].groupby("seed")[measures].mean()
            diff = hi - lo
            for m in measures:
                half = T_975_DF29 * diff[m].std(ddof=1) / np.sqrt(len(diff))
                eff.append({"condition": cond, "factor": f, "low": str(FACTORS[f][0]), "high": str(FACTORS[f][1]),
                            "measure": m, "effect": diff[m].mean(), "ci_low": diff[m].mean() - half,
                            "ci_high": diff[m].mean() + half, "mean_at_low": lo[m].mean(),
                            "mean_at_high": hi[m].mean()})
    pd.DataFrame(eff).to_csv(out / "main_effects.csv", index=False)
    print(f"wrote {out / 'runs.csv'} ({len(runs)} rows) and {out / 'main_effects.csv'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
