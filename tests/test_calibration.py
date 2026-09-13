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
    fill, sims, lead_engine_vs_lane_model = [], [], []
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
                # This uses the engine's own sampling formula (sciti.engine.ops.sample_lane), so
                # it verifies the engine follows the fitted lane model, not that the lane model
                # matches the real workbook data (see test_transit_times_match_workbook_by_mode).
                lane_model = np.mean([max(1.0, m["lead_a"] + m["lead_b"] * float(r["miles"])) for r in sub])
                engine = np.mean([float(r["lead_days"]) for r in sub])
                lead_engine_vs_lane_model.append(engine / lane_model)
    print(f"\nfill rate mean {np.mean(fill):.3f}; demand sim/expected {np.mean(sims) / expected:.3f}; "
          f"lead engine/lane-model {np.mean(lead_engine_vs_lane_model):.3f}")
    assert np.mean(sims) == pytest.approx(expected, rel=0.05)
    assert np.mean(lead_engine_vs_lane_model) == pytest.approx(1.0, rel=0.15)
    assert np.mean(fill) > 0.80


def test_calibration_synthetic(baseline_path, tmp_path):
    _check(baseline_path, tmp_path)


@pytest.mark.realdata
@pytest.mark.skipif(not REAL_BASELINE.exists(), reason="run `sciti prepare` first")
def test_calibration_real(tmp_path):
    _check(REAL_BASELINE, tmp_path)


@pytest.mark.realdata
@pytest.mark.skipif(not REAL_BASELINE.exists(), reason="run `sciti prepare` first")
def test_transit_times_match_workbook_by_mode(tmp_path):
    """Compares simulated MFG->DC transit days against the workbook's own per-mode mean,
    independent of the engine's lane-sampling formula (unlike the lead_ratio check above)."""
    base = json.loads(REAL_BASELINE.read_text())
    ships = []
    for seed in range(10):
        d = run(Config(name="transit", seed=seed, weeks=52,  # policy defaults to "none"
                        baseline_path=str(REAL_BASELINE), output_dir=str(tmp_path)),
                run_dir=tmp_path / f"t{seed}")
        rows = csv.DictReader(open(d / "shipments.csv"))
        ships.extend(r for r in rows if r["src"].startswith("MFG") and r["mode"] != "Supplier")
    failures = []
    for mode in sorted({r["mode"] for r in ships}):
        sub = [r for r in ships if r["mode"] == mode]
        if len(sub) < 20:
            print(f"\n{mode}: skipped ({len(sub)} simulated shipments < 20)")
            continue
        m = base["lanes"]["mfg_dc"]["modes"].get(mode)
        if not m:
            continue
        sim_mean = np.mean([float(r["lead_days"]) for r in sub])
        data_mean = m["mean_lead_days"]
        ratio = sim_mean / data_mean
        print(f"\n{mode}: sim mean {sim_mean:.2f}; data mean {data_mean:.2f}; "
              f"ratio {ratio:.3f}; n={len(sub)}")
        if ratio != pytest.approx(1.0, rel=0.25):
            failures.append(f"{mode} ratio {ratio:.3f}")
    assert not failures, f"modes outside +/-25% of workbook mean: {', '.join(failures)}"
