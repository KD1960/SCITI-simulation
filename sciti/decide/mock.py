"""Scripted policy for tests; never calls an API (spec §11)."""
from __future__ import annotations

from sciti.decide.interface import Brief, Reply

EMPTY = '{"decisions": []}'


class MockPolicy:
    name = "mock"

    def __init__(self, script: list[dict]):
        self.script = {(e["agent"], e["week"], e["pass"]): list(e["replies"]) for e in script}
        self.calls: dict[tuple, int] = {}

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        key = (brief.agent, brief.week, brief.pass_)
        replies = self.script.get(key)
        if not replies:
            return Reply(brief.agent, EMPTY)
        i = self.calls.get(key, 0)
        self.calls[key] = i + 1
        return Reply(brief.agent, replies[min(i, len(replies) - 1)])
