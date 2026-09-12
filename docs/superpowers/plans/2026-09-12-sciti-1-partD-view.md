# SCITI 1 — Part D: Replay web view (Tasks 17–19)

> Part of `2026-09-12-sciti-1.md`. Read that file's Global Constraints first. Requires Parts A–C. Steps use checkbox (`- [ ]`) syntax.

All shell commands run from the project root: `cd "$HOME/Claude/Projects/SCITI simulation"`.

## View decisions (apply to every task in this part)

- Plain HTML/CSS/JS ES modules, Canvas 2D, **no JS libraries and no CDN**. Works offline.
- The page reads only run output files through the local server: `/run/<file>` (the run) and `/base/<file>` (optional paired no-tech baseline).
- The server binds `127.0.0.1` only and serves only a fixed allow-list of file names.
- Map projection: equirectangular, latitudes 75°N to 60°S. Shipments move in straight lon/lat lines (shortest way across the date line).
- JS has no unit-test harness in the MVP. JS tasks are verified in the browser (screenshot + console has no errors) against a real run.

---

### Task 17: View server, `sciti view`, page shell and data loading

**Files:**
- Create: `sciti/viewserver.py`, `view/index.html`, `view/style.css`, `view/data.js`, `view/app.js`
- Modify: `sciti/outputs.py` (write `quality.json`), `sciti/cli.py` (add `view`)
- Test: `tests/test_viewserver.py`

**Interfaces:**
- Consumes: run directory layout (Task 9), `SimState.quality`.
- Produces:
  - `sciti.viewserver.VIEW_DIR: Path` (project `view/`), `RUN_FILES: frozenset[str]`
  - `make_server(run_dir: Path, base_dir: Path | None = None, port: int = 0) -> ThreadingHTTPServer`
  - CLI: `sciti view RUN_DIR [--baseline BASE_RUN_DIR] [--port 8765] [--no-open]`
  - `view/data.js` exports: `parseCSV(text) -> object[]`, `loadRun(prefix) -> Promise<Run | null>` where `Run = {network, weekly, byWeek, ships, events, summary, manifest, quality, decisions, weeks, roles, series}` and `series = {profit, cost, fill, csi, co2, adoptCount}` (arrays of length `weeks`, index = week − 1)
  - `view/app.js`: global `state = {t, playing, speed, roles: Set, tech, node}`, `renderers` array of `(state) => void`, anchor comments `// [imports]` and `// [setup]` used by Tasks 18–19

- [ ] **Step 1: Write the failing test**

`tests/test_viewserver.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_viewserver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.viewserver'`

- [ ] **Step 3: Write `quality.json` in `sciti/outputs.py`**

In `RunWriter.finish`, after writing `summary.json`, add:

```python
        (self.run_dir / "quality.json").write_text(json.dumps([round(q, 6) for q in s.quality]))
```

- [ ] **Step 4: Implement `sciti/viewserver.py`**

```python
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
```

- [ ] **Step 5: Add `view` to `sciti/cli.py`**

Subparser (after `batch`):

```python
    vw = sub.add_parser("view", help="serve the replay web view for a run on 127.0.0.1")
    vw.add_argument("run_dir")
    vw.add_argument("--baseline", default=None)
    vw.add_argument("--port", type=int, default=8765)
    vw.add_argument("--no-open", action="store_true")
```

Handler (before `return 1`):

```python
    if args.cmd == "view":
        import webbrowser
        from sciti.viewserver import make_server
        srv = make_server(Path(args.run_dir), Path(args.baseline) if args.baseline else None, args.port)
        url = f"http://127.0.0.1:{srv.server_address[1]}/"
        print(f"serving {args.run_dir} at {url} (Ctrl+C to stop)")
        if not args.no_open:
            webbrowser.open(url)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
```

- [ ] **Step 6: Write `view/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SCITI 1 replay</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header>
    <h1>SCITI 1 <span id="run-name"></span></h1>
    <span class="badge">Simulation — illustrative parameters</span>
  </header>
  <section id="controls">
    <button id="play" type="button">Play</button>
    <label>Speed
      <select id="speed">
        <option value="1">1 wk/s</option>
        <option value="4" selected>4 wk/s</option>
        <option value="10">10 wk/s</option>
        <option value="20">20 wk/s</option>
      </select>
    </label>
    <input id="week" type="range" min="1" max="156" value="1" aria-label="Week">
    <output id="week-label">Week 1</output>
    <label>Tech <select id="tech"><option value="">All</option></select></label>
    <fieldset id="tiers"><legend>Tiers</legend></fieldset>
  </section>
  <main>
    <div id="map-wrap"><canvas id="map"></canvas><div id="legend"></div></div>
    <aside id="side">
      <div id="node-panel"><p class="hint">Click a node on the map to see its details.</p></div>
      <div id="feed"></div>
    </aside>
  </main>
  <section id="dashboard"></section>
  <p id="error" hidden></p>
  <script type="module" src="app.js"></script>
</body>
</html>
```

