"""Many runs → one tidy results table; spend estimate (spec §4.1, §8, §9.3)."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from sciti.config import config_hash
from sciti.runner import run

EST_TOKENS_IN = 3000
EST_TOKENS_OUT = 400
AGENTS = 48


class SpendConfirmationRequired(Exception):
    pass


def estimate(cfg) -> dict:
    rounds = math.ceil(cfg.weeks / 13)
    D = cfg.decision
    if D.policy != "llm":
        return {"rounds": rounds, "calls_expected": 0, "calls_max": 0, "usd_expected": 0.0, "usd_max": 0.0,
                "note": f"policy {D.policy} makes no API calls"}
    per_call = (EST_TOKENS_IN * D.price_per_mtok_in + EST_TOKENS_OUT * D.price_per_mtok_out) / 1e6
    expected = round(AGENTS * rounds * 1.3)
    worst = min(D.max_llm_calls, AGENTS * rounds * 2 * 2)
    note = ("set decision.price_per_mtok_in/out to the model's current prices to estimate spend"
            if D.price_per_mtok_in == 0 and D.price_per_mtok_out == 0 else
            f"spend is also capped at ${D.max_spend_usd} per run")
    return {"rounds": rounds, "calls_expected": expected, "calls_max": worst,
            "usd_expected": round(expected * per_call, 4), "usd_max": round(worst * per_call, 4), "note": note}


def parse_seeds(text: str) -> list[int]:
    seeds = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def flatten(summary: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in summary.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "_"))
        else:
            out[key] = v
    return out


def run_batch(cfg, seeds, out_dir: Path, with_baseline=False, confirm_spend=False, client=None) -> Path:
    out_dir = Path(out_dir)
    if cfg.decision.policy == "llm":
        total = estimate(cfg)["usd_max"] * len(seeds)
        if total > cfg.decision.confirm_spend_threshold_usd and not confirm_spend:
            raise SpendConfirmationRequired(
                f"worst-case spend ${total:.2f} exceeds ${cfg.decision.confirm_spend_threshold_usd}; pass --confirm-spend")
    rows = []
    for seed in seeds:
        variants = [cfg.model_copy(update={"seed": seed}, deep=True)]
        if with_baseline and cfg.decision.policy != "none":
            base = cfg.model_copy(update={"seed": seed}, deep=True)
            base.decision.policy = "none"
            variants.append(base)
        for c in variants:
            d = run(c, run_dir=out_dir / f"{c.decision.policy}_s{seed}", client=client)
            summary = json.loads((d / "summary.json").read_text())
            rows.append({"seed": seed, "policy": c.decision.policy, "config_hash": config_hash(c),
                         "run_dir": str(d), **flatten(summary)})
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with open(out_dir / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return out_dir
