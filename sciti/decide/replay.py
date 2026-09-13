"""Replays logged decisions so a run can be reproduced with no API calls (spec §9.1)."""
from __future__ import annotations

import json
from pathlib import Path

from sciti.decide.interface import Brief, Reply


class ReplayError(Exception):
    pass


class ReplayPolicy:
    name = "replay"

    def __init__(self, path: str | Path):
        self.log = {}
        for line in Path(path).read_text().splitlines():
            rec = json.loads(line)
            self.log[(rec["week"], rec["pass"], rec["agent"])] = rec["parsed"]

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        key = (brief.week, brief.pass_, brief.agent)
        if key not in self.log:
            raise ReplayError(f"no logged decision for {key}; the replay has diverged from the original run")
        return Reply(brief.agent, json.dumps({"decisions": self.log[key]}))
