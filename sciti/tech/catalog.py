"""Technology catalog: data, not code (spec §6)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

DEFAULT_PATH = Path(__file__).with_name("catalog.yaml")
ROLES = ("Supplier", "CM", "MFG", "DC", "Retail")


@dataclass(frozen=True)
class Effect:
    param: str
    op: Literal["mul", "add"]
    value: float


@dataclass(frozen=True)
class Tech:
    id: str
    name: str
    observatory_name: str
    eligible_roles: tuple[str, ...]
    cost_one_time: dict
    cost_per_week: dict
    setup_weeks: int
    network_requirement: Literal["solo", "pair", "chain"]
    group_bonus: float
    effects: tuple[Effect, ...]
    evidence: str
    assumption: bool


@dataclass
class TechHolding:
    tech: str
    adopted_week: int
    active_week: int
    coalition_id: str | None = None


def load_catalog(path: str | Path | None = None) -> dict[str, Tech]:
    from sciti.tech.effects import PARAMS
    rows = yaml.safe_load(Path(path or DEFAULT_PATH).read_text())
    out = {}
    for r in rows:
        effects = tuple(Effect(**e) for e in r.pop("effects"))
        t = Tech(effects=effects, eligible_roles=tuple(r.pop("eligible_roles")), **r)
        bad = [e.param for e in t.effects if e.param not in PARAMS or e.op not in ("mul", "add")]
        roles_bad = [x for x in t.eligible_roles if x not in ROLES
                     or x not in t.cost_one_time or x not in t.cost_per_week]
        if bad or roles_bad or t.network_requirement not in ("solo", "pair", "chain") or t.id in out:
            raise ValueError(f"catalog entry {t.id!r} invalid: params {bad}, roles {roles_bad}")
        out[t.id] = t
    return out


def catalog_hash(path: str | Path | None = None) -> str:
    return hashlib.sha256(Path(path or DEFAULT_PATH).read_bytes()).hexdigest()
