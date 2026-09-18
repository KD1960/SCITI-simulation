"""Many runs → one tidy results table; spend estimate (spec §4.1, §8, §9.3)."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from sciti.config import config_hash
from sciti.runner import run

EST_TOKENS_IN = 4000   # measured in the 2026-09-18 run: 3,965 in, 762 out per call
EST_TOKENS_OUT = 800
EST_CALLS_PER_AGENT_ROUND = 2.1          # measured 2026-09-18: a proposal call plus response passes, few retries
EST_CALLS_PER_AGENT_ROUND_RETRIES = 2.6  # measured in the 2026-09-16 pilot, when truncated replies were retried
AGENTS = {"Supplier": 30, "CM": 4, "MFG": 2, "DC": 4, "Retail": 8}


class SpendConfirmationRequired(Exception):
    pass


def estimate(cfg) -> dict:
    rounds = math.ceil(cfg.weeks / 13)
    D = cfg.decision
    if D.policy != "llm":
        return {"rounds": rounds, "calls_expected": 0, "calls_max": 0, "usd_expected": 0.0, "usd_max": 0.0,
                "note": f"policy {D.policy} makes no API calls"}
    agents = sum(c for role, c in AGENTS.items() if role not in D.rules_roles)
    per_call = (EST_TOKENS_IN * D.price_per_mtok_in + EST_TOKENS_OUT * D.price_per_mtok_out) / 1e6
    expected = round(agents * rounds * EST_CALLS_PER_AGENT_ROUND)
    with_retries = min(D.max_llm_calls, round(agents * rounds * EST_CALLS_PER_AGENT_ROUND_RETRIES))
    worst = min(D.max_llm_calls, agents * rounds * 2 * 2)
    note = ("set decision.price_per_mtok_in/out to the model's current prices to estimate spend"
            if D.price_per_mtok_in == 0 and D.price_per_mtok_out == 0 else
            f"spend is also capped at ${D.max_spend_usd} per run")
    return {"rounds": rounds, "calls_expected": expected, "calls_with_retries": with_retries,
            "calls_max": worst, "usd_expected": round(expected * per_call, 4),
            "usd_with_retries": round(with_retries * per_call, 4),
            "usd_max": round(worst * per_call, 4), "note": note}


def parse_seeds(text: str) -> list[int]:
    if not text or not text.strip():
        raise ValueError("seed input cannot be empty")
    seeds = []
    seen = set()
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            parts = part.split("-")
            if len(parts) != 2:
                raise ValueError(f"invalid range format: {part}")
            try:
                a, b = int(parts[0]), int(parts[1])
            except ValueError:
                raise ValueError(f"range bounds must be integers: {part}")
            if a > b:
                raise ValueError(f"reversed range: {a}-{b}")
            for seed in range(a, b + 1):
                if seed not in seen:
                    seeds.append(seed)
                    seen.add(seed)
        else:
            try:
                seed = int(part)
            except ValueError:
                raise ValueError(f"seed must be an integer: {part}")
            if seed not in seen:
                seeds.append(seed)
                seen.add(seed)
    if not seeds:
        raise ValueError("no valid seeds after parsing")
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


def _format_config_factors(cfg) -> dict:
    """Extract readable config factors for CSV columns."""
    D = cfg.decision

    # Forced adoptions compact format: w1:control_tower:DC_Shanghai|Retail_5;w2:other_tech:Member1|Member2
    forced = ""
    if cfg.forced_adoptions:
        forced_strs = []
        for fa in cfg.forced_adoptions:
            members_str = "|".join(fa.members)
            forced_strs.append(f"w{fa.week}:{fa.tech}:{members_str}")
        forced = ";".join(forced_strs)

    # Disruptions compact format: CM_4@20+6x0.25+7d;Target@start+durationxcap+ld
    disruptions = ""
    if cfg.disruptions:
        disrup_strs = []
        for d in cfg.disruptions:
            ld = int(d.extra_lead_days) if d.extra_lead_days == int(d.extra_lead_days) else d.extra_lead_days
            disrup_strs.append(f"{d.target}@{d.start_week}+{d.weeks}x{d.capacity_mult}+{ld}d")
        disruptions = ";".join(disrup_strs)

    return {
        "name": cfg.name,
        "weeks": cfg.weeks,
        "decision_model": D.policy or "",
        "demand_growth_mult": cfg.demand.growth_mult,
        "demand_trend_cap": cfg.demand.trend_cap,
        "decision_visibility": D.visibility,
        "decision_cost_split": D.cost_split,
        "decision_chain_accept_share": D.chain_accept_share,
        "decision_max_new_adoptions_per_quarter": D.max_new_adoptions_per_quarter,
        "forced_adoptions": forced,
        "disruptions": disruptions,
    }


def run_batch(cfg, seeds, out_dir: Path, with_baseline=False, confirm_spend=False, client=None) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if cfg.decision.policy == "llm":
        total = estimate(cfg)["usd_max"] * len(seeds)
        if total > cfg.decision.confirm_spend_threshold_usd and not confirm_spend:
            raise SpendConfirmationRequired(
                f"worst-case spend ${total:.2f} exceeds ${cfg.decision.confirm_spend_threshold_usd}; pass --confirm-spend")

    rows = []
    failed_count = 0
    for seed in seeds:
        primary_policy = cfg.decision.policy
        variants = [cfg.model_copy(update={"seed": seed}, deep=True)]
        if with_baseline and cfg.decision.policy != "none":
            base = cfg.model_copy(update={"seed": seed}, deep=True)
            base.decision.policy = "none"
            base.forced_adoptions = []
            variants.append(base)
        for c in variants:
            is_baseline = c.decision.policy == "none" and with_baseline and primary_policy != "none"
            try:
                d = run(c, run_dir=out_dir / f"{c.decision.policy}_s{seed}", client=client)
                summary = json.loads((d / "summary.json").read_text())
                row = {
                    "seed": seed,
                    "policy": c.decision.policy,
                    "baseline_for": primary_policy if is_baseline else "",
                    "config_hash": config_hash(c),
                    "run_dir": str(d),
                    "status": "ok",
                    "error": "",
                    **_format_config_factors(c),
                    **flatten(summary),
                }
                rows.append(row)
            except Exception as e:
                failed_count += 1
                err_msg = f"{type(e).__name__}: {str(e)[:200]}"
                row = {
                    "seed": seed,
                    "policy": c.decision.policy,
                    "baseline_for": primary_policy if is_baseline else "",
                    "config_hash": config_hash(c),
                    "run_dir": "",
                    "status": "failed",
                    "error": err_msg,
                    **_format_config_factors(c),
                }
                rows.append(row)

    columns = list(dict.fromkeys(k for r in rows for k in r))
    with open(out_dir / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

    return out_dir
