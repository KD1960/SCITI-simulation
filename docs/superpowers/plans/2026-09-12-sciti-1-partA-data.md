# SCITI 1 — Part A: Data layer (Tasks 1–5)

> Part of `2026-09-12-sciti-1.md`. Read that file's Global Constraints first. Steps use checkbox (`- [ ]`) syntax.

All shell commands run from the project root: `cd "$HOME/Claude/Projects/SCITI simulation"`.

---

### Task 1: Project scaffold, config schema, RNG streams

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `sciti/__init__.py`, `sciti/config.py`, `sciti/rng.py`, `sciti/data/__init__.py`, `sciti/tech/__init__.py`, `sciti/engine/__init__.py`, `sciti/decide/__init__.py`
- Test: `tests/test_config.py`, `tests/test_rng.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `sciti.config.Config` (pydantic model, fields below), `load_config(path: str | Path) -> Config`, `config_hash(cfg: Config) -> str`
  - `sciti.rng.STREAMS: tuple[str, ...]`, `make_streams(seed: int) -> dict[str, numpy.random.Generator]`

- [ ] **Step 1: Create the scaffold**

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "sciti"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "numpy>=2.0",
  "pandas>=2.2",
  "openpyxl>=3.1",
  "pyyaml>=6.0",
  "pydantic>=2.7",
  "anthropic>=0.40",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
sciti = "sciti.cli:main"

[tool.setuptools.packages.find]
include = ["sciti*"]

[tool.setuptools.package-data]
sciti = ["tech/catalog.yaml", "decide/prompts/*.md"]

[tool.pytest.ini_options]
markers = ["realdata: needs the Ridge Line workbook on disk"]
```

`.gitignore`:

```
.venv/
__pycache__/
*.egg-info/
runs/
data/baseline.json
data/validation_report.md
.DS_Store
```

Create empty `sciti/__init__.py`, `sciti/data/__init__.py`, `sciti/tech/__init__.py`, `sciti/engine/__init__.py`, `sciti/decide/__init__.py`.

Run:

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

Expected: installs without error.

- [ ] **Step 2: Write the failing tests**

`tests/test_config.py`:

```python
import pytest
from pydantic import ValidationError
from sciti.config import load_config, config_hash, Config


def write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text)
    return p


def test_minimal_config_gets_defaults(tmp_path):
    cfg = load_config(write(tmp_path, "name: t\nseed: 3\n"))
    assert cfg.weeks == 156
    assert cfg.decision.policy == "none"
    assert cfg.assumptions.markup["Retail"] == 0.40
    assert cfg.assumptions.satisfaction_weights == {"fill_rate": 0.5, "on_time": 0.3, "quality": 0.2}
    assert cfg.checks.strict is True


def test_unknown_key_is_error(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\nbogus: 1\n"))


def test_unknown_nested_key_is_error(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\ndecision:\n  polcy: rules\n"))


def test_llm_policy_requires_model(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\ndecision:\n  policy: llm\n"))


def test_hash_stable_and_sensitive():
    a = Config(name="t", seed=1)
    b = Config(name="t", seed=1)
    c = Config(name="t", seed=2)
    assert config_hash(a) == config_hash(b)
    assert config_hash(a) != config_hash(c)
```

`tests/test_rng.py`:

```python
from sciti.rng import make_streams, STREAMS


def test_streams_repeat_for_same_seed():
    a, b = make_streams(5), make_streams(5)
    for name in STREAMS:
        assert a[name].random() == b[name].random()


def test_streams_are_independent_of_each_other():
    s = make_streams(5)
    before = make_streams(5)["demand"].random(3)
    s["ops"].random(1000)  # consuming one stream must not change another
    assert (s["demand"].random(3) == before).all()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_config.py tests/test_rng.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.config'`

- [ ] **Step 4: Implement**

`sciti/config.py`:

```python
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
    max_tokens: int = 600
    max_consecutive_failures: int = 5
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
```

`sciti/rng.py`:

```python
"""Named random streams from one master seed (spec §9.1).
Append new stream names at the END only; reordering changes every run."""
import numpy as np

STREAMS = ("demand", "ops", "quality", "personas", "disruptions", "rules", "lead")


def make_streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {name: np.random.default_rng(c) for name, c in zip(STREAMS, children)}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_config.py tests/test_rng.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore sciti/__init__.py sciti/config.py sciti/rng.py sciti/data/__init__.py sciti/tech/__init__.py sciti/engine/__init__.py sciti/decide/__init__.py tests/test_config.py tests/test_rng.py
git commit -m "feat: scaffold, strict config schema, named RNG streams

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Workbook loader → baseline.json + validation report

**Files:**
- Create: `sciti/data/loader.py`, `tests/conftest.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `SKUS: list[str]` (10 sub-components in BOM order), `COMPONENT_CM: dict[str, str]`, `CO2_FACTORS: dict[str, float]`, `CO2_TON_PER_UNIT = 0.05`
  - `parse_bom(glossary: pd.DataFrame) -> dict[str, dict]` → `{sku: {"units": int, "component": str, "cm": str}}`
  - `parse_supplier_params(df: pd.DataFrame) -> dict[str, dict]` → `{"Supplier_1": {"sku", "cm", "lead_days", "price"}}`
  - `parse_transactions(df: pd.DataFrame, suppliers: dict, report: list[str]) -> None` (adds `lead_sd_days`, `defect_share`, `n_rows`, `pooled` to each supplier in place)
  - `parse_lanes(ship: pd.DataFrame, report: list[str]) -> dict[str, dict]` → `{"cm_mfg"|"mfg_dc"|"dc_retail": {"mode_mix": {mode: share}, "modes": {mode: {"lead_a", "lead_b", "lead_resid_sd", "cost_per_unit", "mean_lead_days", "n"}}}}`
  - `parse_demand(df: pd.DataFrame) -> tuple[list[int], dict[str, dict[str, list[float]]]]` → `(years, {"Retail_1": {"A": [...260], "B": [...], "C": [...]}})`
  - `prepare(xlsx: Path, out_dir: Path) -> dict` writes `out_dir/baseline.json` and `out_dir/validation_report.md`, returns the baseline dict
  - Baseline dict keys: `source`, `bom`, `suppliers`, `lanes`, `history_years`, `demand_history`, `co2_factors`, `co2_ton_per_unit`
  - `tests/conftest.py` fixtures: `baseline` (dict, synthetic, same schema) and `baseline_path` (Path to it as JSON)

