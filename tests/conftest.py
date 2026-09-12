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