- [ ] **Step 7: Write `view/style.css`**

```css
:root {
  --bg: #f7f7f5; --panel: #ffffff; --ink: #1d232b; --muted: #5d6b7a; --line: #d9dde2;
  --land: #e3e6e0; --link: rgba(60, 70, 80, 0.12); --danger: #c62828; --accent: #8c1d40;
  --role-Supplier: #7a869a; --role-CM: #3d7ea6; --role-MFG: #8c1d40; --role-DC: #2e7d32; --role-Retail: #ef6c00;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #14171b; --panel: #1c2026; --ink: #e8ebef; --muted: #9aa6b2; --line: #2d333b;
          --land: #2a3038; --link: rgba(200, 210, 220, 0.10); }
}
* { box-sizing: border-box; }
body { margin: 0; font: 14px/1.4 system-ui, -apple-system, "Segoe UI", Arial, sans-serif; background: var(--bg); color: var(--ink); }
header { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--line); }
h1 { font-size: 18px; margin: 0; }
#run-name { font-weight: 400; color: var(--muted); font-size: 13px; }
.badge { margin-left: auto; font-size: 12px; padding: 2px 8px; border: 1px solid var(--accent); color: var(--accent); border-radius: 10px; }
#controls { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px; padding: 8px 16px; border-bottom: 1px solid var(--line); }
#controls fieldset { border: 0; margin: 0; padding: 0; display: flex; gap: 8px; }
#controls legend { float: left; margin-right: 6px; color: var(--muted); }
#week { flex: 1 1 200px; }
button, select { font: inherit; }
main { display: grid; grid-template-columns: minmax(0, 3fr) minmax(260px, 1fr); gap: 12px; padding: 12px 16px; }
@media (max-width: 900px) { main { grid-template-columns: 1fr; } }
#map-wrap { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
#map { width: 100%; display: block; cursor: crosshair; }
#legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 12px; color: var(--muted); padding-top: 6px; }
.swatch { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; vertical-align: middle; }
#side { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
#node-panel, #feed { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px; overflow: auto; }
#feed { max-height: 320px; font-size: 13px; }
#feed p { margin: 0 0 4px; }
.hint { color: var(--muted); margin: 0; }
#dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; padding: 0 16px 16px; }
.chart { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
.chart h3 { margin: 0 0 4px; font-size: 13px; font-weight: 600; }
.chart canvas { width: 100%; height: 120px; display: block; }
table.kv { border-collapse: collapse; width: 100%; font-size: 13px; }
table.kv td { padding: 2px 4px; border-bottom: 1px solid var(--line); }
table.kv td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
#error { color: var(--danger); padding: 0 16px; }
```

- [ ] **Step 8: Write `view/data.js`**

