import json
import threading
import urllib.error
import urllib.request

import pytest

from sciti.config import Config
from sciti.runner import run
from sciti.viewserver import make_server


@pytest.fixture
def served(baseline_path, tmp_path):
    d = run(Config(name="v", seed=1, weeks=13, baseline_path=str(baseline_path), output_dir=str(tmp_path)),
            run_dir=tmp_path / "r")
    srv = make_server(d, base_dir=None, port=0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield d, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def get(url):
    with urllib.request.urlopen(url) as r:
        return r.status, r.read()


def test_binds_localhost(served):
    assert served[1].startswith("http://127.0.0.1:")


def test_serves_page_and_run_files(served):
    d, base = served
    assert get(base + "/")[0] == 200
    assert b"SCITI 1" in get(base + "/")[1]
    assert get(base + "/app.js")[0] == 200
    assert json.loads(get(base + "/run/summary.json")[1])["weeks"] == 13
    assert len(json.loads(get(base + "/run/quality.json")[1])) == 14


@pytest.mark.parametrize("path", ["/run/../manifest.json", "/run/secret.txt", "/base/summary.json", "/../pyproject.toml"])
def test_blocks_other_paths(served, path):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(served[1] + path)
    assert e.value.code == 404
