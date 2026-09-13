"""Decision policy contract and reply validation (spec §7.3)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Protocol

PROPOSAL_ACTIONS = ("adopt", "skip", "propose_group", "drop")
RESPONSE_ACTIONS = ("accept_group", "decline_group")
MAX_REASON_WORDS = 40


class ReplyError(Exception):
    pass


@dataclass
class Brief:
    agent: str
    role: str
    week: int
    quarter: int
    pass_: str
    data: dict


@dataclass
class Decision:
    tech: str
    action: str
    partners: list[str] = field(default_factory=list)
    reason: str = ""
    group_id: str | None = None


@dataclass
class Reply:
    agent: str
    raw: str
    fallback: bool = False
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0


class DecisionPolicy(Protocol):
    name: str

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply: ...


class NonePolicy:
    name = "none"

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        return Reply(brief.agent, '{"decisions": []}')


def parse_reply(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ReplyError("reply contains no JSON object")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as e:
        raise ReplyError(f"reply JSON is malformed: {e}") from e
    if not isinstance(obj, dict):
        raise ReplyError("reply JSON must be an object")
    return obj


def validate_reply(obj: dict, brief: Brief, max_new: int) -> list[Decision]:
    items = obj.get("decisions")
    if not isinstance(items, list):
        raise ReplyError('reply must have a "decisions" list')
    data = brief.data
    eligible = {e["id"] for e in data.get("eligible_technologies", [])}
    held = set(data.get("held", []))
    partners = {p["id"] for p in data.get("partners", [])}
    groups = {p["group_id"] for p in data.get("proposals", [])}
    proposals_by_id = {p["group_id"]: p for p in data.get("proposals", [])}
    allowed = PROPOSAL_ACTIONS if brief.pass_ == "proposal" else RESPONSE_ACTIONS
    out, seen, new = [], set(), 0
    for i, d in enumerate(items):
        if not isinstance(d, dict):
            raise ReplyError(f"decision {i} must be an object")
        tech, action = d.get("tech"), d.get("action")
        reason = d.get("reason", "")
        group_id = d.get("group_id")
        plist = d.get("partners", []) or []

        # Type checks
        if not isinstance(tech, str):
            raise ReplyError(f"decision {i}: tech must be a string")
        if not isinstance(action, str):
            raise ReplyError(f"decision {i}: action must be a string")
        if reason and not isinstance(reason, str):
            raise ReplyError(f"decision {i}: reason must be a string")
        if group_id is not None and not isinstance(group_id, str):
            raise ReplyError(f"decision {i}: group_id must be a string")
        reason = str(reason)

        if action not in allowed:
            raise ReplyError(f"decision {i}: action {action!r} not allowed in {brief.pass_} pass; use one of {allowed}")
        key = group_id if brief.pass_ == "response" else tech
        if key in seen:
            raise ReplyError(f"decision {i}: {key!r} appears twice")
        seen.add(key)
        if len(reason.split()) > MAX_REASON_WORDS:
            raise ReplyError(f"decision {i}: reason exceeds {MAX_REASON_WORDS} words")
        if not isinstance(plist, list) or not all(isinstance(p, str) for p in plist):
            raise ReplyError(f"decision {i}: partners must be a list of ids")
        if brief.pass_ == "response":
            if group_id not in groups:
                raise ReplyError(f"decision {i}: unknown group_id {group_id!r}")
            proposal = proposals_by_id[group_id]
            if tech != proposal["tech"]:
                raise ReplyError(f"decision {i}: tech {tech!r} does not match proposal tech {proposal['tech']!r}")
        elif action == "drop":
            if tech not in held:
                raise ReplyError(f"decision {i}: cannot drop {tech!r}, not held")
        elif action != "skip" or tech not in held:
            if tech not in eligible:
                raise ReplyError(f"decision {i}: {tech!r} is not eligible for you or is already held")
        if action == "propose_group":
            if not plist or not (plist in (["chain"], ["network"]) or set(plist) <= partners):
                raise ReplyError(f"decision {i}: partners must be direct partners, or [\"chain\"] or [\"network\"]")
        if action in ("adopt", "propose_group"):
            new += 1
            if new > max_new:
                raise ReplyError(f"at most {max_new} new adoption(s) per quarter")
        out.append(Decision(tech=tech, action=action, partners=list(plist), reason=reason,
                            group_id=group_id))
    return out


def brief_hash(brief: Brief) -> str:
    return hashlib.sha256(json.dumps(brief.data, sort_keys=True).encode()).hexdigest()