```js
// Loads one run's output files and derives weekly network series (spec §10).
const COST_KEYS = ["purchases", "shipping", "holding", "stockout", "handling", "tech", "cogs"];

export function parseCSV(text) {
  const lines = text.trim().split("\n");
  const head = lines[0].split(",");
  return lines.slice(1).map((line) => {
    const cells = line.split(",");
    const row = {};
    head.forEach((h, i) => {
      const x = cells[i] ?? "";
      const n = Number(x);
      row[h] = x !== "" && !Number.isNaN(n) ? n : x;
    });
    return row;
  });
}

async function get(url, kind) {
  const r = await fetch(url);
  if (!r.ok) return null;
  const text = await r.text();
  if (kind === "csv") return parseCSV(text);
  if (kind === "jsonl") return text.trim() ? text.trim().split("\n").map((l) => JSON.parse(l)) : [];
  return JSON.parse(text);
}

function series(weekly, ships, events, quality, manifest, roles, weeks) {
  const zeros = () => new Array(weeks).fill(0);
  const profit = zeros(), cost = zeros(), demand = zeros(), sales = zeros(), co2 = zeros();
  const onTimeN = zeros(), onTimeOk = zeros(), adoptWeek = zeros();
  for (const r of weekly) {
    const i = r.week - 1;
    profit[i] += r.profit;
    cost[i] += COST_KEYS.reduce((a, k) => a + r[k], 0);
    if (r.role === "Retail") { demand[i] += r.demand; sales[i] += r.sales; }
  }
  for (const s of ships) {
    if (s.ship_week <= weeks) co2[s.ship_week - 1] += s.co2;
    if (roles[s.dst] === "Retail" && s.arrive_week <= weeks) {
      onTimeN[s.arrive_week - 1] += 1;
      if (s.arrive_week <= s.due_week) onTimeOk[s.arrive_week - 1] += 1;
    }
  }
  for (const e of events) if (e.type === "adopt" && e.week <= weeks) adoptWeek[e.week - 1] += 1;
  const adoptCount = [];
  adoptWeek.reduce((acc, v, i) => (adoptCount[i] = acc + v), 0);
  const w = manifest?.config?.assumptions?.satisfaction_weights ?? { fill_rate: 0.5, on_time: 0.3, quality: 0.2 };
  const fill = demand.map((d, i) => (d > 0 ? sales[i] / d : 1));
  const onTime = onTimeN.map((n, i) => (n > 0 ? onTimeOk[i] / n : 1));
  const q = (i) => quality[i + 1] ?? quality[quality.length - 1] ?? 1;
  const csi = fill.map((f, i) => w.fill_rate * f + w.on_time * onTime[i] + w.quality * q(i));
  return { profit, cost, fill, csi, co2, adoptCount };
}

export async function loadRun(prefix) {
  const [network, weekly, ships, events, summary, manifest, quality, decisions] = await Promise.all([
    get(`${prefix}/network.json`), get(`${prefix}/weekly_nodes.csv`, "csv"), get(`${prefix}/shipments.csv`, "csv"),
    get(`${prefix}/events.jsonl`, "jsonl"), get(`${prefix}/summary.json`), get(`${prefix}/manifest.json`),
    get(`${prefix}/quality.json`), get(`${prefix}/decisions.jsonl`, "jsonl"),
  ]);
  if (!weekly || !network) return null;
  const weeks = weekly.reduce((m, r) => Math.max(m, r.week), 0);
  const byWeek = Array.from({ length: weeks + 1 }, () => ({}));
  for (const r of weekly) byWeek[r.week][r.node] = r;
  const roles = Object.fromEntries(network.nodes.map((n) => [n.id, n.role]));
  const slim = (decisions ?? []).map((d) => ({ week: d.week, pass: d.pass, agent: d.agent, parsed: d.parsed, fallback: d.fallback }));
  const s = ships ?? [], ev = events ?? [], q = quality ?? [];
  return { network, weekly, byWeek, ships: s, events: ev, summary, manifest, quality: q, decisions: slim, weeks, roles,
           series: series(weekly, s, ev, q, manifest, roles, weeks) };
}
```

- [ ] **Step 9: Write `view/app.js`**

```js
import { loadRun } from "./data.js";
// [imports]

const ROLES = ["Supplier", "CM", "MFG", "DC", "Retail"];
const $ = (id) => document.getElementById(id);
export const state = { t: 1, playing: false, speed: 4, roles: new Set(ROLES), tech: "", node: null };
const renderers = [];
let run = null;
let base = null;
let last = null;

function setWeek(t) {
  state.t = Math.max(1, Math.min(run.weeks + 0.999, t));
  const w = Math.floor(state.t);
  $("week").value = w;
  $("week-label").textContent = `Week ${w}`;
  for (const r of renderers) r(state);
}

function tick(now) {
  if (state.playing && last !== null) {
    const next = state.t + (state.speed * (now - last)) / 1000;
    if (next >= run.weeks + 0.999) {
      state.playing = false;
      $("play").textContent = "Play";
    }
    setWeek(next);
  }
  last = now;
  requestAnimationFrame(tick);
}

async function main() {
  run = await loadRun("run");
  if (!run) {
    $("error").hidden = false;
    $("error").textContent = "Could not load the run files. Start the page with `sciti view RUN_DIR`.";
    return;
  }
  base = await loadRun("base");
  $("run-name").textContent = run.manifest?.run_id ?? "";
  $("week").max = run.weeks;
  for (const [id, name] of Object.entries(run.network.techs).sort()) $("tech").append(new Option(name, id));
  for (const role of ROLES) {
    const label = document.createElement("label");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = true;
    box.onchange = () => { box.checked ? state.roles.add(role) : state.roles.delete(role); setWeek(state.t); };
    label.append(box, ` ${role}`);
    $("tiers").append(label);
  }
  $("play").onclick = () => {
    if (!state.playing && state.t >= run.weeks) setWeek(1);
    state.playing = !state.playing;
    $("play").textContent = state.playing ? "Pause" : "Play";
  };
  $("speed").onchange = (e) => { state.speed = Number(e.target.value); };
  $("week").oninput = (e) => {
    state.playing = false;
    $("play").textContent = "Play";
    setWeek(Number(e.target.value));
  };
  $("tech").onchange = (e) => { state.tech = e.target.value; setWeek(state.t); };
  // [setup]
  setWeek(1);
  requestAnimationFrame(tick);
}

main();
```

