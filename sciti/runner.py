"""One simulation run (spec §4, §8)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from sciti.checks import SimulationError, enforce
from sciti.data.demand import DemandModel
from sciti.disruptions import validate_disruptions
from sciti.engine.adoption import apply_forced
from sciti.engine.ops import step_week
from sciti.engine.state import init_state
from sciti.metrics import summarize, week_rows
from sciti.network import build_network
from sciti.outputs import RunWriter, build_manifest, now
from sciti.rng import make_streams
from sciti.tech.catalog import catalog_hash, load_catalog


def quarter_start(t: int) -> bool:
    return (t - 1) % 13 == 0


def run(cfg, run_dir: Path | None = None, policy=None) -> Path:
    started = now()
    baseline_file = Path(cfg.baseline_path)
    if not baseline_file.exists():
        raise FileNotFoundError(f"{baseline_file} not found; run `sciti prepare` first")
    baseline = json.loads(baseline_file.read_text())
    net = build_network(baseline, cfg.assumptions)
    validate_disruptions(cfg.disruptions, net)
    catalog = load_catalog(cfg.catalog_path)
    for fa in cfg.forced_adoptions:
        if fa.tech not in catalog or any(m not in net.nodes for m in fa.members):
            raise ValueError(f"forced adoption refers to unknown tech or node: {fa}")
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(cfg.seed)
    demand = dm.generate(cfg.weeks, streams["demand"])
    s = init_state(cfg, baseline, net, dm, demand, catalog, streams)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{cfg.name}_s{cfg.seed}_{stamp}"
    run_dir = Path(run_dir) if run_dir else Path(cfg.output_dir) / run_id
    writer = RunWriter(run_dir)
    rows: list[dict] = []
    checks = "passed" if cfg.checks.strict else "warnings-allowed"
    extra = {"catalog_sha256": catalog_hash(cfg.catalog_path), "xlsx_sha256": baseline["source"]["xlsx_sha256"]}
    try:
        for t in range(1, cfg.weeks + 1):
            # Correction (2026-09-12, review): apply_forced must run every week -- it
            # already filters by fa.week == week internally. Gating it on quarter_start
            # would silently drop forced adoptions scheduled outside week 1/14/27/...
            apply_forced(s, t)
            step_week(s, t)
            enforce(s, t, cfg.checks.strict)
            rows.extend(week_rows(s, t))
    except SimulationError as e:
        checks = f"failed: {e}"
        writer.finish(s, rows, {"error": str(e)}, build_manifest(cfg, run_id, started, now(), {**extra, "checks": checks}))
        writer.close()
        raise
    summary = summarize(s, rows)
    writer.finish(s, rows, summary, build_manifest(cfg, run_id, started, now(), {**extra, "checks": checks}))
    writer.close()
    return run_dir