Workbook layout facts (verified 2026-09-12):
- `Glossary`: rows 2–11 (0-based, header=None): col 1 component (forward-fill), col 2 sku, col 4 units.
- `Supplier Data` columns Q:W, first 30 data rows: Product Name, Product Family, Suppliers, Contract Mfg, Lead Time, Price/Unit, Units.
- `Supplier Data` columns A:L: transactions; only 500 rows have a numeric `Lead Time`.
- `Shipment_CM_MFG_DC_Retailers` (header=None): row 0 headers; columns 0–13 CM→MFG, 15–28 MFG→DC, 30–43 DC→Retailer.
- `Demand_Retailer` (header=None): rows 4–263 data; col 0 year, col 1 week; retailer r (1–8) product columns at `3 + 3*(r-1)` (A), `+1` (B), `+2` (C).

- [ ] **Step 1: Write the failing tests**

`tests/test_loader.py`:

```python
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sciti.data import loader

XLSX = Path.home() / "Docs/School/LE/SCM and AI Oct2026 workshop/Master Data Set_4.xlsx"


def test_parse_bom_totals_160():
    g = pd.DataFrame([[None] * 5] * 2 + [
        ["A", "Semiconductor", "SR_MCU", "x", 10], ["B", None, "SR_MOS_KIT", "x", 10],
        ["C", "Steel", "AL_Sheet", "x", 5], [None, None, "HSS_Coil", "x", 5],
        [None, "Plastic", "PP_Resin", "x", 15], [None, None, "Poly_F_EU", "x", 15],
        [None, "Glass", "LGS_4_W", "x", 10], [None, None, "TGP_5_Q", "x", 10],
        [None, "Elastomer", "EPDM", "x", 40], [None, None, "NR_201", "x", 40]])
    bom = loader.parse_bom(g)
    assert sum(v["units"] for v in bom.values()) == 160
    assert bom["TGP_5_Q"] == {"units": 10, "component": "Glass", "cm": "CM_4"}
    assert bom["NR_201"]["cm"] == "CM_3"


def test_parse_transactions_pools_missing_suppliers():
    sups = {"Supplier_1": {"sku": "SR_MCU", "cm": "CM_1", "lead_days": 10, "price": 20},
            "Supplier_2": {"sku": "SR_MCU", "cm": "CM_1", "lead_days": 12, "price": 20}}
    tx = pd.DataFrame({"Supplier": ["Supplier 1"] * 5, "Product Name": ["SR_MCU"] * 5,
                       "Lead Time": [8, 10, 12, 10, 10], "Sentiment Score": [1, 3, 3, 3, 3]})
    report = []
    loader.parse_transactions(tx, sups, report)
    assert sups["Supplier_1"]["defect_share"] == 0.2
    assert sups["Supplier_1"]["pooled"] is False
    assert sups["Supplier_2"]["pooled"] is True
    assert sups["Supplier_2"]["lead_sd_days"] == pytest.approx(np.std([8, 10, 12, 10, 10], ddof=1))
    assert any("Supplier_2" in line for line in report)


def test_parse_lanes_mode_mix_and_regression():
    header = ["Shipment_ID", "Ship_Date", "a", "b", "c", "d", "e", "Mode", "Distance (Miles)",
              "Lead Time (days)", "Quantity", "Shipping Cost/Unit", "Total_Cost", "CO2 Emissions (kg)"]
    rows = []
    for i in range(10):
        miles = 1000 + 500 * i
        rows.append(["x", "d", "", "", "", "", "", "Air", miles, 1 + miles / 1000, 100, 10.0, 0, 0])
    for i in range(10):
        rows.append(["x", "d", "", "", "", "", "", "Ship", 5000, 20, 100, 2.0, 0, 0])
    block = pd.DataFrame([header] + rows)
    gap = pd.DataFrame([[None]] * len(block))
    ship = pd.concat([block, gap, block, gap, block], axis=1, ignore_index=True)
    lanes = loader.parse_lanes(ship, [])
    air = lanes["mfg_dc"]["modes"]["Air"]
    assert lanes["cm_mfg"]["mode_mix"] == {"Air": 0.5, "Ship": 0.5}
    assert air["lead_b"] == pytest.approx(0.001)
    assert air["lead_a"] == pytest.approx(1.0)
    assert air["cost_per_unit"] == pytest.approx(10.0)
    assert lanes["dc_retail"]["modes"]["Ship"]["lead_b"] == 0.0  # constant distance → flat


def test_parse_demand_shapes():
    rows = [[None] * 27] * 4
    for y in (2020, 2021):
        for w in range(1, 53):
            rows.append([y, w, "Q1"] + [float(w)] * 24)
    years, hist = loader.parse_demand(pd.DataFrame(rows))
    assert years == [2020, 2021]
    assert sorted(hist) == [f"Retail_{r}" for r in range(1, 9)]
    assert len(hist["Retail_8"]["C"]) == 104


@pytest.mark.realdata
@pytest.mark.skipif(not XLSX.exists(), reason="workbook not on this machine")
def test_prepare_real_workbook(tmp_path):
    base = loader.prepare(XLSX, tmp_path)
    assert len(base["suppliers"]) == 30
    assert base["history_years"] == [2020, 2021, 2022, 2023, 2024]
    assert sum(base["demand_history"]["Retail_1"]["A"][-52:]) == pytest.approx(129239, rel=0.01)
    assert set(base["lanes"]) == {"cm_mfg", "mfg_dc", "dc_retail"}
    assert json.loads((tmp_path / "baseline.json").read_text())["source"]["xlsx_sha256"]
    assert (tmp_path / "validation_report.md").read_text().startswith("# Validation report")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_loader.py -v`
Expected: FAIL with `ImportError: cannot import name 'loader'`

- [ ] **Step 3: Implement `sciti/data/loader.py`**

