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
