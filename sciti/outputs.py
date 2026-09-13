"""Run output files and manifest (spec §8, §9.1, §9.6)."""
from __future__ import annotations

import csv
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata as md
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path

from sciti.config import config_hash
from sciti.engine.state import Shipment
from sciti.metrics import WEEK_COLUMNS

DETERMINISTIC_FILES = ("weekly_nodes.csv", "shipments.csv", "events.jsonl", "summary.json")
KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHIPMENT_COLUMNS = [f.name for f in dataclasses.fields(Shipment)]


def scrub(text: str) -> str:
    return KEY_PATTERN.sub("[REDACTED]", text)


def _dumps(obj) -> str:
    return scrub(json.dumps(obj, sort_keys=True, default=str))


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def _git() -> dict:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "sciti", "configs"],
                                    cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip())
        return {"git_commit": commit, "git_dirty": dirty}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"git_commit": None, "git_dirty": None}


def build_manifest(cfg, run_id: str, started: str, finished: str, extra: dict) -> dict:
    versions = {}
    for pkg in ("numpy", "pandas", "pydantic", "pyyaml", "anthropic"):
        try:
            versions[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            versions[pkg] = None
    return {"run_id": run_id, "name": cfg.name, "seed": cfg.seed, "started": started, "finished": finished,
            "config": cfg.model_dump(mode="json"), "config_hash": config_hash(cfg),
            "python": platform.python_version(), "packages": versions,
            "baseline_sha256": _sha256(Path(cfg.baseline_path)),
            "decision_policy": cfg.decision.policy, "model": cfg.decision.model, **_git(), **extra}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class RunWriter:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._decisions = open(self.run_dir / "decisions.jsonl", "w")

    def log_decision(self, record: dict) -> None:
        self._decisions.write(_dumps(record) + "\n")
        self._decisions.flush()

    def finish(self, s, rows: list[dict], summary: dict, manifest: dict) -> None:
        with open(self.run_dir / "weekly_nodes.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=WEEK_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        ships = sorted(s.arrived + s.in_transit, key=lambda sh: sh.id)
        with open(self.run_dir / "shipments.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SHIPMENT_COLUMNS)
            w.writeheader()
            for sh in ships:
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in dataclasses.asdict(sh).items()})
        (self.run_dir / "events.jsonl").write_text("".join(_dumps(e) + "\n" for e in s.events))
        (self.run_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
        net = {"nodes": [{"id": n, "role": s.net.nodes[n].role, "city": s.net.nodes[n].city,
                          "lat": s.net.nodes[n].lat, "lon": s.net.nodes[n].lon} for n in s.net.order],
               "links": [[a, b] for a in s.net.order for b in s.net.downstream[a]],
               "techs": {t.id: t.name for t in s.catalog.values()}}
        (self.run_dir / "network.json").write_text(json.dumps(net, indent=1))
        (self.run_dir / "manifest.json").write_text(scrub(json.dumps(manifest, indent=1, sort_keys=True, default=str)))
        report = Path(s.cfg.baseline_path).with_name("validation_report.md")
        if report.exists():
            shutil.copy(report, self.run_dir / "validation_report.md")

    def close(self) -> None:
        self._decisions.close()