```python
"""Read the Ridge Line workbook once and write data/baseline.json (spec §2, §9.5)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SKUS = ["SR_MCU", "SR_MOS_KIT", "AL_Sheet", "HSS_Coil", "PP_Resin",
        "Poly_F_EU", "EPDM", "NR_201", "LGS_4_W", "TGP_5_Q"]
COMPONENT_CM = {"Semiconductor": "CM_1", "Steel": "CM_2", "Plastic": "CM_3",
                "Elastomer": "CM_3", "Glass": "CM_4"}
CO2_FACTORS = {"Air": 2.1, "Road": 0.163, "Rail": 0.028, "Ship": 0.037}
CO2_TON_PER_UNIT = 0.05
LANE_BLOCKS = {"cm_mfg": 0, "mfg_dc": 15, "dc_retail": 30}
MIN_ROWS = 5


def parse_bom(glossary: pd.DataFrame) -> dict[str, dict]:
    block = glossary.iloc[2:12, [1, 2, 4]].copy()
    block.columns = ["component", "sku", "units"]
    block["component"] = block["component"].ffill()
    bom = {}
    for _, r in block.iterrows():
        bom[str(r.sku)] = {"units": int(r.units), "component": str(r.component),
                           "cm": COMPONENT_CM[str(r.component)]}
    return bom


def parse_supplier_params(df: pd.DataFrame) -> dict[str, dict]:
    df = df.iloc[:30, :7].copy()
    df.columns = ["sku", "family", "supplier", "cm", "lead_days", "price", "units"]
    out = {}
    for _, r in df.iterrows():
        sid = str(r.supplier).replace(" ", "_")
        out[sid] = {"sku": str(r.sku), "cm": str(r.cm), "lead_days": float(r.lead_days),
                    "price": float(r.price)}
    return out


def parse_transactions(df: pd.DataFrame, suppliers: dict, report: list[str]) -> None:
    tx = df[pd.to_numeric(df["Lead Time"], errors="coerce").notna()].copy()
    tx["sid"] = tx["Supplier"].astype(str).str.replace(" ", "_")
    report.append(f"- Supplier transactions: {len(tx)} valid rows of {len(df)}")
    for sid in sorted(suppliers, key=lambda s: int(s.split("_")[1])):
        s = suppliers[sid]
        own = tx[tx["sid"] == sid]
        pooled = len(own) < MIN_ROWS
        rows = tx[tx["Product Name"] == s["sku"]] if pooled else own
        if pooled:
            report.append(f"- {sid}: {len(own)} rows; lead SD and defect share pooled from {s['sku']} ({len(rows)} rows)")
        lead = rows["Lead Time"].astype(float)
        s["lead_sd_days"] = float(lead.std(ddof=1)) if len(lead) > 1 else 2.0
        s["defect_share"] = float((rows["Sentiment Score"].astype(float) == 1).mean()) if len(rows) else 0.1
        s["n_rows"] = int(len(own))
        s["pooled"] = bool(pooled)


def _fit_mode(g: pd.DataFrame) -> dict:
    miles = g["Distance (Miles)"].astype(float).to_numpy()
    lead = g["Lead Time (days)"].astype(float).to_numpy()
    if len(g) >= 2 and np.ptp(miles) > 0:
        b, a = np.polyfit(miles, lead, 1)
    else:
        b, a = 0.0, float(lead.mean())
    resid = lead - (a + b * miles)
    return {"lead_a": float(a), "lead_b": float(b),
            "lead_resid_sd": float(resid.std(ddof=1)) if len(g) > 2 else 1.0,
            "cost_per_unit": float(g["Shipping Cost/Unit"].astype(float).mean()),
            "mean_lead_days": float(lead.mean()), "n": int(len(g))}


def parse_lanes(ship: pd.DataFrame, report: list[str]) -> dict[str, dict]:
    blocks = {}
    for name, start in LANE_BLOCKS.items():
        b = ship.iloc[1:, start:start + 14].copy()
        b.columns = list(ship.iloc[0, start:start + 14])
        blocks[name] = b.dropna(subset=["Mode"])
    allrows = pd.concat(blocks.values())
    lanes = {}
    for name, b in blocks.items():
        counts = b["Mode"].value_counts()
        mix = {m: float(counts[m] / counts.sum()) for m in sorted(counts.index)}
        modes = {}
        for m in sorted(counts.index):
            g = b[b["Mode"] == m]
            if len(g) < MIN_ROWS:
                report.append(f"- Lane {name}/{m}: {len(g)} rows; lead model pooled across lane types")
                g = allrows[allrows["Mode"] == m]
            modes[m] = _fit_mode(g)
        lanes[name] = {"mode_mix": mix, "modes": modes}
    return lanes


def parse_demand(df: pd.DataFrame) -> tuple[list[int], dict[str, dict[str, list[float]]]]:
    d = df.iloc[4:].copy()
    d = d[pd.to_numeric(d[0], errors="coerce").notna()]
    years = sorted(int(y) for y in d[0].unique())
    hist = {}
    for r in range(1, 9):
        c = 3 + 3 * (r - 1)
        hist[f"Retail_{r}"] = {p: [float(v) for v in d[c + i]] for i, p in enumerate("ABC")}
    return years, hist


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prepare(xlsx: Path, out_dir: Path) -> dict:
    xlsx, out_dir = Path(xlsx), Path(out_dir)
    required = ["Glossary", "Supplier Data", "Shipment_CM_MFG_DC_Retailers", "Demand_Retailer"]
    present = pd.ExcelFile(xlsx).sheet_names
    missing = [s for s in required if s not in present]
    if missing:
        raise ValueError(f"Workbook is missing sheets: {missing}")
    report = ["# Validation report", "", f"Source: `{xlsx}`", ""]
    bom = parse_bom(pd.read_excel(xlsx, sheet_name="Glossary", header=None))
    if sorted(bom) != sorted(SKUS) or sum(v["units"] for v in bom.values()) != 160:
        raise ValueError(f"BOM does not match spec: {bom}")
    suppliers = parse_supplier_params(pd.read_excel(xlsx, sheet_name="Supplier Data", usecols="Q:W", nrows=30))
    parse_transactions(pd.read_excel(xlsx, sheet_name="Supplier Data", usecols="A:L"), suppliers, report)
    for sid, s in suppliers.items():
        if bom[s["sku"]]["cm"] != s["cm"]:
            raise ValueError(f"{sid} ships {s['sku']} to {s['cm']} but BOM says {bom[s['sku']]['cm']}")
    lanes = parse_lanes(pd.read_excel(xlsx, sheet_name="Shipment_CM_MFG_DC_Retailers", header=None), report)
    years, hist = parse_demand(pd.read_excel(xlsx, sheet_name="Demand_Retailer", header=None))
    for rid, prods in hist.items():
        for p, series in prods.items():
            if len(series) != 52 * len(years):
                raise ValueError(f"{rid}/{p}: {len(series)} weeks, expected {52 * len(years)}")
    report += ["- Data names `MFG_LA`; treated as `MFG_US`.",
               "- DC→Retailer rows spread all DCs across all retailers; network links follow the document, "
               "lane statistics use the data pooled by mode."]
    base = {"source": {"xlsx": str(xlsx), "xlsx_sha256": _sha256(xlsx),
                       "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat()},
            "bom": bom, "suppliers": suppliers, "lanes": lanes,
            "history_years": years, "demand_history": hist,
            "co2_factors": CO2_FACTORS, "co2_ton_per_unit": CO2_TON_PER_UNIT}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baseline.json").write_text(json.dumps(base, indent=1, sort_keys=True))
    (out_dir / "validation_report.md").write_text("\n".join(report) + "\n")
    return base
```

- [ ] **Step 4: Create the synthetic fixture `tests/conftest.py`**

