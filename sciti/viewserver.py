"""Local-only server for the replay view (spec §9.6, §10)."""
from __future__ import annotations

import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

VIEW_DIR = Path(__file__).resolve().parents[1] / "view"
RUN_FILES = frozenset({"network.json", "weekly_nodes.csv", "shipments.csv", "events.jsonl", "summary.json",
                       "manifest.json", "quality.json", "decisions.jsonl"})
VIEW_FILES = frozenset({"index.html", "style.css", "data.js", "app.js", "map.js", "dash.js", "ne_110m_land.geojson"})


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, run_dir: Path, base_dir: Path | None, **kw):
        self.run_dir, self.base_dir = run_dir, base_dir
        super().__init__(*args, directory=str(VIEW_DIR), **kw)

    def _resolve(self) -> Path | None:
        path = unquote(urlparse(self.path).path)
        if path == "/":
            return VIEW_DIR / "index.html"
        parts = path.strip("/").split("/")
        if len(parts) == 1 and parts[0] in VIEW_FILES:
            return VIEW_DIR / parts[0]
        if len(parts) == 2 and parts[1] in RUN_FILES:
            if parts[0] == "run":
                return self.run_dir / parts[1]
            if parts[0] == "base" and self.base_dir is not None:
                return self.base_dir / parts[1]
        return None

    def do_GET(self):
        target = self._resolve()
        if target is None or not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        ctype = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json",
                 ".geojson": "application/json", ".csv": "text/csv", ".jsonl": "text/plain"}[target.suffix]
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def make_server(run_dir: Path, base_dir: Path | None = None, port: int = 0) -> ThreadingHTTPServer:
    handler = functools.partial(Handler, run_dir=Path(run_dir), base_dir=Path(base_dir) if base_dir else None)
    return ThreadingHTTPServer(("127.0.0.1", port), handler)