- [ ] **Step 10: Run tests**

Run: `.venv/bin/pytest tests/test_viewserver.py -v`
Expected: 6 passed

- [ ] **Step 11: Browser check**

```bash
.venv/bin/sciti run configs/rules.yaml --run-dir runs/view_check
.venv/bin/sciti view runs/view_check --port 8765 --no-open
```

Run the second command in the background. Open `http://127.0.0.1:8765/` in the in-app browser (Claude Browser `preview_start` with that url, or the `run` skill). Expected: header with run id and the "Simulation — illustrative parameters" badge; controls; slider moves the week label; Tech dropdown lists 8 technologies; browser console shows no errors. Stop the server afterwards.

- [ ] **Step 12: Commit**

```bash
git add sciti/viewserver.py sciti/outputs.py sciti/cli.py view/index.html view/style.css view/data.js view/app.js tests/test_viewserver.py
git commit -m "feat: local-only view server and replay page shell with data loading

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 18: Map animation and adoption display

**Files:**
- Create: `view/map.js`, `view/ne_110m_land.geojson` (downloaded only with user approval)
- Modify: `view/app.js` (anchors `// [imports]`, `// [setup]`)

**Interfaces:**
- Consumes: `Run` from `data.js`; `state` from `app.js`.
- Produces: `view/map.js` export `createMap(canvas, run, land) -> {draw(t, state), pick(x, y) -> nodeId | null, techColor: {techId: color}, modeColor: {mode: color}}`

Drawing rules (spec §10): land (or a 30° graticule if no land file); faint network links; coalition links as dashed lines in the tech's color from the first member to each other member; in-transit shipments as dots (radius `1 + 4·sqrt(units / max units for that source role)`, color by mode); nodes as circles colored by role (radius Supplier 3, CM 6, MFG 8, DC 7, Retail 6); tech ring segments around each node (one color per tech, only the selected tech if the filter is set); red pulsing ring on retailers with lost sales that week; dashed red ring on nodes with `capacity_factor < 1`; labels for CM, MFG, DC and Retail nodes. Role and tech filters hide nodes, links and shipments from hidden roles.

- [ ] **Step 1: Ask before downloading the land outline**

Ask the user in chat: "May I download `ne_110m_land.geojson` (Natural Earth 1:110m land, public domain) from `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson` into `view/`? It is used only to draw coastlines." First check its size with `curl -sIL <url> | grep -i content-length` and include the size in the question.

If approved:

```bash
curl -fsSL -o view/ne_110m_land.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
python3 -c "import json; d=json.load(open('view/ne_110m_land.geojson')); print(d['type'], len(d['features']))"
```

Expected: `FeatureCollection` and a feature count > 100. If declined, skip; the map draws a graticule.

- [ ] **Step 2: Write `view/map.js`**

