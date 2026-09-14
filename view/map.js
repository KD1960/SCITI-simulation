// World map with moving shipments, adoption rings and coalitions (spec §10).
const LAT_TOP = 75;
const LAT_BOTTOM = -60;
const ROLE_R = { Supplier: 3, CM: 6, MFG: 8, DC: 7, Retail: 6 };
const MODE_COLOR = { Air: "#e4572e", Ship: "#1b998b", Road: "#f3a712", Rail: "#8e5572", Supplier: "#7a869a" };
const TECH_COLORS = ["#4e79a7", "#76b7b2", "#59a14f", "#b07aa1", "#9c755f", "#bab0ac", "#edc948", "#17becf"];

const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// Pure hit-test. Clicking a node selects that node; overlap ties go to the larger node:
//   1. Direct hits (distance d <= that node's own radius r) win outright over any near miss,
//      however big — largest r first, then smallest d. This is what makes a click squarely on a
//      small CM or DC dot select it even when a bigger MFG dot's reach circle also covers the click.
//   2. With no direct hit, fall back to near misses (d <= r + 6px): the closest edge (smallest
//      d - r) wins, then the larger radius on a tie.
// Nodes whose role isn't in `roles` (the tier filter) are skipped. `project(node)` -> [x, y].
export function pickNode(nodes, project, roles, mx, my) {
  let hit = null, hitR = -1, hitD = Infinity;
  let near = null, nearEdge = Infinity, nearR = -1;
  for (const n of nodes) {
    if (roles && !roles.has(n.role)) continue;
    const r = ROLE_R[n.role];
    const [x, y] = project(n);
    const d = Math.hypot(x - mx, y - my);
    if (d <= r) {
      if (r > hitR || (r === hitR && d < hitD)) { hit = n.id; hitR = r; hitD = d; }
    } else if (d <= r + 6) {
      const edge = d - r;
      if (edge < nearEdge || (edge === nearEdge && r > nearR)) { near = n.id; nearEdge = edge; nearR = r; }
    }
  }
  return hit ?? near;
}

function lonLerp(a, b, f) {
  let d = b - a;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  let v = a + d * f;
  if (v > 180) v -= 360;
  if (v < -180) v += 360;
  return v;
}

export function createMap(canvas, run, land, onResize) {
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

    const held = holdingsAt(week);
    const pulse = 1 - (t % 1);

    ctx.setLineDash([5, 4]);
    for (const e of run.events) {
      if (e.week > week) break;
      if (e.type !== "coalition" || (st.tech && e.tech !== st.tech)) continue;
      const members = e.members.filter((m) => show(m) && held[m]?.[e.tech]?.coalition === e.id);
      if (members.length < 2) continue;
      const current = e.week === week;
      ctx.strokeStyle = techColor[e.tech];
      ctx.lineWidth = current ? 3 : 1.5;
      ctx.globalAlpha = current ? pulse : 1;
      const [x0, y0] = px(byId[members[0]].lon, byId[members[0]].lat);
      for (const m of members.slice(1)) {
        const [x, y] = px(byId[m].lon, byId[m].lat);
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
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

    const row = run.byWeek[week] ?? {};
    ctx.font = "11px system-ui, sans-serif";
    for (const n of nodes) {
      if (!st.roles.has(n.role)) continue;
      const [x, y] = px(n.lon, n.lat);
      const r = ROLE_R[n.role];
      const wr = row[n.id];
      if (wr && wr.capacity_factor < 1) {
        for (const [a, b] of run.network.links) {
          if (a !== n.id || !show(a) || !show(b)) continue;
          const [x2, y2] = px(byId[b].lon, byId[b].lat);
          ctx.strokeStyle = css("--danger"); ctx.lineWidth = 1.5; ctx.setLineDash([5, 4]);
          ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]);
        }
        const R = r + 7;
        ctx.save();
        circle(x, y, R); ctx.clip();
        ctx.strokeStyle = css("--danger"); ctx.globalAlpha = 0.7; ctx.lineWidth = 1;
        for (let d = -2 * R; d <= 2 * R; d += 3) {
          ctx.beginPath();
          ctx.moveTo(x - R + d, y - R);
          ctx.lineTo(x - R + d + 2 * R, y - R + 2 * R);
          ctx.stroke();
        }
        ctx.restore();
        ctx.globalAlpha = 1; ctx.lineWidth = 1;
        ctx.strokeStyle = css("--danger");
        circle(x, y, R); ctx.stroke();
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

    for (const e of run.events) {
      if (e.week > week) break;
      if (e.week < week || e.type !== "adopt" || (st.tech && e.tech !== st.tech) || !show(e.node)) continue;
      const [x, y] = px(byId[e.node].lon, byId[e.node].lat);
      const r = ROLE_R[byId[e.node].role];
      ctx.strokeStyle = techColor[e.tech]; ctx.globalAlpha = pulse; ctx.lineWidth = 2;
      circle(x, y, r + 4 + 12 * (1 - pulse)); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  // Reads the canvas's live size at click time (not the closed-over W/H, which is only as fresh
  // as the last resize()) so a click can never be projected in a stale frame.
  function pick(mx, my, roles) {
    const w = canvas.clientWidth;
    const h = (w * (LAT_TOP - LAT_BOTTOM)) / 360;
    const project = (n) => [((n.lon + 180) / 360) * w, ((LAT_TOP - n.lat) / (LAT_TOP - LAT_BOTTOM)) * h];
    return pickNode(nodes, project, roles, mx, my);
  }

  window.addEventListener("resize", resize);
  resize();

  // The canvas's CSS width can change when the page layout settles (e.g. the dashboard grid
  // below it reflows) with no `window` resize event at all; W/H would then stay stale even
  // though clientWidth already moved. Watch the canvas's own container and re-run resize()
  // whenever its width actually changes (guarded so ResizeObserver's own layout changes to the
  // canvas, via resize()'s `canvas.style.height`, don't retrigger themselves).
  let lastW = canvas.clientWidth;
  if (typeof ResizeObserver !== "undefined" && canvas.parentElement) {
    const ro = new ResizeObserver(() => {
      const w = canvas.clientWidth;
      if (w === lastW) return;
      lastW = w;
      resize();
      onResize?.();
    });
    ro.observe(canvas.parentElement);
  }

  return { draw, pick, techColor, modeColor: MODE_COLOR };
}