```python
"""Synthetic baseline with the real schema, so engine tests never need the workbook."""
import json

import numpy as np
import pytest

from sciti.data.loader import SKUS, COMPONENT_CM, CO2_FACTORS, CO2_TON_PER_UNIT

UNITS = {"SR_MCU": 10, "SR_MOS_KIT": 10, "AL_Sheet": 5, "HSS_Coil": 5, "PP_Resin": 15,
         "Poly_F_EU": 15, "EPDM": 40, "NR_201": 40, "LGS_4_W": 10, "TGP_5_Q": 10}
COMPONENT = {"SR_MCU": "Semiconductor", "SR_MOS_KIT": "Semiconductor", "AL_Sheet": "Steel",
             "HSS_Coil": "Steel", "PP_Resin": "Plastic", "Poly_F_EU": "Plastic", "EPDM": "Elastomer",
             "NR_201": "Elastomer", "LGS_4_W": "Glass", "TGP_5_Q": "Glass"}
PRICE = {"SR_MCU": 20, "SR_MOS_KIT": 30, "AL_Sheet": 100, "HSS_Coil": 60, "PP_Resin": 40,
         "Poly_F_EU": 70, "EPDM": 20, "NR_201": 30, "LGS_4_W": 30, "TGP_5_Q": 35}
SCALE = {1: (1, 1, 1), 2: (.5, .5, .5), 3: (.7, .7, .7), 4: (.2, .2, .2),
         5: (.8, .8, .8), 6: (.1, .1, .1), 7: (.8, .5, .4), 8: (.9, .9, .9)}


def make_baseline() -> dict:
    rng = np.random.default_rng(0)
    bom = {s: {"units": UNITS[s], "component": COMPONENT[s], "cm": COMPONENT_CM[COMPONENT[s]]} for s in SKUS}
    suppliers = {}
    for i in range(30):
        sku = SKUS[i // 3]
        suppliers[f"Supplier_{i + 1}"] = {"sku": sku, "cm": bom[sku]["cm"], "lead_days": 10.0,
                                          "price": float(PRICE[sku]), "lead_sd_days": 2.0,
                                          "defect_share": 0.1, "n_rows": 0, "pooled": True}
    mode = lambda a, b, cost: {"lead_a": a, "lead_b": b, "lead_resid_sd": 1.0,
                               "cost_per_unit": cost, "mean_lead_days": a + b * 5000, "n": 50}
    lane = {"mode_mix": {"Air": 0.55, "Ship": 0.35, "Road": 0.05, "Rail": 0.05},
            "modes": {"Air": mode(1.5, 0.0002, 10.0), "Ship": mode(5.0, 0.003, 2.5),
                      "Road": mode(3.0, 0.001, 1.9), "Rail": mode(3.0, 0.0015, 1.8)}}
    weeks = np.arange(260)
    season = 1 + 0.2 * np.sin(2 * np.pi * weeks / 52)
    hist = {}
    for r, sc in SCALE.items():
        hist[f"Retail_{r}"] = {}
        for p, k in zip("ABC", sc):
            base = 2000 * k * (1.05 ** (weeks / 52)) * season
            hist[f"Retail_{r}"][p] = [float(v) for v in base * rng.lognormal(0, 0.05, 260)]
    return {"source": {"xlsx": "synthetic", "xlsx_sha256": "synthetic", "prepared_at": "n/a"},
            "bom": bom, "suppliers": suppliers,
            "lanes": {"cm_mfg": lane, "mfg_dc": lane, "dc_retail": lane},
            "history_years": [2020, 2021, 2022, 2023, 2024], "demand_history": hist,
            "co2_factors": CO2_FACTORS, "co2_ton_per_unit": CO2_TON_PER_UNIT}


@pytest.fixture
def baseline():
    return make_baseline()


@pytest.fixture
def baseline_path(tmp_path, baseline):
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps(baseline))
    return p
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_loader.py -v`
Expected: 5 passed (the `realdata` test takes ~10 s; it is skipped on machines without the workbook).

- [ ] **Step 6: Commit**

```bash
git add sciti/data/loader.py tests/conftest.py tests/test_loader.py
git commit -m "feat: workbook loader writes baseline.json and validation report

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Demand model

**Files:**
- Create: `sciti/data/demand.py`
- Test: `tests/test_demand.py`

**Interfaces:**
- Consumes: baseline `demand_history` (Task 2 schema).
- Produces:
  - `SeriesFit` dataclass: `level: float, growth: float, season: list[float], resid_sd: float, phi: float, n_hist: int`
  - `fit_series(values: Sequence[float], trend_cap: float) -> SeriesFit`
  - `DemandModel(fits: dict[tuple[str, str], SeriesFit], growth_mult: float = 1.0)`
    - `.from_baseline(baseline: dict, trend_cap: float, growth_mult: float) -> DemandModel` (classmethod)
    - `.keys -> list[tuple[str, str]]` sorted `(retailer, product)`
    - `.expected(retailer: str, product: str, week: int) -> float` (week is 1-based future week)
    - `.generate(weeks: int, rng: np.random.Generator) -> dict[tuple[str, str], np.ndarray]` (integer-valued float arrays, length `weeks`)

Model (spec §5.2): `E[d_i] = level · (1+g)^(i/52) · season[i mod 52]`, `i` counts weeks from the first history week; future week `w` has `i = n_hist + w − 1`; `g = clip(growth, ±cap) · growth_mult`. Noise is log-AR(1): `e_i = φ e_{i−1} + sqrt(1−φ²) · sd · z`, `d = E · exp(e − sd²/2)`, rounded, floored at 0. `φ` is the lag-1 autocorrelation of log residuals if > 0.2, else 0.

- [ ] **Step 1: Write the failing tests**

`tests/test_demand.py`:

```python
import numpy as np
import pytest

from sciti.data.demand import fit_series, DemandModel


def synthetic(growth=0.10, years=5, noise=0.0, seed=0):
    i = np.arange(52 * years)
    season = 1 + 0.3 * np.sin(2 * np.pi * i / 52)
    rng = np.random.default_rng(seed)
    return 1000 * (1 + growth) ** (i / 52) * season * rng.lognormal(0, noise, i.size) if noise else \
        1000 * (1 + growth) ** (i / 52) * season


def test_fit_recovers_growth_and_season():
    f = fit_series(synthetic(0.10), trend_cap=0.15)
    assert f.growth == pytest.approx(0.10, abs=0.005)
    assert np.mean(f.season) == pytest.approx(1.0)
    assert max(f.season) == pytest.approx(1.3, abs=0.02)
    assert f.n_hist == 260


def test_growth_is_capped():
    f = fit_series(synthetic(0.40), trend_cap=0.15)
    assert f.growth == 0.15


def test_generate_is_seeded_and_nonnegative(baseline):
    m = DemandModel.from_baseline(baseline, trend_cap=0.15, growth_mult=1.0)
    a = m.generate(156, np.random.default_rng(1))
    b = m.generate(156, np.random.default_rng(1))
    k = ("Retail_1", "A")
    assert np.array_equal(a[k], b[k])
    assert len(a[k]) == 156
    assert all((v >= 0).all() and np.array_equal(v, np.round(v)) for v in a.values())
    assert m.keys == sorted(m.keys) and len(m.keys) == 24


