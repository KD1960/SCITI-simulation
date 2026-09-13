import csv
import json
from pathlib import Path

import numpy as np
import pytest

from sciti.config import Config
from sciti.data.demand import DemandModel
from sciti.runner import run

REAL_BASELINE = Path(__file__).resolve().parents[1] / "data" / "baseline.json"


def _check(baseline_file: Path, tmp_path):
    base = json.loads(baseline_file.read_text())
    dm = DemandModel.from_baseline(base, 0.15, 1.0)
    fill, sims, lead_ratio = [], [], []
    expected = sum(dm.expected(r, p, w) for r, p in dm.keys for w in range(1, 53))
    for seed in range(10):
        d = run(Config(name="cal", seed=seed, weeks=52, baseline_path=str(baseline_file), output_dir=str(tmp_path)),
                run_dir=tmp_path / f"c{seed}")
        rows = [r for r in csv.DictReader(open(d / "weekly_nodes.csv")) if r["role"] == "Retail"]
        sims.append(sum(float(r["demand"]) for r in rows))
        fill.append(json.loads((d / "summary.json").read_text())["fill_rate"])
        ships = [r for r in csv.DictReader(open(d / "shipments.csv")) if r["mode"] != "Supplier"]
        for mode in sorted({r["mode"] for r in ships}):
            m = base["lanes"]["mfg_dc"]["modes"].get(mode)
            sub = [r for r in ships if r["mode"] == mode and r["src"].startswith("MFG")]
            if m and sub:
                predicted = np.mean([max(1.0, m["lead_a"] + m["lead_b"] * float(r["miles"])) for r in sub])
                actual = np.mean([float(r["lead_days"]) for r in sub])
                lead_ratio.append(actual / predicted)
    print(f"\nfill rate mean {np.mean(fill):.3f}; demand sim/expected {np.mean(sims) / expected:.3f}; "
          f"lead actual/predicted {np.mean(lead_ratio):.3f}")
    assert np.mean(sims) == pytest.approx(expected, rel=0.05)
    assert np.mean(lead_ratio) == pytest.approx(1.0, rel=0.15)
    assert np.mean(fill) > 0.80


def test_calibration_synthetic(baseline_path, tmp_path):
    _check(baseline_path, tmp_path)


@pytest.mark.realdata
@pytest.mark.skipif(not REAL_BASELINE.exists(), reason="run `sciti prepare` first")
def test_calibration_real(tmp_path):
    _check(REAL_BASELINE, tmp_path)