```js
// World map with moving shipments, adoption rings and coalitions (spec §10).
const LAT_TOP = 75;
const LAT_BOTTOM = -60;
const ROLE_R = { Supplier: 3, CM: 6, MFG: 8, DC: 7, Retail: 6 };
const MODE_COLOR = { Air: "#e4572e", Ship: "#1b998b", Road: "#f3a712", Rail: "#8e5572", Supplier: "#7a869a" };
const TECH_COLORS = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7"];

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function lonLerp(a, b, f) {
  let d = b - a;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  let v = a + d * f;
  if (v > 180) v -= 360;
  if (v < -180) v += 360;
  return v;
}

export function createMap(canvas, run, land) {
  const ctx = canvas.getContext("2d");
  const nodes = run.network.nodes;
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const techIds = Object.keys(run.network.techs).sort();
  const techColor = Object.fromEntries(techIds.map((t, i) => [t, TECH_COLORS[i % TECH_COLORS.length]]));
  const maxUnits = {};
  for (const s of run.ships) {
    const role = byId[s.src].role;
    maxUnits[role] = Math.max(maxUnits[role] ?? 0, s.units);
  }
  let W = 0;
  let H = 0;

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    W = canvas.clientWidth;
    H = (W * (LAT_TOP - LAT_BOTTOM)) / 360;
    canvas.style.height = `${H}px`;
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  const px = (lon, lat) => [((lon + 180) / 360) * W, ((LAT_TOP - lat) / (LAT_TOP - LAT_BOTTOM)) * H];

  function holdingsAt(week) {
    const h = {};
    for (const e of run.events) {
      if (e.week > week) break;
      if (e.type === "adopt") (h[e.node] ??= {})[e.tech] = e;
      else if (e.type === "drop" && h[e.node]) delete h[e.node][e.tech];
    }
    return h;
  }

  function drawLand() {
    if (!land) {
      ctx.strokeStyle = css("--line");
      ctx.lineWidth = 0.5;
      for (let lon = -180; lon <= 180; lon += 30) {
        const [x] = px(lon, 0);
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let lat = -60; lat <= 75; lat += 30) {
        const [, y] = px(0, lat);
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }
      return;
    }
    ctx.fillStyle = css("--land");
    for (const f of land.features) {
      const g = f.geometry;
      const polys = g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
      for (const poly of polys) {
        ctx.beginPath();
        for (const ring of poly) {
          ring.forEach(([lon, lat], i) => {
            const [x, y] = px(lon, lat);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          });
          ctx.closePath();
        }
        ctx.fill("evenodd");
      }
    }
  }

  function circle(x, y, r) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
  }

  function draw(t, st) {
    const week = Math.max(1, Math.min(run.weeks, Math.floor(t)));
    const show = (id) => st.roles.has(byId[id].role);
    ctx.clearRect(0, 0, W, H);
    drawLand();

    ctx.strokeStyle = css("--link");
    ctx.lineWidth = 0.7;
    for (const [a, b] of run.network.links) {
      if (!show(a) || !show(b)) continue;
      const [x1, y1] = px(byId[a].lon, byId[a].lat);
      const [x2, y2] = px(byId[b].lon, byId[b].lat);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
    }

    ctx.setLineDash([5, 4]);
    ctx.lineWidth = 1.5;
    for (const e of run.events) {
      if (e.week > week) break;
      if (e.type !== "coalition" || (st.tech && e.tech !== st.tech)) continue;
      const members = e.members.filter(show);
      if (members.length < 2) continue;
      ctx.strokeStyle = techColor[e.tech];
      const [x0, y0] = px(byId[members[0]].lon, byId[members[0]].lat);
      for (const m of members.slice(1)) {
        const [x, y] = px(byId[m].lon, byId[m].lat);
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke();
      }
    }
    ctx.setLineDash([]);

    for (const s of run.ships) {
      if (s.ship_week > t || s.arrive_week <= t || !show(s.src) || !show(s.dst)) continue;
      const a = byId[s.src];
      const b = byId[s.dst];
      const f = (t - s.ship_week) / (s.arrive_week - s.ship_week);
      const [x, y] = px(lonLerp(a.lon, b.lon, f), a.lat + (b.lat - a.lat) * f);
      ctx.fillStyle = MODE_COLOR[s.mode] ?? "#999";
      ctx.globalAlpha = 0.8;
      circle(x, y, 1 + 4 * Math.sqrt(s.units / (maxUnits[a.role] || 1)));
      ctx.fill();
    }
    ctx.globalAlpha = 1;

    const held = holdingsAt(week);
    const row = run.byWeek[week] ?? {};
    const pulse = 1 - (t % 1);
    ctx.font = "11px system-ui, sans-serif";
    for (const n of nodes) {
      if (!st.roles.has(n.role)) continue;
      const [x, y] = px(n.lon, n.lat);
      const r = ROLE_R[n.role];
      const wr = row[n.id];
      if (wr && wr.capacity_factor < 1) {
        ctx.strokeStyle = css("--danger"); ctx.lineWidth = 2; ctx.setLineDash([2, 2]);
        circle(x, y, r + 7); ctx.stroke(); ctx.setLineDash([]);
      }
      if (wr && n.role === "Retail" && wr.lost > 0) {
        ctx.strokeStyle = css("--danger"); ctx.globalAlpha = pulse; ctx.lineWidth = 2;
        circle(x, y, r + 5 + 4 * (1 - pulse)); ctx.stroke(); ctx.globalAlpha = 1;
      }
      const techs = Object.keys(held[n.id] ?? {}).filter((k) => !st.tech || k === st.tech).sort();
      techs.forEach((k, i) => {
        const span = (Math.PI * 2) / techs.length;
        const a0 = -Math.PI / 2 + i * span;
        ctx.strokeStyle = techColor[k]; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(x, y, r + 3, a0, a0 + span); ctx.stroke();
      });
      ctx.fillStyle = css(`--role-${n.role}`);
      circle(x, y, r); ctx.fill();
      if (n.id === st.node) { ctx.strokeStyle = css("--ink"); ctx.lineWidth = 1.5; circle(x, y, r + 1.5); ctx.stroke(); }
      if (n.role !== "Supplier") {
        ctx.fillStyle = css("--muted");
        ctx.fillText(n.id.replace("Retail_", "R").replace("DC_", "").replace("MFG_", ""), x + r + 4, y + 4);
      }
    }
  }

  function pick(mx, my) {
    let best = null;
    let bestD = 12;
    for (const n of nodes) {
      const [x, y] = px(n.lon, n.lat);
      const d = Math.hypot(x - mx, y - my);
      if (d < bestD) { best = n.id; bestD = d; }
    }
    return best;
  }

  window.addEventListener("resize", resize);
  resize();
  return { draw, pick, techColor, modeColor: MODE_COLOR };
}
```