def test_first_year_matches_expected_within_5pct(baseline):
    m = DemandModel.from_baseline(baseline, trend_cap=0.15, growth_mult=1.0)
    k = ("Retail_3", "B")
    expected = sum(m.expected(*k, w) for w in range(1, 53))
    sims = [m.generate(52, np.random.default_rng(s))[k].sum() for s in range(10)]
    assert np.mean(sims) == pytest.approx(expected, rel=0.05)


def test_growth_mult_scales_future(baseline):
    lo = DemandModel.from_baseline(baseline, 0.15, growth_mult=0.0)
    hi = DemandModel.from_baseline(baseline, 0.15, growth_mult=2.0)
    assert hi.expected("Retail_1", "A", 150) > lo.expected("Retail_1", "A", 150)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_demand.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.data.demand'`

- [ ] **Step 3: Implement `sciti/data/demand.py`**

```python
"""Future demand from 2020–2024 weekly history (spec §5.2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass
class SeriesFit:
    level: float
    growth: float
    season: list[float]
    resid_sd: float
    phi: float
    n_hist: int


def fit_series(values: Sequence[float], trend_cap: float) -> SeriesFit:
    y = np.asarray(values, dtype=float)
    years = y.size // 52
    y = y[: years * 52]
    annual = y.reshape(years, 52).sum(axis=1)
    slope = np.polyfit(np.arange(years), np.log(np.maximum(annual, 1e-9)), 1)[0]
    growth = float(np.clip(np.exp(slope) - 1, -trend_cap, trend_cap))
    i = np.arange(y.size)
    trend = (1 + growth) ** (i / 52)
    detr = y / trend
    season = detr.reshape(years, 52).mean(axis=0)
    season = season / season.mean()
    level = float(np.mean(detr / season[i % 52]))
    fitted = level * trend * season[i % 52]
    resid = np.log(np.maximum(y, 1e-9) / fitted)
    sd = float(resid.std(ddof=1))
    phi = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if sd > 0 else 0.0
    return SeriesFit(level, growth, [float(s) for s in season], sd, phi if phi > 0.2 else 0.0, int(y.size))


class DemandModel:
    def __init__(self, fits: dict[tuple[str, str], SeriesFit], growth_mult: float = 1.0):
        self.fits = fits
        self.growth_mult = growth_mult
        self.keys = sorted(fits)

    @classmethod
    def from_baseline(cls, baseline: dict, trend_cap: float, growth_mult: float) -> "DemandModel":
        fits = {(r, p): fit_series(series, trend_cap)
                for r, prods in baseline["demand_history"].items() for p, series in prods.items()}
        return cls(fits, growth_mult)

    def expected(self, retailer: str, product: str, week: int) -> float:
        f = self.fits[(retailer, product)]
        i = f.n_hist + week - 1
        return f.level * (1 + f.growth * self.growth_mult) ** (i / 52) * f.season[i % 52]

    def generate(self, weeks: int, rng: np.random.Generator) -> dict[tuple[str, str], np.ndarray]:
        out = {}
        for key in self.keys:
            f = self.fits[key]
            z = rng.standard_normal(weeks)
            e = np.empty(weeks)
            prev = 0.0
            scale = np.sqrt(1 - f.phi ** 2) * f.resid_sd
            for t in range(weeks):
                prev = f.phi * prev + scale * z[t]
                e[t] = prev
            mean = np.array([self.expected(*key, w) for w in range(1, weeks + 1)])
            out[key] = np.maximum(0.0, np.round(mean * np.exp(e - f.resid_sd ** 2 / 2)))
        return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_demand.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add sciti/data/demand.py tests/test_demand.py
git commit -m "feat: seasonal-trend demand model with seeded log-AR(1) noise

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Network builder

**Files:**
- Create: `sciti/network.py`
- Test: `tests/test_network.py`

**Interfaces:**
- Consumes: baseline dict (Task 2), `Config.assumptions.dc_split`, `.mfg_share` (Task 1).
- Produces:
  - `ROLES = ("Supplier", "CM", "MFG", "DC", "Retail")`, `PRODUCTS = ("A", "B", "C")`
  - `Node` dataclass: `id: str, role: str, city: str, lat: float, lon: float, skus: tuple[str, ...]` (Supplier: its sku; CM: the skus it makes; others: empty)
  - `Network` dataclass:
    - `nodes: dict[str, Node]`, `order: list[str]` (upstream → downstream, fixed)
    - `upstream: dict[str, list[str]]`, `downstream: dict[str, list[str]]` (sorted lists)
    - `bom: dict[str, int]` (sku → units per product), `skus: list[str]`
    - `suppliers_of: dict[str, list[str]]` (sku → supplier ids), `cm_of: dict[str, str]` (sku → CM id)
    - `source_share: dict[str, dict[str, float]]` (buyer → {seller: share}) for DC←MFG and Retail←DC
    - `partners(node_id) -> list[str]` (sorted upstream + downstream)
    - `miles(a: str, b: str) -> float`
    - `by_role(role: str) -> list[str]` (in `order`)
  - `great_circle_miles(lat1, lon1, lat2, lon2) -> float`
  - `build_network(baseline: dict, assumptions: Assumptions) -> Network`

- [ ] **Step 1: Write the failing tests**

`tests/test_network.py`:

```python
import pytest

from sciti.config import Assumptions
from sciti.network import build_network, great_circle_miles


@pytest.fixture
def net(baseline):
    return build_network(baseline, Assumptions())


def test_48_nodes_in_tier_order(net):
    assert len(net.order) == 48
    roles = [net.nodes[n].role for n in net.order]
    assert roles == sorted(roles, key=["Supplier", "CM", "MFG", "DC", "Retail"].index)
    assert net.order[:2] == ["Supplier_1", "Supplier_2"]
    assert net.order[-1] == "Retail_8"


def test_links_follow_document(net):
    assert net.downstream["Supplier_1"] == ["CM_1"]
    assert net.downstream["CM_4"] == ["MFG_China", "MFG_US"]
    assert net.downstream["MFG_US"] == ["DC_Dubai", "DC_Houston", "DC_Shanghai", "DC_Sofia"]
    assert net.upstream["Retail_3"] == ["DC_Dubai", "DC_Sofia"]
    assert net.upstream["Retail_7"] == ["DC_Shanghai"]
    assert net.downstream["DC_Houston"] == ["Retail_1", "Retail_2"]


def test_shares_sum_to_one(net):
    for buyer, shares in net.source_share.items():
        assert sum(shares.values()) == pytest.approx(1.0), buyer
    assert net.source_share["Retail_1"] == {"DC_Houston": 1.0}


def test_bom_and_sourcing(net):
    assert sum(net.bom.values()) == 160
    assert net.suppliers_of["EPDM"] == ["Supplier_19", "Supplier_20", "Supplier_21"]
    assert net.cm_of["EPDM"] == "CM_3"
    assert net.nodes["CM_3"].skus == ("PP_Resin", "Poly_F_EU", "EPDM", "NR_201")


