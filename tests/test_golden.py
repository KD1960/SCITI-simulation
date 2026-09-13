import json
import os
from pathlib import Path

import pytest

from sciti.config import Config, Disruption, ForcedAdoption
from sciti.runner import run

GOLDEN = Path(__file__).parent / "golden" / "none_seed7_summary.json"


def golden_cfg(baseline_path, tmp_path):
    return Config(name="golden", seed=7, weeks=52, baseline_path=str(baseline_path),
                  output_dir=str(tmp_path),
                  forced_adoptions=[ForcedAdoption(week=1, tech="control_tower",
                                                   members=["DC_Shanghai", "Retail_5", "Retail_6", "Retail_7", "Retail_8"])],
                  disruptions=[Disruption(target="CM_4", start_week=10, weeks=4, capacity_mult=0.3)])


def test_golden_summary(baseline_path, tmp_path):
    d = run(golden_cfg(baseline_path, tmp_path), run_dir=tmp_path / "g")
    got = json.loads((d / "summary.json").read_text())
    if os.environ.get("SCITI_UPDATE_GOLDEN") == "1":
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True))
        pytest.skip("golden file updated")
    assert got == json.loads(GOLDEN.read_text())


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_full_horizon_invariants(baseline_path, tmp_path, seed):
    c = Config(name="inv", seed=seed, weeks=156, baseline_path=str(baseline_path), output_dir=str(tmp_path))
    run(c, run_dir=tmp_path / f"s{seed}")  # strict checks raise on any violation