- [ ] **Step 3: Wire the map into `view/app.js`**

Replace the line `// [imports]` with:

```js
import { createMap } from "./map.js";
// [imports]
```

Replace the line `  // [setup]` with:

```js
  const land = await fetch("ne_110m_land.geojson").then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const map = createMap($("map"), run, land);
  renderers.push((s) => map.draw(s.t, s));
  $("map").onclick = (e) => {
    const rect = $("map").getBoundingClientRect();
    const id = map.pick(e.clientX - rect.left, e.clientY - rect.top);
    if (id) { state.node = id; setWeek(state.t); }
  };
  window.addEventListener("resize", () => setWeek(state.t));
  const legend = $("legend");
  const swatch = (color, text) => {
    const span = document.createElement("span");
    const dot = document.createElement("i");
    dot.className = "swatch";
    dot.style.background = color;
    span.append(dot, text);
    legend.append(span);
  };
  for (const [mode, color] of Object.entries(map.modeColor)) swatch(color, `${mode} shipment`);
  for (const [tech, color] of Object.entries(map.techColor)) swatch(color, run.network.techs[tech]);
  // [setup]
```

- [ ] **Step 4: Browser check with coalitions and a disruption**

```bash
.venv/bin/sciti run configs/classroom_shanghai_tower.yaml --run-dir runs/view_map
.venv/bin/sciti view runs/view_map --port 8765 --no-open
```

Run the view in the background, open `http://127.0.0.1:8765/`, press Play. Expected, verified by screenshots at weeks 1, 22 and 60: coastlines (or graticule); colored dots moving along lanes; Shanghai chain nodes show a control-tower ring segment and dashed coalition lines from week 1; CM_4 (Munich) shows a dashed red ring during weeks 20–25; retailer red pulses when they lose sales; unticking "Supplier" hides supplier dots and their shipments; clicking a node outlines it. Console has no errors. Stop the server.

- [ ] **Step 5: Commit**

```bash
git add view/map.js view/app.js
git commit -m "feat: animated world map with shipments, adoption rings, coalitions, disruptions

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

If the land file was downloaded, commit it separately:

```bash
git add view/ne_110m_land.geojson
git commit -m "chore: add Natural Earth 1:110m land outline (public domain)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 19: Dashboard, node panel, event feed, final verification

**Files:**
- Create: `view/dash.js`
- Modify: `view/app.js` (anchors), `docs/superpowers/specs/2026-09-12-sciti-1-design.md` (§4 file tree and §11 calibration wording to match the built code)

**Interfaces:**
- Consumes: `Run.series`, `Run.byWeek`, `Run.events`, `Run.decisions`, `techColor`.
- Produces: `view/dash.js` exports `createDashboard(el, run, base) -> {update(week)}`, `renderNodePanel(el, run, nodeId, week, techColor)`, `renderFeed(el, run, week)`, `describe(event, techs) -> string`

Panels (spec §10): Network profit / week, Total cost / week, Customer satisfaction index, Fill rate, CO2 (kg) / week, Technologies adopted (cumulative). Each draws the run as a solid line, the paired baseline (if loaded) as a dashed line, and a vertical marker at the current week.

- [ ] **Step 1: Write `view/dash.js`**

