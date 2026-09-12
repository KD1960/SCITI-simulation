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
