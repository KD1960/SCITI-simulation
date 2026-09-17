"""Run configuration. Unknown keys are errors (spec §9.5)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DemandCfg(Strict):
    trend_cap: float = 0.15
    growth_mult: float = 1.0


class DecisionCfg(Strict):
    policy: Literal["none", "rules", "mock", "llm", "replay"] = "none"
    model: str | None = None
    replay_from: str | None = None
    mock_script: list[dict] = Field(default_factory=list)
    max_llm_calls: int = 2000
    max_spend_usd: float = 25.0
    price_per_mtok_in: float = 0.0
    price_per_mtok_out: float = 0.0
    max_tokens: int = 2000   # thinking shares this budget; 600 truncated replies in the 2026-09-16 pilot
    max_consecutive_failures: int = 5
    request_timeout_s: float = 60.0
    confirm_spend_threshold_usd: float = 10.0
    max_new_adoptions_per_quarter: int = 1
    visibility: Literal["partners", "network"] = "partners"
    chain_accept_share: float = 0.6
    cost_split: Literal["equal", "by_size"] = "equal"

    @model_validator(mode="after")
    def _needs(self):
        if self.policy == "llm" and not self.model:
            raise ValueError("decision.model is required when policy is llm")
        if self.policy == "replay" and not self.replay_from:
            raise ValueError("decision.replay_from is required when policy is replay")
        return self


class Assumptions(Strict):
    markup: dict[str, float] = Field(
        default_factory=lambda: {"CM": 0.20, "MFG": 0.25, "DC": 0.10, "Retail": 0.40})
    holding_rate_annual: float = 0.25
    goodwill_penalty_per_unit: float = 5.0
    capacity_mult: dict[str, float] = Field(
        default_factory=lambda: {"Supplier": 1.5, "CM": 1.3, "MFG": 1.3})
    handling_cost_per_unit: float = 0.5
    dispatch_delay_days: float = 2.0
    record_error_sd: float = 0.05
    shrink_rate_weekly: float = 0.002
    inspection_catch: float = 0.8
    target_service_level: float = 0.95
    smoothing_alpha: float = 0.3
    dc_split: dict[str, dict[str, float]] = Field(default_factory=lambda: {
        "Retail_3": {"DC_Dubai": 0.5, "DC_Sofia": 0.5},
        "Retail_5": {"DC_Dubai": 0.5, "DC_Shanghai": 0.5}})
    mfg_share: dict[str, dict[str, float]] = Field(default_factory=lambda: {
        "DC_Houston": {"MFG_US": 0.8, "MFG_China": 0.2},
        "DC_Sofia": {"MFG_US": 0.6, "MFG_China": 0.4},
        "DC_Dubai": {"MFG_US": 0.4, "MFG_China": 0.6},
        "DC_Shanghai": {"MFG_US": 0.1, "MFG_China": 0.9}})
    satisfaction_weights: dict[str, float] = Field(
        default_factory=lambda: {"fill_rate": 0.5, "on_time": 0.3, "quality": 0.2})
    persona_budget_share: tuple[float, float] = (0.02, 0.10)
    persona_horizon_weeks: tuple[int, int] = (26, 104)
    supplier_cogs_share: float = 0.7
    fg_cover_weeks: float = 2.0
    initial_cash_weeks: float = 13.0
    part_weight_tons: float = 0.05 / 160  # the Glossary's 0.05 t per product, spread over its 160 parts
    defect_concentration: float = 50.0  # Beta concentration for per-shipment defect draws (spec §5.3 step 8), an assumption


class ChecksCfg(Strict):
    strict: bool = True


class ForcedAdoption(Strict):
    week: int
    tech: str
    members: list[str]


class Disruption(Strict):
    target: str               # node id, e.g. "CM_4"
    start_week: int
    weeks: int
    capacity_mult: float = 1.0
    extra_lead_days: float = 0.0


class Config(Strict):
    name: str
    seed: int
    weeks: int = 156
    baseline_path: str = "data/baseline.json"
    catalog_path: str | None = None
    output_dir: str = "runs"
    demand: DemandCfg = Field(default_factory=DemandCfg)
    decision: DecisionCfg = Field(default_factory=DecisionCfg)
    assumptions: Assumptions = Field(default_factory=Assumptions)
    checks: ChecksCfg = Field(default_factory=ChecksCfg)
    forced_adoptions: list[ForcedAdoption] = Field(default_factory=list)
    disruptions: list[Disruption] = Field(default_factory=list)


def load_config(path: str | Path) -> Config:
    data = yaml.safe_load(Path(path).read_text()) or {}
    return Config.model_validate(data)


def config_hash(cfg: Config) -> str:
    canon = json.dumps(cfg.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()
