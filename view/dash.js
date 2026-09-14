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
  const sign = v < 0 ? "-" : "";
  const a = Math.abs(v);
  const s = a >= 1e9 ? `${(a / 1e9).toFixed(2)}B` : a >= 1e6 ? `${(a / 1e6).toFixed(2)}M` : a >= 1e3 ? `${(a / 1e3).toFixed(1)}k`
    : a < 2 && a !== 0 && !Number.isInteger(a) ? a.toFixed(3) : a.toFixed(0);
  return `${sign}${unit}${s}`;
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

// Plain-language reasons for coalition_failed (sciti/coalitions.py) and rejected events.
const FAILED_REASON = {
  "no eligible partners": "no one eligible to invite",
  held: "the proposer already holds it",
  quota: "the proposer's one-new-tech quota was used up",
  acceptance: "not enough members accepted",
  budget: "a member could not afford its share",
};

export function describe(e, techs) {
  const t = techs[e.tech] ?? e.tech;
  switch (e.type) {
    case "adopt": return `${e.node} adopted ${t}${e.coalition ? ` (group ${e.coalition})` : " (alone)"}`;
    case "drop": return `${e.node} dropped ${t}`;
    case "coalition": return `${e.kind} formed for ${t}: ${e.members.join(", ")}`;
    case "coalition_failed": {
      const why = FAILED_REASON[e.reason] ?? e.reason;
      return `Group for ${t} proposed by ${e.proposer} did not form (${why})`;
    }
    case "rejected": return `${e.node} could not afford ${t} (${e.reason})`;
    case "disruption_start": return `Disruption at ${e.target} until week ${e.until}`;
    case "check_warning": return `Check warning: ${e.detail}`;
    default: return e.type;
  }
}

// Builds the last-60, newest-first feed lines (spec §10). `coalition_failed` events are
// grouped one line per week ("W144: 9 group proposals did not form (7 acceptance, 2 held)")
// so a week with many failed proposals doesn't push adoptions and formed groups off the feed.
// Every other kept event (adopt alone, coalition formed, drop, rejected, disruption, check
// warning) still gets its own line. Adopt events belonging to a coalition stay hidden, as before.
export function feedLines(events, week, techs) {
  const items = events.filter((e) => e.week <= week && !(e.type === "adopt" && e.coalition));
  const entries = []; // { week, text } | { week, counts: Map<reason, n> }
  const groupAt = new Map(); // week -> index into entries, for the running coalition_failed group
  for (const e of items) {
    if (e.type === "coalition_failed") {
      let idx = groupAt.get(e.week);
      if (idx === undefined) {
        idx = entries.length;
        entries.push({ week: e.week, counts: new Map() });
        groupAt.set(e.week, idx);
      }
      const why = FAILED_REASON[e.reason] ?? e.reason;
      const counts = entries[idx].counts;
      counts.set(why, (counts.get(why) ?? 0) + 1);
    } else {
      entries.push({ week: e.week, text: describe(e, techs) });
    }
  }
  const lines = entries.map((en) => {
    if (!en.counts) return `W${en.week}: ${en.text}`;
    const total = [...en.counts.values()].reduce((a, b) => a + b, 0);
    const parts = [...en.counts.entries()].sort((a, b) => b[1] - a[1]).map(([why, n]) => `${n} ${why}`);
    return `W${en.week}: ${total} group proposal${total === 1 ? "" : "s"} did not form (${parts.join(", ")})`;
  });
  return lines.slice(-60).reverse();
}

export function renderFeed(el, run, week) {
  const lines = feedLines(run.events, week, run.network.techs);
  el.replaceChildren();
  for (const text of lines) {
    const p = document.createElement("p");
    p.textContent = text;
    el.append(p);
  }
  if (!lines.length) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No events yet.";
    el.append(p);
  }
}

// The node's current tech holdings that came from a coalition (reflecting drops up to `week`),
// paired with that coalition's kind and other members from the matching `coalition` event.
export function currentCoalitions(run, nodeId, week) {
  const holding = {}; // tech -> coalition id (or null for a solo adopt)
  for (const e of run.events) {
    if (e.week > week) break;
    if (e.type === "adopt" && e.node === nodeId) holding[e.tech] = e.coalition ?? null;
    else if (e.type === "drop" && e.node === nodeId) delete holding[e.tech];
  }
  const coalitionById = new Map();
  for (const e of run.events) {
    if (e.week > week) break;
    if (e.type === "coalition") coalitionById.set(e.id, e);
  }
  return Object.entries(holding)
    .filter(([, cid]) => cid)
    .map(([tech, cid]) => {
      const ce = coalitionById.get(cid);
      return { tech, kind: ce?.kind ?? "group", others: (ce?.members ?? []).filter((m) => m !== nodeId) };
    });
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
  const gh = document.createElement("h3");
  gh.textContent = "Groups";
  el.append(gh);
  const groups = currentCoalitions(run, nodeId, week);
  if (!groups.length) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "Not in any group.";
    el.append(p);
  } else {
    for (const g of groups) {
      const p = document.createElement("p");
      const dot = document.createElement("i");
      dot.className = "swatch";
      dot.style.background = techColor[g.tech] ?? "#999";
      p.append(dot, `${run.network.techs[g.tech] ?? g.tech} — ${g.kind} with ${g.others.join(", ")}`);
      el.append(p);
    }
  }
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