```js
// Dashboard charts, node panel and plain-language event feed (spec §10).
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const PANELS = [
  ["profit", "Network profit / week", "$"],
  ["cost", "Total cost / week", "$"],
  ["csi", "Customer satisfaction index", ""],
  ["fill", "Fill rate", ""],
  ["co2", "CO2 (kg) / week", ""],
  ["adoptCount", "Technologies adopted (cumulative)", ""],
];

const fmt = (v, unit) => {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  const a = Math.abs(v);
  const s = a >= 1e9 ? `${(v / 1e9).toFixed(2)}B` : a >= 1e6 ? `${(v / 1e6).toFixed(2)}M` : a >= 1e3 ? `${(v / 1e3).toFixed(1)}k`
    : a < 2 && a !== 0 && !Number.isInteger(v) ? v.toFixed(3) : v.toFixed(0);
  return unit + s;
};

function drawChart(canvas, runSeries, baseSeries, week, unit) {
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth;
  const H = canvas.clientHeight;
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const all = runSeries.concat(baseSeries ?? []).filter(Number.isFinite);
  let lo = Math.min(...all);
  let hi = Math.max(...all);
  if (lo === hi) { lo -= 1; hi += 1; }
  const n = runSeries.length;
  const pad = 18;
  const x = (i) => pad + (i / Math.max(1, n - 1)) * (W - pad - 4);
  const y = (v) => 4 + (1 - (v - lo) / (hi - lo)) * (H - 20);
  const line = (s, color, dash) => {
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash(dash);
    ctx.beginPath();
    s.forEach((v, i) => (i === 0 ? ctx.moveTo(x(i), y(v)) : ctx.lineTo(x(i), y(v))));
    ctx.stroke(); ctx.setLineDash([]);
  };
  if (baseSeries) line(baseSeries, css("--muted"), [4, 3]);
  line(runSeries, css("--accent"), []);
  ctx.strokeStyle = css("--ink"); ctx.globalAlpha = 0.4;
  ctx.beginPath(); ctx.moveTo(x(week - 1), 0); ctx.lineTo(x(week - 1), H - 14); ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.fillStyle = css("--muted"); ctx.font = "11px system-ui, sans-serif";
  ctx.fillText(`${fmt(runSeries[week - 1], unit)}${baseSeries ? `  (base ${fmt(baseSeries[week - 1], unit)})` : ""}`, pad, H - 2);
}

export function createDashboard(el, run, base) {
  const canvases = {};
  for (const [key, title] of PANELS) {
    const box = document.createElement("div");
    box.className = "chart";
    const h = document.createElement("h3");
    h.textContent = title;
    const c = document.createElement("canvas");
    box.append(h, c);
    el.append(box);
    canvases[key] = c;
  }
  return {
    update(week) {
      for (const [key, , unit] of PANELS) {
        const b = base && base.weeks === run.weeks ? base.series[key] : null;
        drawChart(canvases[key], run.series[key], b, week, unit);
      }
    },
  };
}

export function describe(e, techs) {
  const t = techs[e.tech] ?? e.tech;
  switch (e.type) {
    case "adopt": return `${e.node} adopted ${t}${e.coalition ? ` (group ${e.coalition})` : " (alone)"}`;
    case "drop": return `${e.node} dropped ${t}`;
    case "coalition": return `${e.kind} formed for ${t}: ${e.members.join(", ")}`;
    case "coalition_failed": return `Group for ${t} proposed by ${e.proposer} did not form`;
    case "rejected": return `${e.node} could not afford ${t}`;
    case "disruption_start": return `Disruption at ${e.target} until week ${e.until}`;
    case "check_warning": return `Check warning: ${e.detail}`;
    default: return e.type;
  }
}

export function renderFeed(el, run, week) {
  // every event so far, except coalition members' adopt events (the coalition line reports those)
  const items = run.events.filter((e) => e.week <= week && !(e.type === "adopt" && e.coalition));
  el.replaceChildren();
  for (const e of items.slice(-60).reverse()) {
    const p = document.createElement("p");
    p.textContent = `W${e.week}: ${describe(e, run.network.techs)}`;
    el.append(p);
  }
  if (!items.length) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No events yet.";
    el.append(p);
  }
}

export function renderNodePanel(el, run, nodeId, week, techColor) {
  if (!nodeId) return;
  const node = run.network.nodes.find((n) => n.id === nodeId);
  const row = run.byWeek[week]?.[nodeId];
  el.replaceChildren();
  const h = document.createElement("h3");
  h.textContent = `${node.id} · ${node.role}`;
  const city = document.createElement("p");
  city.className = "hint";
  city.textContent = node.city;
  const table = document.createElement("table");
  table.className = "kv";
  const add = (k, v) => {
    const tr = table.insertRow();
    tr.insertCell().textContent = k;
    tr.insertCell().textContent = v;
  };
  if (row) {
    add("Week", String(week));
    add("Stock (units)", fmt(row.stock_units, ""));
    add("Cash", fmt(row.cash, "$"));
    add("Profit this week", fmt(row.profit, "$"));
    if (node.role === "Retail") add("Lost sales", fmt(row.lost, ""));
    add("Capacity factor", String(row.capacity_factor));
    add("Active techs", row.techs || "none");
  }
  el.append(h, city, table);
  const mine = run.decisions.filter((d) => d.agent === nodeId && d.week <= week)
    .flatMap((d) => d.parsed.filter((p) => p.action !== "skip").map((p) => ({ ...p, week: d.week, fallback: d.fallback })));
  const dh = document.createElement("h3");
  dh.textContent = "Decisions";
  el.append(dh);
  if (!mine.length) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No adoption decisions yet.";
    el.append(p);
  }
  for (const d of mine.slice(-8).reverse()) {
    const p = document.createElement("p");
    const dot = document.createElement("i");
    dot.className = "swatch";
    dot.style.background = techColor[d.tech] ?? "#999";
    p.append(dot, `W${d.week} ${d.action} ${run.network.techs[d.tech] ?? d.tech}${d.fallback ? " [rule fallback]" : ""}: ${d.reason}`);
    el.append(p);
  }
}
```