def test_distance_la_to_shenzhen(net):
    assert net.miles("MFG_US", "MFG_China") == pytest.approx(7250, rel=0.03)
    assert great_circle_miles(0, 0, 0, 0) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_network.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.network'`

- [ ] **Step 3: Implement `sciti/network.py`**

```python
"""Ridge Line network: 48 nodes, links per the document (spec §5.1)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from sciti.data.loader import SKUS

ROLES = ("Supplier", "CM", "MFG", "DC", "Retail")
PRODUCTS = ("A", "B", "C")

SITES = {  # id: (role, city, lat, lon)
    "CM_1": ("CM", "Taipei, Taiwan", 25.03, 121.57),
    "CM_2": ("CM", "Bangalore, India", 12.97, 77.59),
    "CM_3": ("CM", "Guadalajara, Mexico", 20.67, -103.35),
    "CM_4": ("CM", "Munich, Germany", 48.14, 11.58),
    "MFG_US": ("MFG", "Los Angeles, CA", 34.05, -118.24),
    "MFG_China": ("MFG", "Shenzhen, China", 22.54, 114.06),
    "DC_Houston": ("DC", "Houston, TX", 29.76, -95.37),
    "DC_Dubai": ("DC", "Dubai, UAE", 25.20, 55.27),
    "DC_Shanghai": ("DC", "Shanghai, China", 31.23, 121.47),
    "DC_Sofia": ("DC", "Sofia, Bulgaria", 42.70, 23.32),
    "Retail_1": ("Retail", "Columbus, OH", 39.96, -83.00),
    "Retail_2": ("Retail", "São Paulo, Brazil", -23.55, -46.63),
    "Retail_3": ("Retail", "Barcelona, Spain", 41.39, 2.17),
    "Retail_4": ("Retail", "Nairobi, Kenya", -1.29, 36.82),
    "Retail_5": ("Retail", "Mumbai, India", 19.08, 72.88),
    "Retail_6": ("Retail", "Singapore", 1.35, 103.82),
    "Retail_7": ("Retail", "Tokyo, Japan", 35.68, 139.69),
    "Retail_8": ("Retail", "Melbourne, Australia", -37.81, 144.96),
}
DC_RETAIL = {
    "DC_Houston": ["Retail_1", "Retail_2"],
    "DC_Dubai": ["Retail_3", "Retail_4", "Retail_5"],
    "DC_Sofia": ["Retail_3"],
    "DC_Shanghai": ["Retail_5", "Retail_6", "Retail_7", "Retail_8"],
}


def great_circle_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 3958.8 * 2 * math.asin(min(1.0, math.sqrt(a)))


@dataclass
class Node:
    id: str
    role: str
    city: str
    lat: float
    lon: float
    skus: tuple[str, ...] = ()


@dataclass
class Network:
    nodes: dict[str, Node]
    order: list[str]
    upstream: dict[str, list[str]]
    downstream: dict[str, list[str]]
    bom: dict[str, int]
    skus: list[str]
    suppliers_of: dict[str, list[str]]
    cm_of: dict[str, str]
    source_share: dict[str, dict[str, float]] = field(default_factory=dict)

    def partners(self, node_id: str) -> list[str]:
        return sorted(set(self.upstream[node_id]) | set(self.downstream[node_id]))

    def miles(self, a: str, b: str) -> float:
        na, nb = self.nodes[a], self.nodes[b]
        return great_circle_miles(na.lat, na.lon, nb.lat, nb.lon)

    def by_role(self, role: str) -> list[str]:
        return [n for n in self.order if self.nodes[n].role == role]


def build_network(baseline: dict, assumptions) -> Network:
    bom = {sku: v["units"] for sku, v in baseline["bom"].items()}
    skus = [s for s in SKUS if s in baseline["bom"]]  # BOM order; baseline.json keys are sorted
    cm_of = {sku: v["cm"] for sku, v in baseline["bom"].items()}
    nodes: dict[str, Node] = {}
    sup_ids = sorted(baseline["suppliers"], key=lambda s: int(s.split("_")[1]))
    for k, sid in enumerate(sup_ids):
        s = baseline["suppliers"][sid]
        _, _, clat, clon = SITES[s["cm"]]
        ang = 2 * math.pi * (k % 12) / 12   # illustrative ring around the CM (spec §5.1)
        nodes[sid] = Node(sid, "Supplier", f"near {SITES[s['cm']][1]} (illustrative)",
                          clat + 4 * math.sin(ang), clon + 4 * math.cos(ang), (s["sku"],))
    for nid, (role, city, lat, lon) in SITES.items():
        made = tuple(sku for sku in skus if cm_of[sku] == nid) if role == "CM" else ()
        nodes[nid] = Node(nid, role, city, lat, lon, made)
    order = sup_ids + [n for r in ROLES[1:] for n in sorted((i for i in SITES if SITES[i][0] == r),
                                                             key=_natural)]
    up = {n: [] for n in order}
    down = {n: [] for n in order}

    def link(a, b):
        down[a].append(b)
        up[b].append(a)

    for sid in sup_ids:
        link(sid, baseline["suppliers"][sid]["cm"])
    for cm in ("CM_1", "CM_2", "CM_3", "CM_4"):
        for mfg in ("MFG_US", "MFG_China"):
            link(cm, mfg)
    for mfg in ("MFG_US", "MFG_China"):
        for dc in DC_RETAIL:
            link(mfg, dc)
    for dc, rets in DC_RETAIL.items():
        for r in rets:
            link(dc, r)
    up = {k: sorted(v) for k, v in up.items()}
    down = {k: sorted(v) for k, v in down.items()}
    suppliers_of = {sku: [s for s in sup_ids if baseline["suppliers"][s]["sku"] == sku] for sku in skus}
    share = {}
    for dc in DC_RETAIL:
        share[dc] = dict(assumptions.mfg_share[dc])
    for r in [n for n in order if nodes[n].role == "Retail"]:
        share[r] = dict(assumptions.dc_split.get(r, {up[r][0]: 1.0}))
    for buyer, s in share.items():
        if sorted(s) != up[buyer] or abs(sum(s.values()) - 1) > 1e-9:
            raise ValueError(f"source shares for {buyer} must cover {up[buyer]} and sum to 1: {s}")
    return Network(nodes, order, up, down, bom, skus, suppliers_of, cm_of, share)


def _natural(node_id: str):
    head, _, tail = node_id.rpartition("_")
    return (head, int(tail)) if tail.isdigit() else (node_id, 0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_network.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add sciti/network.py tests/test_network.py
git commit -m "feat: build 48-node Ridge Line network from baseline

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Technology catalog and effects

**Files:**
- Create: `sciti/tech/catalog.yaml`, `sciti/tech/catalog.py`, `sciti/tech/effects.py`
- Test: `tests/test_tech.py`

**Interfaces:**
- Consumes: `Network` (Task 4), `Assumptions` (Task 1).
- Produces:
  - `sciti.tech.catalog.Effect` dataclass: `param: str, op: Literal["mul", "add"], value: float`
  - `Tech` dataclass: `id, name, observatory_name, eligible_roles: tuple[str, ...], cost_one_time: dict[str, float], cost_per_week: dict[str, float], setup_weeks: int, network_requirement: Literal["solo", "pair", "chain"], group_bonus: float, effects: tuple[Effect, ...], evidence: str, assumption: bool`
  - `TechHolding` dataclass: `tech: str, adopted_week: int, active_week: int, coalition_id: str | None = None`
  - `load_catalog(path: str | Path | None = None) -> dict[str, Tech]` (None → packaged `catalog.yaml`); raises `ValueError` on unknown params/roles
  - `catalog_hash(path: str | Path | None = None) -> str`
  - `sciti.tech.effects.PARAMS: tuple[str, ...]`
  - `base_params(role: str, assumptions: Assumptions) -> dict[str, float]`
  - `effective_params(node_id: str, week: int, holdings: dict[str, dict[str, TechHolding]], catalog: dict[str, Tech], network: Network, base: dict[str, float]) -> dict[str, float]`
    - `holdings[node_id][tech_id]`; a holding is active when `week >= active_week`.
    - `solo`: full effect. `pair`: effect only if at least one partner (`network.partners`) holds the same tech active. `chain`: effect scaled by `s` = share of the node's downstream partners (retailers: upstream partners) holding it active.
    - Scaling: `mul m → 1 − (1 − m)·s`; `add v → v·s`. Group bonus when `coalition_id` is set: `mul m → max(0, 1 − (1 − m)(1 + bonus))`; `add v → v·(1 + bonus)`.
    - Techs applied in sorted id order.

Parameters (`PARAMS`) and base values:

| param | base | meaning |
|---|---|---|
| `forecast_skill` | 0.0 | weight on the demand model's expected value in the node's forecast |
| `visibility` | 0.0 | weight on end-customer demand signal instead of orders received |
| `record_error_sd` | `assumptions.record_error_sd` | SD of inventory record error (fraction) |
| `shrink_rate` | `assumptions.shrink_rate_weekly` | weekly stock loss fraction |
| `capacity_mult` | 1.0 | multiplies base capacity |
| `ship_cost_mult` | 1.0 | multiplies outbound shipping cost |
| `co2_mult` | 1.0 | multiplies outbound CO2 |
| `handling_cost_per_unit` | DC: `assumptions.handling_cost_per_unit`, else 0 | per unit shipped out |
| `dispatch_delay_days` | DC: `assumptions.dispatch_delay_days`, else 0 | added to outbound lead time |
| `defect_mult` | 1.0 | multiplies supplier defect share |
| `recovery_mult` | 1.0 | multiplies disruption duration at this node |
| `early_warning_weeks` | 0.0 | weeks of warning before an upstream disruption |

- [ ] **Step 1: Write the failing tests**

`tests/test_tech.py`:

```python
import pytest

