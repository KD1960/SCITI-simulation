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


def _check_columns(xlsx: Path) -> None:
    """Validate that required columns exist. Stops before any parsing."""
    missing = []

    # Check Supplier Data transaction columns (A:L)
    tx_df = pd.read_excel(xlsx, sheet_name="Supplier Data", nrows=0)
    req_tx = ["Lead Time", "Supplier", "Product Name", "Sentiment Score"]
    for col in req_tx:
        if col not in tx_df.columns:
            missing.append(("Supplier Data", col))

    # Check shipment lane header columns per block
    ship_df = pd.read_excel(xlsx, sheet_name="Shipment_CM_MFG_DC_Retailers", header=None, nrows=1)
    req_cols = ["Mode", "Distance (Miles)", "Lead Time (days)", "Shipping Cost/Unit"]
    block_names = ["cm_mfg", "mfg_dc", "dc_retail"]
    for block_name, start in zip(block_names, [0, 15, 30]):
        if start + 14 <= len(ship_df.columns):
            lane_cols = [ship_df.iloc[0, start + i] for i in range(14)]
            for col in req_cols:
                if col not in lane_cols:
                    missing.append((f"Shipment_CM_MFG_DC_Retailers[{block_name}]", col))

    if missing:
        msg = "Workbook is missing columns: " + "; ".join(f"({sheet}, {col})" for sheet, col in missing)
        raise ValueError(msg)


def prepare(xlsx: Path, out_dir: Path) -> dict:
    xlsx, out_dir = Path(xlsx), Path(out_dir)
    required = ["Glossary", "Supplier Data", "Shipment_CM_MFG_DC_Retailers", "Demand_Retailer"]
    present = pd.ExcelFile(xlsx).sheet_names
    missing = [s for s in required if s not in present]
    if missing:
        raise ValueError(f"Workbook is missing sheets: {missing}")
    _check_columns(xlsx)
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
