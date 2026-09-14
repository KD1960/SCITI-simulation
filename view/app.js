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
  const config = await fetch("config.json").then((r) => r.json());
  base = config.has_baseline ? await loadRun("base") : null;
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