- [ ] **Step 2: Wire the dashboard into `view/app.js`**

Replace the line `// [imports]` with:

```js
import { createDashboard, renderFeed, renderNodePanel } from "./dash.js";
```

Replace the line `  // [setup]` with:

```js
  const dash = createDashboard($("dashboard"), run, base);
  let shownWeek = null;
  let shownNode = null;
  renderers.push((s) => {
    const w = Math.floor(s.t);
    if (w === shownWeek && s.node === shownNode) return;
    shownWeek = w;
    shownNode = s.node;
    dash.update(w);
    renderFeed($("feed"), run, w);
    renderNodePanel($("node-panel"), run, s.node, w, map.techColor);
  });
  window.addEventListener("resize", () => { shownWeek = null; setWeek(state.t); });
```

- [ ] **Step 3: Browser check with a paired baseline**

```bash
.venv/bin/sciti run configs/baseline.yaml --run-dir runs/view_base
.venv/bin/sciti run configs/rules.yaml --run-dir runs/view_rules
.venv/bin/sciti view runs/view_rules --baseline runs/view_base --port 8765 --no-open
```

Run the view in the background, open `http://127.0.0.1:8765/`. Expected (screenshots at weeks 10 and 150): six chart panels, each with a solid run line, dashed baseline line and week marker that moves while playing; the feed lists adoptions, groups and budget rejections in plain language; clicking a DC shows stock/cash/profit and its decisions with reasons; resizing the window keeps charts sharp; console has no errors. `configs/baseline.yaml` and `configs/rules.yaml` both use seed 1 and 156 weeks, so the baseline aligns.

- [ ] **Step 4: Update the spec to match what was built**

In `docs/superpowers/specs/2026-09-12-sciti-1-design.md`:

1. Replace the §4 code-block file tree with the File Map from `docs/superpowers/plans/2026-09-12-sciti-1.md` (engine lives in `sciti/engine/`, view files are `index.html, style.css, data.js, app.js, map.js, dash.js`, land outline `ne_110m_land.geojson`, server `sciti/viewserver.py`).
2. In §11 replace the lead-time half of the calibration bullet with: "simulated MFG→DC lead times match the fitted lane model's predictions at the simulated distances within ±15% (the data's own distances differ from the network's great-circle distances)".

- [ ] **Step 5: Final verification (evidence before claims)**

Run each command and paste the key output lines into the task report:

```bash
.venv/bin/pytest -v
.venv/bin/pytest -m realdata -v
.venv/bin/sciti prepare
.venv/bin/sciti run configs/baseline.yaml --run-dir runs/final_base
.venv/bin/sciti run configs/rules.yaml --run-dir runs/final_rules
.venv/bin/sciti replay runs/final_rules --out runs/final_rules_replay
.venv/bin/sciti batch configs/rules.yaml --seeds 1-30 --with-baseline --out runs/final_batch
.venv/bin/sciti estimate configs/mvp_llm.yaml
```

Expected: all tests pass; realdata tests pass; replay prints `replication: exact`; batch writes `runs/final_batch/results.csv` with 60 rows; estimate prints JSON. Compare `runs/final_rules/summary.json` with `runs/final_base/summary.json` and report the difference in `network_profit` and `satisfaction_index` (spec §12 criterion 4 — any direction). Check each spec §12 success criterion and state which are met; criterion 3 (paid LLM run) needs the user's go-ahead as described at the end of Part C.

- [ ] **Step 6: Commit**

```bash
git add view/dash.js view/app.js docs/superpowers/specs/2026-09-12-sciti-1-design.md
git commit -m "feat: dashboard with baseline overlay, node panel with decision reasons, event feed

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