from sciti.config import Assumptions
from sciti.network import build_network
from sciti.tech.catalog import load_catalog, TechHolding, catalog_hash
from sciti.tech.effects import base_params, effective_params


@pytest.fixture
def world(baseline):
    return build_network(baseline, Assumptions()), load_catalog()


def H(tech, week=1, coalition=None):
    return TechHolding(tech=tech, adopted_week=week, active_week=week, coalition_id=coalition)


def test_catalog_has_the_8_mvp_techs():
    cat = load_catalog()
    assert sorted(cat) == sorted(["ml_forecast", "control_tower", "rfid", "aps", "routing",
                                  "wh_robotics", "blockchain", "risk_intel"])
    assert all(t.assumption for t in cat.values())
    assert cat["wh_robotics"].eligible_roles == ("DC",)
    assert len(catalog_hash()) == 64


def test_bad_catalog_param_rejected(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("- {id: x, name: X, observatory_name: X, eligible_roles: [DC], cost_one_time: {DC: 1},"
                 " cost_per_week: {DC: 1}, setup_weeks: 1, network_requirement: solo, group_bonus: 0,"
                 " effects: [{param: nope, op: mul, value: 0.5}], evidence: e, assumption: true}\n")
    with pytest.raises(ValueError):
        load_catalog(p)


def test_solo_effect_applies_after_setup(world):
    net, cat = world
    base = base_params("Retail", Assumptions())
    holdings = {"Retail_1": {"ml_forecast": TechHolding("ml_forecast", 1, 5)}}
    assert effective_params("Retail_1", 4, holdings, cat, net, base)["forecast_skill"] == 0.0
    assert effective_params("Retail_1", 5, holdings, cat, net, base)["forecast_skill"] == pytest.approx(0.3)


def test_pair_needs_partner(world):
    net, cat = world
    base = base_params("Supplier", Assumptions())
    alone = {"Supplier_1": {"blockchain": H("blockchain")}}
    assert effective_params("Supplier_1", 2, alone, cat, net, base)["defect_mult"] == 1.0
    both = {"Supplier_1": {"blockchain": H("blockchain")}, "CM_1": {"blockchain": H("blockchain")}}
    assert effective_params("Supplier_1", 2, both, cat, net, base)["defect_mult"] == pytest.approx(0.6)


def test_chain_scales_by_downstream_share(world):
    net, cat = world
    base = base_params("DC", Assumptions())
    h = {"DC_Houston": {"control_tower": H("control_tower")}, "Retail_1": {"control_tower": H("control_tower")}}
    assert effective_params("DC_Houston", 2, h, cat, net, base)["visibility"] == pytest.approx(0.5)


def test_group_bonus(world):
    net, cat = world
    base = base_params("DC", Assumptions())
    h = {"DC_Houston": {"routing": H("routing", coalition="c1")}}
    # routing ship_cost_mult 0.92, bonus 0.25 → 1 - 0.08*1.25 = 0.90
    assert effective_params("DC_Houston", 2, h, cat, net, base)["ship_cost_mult"] == pytest.approx(0.90)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_tech.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.tech.catalog'`

- [ ] **Step 3: Write `sciti/tech/catalog.yaml`**

Costs are assumptions sized against weekly node revenue (retail product ≈ $13k/unit, network ≈ 15k products/week).

```yaml
# SCITI 1 MVP technology catalog. All effect sizes and costs are assumptions (spec §6, §9.7).
- id: ml_forecast
  name: ML demand forecasting
  observatory_name: ML demand forecasting
  eligible_roles: [Retail, DC, MFG]
  cost_one_time: {Retail: 400000, DC: 600000, MFG: 900000}
  cost_per_week: {Retail: 4000, DC: 6000, MFG: 9000}
  setup_weeks: 8
  network_requirement: solo
  group_bonus: 0.25
  effects: [{param: forecast_skill, op: add, value: 0.3}]
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: control_tower
  name: Supply chain control tower
  observatory_name: Supply chain control towers
  eligible_roles: [Supplier, CM, MFG, DC, Retail]
  cost_one_time: {Supplier: 150000, CM: 500000, MFG: 1200000, DC: 700000, Retail: 250000}
  cost_per_week: {Supplier: 1500, CM: 5000, MFG: 12000, DC: 7000, Retail: 2500}
  setup_weeks: 12
  network_requirement: chain
  group_bonus: 0.25
  effects: [{param: visibility, op: add, value: 1.0}]
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: rfid
  name: Item-level RFID
  observatory_name: Item-level RFID
  eligible_roles: [CM, MFG, DC, Retail]
  cost_one_time: {CM: 300000, MFG: 500000, DC: 400000, Retail: 200000}
  cost_per_week: {CM: 3000, MFG: 5000, DC: 4000, Retail: 2000}
  setup_weeks: 6
  network_requirement: solo
  group_bonus: 0.25
  effects:
    - {param: record_error_sd, op: mul, value: 0.2}
    - {param: shrink_rate, op: mul, value: 0.5}
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: aps
  name: Advanced planning and scheduling
  observatory_name: Advanced planning and scheduling
  eligible_roles: [CM, MFG]
  cost_one_time: {CM: 600000, MFG: 1500000}
  cost_per_week: {CM: 6000, MFG: 15000}
  setup_weeks: 10
  network_requirement: solo
  group_bonus: 0.25
  effects: [{param: capacity_mult, op: add, value: 0.08}]
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: routing
  name: Vehicle routing and path optimization
  observatory_name: Vehicle routing and path optimization
  eligible_roles: [CM, MFG, DC]
  cost_one_time: {CM: 200000, MFG: 400000, DC: 300000}
  cost_per_week: {CM: 2000, MFG: 4000, DC: 3000}
  setup_weeks: 4
  network_requirement: solo
  group_bonus: 0.25
  effects:
    - {param: ship_cost_mult, op: mul, value: 0.92}
    - {param: co2_mult, op: mul, value: 0.90}
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: wh_robotics
  name: Warehouse robotics
  observatory_name: Warehouse robotics
  eligible_roles: [DC]
  cost_one_time: {DC: 2500000}
  cost_per_week: {DC: 15000}
  setup_weeks: 16
  network_requirement: solo
  group_bonus: 0.25
  effects:
    - {param: handling_cost_per_unit, op: mul, value: 0.8}
    - {param: dispatch_delay_days, op: add, value: -1.0}
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: blockchain
  name: Blockchain traceability
  observatory_name: Blockchain traceability
  eligible_roles: [Supplier, CM, MFG]
  cost_one_time: {Supplier: 100000, CM: 300000, MFG: 500000}
  cost_per_week: {Supplier: 1000, CM: 3000, MFG: 5000}
  setup_weeks: 8
  network_requirement: pair
  group_bonus: 0.25
  effects: [{param: defect_mult, op: mul, value: 0.6}]
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
- id: risk_intel
  name: Supply chain risk intelligence
  observatory_name: Supply chain risk intelligence
  eligible_roles: [CM, MFG, DC]
  cost_one_time: {CM: 250000, MFG: 500000, DC: 300000}
  cost_per_week: {CM: 2500, MFG: 5000, DC: 3000}
  setup_weeks: 4
  network_requirement: solo
  group_bonus: 0.25
  effects:
    - {param: recovery_mult, op: mul, value: 0.6}
    - {param: early_warning_weeks, op: add, value: 2.0}
  evidence: "Placeholder; replace with cited effect size."
  assumption: true
```

- [ ] **Step 4: Implement `sciti/tech/catalog.py`**

```python
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
```

- [ ] **Step 5: Implement `sciti/tech/effects.py`**

```python
"""Turn a node's active technologies into effective parameters (spec §6)."""
from __future__ import annotations

PARAMS = ("forecast_skill", "visibility", "record_error_sd", "shrink_rate", "capacity_mult",
          "ship_cost_mult", "co2_mult", "handling_cost_per_unit", "dispatch_delay_days",
          "defect_mult", "recovery_mult", "early_warning_weeks")


def base_params(role: str, assumptions) -> dict[str, float]:
    is_dc = role == "DC"
    return {"forecast_skill": 0.0, "visibility": 0.0,
            "record_error_sd": assumptions.record_error_sd,
            "shrink_rate": assumptions.shrink_rate_weekly,
            "capacity_mult": 1.0, "ship_cost_mult": 1.0, "co2_mult": 1.0,
            "handling_cost_per_unit": assumptions.handling_cost_per_unit if is_dc else 0.0,
            "dispatch_delay_days": assumptions.dispatch_delay_days if is_dc else 0.0,
            "defect_mult": 1.0, "recovery_mult": 1.0, "early_warning_weeks": 0.0}


def _active(holdings, node_id, tech_id, week) -> bool:
    h = holdings.get(node_id, {}).get(tech_id)
    return h is not None and week >= h.active_week


def effective_params(node_id, week, holdings, catalog, network, base) -> dict[str, float]:
    p = dict(base)
    mine = holdings.get(node_id, {})
    for tech_id in sorted(mine):
        if not _active(holdings, node_id, tech_id, week):
            continue
        tech = catalog[tech_id]
        if tech.network_requirement == "solo":
            s = 1.0
        elif tech.network_requirement == "pair":
            s = 1.0 if any(_active(holdings, q, tech_id, week) for q in network.partners(node_id)) else 0.0
        else:
            role = network.nodes[node_id].role
            ref = network.upstream[node_id] if role == "Retail" else network.downstream[node_id]
            s = sum(_active(holdings, q, tech_id, week) for q in ref) / len(ref) if ref else 0.0
        bonus = tech.group_bonus if mine[tech_id].coalition_id else 0.0
        for e in tech.effects:
            if e.op == "mul":
                m = 1 - (1 - e.value) * s
                m = max(0.0, 1 - (1 - m) * (1 + bonus))
                p[e.param] *= m
            else:
                p[e.param] += e.value * s * (1 + bonus)
    p["dispatch_delay_days"] = max(0.0, p["dispatch_delay_days"])
    p["forecast_skill"] = min(1.0, p["forecast_skill"])
    p["visibility"] = min(1.0, p["visibility"])
    return p
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_tech.py -v`
Expected: 6 passed

- [ ] **Step 7: Run the whole suite and commit**

Run: `.venv/bin/pytest -v`
Expected: all Part A tests pass.

```bash
git add sciti/tech/catalog.yaml sciti/tech/catalog.py sciti/tech/effects.py tests/test_tech.py
git commit -m "feat: 8-technology catalog with solo/pair/chain effects and group bonus

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
