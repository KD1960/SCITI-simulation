"""One simulation run (spec §4, §8)."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from sciti.checks import enforce
from sciti.coalitions import DecisionContext, run_decision_round
from sciti.data.demand import DemandModel
from sciti.decide.briefs import make_personas
from sciti.decide.interface import NonePolicy
from sciti.decide.mock import MockPolicy
from sciti.decide.rules import RulesPolicy
from sciti.disruptions import validate_disruptions
from sciti.engine.adoption import apply_forced, validate_forced_adoptions
from sciti.engine.ops import step_week
from sciti.engine.state import init_state
from sciti.metrics import summarize, week_rows
from sciti.network import build_network
from sciti.outputs import RunWriter, build_manifest, now
from sciti.rng import make_streams
from sciti.tech.catalog import catalog_hash, load_catalog


def quarter_start(t: int) -> bool:
    return (t - 1) % 13 == 0


def make_policy(cfg, s, client=None):
    """Return (policy, fallback). Tasks 14–15 extend this."""
    kind = cfg.decision.policy
    fallback = RulesPolicy(s.streams["rules"], s.catalog)
    if kind == "none":
        return NonePolicy(), NonePolicy()
    if kind == "rules":
        return fallback, fallback
    if kind == "mock":
        return MockPolicy(cfg.decision.mock_script), fallback
    if kind == "llm":
        from sciti.decide.llm import LLMPolicy
        return LLMPolicy(cfg.decision, fallback, client=client), fallback
    if kind == "replay":
        from sciti.decide.replay import ReplayPolicy
        return ReplayPolicy(cfg.decision.replay_from), fallback
    raise ValueError(f"unsupported decision policy {kind!r}")


def run(cfg, run_dir: Path | None = None, client=None) -> Path:
    started = now()
    baseline_file = Path(cfg.baseline_path)
    if not baseline_file.exists():
        raise FileNotFoundError(f"{baseline_file} not found; run `sciti prepare` first")
    baseline = json.loads(baseline_file.read_text())
    net = build_network(baseline, cfg.assumptions)
    validate_disruptions(cfg.disruptions, net)
    catalog = load_catalog(cfg.catalog_path)
    validate_forced_adoptions(cfg.forced_adoptions, net, catalog, cfg.weeks)
    dm = DemandModel.from_baseline(baseline, cfg.demand.trend_cap, cfg.demand.growth_mult)
    streams = make_streams(cfg.seed)
    demand = dm.generate(cfg.weeks, streams["demand"])
    s = init_state(cfg, baseline, net, dm, demand, catalog, streams)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{cfg.name}_s{cfg.seed}_{stamp}"
    run_dir = Path(run_dir) if run_dir else Path(cfg.output_dir) / run_id
    policy, fallback = make_policy(cfg, s, client)
    writer = RunWriter(run_dir)
    ctx = DecisionContext(policy=policy, fallback=fallback, writer=writer,
                          personas=make_personas(net, cfg.assumptions, streams["personas"]), recent={})
    decision_stats = {"calls": 0, "fallbacks": 0, "errors": 0}
    rows: list[dict] = []
    checks = "passed" if cfg.checks.strict else "warnings-allowed"
    assumptions = {"config": sorted(type(cfg.assumptions).model_fields),
                   "catalog_assumed_techs": sorted(t.id for t in catalog.values() if t.assumption)}
    extra = {"catalog_sha256": catalog_hash(cfg.catalog_path), "xlsx_sha256": baseline["source"]["xlsx_sha256"],
             "assumptions": assumptions}

    def manifest_extra(checks_value):
        return {**extra, "checks": checks_value, "decisions": decision_stats,
                "policy_stats": getattr(policy, "stats", lambda: {})()}

    try:
        for t in range(1, cfg.weeks + 1):
            # Correction (2026-09-12, review): apply_forced must run every week -- it
            # already filters by fa.week == week internally. Gating it on quarter_start
            # would silently drop forced adoptions scheduled outside week 1/14/27/...
            apply_forced(s, t)
            if quarter_start(t) and cfg.decision.policy != "none":
                ctx.recent = {n: [r for r in rows[-13 * len(net.order):] if r["node"] == n] for n in net.order}
                for k, v in run_decision_round(s, t, ctx).items():
                    decision_stats[k] += v
            step_week(s, t)
            enforce(s, t, cfg.checks.strict)
            rows.extend(week_rows(s, t))
    except Exception as e:
        label = f"{type(e).__name__}: {e}"
        checks = f"failed: {label}"
        writer.finish(s, rows, {"error": label}, build_manifest(cfg, run_id, started, now(), manifest_extra(checks)))
        writer.close()
        raise
    summary = summarize(s, rows)
    writer.finish(s, rows, summary, build_manifest(cfg, run_id, started, now(), manifest_extra(checks)))
    writer.close()
    return run_dir


def commit_note(original: Path) -> str:
    """Says which commit to check out when a run was made by different code than this."""
    from sciti.outputs import _git
    made, here = json.loads((Path(original) / "manifest.json").read_text()).get("git_commit"), _git()["git_commit"]
    if not made or made == here:
        return ""
    return f" (the run was made at commit {made}; this code is at {here}: check out {made} to replay it)"


def replay_run(original: Path, out_dir: Path) -> list[str]:
    from sciti.config import Config
    from sciti.decide.replay import ReplayError
    from sciti.outputs import DETERMINISTIC_FILES
    original = Path(original)
    data = json.loads((original / "manifest.json").read_text())["config"]
    if data["decision"]["policy"] != "none":
        data["decision"]["policy"] = "replay"
        data["decision"]["replay_from"] = str(original / "decisions.jsonl")
    try:
        out = run(Config.model_validate(data), run_dir=Path(out_dir))
    except ReplayError as e:
        raise ReplayError(f"{e}{commit_note(original)}") from e
    return [f for f in DETERMINISTIC_FILES if (original / f).read_bytes() != (out / f).read_bytes()]
