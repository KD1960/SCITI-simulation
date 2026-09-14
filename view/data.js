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
