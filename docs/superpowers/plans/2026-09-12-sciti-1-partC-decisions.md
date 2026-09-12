# SCITI 1 — Part C: Decisions (Tasks 11–16)

> Part of `2026-09-12-sciti-1.md`. Read that file's Global Constraints first. Requires Parts A and B. Steps use checkbox (`- [ ]`) syntax.

All shell commands run from the project root: `cd "$HOME/Claude/Projects/SCITI simulation"`.

## Decision model (applies to every task in this part)

- Every quarter start (`quarter_start(t)`), after forced adoptions, the runner calls `run_decision_round`.
- **Proposal pass:** every agent, in `net.order`, gets a brief and replies. Allowed actions: `adopt`, `skip`, `propose_group`, `drop`.
- **Response pass:** each agent that received at least one group proposal gets a second brief listing them. Allowed actions: `accept_group`, `decline_group` (each must name a `group_id`). Unanswered proposals count as declines.
- **Validation → one retry → rules fallback.** A reply that fails `validate_reply` is retried once with the error text as feedback; a second failure uses `RulesPolicy` for that agent and sets `fallback: true` in the log.
- **Budget** = `min(cash, persona.budget_share × revenue of the last 13 weeks)`. Over-budget adopts/accepts are rejected with an event `{"type": "rejected", "reason": "budget"}` (not a reply error).
- **Group members.** Explicit partner list → exactly those partners. `"chain"` → proposer's upstream ancestors and downstream descendants. `"network"` → all nodes. In every case, only nodes eligible for the tech and not already holding it are invited.
- **Formation.** Explicit lists and `pair` techs need every invitee to accept. `chain`/`network` need `accepted ÷ invited ≥ chain_accept_share`. Members' one-time cost share: `equal` = total of members' role costs ÷ member count; `by_size` = own role cost.
- **Log record** (one JSON line per agent per pass): `week, quarter, pass, agent, policy, brief, brief_hash, raw, error, retry_raw, retry_error, fallback, parsed, tokens_in, tokens_out, latency_s`. `parsed` is the final list of decisions actually used. Replay reads `parsed`.
- LLM operational notices (spend cap reached, policy disabled) go in the manifest, **not** `events.jsonl`, so replays match.

---

### Task 11: Decision interface, reply validation, briefs, mock policy

**Files:**
- Create: `sciti/decide/interface.py`, `sciti/decide/briefs.py`, `sciti/decide/mock.py`
- Test: `tests/test_decide_interface.py`

**Interfaces:**
- Consumes: `SimState`, `Network`, `Tech`, `TechHolding` (Parts A–B); `Assumptions.persona_budget_share`, `.persona_horizon_weeks`.
- Produces:
  - `sciti.decide.interface`: `PROPOSAL_ACTIONS = ("adopt", "skip", "propose_group", "drop")`; `RESPONSE_ACTIONS = ("accept_group", "decline_group")`; `MAX_REASON_WORDS = 40`; `ReplyError(Exception)`; dataclasses `Brief(agent, role, week, quarter, pass_, data: dict)`, `Decision(tech, action, partners: list[str], reason, group_id: str | None = None)`, `Reply(agent, raw: str, fallback=False, error: str | None = None, tokens_in=0, tokens_out=0, latency_s=0.0)`; `DecisionPolicy` Protocol with `name: str` and `decide(brief: Brief, feedback: str | None = None) -> Reply`; `NonePolicy`; `parse_reply(text: str) -> dict`; `validate_reply(obj: dict, brief: Brief, max_new: int) -> list[Decision]`; `brief_hash(brief: Brief) -> str`
  - `sciti.decide.briefs`: `make_personas(net, assumptions, rng) -> dict[str, dict]` (`risk` ∈ cautious/balanced/bold, `budget_share`, `horizon_weeks`); `budget_available(s, node_id, persona, recent: list[dict]) -> float`; `build_brief(s, node_id, week, pass_, persona, recent: list[dict], visibility: str, max_new: int, proposals: list[dict] | None = None) -> Brief`
  - `sciti.decide.mock`: `MockPolicy(script: list[dict])` — script entries `{"agent", "week", "pass", "replies": [str, ...]}`; the n-th call for that key returns the n-th string (last one repeats); default reply `'{"decisions": []}'`

Brief `data` keys: `you` (`id, role, city, persona`), `last_quarter` (`revenue, profit, cash, costs{…}, lost_sales, shipped_units, on_time_outbound`), `budget_available`, `your_technologies` (`tech, since_week, active, coalition`), `partners` (`id, role, technologies`), `eligible_technologies` (`id, name, one_time_cost, weekly_cost, setup_weeks, network_requirement, group_bonus, effects`) — eligible for the role and not already held; `held` (list of held tech ids), `network_adoption_counts` (only when visibility is `network`), `proposals` (response pass), `rules` (`pass, allowed_actions, max_new_adoptions, max_reason_words`).

- [ ] **Step 1: Write the failing tests**

`tests/test_decide_interface.py`:

```python
import json

import numpy as np
import pytest

from sciti.config import Assumptions
from sciti.decide.briefs import build_brief, make_personas
from sciti.decide.interface import Brief, ReplyError, parse_reply, validate_reply
from sciti.decide.mock import MockPolicy
from sciti.engine.adoption import adopt
from sciti.engine.ops import step_week
from tests.helpers import make_state


def brief(pass_="proposal", eligible=("routing", "rfid", "control_tower"), held=(), partners=("MFG_US", "MFG_China"),
          proposals=()):
    return Brief("DC_Houston", "DC", 14, 2, pass_, {
        "eligible_technologies": [{"id": t} for t in eligible], "held": list(held),
        "partners": [{"id": p} for p in partners], "proposals": [{"group_id": g} for g in proposals]})


def test_parse_reply_extracts_json_from_prose():
    assert parse_reply('Sure! {"decisions": []} done') == {"decisions": []}
    with pytest.raises(ReplyError):
        parse_reply("no json here")


def test_valid_proposal_reply():
    obj = {"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "cuts freight"},
                         {"tech": "control_tower", "action": "propose_group", "partners": ["chain"], "reason": "x"}]}
    ds = validate_reply(obj, brief(), max_new=2)
    assert [d.action for d in ds] == ["adopt", "propose_group"]


@pytest.mark.parametrize("obj,msg", [
    ({"nope": []}, "decisions"),
    ({"decisions": [{"tech": "wh_robotics", "action": "adopt", "partners": [], "reason": "x"}]}, "not eligible"),
    ({"decisions": [{"tech": "routing", "action": "fly", "partners": [], "reason": "x"}]}, "action"),
    ({"decisions": [{"tech": "routing", "action": "propose_group", "partners": ["Retail_8"], "reason": "x"}]}, "partner"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "word " * 41}]}, "words"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "a"},
                    {"tech": "rfid", "action": "adopt", "partners": [], "reason": "b"}]}, "at most"),
    ({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": "a"},
                    {"tech": "routing", "action": "skip", "partners": [], "reason": "b"}]}, "twice"),
    ({"decisions": [{"tech": "routing", "action": "drop", "partners": [], "reason": "a"}]}, "not held"),
    ({"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "a"}]}, "action"),
])
def test_invalid_replies_rejected(obj, msg):
    with pytest.raises(ReplyError, match=msg):
        validate_reply(obj, brief(), max_new=1)


def test_response_pass_needs_known_group():
    b = brief(pass_="response", proposals=["q2_MFG_US_routing"])
    ok = {"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "y",
                         "group_id": "q2_MFG_US_routing"}]}
    assert validate_reply(ok, b, max_new=1)[0].group_id == "q2_MFG_US_routing"
    bad = {"decisions": [{"tech": "routing", "action": "accept_group", "partners": [], "reason": "y",
                          "group_id": "q9_other"}]}
    with pytest.raises(ReplyError, match="group"):
        validate_reply(bad, b, max_new=1)


def test_personas_seeded(baseline):
    s = make_state(baseline)
    a = make_personas(s.net, Assumptions(), np.random.default_rng(3))
    b = make_personas(s.net, Assumptions(), np.random.default_rng(3))
    assert a == b and len(a) == 48
    assert a["Retail_1"]["risk"] in ("cautious", "balanced", "bold")


def test_brief_contents(baseline):
    s = make_state(baseline)
    for t in range(1, 14):
        step_week(s, t)
    adopt(s, "DC_Houston", "routing", 13)
    personas = make_personas(s.net, s.cfg.assumptions, np.random.default_rng(0))
    b = build_brief(s, "DC_Houston", 14, "proposal", personas["DC_Houston"], recent=[], visibility="partners", max_new=1)
    ids = [e["id"] for e in b.data["eligible_technologies"]]
    assert "routing" not in ids and "wh_robotics" in ids and "blockchain" not in ids
    assert b.data["held"] == ["routing"]
    assert [p["id"] for p in b.data["partners"]] == ["MFG_China", "MFG_US", "Retail_1", "Retail_2"]
    assert "network_adoption_counts" not in b.data
    json.dumps(b.data)  # must be JSON-serializable


def test_mock_policy_script_sequence():
    m = MockPolicy([{"agent": "DC_Houston", "week": 14, "pass": "proposal", "replies": ["bad", '{"decisions": []}']}])
    b = brief()
    assert m.decide(b).raw == "bad"
    assert m.decide(b, feedback="err").raw == '{"decisions": []}'
    assert m.decide(Brief("Retail_1", "Retail", 14, 2, "proposal", {})).raw == '{"decisions": []}'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_decide_interface.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.decide.interface'`

- [ ] **Step 3: Implement `sciti/decide/interface.py`**

```python
"""Decision policy contract and reply validation (spec §7.3)."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Protocol

PROPOSAL_ACTIONS = ("adopt", "skip", "propose_group", "drop")
RESPONSE_ACTIONS = ("accept_group", "decline_group")
MAX_REASON_WORDS = 40


class ReplyError(Exception):
    pass


@dataclass
class Brief:
    agent: str
    role: str
    week: int
    quarter: int
    pass_: str
    data: dict


@dataclass
class Decision:
    tech: str
    action: str
    partners: list[str] = field(default_factory=list)
    reason: str = ""
    group_id: str | None = None


@dataclass
class Reply:
    agent: str
    raw: str
    fallback: bool = False
    error: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0


class DecisionPolicy(Protocol):
    name: str

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply: ...


class NonePolicy:
    name = "none"

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        return Reply(brief.agent, '{"decisions": []}')


def parse_reply(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        raise ReplyError("reply contains no JSON object")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as e:
        raise ReplyError(f"reply JSON is malformed: {e}") from e
    if not isinstance(obj, dict):
        raise ReplyError("reply JSON must be an object")
    return obj


def validate_reply(obj: dict, brief: Brief, max_new: int) -> list[Decision]:
    items = obj.get("decisions")
    if not isinstance(items, list):
        raise ReplyError('reply must have a "decisions" list')
    data = brief.data
    eligible = {e["id"] for e in data.get("eligible_technologies", [])}
    held = set(data.get("held", []))
    partners = {p["id"] for p in data.get("partners", [])}
    groups = {p["group_id"] for p in data.get("proposals", [])}
    allowed = PROPOSAL_ACTIONS if brief.pass_ == "proposal" else RESPONSE_ACTIONS
    out, seen, new = [], set(), 0
    for i, d in enumerate(items):
        if not isinstance(d, dict):
            raise ReplyError(f"decision {i} must be an object")
        tech, action = d.get("tech"), d.get("action")
        reason = str(d.get("reason", ""))
        plist = d.get("partners", []) or []
        if action not in allowed:
            raise ReplyError(f"decision {i}: action {action!r} not allowed in {brief.pass_} pass; use one of {allowed}")
        key = d.get("group_id") if brief.pass_ == "response" else tech
        if key in seen:
            raise ReplyError(f"decision {i}: {key!r} appears twice")
        seen.add(key)
        if len(reason.split()) > MAX_REASON_WORDS:
            raise ReplyError(f"decision {i}: reason exceeds {MAX_REASON_WORDS} words")
        if not isinstance(plist, list) or not all(isinstance(p, str) for p in plist):
            raise ReplyError(f"decision {i}: partners must be a list of ids")
        if brief.pass_ == "response":
            if d.get("group_id") not in groups:
                raise ReplyError(f"decision {i}: unknown group_id {d.get('group_id')!r}")
        elif action == "drop":
            if tech not in held:
                raise ReplyError(f"decision {i}: cannot drop {tech!r}, not held")
        elif action != "skip" or tech not in held:
            if tech not in eligible:
                raise ReplyError(f"decision {i}: {tech!r} is not eligible for you or is already held")
        if action == "propose_group":
            if not plist or not (plist in (["chain"], ["network"]) or set(plist) <= partners):
                raise ReplyError(f"decision {i}: partners must be direct partners, or [\"chain\"] or [\"network\"]")
        if action in ("adopt", "propose_group"):
            new += 1
            if new > max_new:
                raise ReplyError(f"at most {max_new} new adoption(s) per quarter")
        out.append(Decision(tech=tech, action=action, partners=list(plist), reason=reason,
                            group_id=d.get("group_id")))
    return out


def brief_hash(brief: Brief) -> str:
    return hashlib.sha256(json.dumps(brief.data, sort_keys=True).encode()).hexdigest()
```

- [ ] **Step 4: Implement `sciti/decide/briefs.py`**

```python
"""What an agent may see at a quarterly decision (spec §7.2)."""
from __future__ import annotations

from sciti.decide.interface import Brief, PROPOSAL_ACTIONS, RESPONSE_ACTIONS, MAX_REASON_WORDS
from sciti.engine.state import PROFIT_COST_KEYS

RISKS = ("cautious", "balanced", "bold")


def make_personas(net, assumptions, rng) -> dict[str, dict]:
    lo, hi = assumptions.persona_budget_share
    hlo, hhi = assumptions.persona_horizon_weeks
    out = {}
    for n in net.order:
        out[n] = {"risk": RISKS[int(rng.integers(0, 3))],
                  "budget_share": round(float(rng.uniform(lo, hi)), 4),
                  "horizon_weeks": int(rng.integers(hlo, hhi + 1))}
    return out


def budget_available(s, node_id: str, persona: dict, recent: list[dict]) -> float:
    ns = s.nodes[node_id]
    rev = sum(r["revenue"] for r in recent)
    if not recent:
        rev = ns.cash / s.cfg.assumptions.initial_cash_weeks * 13
    return max(0.0, min(ns.cash, persona["budget_share"] * rev))


def _effects_text(tech) -> str:
    return "; ".join(f"{e.param} {'x' if e.op == 'mul' else '+'}{e.value}" for e in tech.effects)


def build_brief(s, node_id, week, pass_, persona, recent, visibility, max_new, proposals=None) -> Brief:
    net, ns = s.net, s.nodes[node_id]
    node = net.nodes[node_id]
    held = sorted(s.holdings[node_id])
    ships = [sh for sh in s.arrived if sh.src == node_id and sh.ship_week > week - 14]
    data = {
        "you": {"id": node_id, "role": node.role, "city": node.city, "persona": persona},
        "last_quarter": {
            "revenue": round(sum(r["revenue"] for r in recent), 2),
            "profit": round(sum(r["profit"] for r in recent), 2),
            "cash": round(ns.cash, 2),
            "costs": {k: round(sum(r[k] for r in recent), 2) for k in PROFIT_COST_KEYS + ("scrap",)},
            "lost_sales": round(sum(r["lost"] for r in recent), 2),
            "shipped_units": round(sum(r["shipped"] for r in recent), 2),
            "on_time_outbound": round(sum(sh.arrive_week <= sh.due_week for sh in ships) / len(ships), 4) if ships else None,
        },
        "budget_available": round(budget_available(s, node_id, persona, recent), 2),
        "your_technologies": [{"tech": t, "since_week": h.adopted_week, "active": week >= h.active_week,
                               "coalition": h.coalition_id} for t, h in sorted(s.holdings[node_id].items())],
        "held": held,
        "partners": [{"id": p, "role": net.nodes[p].role, "technologies": sorted(s.holdings[p])}
                     for p in net.partners(node_id)],
        "eligible_technologies": [
            {"id": t.id, "name": t.name, "one_time_cost": t.cost_one_time[node.role],
             "weekly_cost": t.cost_per_week[node.role], "setup_weeks": t.setup_weeks,
             "network_requirement": t.network_requirement, "group_bonus": t.group_bonus,
             "effects": _effects_text(t)}
            for t in sorted(s.catalog.values(), key=lambda x: x.id)
            if node.role in t.eligible_roles and t.id not in held],
        "rules": {"pass": pass_, "allowed_actions": list(PROPOSAL_ACTIONS if pass_ == "proposal" else RESPONSE_ACTIONS),
                  "max_new_adoptions": max_new, "max_reason_words": MAX_REASON_WORDS},
    }
    if visibility == "network":
        counts = {}
        for n in net.order:
            for t in s.holdings[n]:
                counts[t] = counts.get(t, 0) + 1
        data["network_adoption_counts"] = dict(sorted(counts.items()))
    if pass_ == "response":
        data["proposals"] = proposals or []
    return Brief(node_id, node.role, week, (week - 1) // 13 + 1, pass_, data)
```

- [ ] **Step 5: Implement `sciti/decide/mock.py`**

```python
"""Scripted policy for tests; never calls an API (spec §11)."""
from __future__ import annotations

from sciti.decide.interface import Brief, Reply

EMPTY = '{"decisions": []}'


class MockPolicy:
    name = "mock"

    def __init__(self, script: list[dict]):
        self.script = {(e["agent"], e["week"], e["pass"]): list(e["replies"]) for e in script}
        self.calls: dict[tuple, int] = {}

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        key = (brief.agent, brief.week, brief.pass_)
        replies = self.script.get(key)
        if not replies:
            return Reply(brief.agent, EMPTY)
        i = self.calls.get(key, 0)
        self.calls[key] = i + 1
        return Reply(brief.agent, replies[min(i, len(replies) - 1)])
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_decide_interface.py -v`
Expected: 16 passed

- [ ] **Step 7: Commit**

```bash
git add sciti/decide/interface.py sciti/decide/briefs.py sciti/decide/mock.py tests/test_decide_interface.py
git commit -m "feat: decision contract, strict reply validation, agent briefs, mock policy

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: Coalitions and the quarterly decision round

**Files:**
- Create: `sciti/coalitions.py`
- Modify: `sciti/runner.py` (build personas, policy, and call the round)
- Test: `tests/test_coalitions.py`

**Interfaces:**
- Consumes: Task 11 interfaces; `adopt`, `drop`, `coalition_kind` (Task 9); `RunWriter.log_decision`.
- Produces:
  - `sciti.coalitions.group_members(net, holdings, catalog, proposer, tech_id, partners: list[str]) -> list[str]` (sorted, includes proposer)
  - `sciti.coalitions.DecisionContext` dataclass: `policy, fallback, writer, personas: dict, recent: dict[str, list[dict]]`
  - `sciti.coalitions.run_decision_round(s, t: int, ctx: DecisionContext) -> dict` returning stats `{"calls", "fallbacks", "errors"}`
  - `sciti.runner.make_policy(cfg, s, client=None)` → `(policy, fallback)`; in this task supports `none` and `mock` (Tasks 13–15 add `rules`, `llm`, `replay`)
  - `run(cfg, run_dir=None, client=None) -> Path` — the `policy` argument from Task 9 is replaced by `client` (used by `llm`)

- [ ] **Step 1: Write the failing tests**

`tests/test_coalitions.py`:

```python
import json

from sciti.config import Config, DecisionCfg
from sciti.coalitions import group_members
from sciti.runner import run
from tests.helpers import make_state


def reply(*decisions):
    return json.dumps({"decisions": list(decisions)})


def d(tech, action, partners=(), group_id=None, reason="ok"):
    out = {"tech": tech, "action": action, "partners": list(partners), "reason": reason}
    if group_id:
        out["group_id"] = group_id
    return out


def mock_cfg(baseline_path, tmp_path, script, **decision):
    return Config(name="m", seed=2, weeks=27, baseline_path=str(baseline_path), output_dir=str(tmp_path),
                  decision=DecisionCfg(policy="mock", mock_script=script, **decision))


def events(run_dir):
    return [json.loads(x) for x in (run_dir / "events.jsonl").read_text().splitlines()]


def test_group_members_chain_and_network(baseline):
    s = make_state(baseline)
    chain = group_members(s.net, s.holdings, s.catalog, "DC_Shanghai", "control_tower", ["chain"])
    assert "Retail_8" in chain and "MFG_China" in chain and "Supplier_1" in chain and "Retail_1" not in chain
    net_all = group_members(s.net, s.holdings, s.catalog, "DC_Shanghai", "wh_robotics", ["network"])
    assert net_all == ["DC_Dubai", "DC_Houston", "DC_Shanghai", "DC_Sofia"]
    pair = group_members(s.net, s.holdings, s.catalog, "CM_1", "blockchain", ["Supplier_1", "Supplier_2"])
    assert pair == ["CM_1", "Supplier_1", "Supplier_2"]


def test_solo_adopt_logged_and_applied(baseline_path, tmp_path):
    script = [{"agent": "MFG_US", "week": 14, "pass": "proposal", "replies": [reply(d("routing", "adopt"))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = [e for e in events(out) if e["type"] == "adopt"]
    assert ev == [{"week": 14, "type": "adopt", "node": "MFG_US", "tech": "routing", "coalition": None, "one_time": 400000}]
    logs = [json.loads(x) for x in (out / "decisions.jsonl").read_text().splitlines()]
    assert len([l for l in logs if l["pass"] == "proposal"]) == 48 * 3
    mine = [l for l in logs if l["agent"] == "MFG_US" and l["week"] == 14][0]
    assert mine["parsed"][0]["action"] == "adopt" and mine["fallback"] is False


def test_dyad_forms_when_partner_accepts(baseline_path, tmp_path):
    gid = "q2_CM_1_blockchain"
    script = [
        {"agent": "CM_1", "week": 14, "pass": "proposal", "replies": [reply(d("blockchain", "propose_group", ["Supplier_1"]))]},
        {"agent": "Supplier_1", "week": 14, "pass": "response",
         "replies": [reply(d("blockchain", "accept_group", group_id=gid))]},
    ]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    co = [e for e in ev if e["type"] == "coalition"]
    assert co == [{"week": 14, "type": "coalition", "id": gid, "tech": "blockchain",
                   "members": ["CM_1", "Supplier_1"], "kind": "dyad"}]
    shares = sorted(e["one_time"] for e in ev if e["type"] == "adopt")
    assert shares == [200000.0, 200000.0]  # (300k + 100k) / 2


def test_group_fails_when_partner_declines(baseline_path, tmp_path):
    script = [{"agent": "CM_1", "week": 14, "pass": "proposal",
               "replies": [reply(d("blockchain", "propose_group", ["Supplier_1"]))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    ev = events(out)
    assert [e["type"] for e in ev if e["type"].startswith("coalition")] == ["coalition_failed"]
    assert not [e for e in ev if e["type"] == "adopt"]


def test_bad_reply_retry_then_fallback(baseline_path, tmp_path):
    script = [{"agent": "Retail_2", "week": 14, "pass": "proposal", "replies": ["garbage", "still garbage"]},
              {"agent": "Retail_3", "week": 14, "pass": "proposal",
               "replies": ["garbage", reply(d("rfid", "skip"))]}]
    out = run(mock_cfg(baseline_path, tmp_path, script), run_dir=tmp_path / "r")
    logs = {(l["agent"], l["week"], l["pass"]): l for l in map(json.loads, (out / "decisions.jsonl").read_text().splitlines())}
    r2, r3 = logs[("Retail_2", 14, "proposal")], logs[("Retail_3", 14, "proposal")]
    assert r2["fallback"] is True and r2["error"] and r2["retry_error"]
    assert r3["fallback"] is False and r3["error"] and r3["retry_error"] is None
    assert r3["parsed"] == [{"tech": "rfid", "action": "skip", "partners": [], "reason": "ok", "group_id": None}]


def test_over_budget_rejected(baseline_path, tmp_path):
    script = [{"agent": "Retail_6", "week": 14, "pass": "proposal", "replies": [reply(d("control_tower", "propose_group", ["network"]))]},
              {"agent": "DC_Sofia", "week": 14, "pass": "proposal", "replies": [reply(d("wh_robotics", "adopt"))]}]
    c = mock_cfg(baseline_path, tmp_path, script)
    c.assumptions.persona_budget_share = (0.0, 0.0)
    out = run(c, run_dir=tmp_path / "r")
    ev = events(out)
    assert {"week": 14, "type": "rejected", "node": "DC_Sofia", "tech": "wh_robotics", "reason": "budget"} in ev
    assert not [e for e in ev if e["type"] == "adopt"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_coalitions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.coalitions'`

- [ ] **Step 3: Implement `sciti/coalitions.py`**

```python
"""Quarterly decision round: proposals, responses, coalitions (spec §7.4)."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from sciti.decide.briefs import budget_available, build_brief
from sciti.decide.interface import ReplyError, brief_hash, parse_reply, validate_reply
from sciti.engine.adoption import adopt, coalition_kind, drop


@dataclass
class DecisionContext:
    policy: object
    fallback: object
    writer: object
    personas: dict
    recent: dict


def _reach(net, start, edges):
    seen, stack = set(), [start]
    while stack:
        for nxt in edges[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def group_members(net, holdings, catalog, proposer, tech_id, partners) -> list[str]:
    tech = catalog[tech_id]
    if partners == ["network"]:
        pool = set(net.order)
    elif partners == ["chain"]:
        pool = _reach(net, proposer, net.upstream) | _reach(net, proposer, net.downstream)
    else:
        pool = set(partners)
    pool.add(proposer)
    return sorted(n for n in pool if net.nodes[n].role in tech.eligible_roles
                  and (n == proposer or tech_id not in holdings[n]))


def _ask(s, t, ctx, brief, max_new):
    """Policy reply → validate → one retry → rules fallback. Returns decisions and writes the log."""
    rec = {"week": t, "quarter": brief.quarter, "pass": brief.pass_, "agent": brief.agent,
           "policy": ctx.policy.name, "brief": brief.data, "brief_hash": brief_hash(brief),
           "raw": None, "error": None, "retry_raw": None, "retry_error": None, "fallback": False,
           "tokens_in": 0, "tokens_out": 0, "latency_s": 0.0}
    reply = ctx.policy.decide(brief)
    rec.update(raw=reply.raw, fallback=reply.fallback, tokens_in=reply.tokens_in,
               tokens_out=reply.tokens_out, latency_s=reply.latency_s)
    if reply.fallback:
        rec["error"] = reply.error
    try:
        decisions = validate_reply(parse_reply(reply.raw), brief, max_new)
    except ReplyError as e:
        rec["error"] = str(e)
        retry = ctx.policy.decide(brief, feedback=str(e))
        rec.update(retry_raw=retry.raw, tokens_in=rec["tokens_in"] + retry.tokens_in,
                   tokens_out=rec["tokens_out"] + retry.tokens_out)
        try:
            decisions = validate_reply(parse_reply(retry.raw), brief, max_new)
        except ReplyError as e2:
            rec["retry_error"] = str(e2)
            rec["fallback"] = True
            decisions = validate_reply(parse_reply(ctx.fallback.decide(brief).raw), brief, max_new)
    rec["parsed"] = [dataclasses.asdict(d) for d in decisions]
    ctx.writer.log_decision(rec)
    return decisions, rec


def run_decision_round(s, t: int, ctx: DecisionContext) -> dict:
    D = s.cfg.decision
    net = s.net
    stats = {"calls": 0, "fallbacks": 0, "errors": 0}
    budget = {n: budget_available(s, n, ctx.personas[n], ctx.recent.get(n, [])) for n in net.order}
    new_count = {n: 0 for n in net.order}
    groups: dict[str, dict] = {}

    def charge(node, tech_id, cost):
        if cost > budget[node] + 1e-9:
            s.events.append({"week": t, "type": "rejected", "node": node, "tech": tech_id, "reason": "budget"})
            return False
        budget[node] -= cost
        return True

    for n in net.order:
        brief = build_brief(s, n, t, "proposal", ctx.personas[n], ctx.recent.get(n, []), D.visibility,
                            D.max_new_adoptions_per_quarter)
        decisions, rec = _ask(s, t, ctx, brief, D.max_new_adoptions_per_quarter)
        stats["calls"] += 1
        stats["fallbacks"] += rec["fallback"]
        stats["errors"] += rec["error"] is not None
        for dcs in decisions:
            role = net.nodes[n].role
            if dcs.action == "drop":
                drop(s, n, dcs.tech, t)
            elif dcs.action == "adopt":
                if charge(n, dcs.tech, s.catalog[dcs.tech].cost_one_time[role]):
                    adopt(s, n, dcs.tech, t)
                    new_count[n] += 1
            elif dcs.action == "propose_group":
                members = group_members(net, s.holdings, s.catalog, n, dcs.tech, dcs.partners)
                invited = [m for m in members if m != n]
                if not invited:
                    s.events.append({"week": t, "type": "coalition_failed", "id": None, "tech": dcs.tech,
                                     "proposer": n, "reason": "no eligible partners"})
                    continue
                gid = f"q{brief.quarter}_{n}_{dcs.tech}"
                strict = dcs.partners not in (["chain"], ["network"]) or s.catalog[dcs.tech].network_requirement == "pair"
                groups[gid] = {"id": gid, "tech": dcs.tech, "proposer": n, "invited": invited,
                               "members": members, "strict": strict, "accepted": []}

    inbox: dict[str, list[dict]] = {}
    for g in groups.values():
        for m in g["invited"]:
            inbox.setdefault(m, []).append(g)
    for n in [x for x in net.order if x in inbox]:
        props = []
        for g in sorted(inbox[n], key=lambda g: g["id"]):
            props.append({"group_id": g["id"], "tech": g["tech"], "from": g["proposer"], "members": g["members"],
                          "your_cost_share": _share(s, g["tech"], g["members"], n)})
        brief = build_brief(s, n, t, "response", ctx.personas[n], ctx.recent.get(n, []), D.visibility,
                            D.max_new_adoptions_per_quarter, proposals=props)
        decisions, rec = _ask(s, t, ctx, brief, len(props))
        stats["calls"] += 1
        stats["fallbacks"] += rec["fallback"]
        stats["errors"] += rec["error"] is not None
        for dcs in sorted(decisions, key=lambda x: x.group_id):
            if dcs.action == "accept_group" and new_count[n] < D.max_new_adoptions_per_quarter:
                g = groups[dcs.group_id]
                if g["tech"] not in s.holdings[n]:
                    g["accepted"].append(n)
                    new_count[n] += 1

    for gid in sorted(groups):
        g = groups[gid]
        # a member may have joined an earlier group for the same tech this round
        accepted = sorted(m for m in g["accepted"] if g["tech"] not in s.holdings[m])
        ok = len(accepted) == len(g["invited"]) if g["strict"] else \
            len(accepted) / len(g["invited"]) >= D.chain_accept_share
        final = sorted([g["proposer"]] + accepted)
        if ok:
            affordable = [m for m in final if _share(s, g["tech"], final, m) <= budget[m] + 1e-9]
            if len(affordable) < len(final):
                for m in sorted(set(final) - set(affordable)):
                    s.events.append({"week": t, "type": "rejected", "node": m, "tech": g["tech"], "reason": "budget"})
                accepted = [m for m in accepted if m in affordable]
                ok = g["proposer"] in affordable and (
                    len(accepted) == len(g["invited"]) if g["strict"] else len(accepted) / len(g["invited"]) >= D.chain_accept_share)
                final = sorted([g["proposer"]] + accepted)
        if not ok or len(final) < 2 or g["tech"] in s.holdings[g["proposer"]]:
            s.events.append({"week": t, "type": "coalition_failed", "id": gid, "tech": g["tech"],
                             "proposer": g["proposer"], "accepted": accepted})
            continue
        s.events.append({"week": t, "type": "coalition", "id": gid, "tech": g["tech"], "members": final,
                         "kind": coalition_kind(net, final)})
        for m in final:
            cost = _share(s, g["tech"], final, m)
            budget[m] -= cost
            adopt(s, m, g["tech"], t, gid, cost)
    return stats


def _share(s, tech_id, members, node) -> float:
    tech = s.catalog[tech_id]
    if s.cfg.decision.cost_split == "by_size":
        return float(tech.cost_one_time[s.nodes[node].role])
    return sum(tech.cost_one_time[s.nodes[m].role] for m in members) / len(members)
```

- [ ] **Step 4: Modify `sciti/runner.py`**

Add imports:

```python
from sciti.coalitions import DecisionContext, run_decision_round
from sciti.decide.briefs import make_personas
from sciti.decide.interface import NonePolicy
from sciti.decide.mock import MockPolicy
```

Add this function above `run`:

```python
def make_policy(cfg, s, client=None):
    """Return (policy, fallback). Tasks 13–15 extend this."""
    kind = cfg.decision.policy
    fallback = NonePolicy()
    if kind == "none":
        return NonePolicy(), fallback
    if kind == "mock":
        return MockPolicy(cfg.decision.mock_script), fallback
    raise ValueError(f"unsupported decision policy {kind!r}")
```

Change the signature to `def run(cfg, run_dir: Path | None = None, client=None) -> Path:`.

After `writer = RunWriter(run_dir)` add:

```python
    policy, fallback = make_policy(cfg, s, client)
    ctx = DecisionContext(policy=policy, fallback=fallback, writer=writer,
                          personas=make_personas(net, cfg.assumptions, streams["personas"]), recent={})
    decision_stats = {"calls": 0, "fallbacks": 0, "errors": 0}
```

Replace the quarter block inside the week loop with:

```python
            if quarter_start(t):
                apply_forced(s, t)
                if cfg.decision.policy != "none":
                    ctx.recent = {n: [r for r in rows[-13 * len(net.order):] if r["node"] == n] for n in net.order}
                    for k, v in run_decision_round(s, t, ctx).items():
                        decision_stats[k] += v
```

Change both `extra` dicts passed to `build_manifest` to include decision stats and any policy stats:

```python
    extra = {"catalog_sha256": catalog_hash(cfg.catalog_path), "xlsx_sha256": baseline["source"]["xlsx_sha256"]}
```

becomes (define just before the `try:`; policy stats are read at finish time):

```python
    def manifest_extra(checks_value):
        return {"catalog_sha256": catalog_hash(cfg.catalog_path), "xlsx_sha256": baseline["source"]["xlsx_sha256"],
                "checks": checks_value, "decisions": decision_stats,
                "policy_stats": getattr(policy, "stats", lambda: {})()}
```

and each `build_manifest(cfg, run_id, started, now(), {**extra, "checks": checks})` becomes `build_manifest(cfg, run_id, started, now(), manifest_extra(checks))`.

Note: with policy `none` no decision round runs, so `decisions.jsonl` stays empty and earlier golden output is unchanged.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_coalitions.py tests/test_runner.py tests/test_golden.py -v`
Expected: all pass (golden summary unchanged because policy is `none`).

- [ ] **Step 6: Commit**

```bash
git add sciti/coalitions.py sciti/runner.py tests/test_coalitions.py
git commit -m "feat: quarterly decision round with coalitions, retry, fallback, budgets

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 13: Rules policy

**Files:**
- Create: `sciti/decide/rules.py`, `configs/rules.yaml`
- Modify: `sciti/runner.py` (`make_policy`: `rules`, and rules as fallback for every policy except `none`)
- Test: `tests/test_rules.py`

**Interfaces:**
- Consumes: `Brief`, `Reply` (Task 11), brief data keys.
- Produces:
  - `sciti.decide.rules.TECH_SAVINGS: dict[str, dict[str, float]]` (tech → {cost key: fraction saved})
  - `RulesPolicy(rng)` with `name = "rules"`, `decide(brief, feedback=None) -> Reply` (always valid JSON)
  - Rule (proposal): for each eligible tech in id order draw `noise = rng.lognormal(0, 0.3)`; weekly saving = `Σ last_quarter.costs[k] · frac / 13 · noise · RISK[risk]` (RISK: cautious 0.7, balanced 1.0, bold 1.3); net = saving − weekly_cost; payback = one_time ÷ net; candidate if `net > 0`, `payback ≤ horizon_weeks`, `one_time ≤ budget_available`. Choose the smallest paybacks up to `max_new_adoptions`. Action: `solo` → `adopt`; `chain` → `propose_group ["chain"]`; `pair` → `propose_group` with all partners whose role is in the tech's eligibility (from `partners[].role`; eligibility read from `TECH_ROLES`); if none, skip.
  - Rule (response): for each proposal in group-id order: look up saving with `group_bonus` from `TECH_BONUS`; accept if `net > 0` and `your_cost_share ÷ net ≤ horizon_weeks` and `your_cost_share ≤ budget_available`; else decline. Draw one noise value per proposal.

- [ ] **Step 1: Write the failing test**

`tests/test_rules.py`:

```python
import json

import numpy as np

from sciti.config import Config, DecisionCfg
from sciti.decide.interface import Brief, validate_reply, parse_reply
from sciti.decide.rules import RulesPolicy
from sciti.runner import run


def brief(costs, budget=1e9, horizon=104, risk="balanced", eligible=None, pass_="proposal", proposals=()):
    eligible = eligible or [{"id": "routing", "one_time_cost": 300000, "weekly_cost": 3000,
                             "network_requirement": "solo", "group_bonus": 0.25}]
    return Brief("DC_Houston", "DC", 14, 2, pass_, {
        "you": {"persona": {"risk": risk, "budget_share": 0.05, "horizon_weeks": horizon}},
        "last_quarter": {"costs": costs}, "budget_available": budget,
        "eligible_technologies": eligible, "held": [], "partners": [{"id": "MFG_US", "role": "MFG"}],
        "proposals": list(proposals), "rules": {"max_new_adoptions": 1}})


def test_adopts_when_payback_short():
    b = brief({"shipping": 13 * 200000})  # saves ~16k/week vs 3k cost → payback ~23 weeks
    ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(0)).decide(b).raw), b, 1)
    assert [(d.tech, d.action) for d in ds] == [("routing", "adopt")]


def test_skips_when_no_saving_or_no_budget():
    p = RulesPolicy(np.random.default_rng(0))
    assert json.loads(p.decide(brief({"shipping": 0})).raw) == {"decisions": []}
    assert json.loads(p.decide(brief({"shipping": 13 * 200000}, budget=10)).raw) == {"decisions": []}


def test_response_accepts_affordable_share():
    prop = {"group_id": "g1", "tech": "routing", "from": "MFG_US", "members": ["DC_Houston", "MFG_US"],
            "your_cost_share": 350000}
    b = brief({"shipping": 13 * 200000}, pass_="response", proposals=[prop])
    ds = validate_reply(parse_reply(RulesPolicy(np.random.default_rng(1)).decide(b).raw), b, 1)
    assert ds[0].action == "accept_group" and ds[0].group_id == "g1"


def test_rules_run_is_deterministic_and_adopts(baseline_path, tmp_path):
    c = Config(name="r", seed=5, weeks=52, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    a = run(c, run_dir=tmp_path / "a")
    b = run(c, run_dir=tmp_path / "b")
    assert (a / "events.jsonl").read_bytes() == (b / "events.jsonl").read_bytes()
    summary = json.loads((a / "summary.json").read_text())
    assert summary["adoptions"] > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_rules.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.decide.rules'`

- [ ] **Step 3: Implement `sciti/decide/rules.py`**

```python
"""Transparent payback rule; also the fallback for every other policy (spec §4.2, §9.2)."""
from __future__ import annotations

import json

from sciti.decide.interface import Brief, Reply
from sciti.tech.catalog import load_catalog

TECH_SAVINGS = {
    "ml_forecast": {"stockout": 0.20, "holding": 0.10},
    "control_tower": {"stockout": 0.10, "holding": 0.10},
    "rfid": {"stockout": 0.05, "scrap": 0.50},
    "aps": {"stockout": 0.10},
    "routing": {"shipping": 0.08},
    "wh_robotics": {"handling": 0.20},
    "blockchain": {"scrap": 0.40, "purchases": 0.002},
    "risk_intel": {"stockout": 0.05},
}
RISK = {"cautious": 0.7, "balanced": 1.0, "bold": 1.3}
_CAT = load_catalog()
TECH_ROLES = {t.id: t.eligible_roles for t in _CAT.values()}
TECH_BONUS = {t.id: t.group_bonus for t in _CAT.values()}
TECH_WEEKLY = {t.id: t.cost_per_week for t in _CAT.values()}


class RulesPolicy:
    name = "rules"

    def __init__(self, rng):
        self.rng = rng

    def _saving(self, data, tech_id, noise, bonus=0.0) -> float:
        costs = data["last_quarter"]["costs"]
        risk = RISK[data["you"]["persona"]["risk"]]
        base = sum(costs.get(k, 0.0) * f for k, f in TECH_SAVINGS.get(tech_id, {}).items()) / 13
        return base * noise * risk * (1 + bonus)

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        data = brief.data
        persona = data["you"]["persona"]
        out = []
        if brief.pass_ == "proposal":
            cands = []
            for e in sorted(data["eligible_technologies"], key=lambda e: e["id"]):
                noise = float(self.rng.lognormal(0, 0.3))
                net = self._saving(data, e["id"], noise) - e["weekly_cost"]
                if net <= 0 or e["one_time_cost"] > data["budget_available"]:
                    continue
                payback = e["one_time_cost"] / net
                if payback <= persona["horizon_weeks"]:
                    cands.append((payback, e))
            for payback, e in sorted(cands, key=lambda x: (x[0], x[1]["id"]))[: data["rules"]["max_new_adoptions"]]:
                reason = f"payback about {payback:.0f} weeks"
                if e["network_requirement"] == "solo":
                    out.append({"tech": e["id"], "action": "adopt", "partners": [], "reason": reason})
                elif e["network_requirement"] == "chain":
                    out.append({"tech": e["id"], "action": "propose_group", "partners": ["chain"], "reason": reason})
                else:
                    ps = sorted(p["id"] for p in data["partners"] if p["role"] in TECH_ROLES[e["id"]])
                    if ps:
                        out.append({"tech": e["id"], "action": "propose_group", "partners": ps, "reason": reason})
        else:
            for p in sorted(data.get("proposals", []), key=lambda p: p["group_id"]):
                noise = float(self.rng.lognormal(0, 0.3))
                weekly = TECH_WEEKLY[p["tech"]].get(brief.role, 0.0)
                net = self._saving(data, p["tech"], noise, TECH_BONUS[p["tech"]]) - weekly
                share = p["your_cost_share"]
                ok = net > 0 and share / net <= persona["horizon_weeks"] and share <= data["budget_available"]
                out.append({"tech": p["tech"], "action": "accept_group" if ok else "decline_group",
                            "partners": [], "reason": "worth it" if ok else "not worth it", "group_id": p["group_id"]})
        return Reply(brief.agent, json.dumps({"decisions": out}))
```

Note: `TECH_ROLES`, `TECH_BONUS`, `TECH_WEEKLY` come from the packaged catalog. A run with a custom `catalog_path` and new tech ids gets zero estimated savings for those techs (rules never adopt them); that is the intended conservative default.

- [ ] **Step 4: Modify `make_policy` in `sciti/runner.py`**

```python
from sciti.decide.rules import RulesPolicy
```

```python
def make_policy(cfg, s, client=None):
    """Return (policy, fallback). Tasks 14–15 extend this."""
    kind = cfg.decision.policy
    fallback = RulesPolicy(s.streams["rules"])
    if kind == "none":
        return NonePolicy(), NonePolicy()
    if kind == "rules":
        return fallback, fallback
    if kind == "mock":
        return MockPolicy(cfg.decision.mock_script), fallback
    raise ValueError(f"unsupported decision policy {kind!r}")
```

`configs/rules.yaml`:

```yaml
# Agents decide with the transparent payback rule (no API calls).
name: rules
seed: 1
weeks: 156
decision:
  policy: rules
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_rules.py tests/test_coalitions.py -v`
Expected: all pass. `test_bad_reply_retry_then_fallback` now falls back to rules (still valid).

- [ ] **Step 6: Commit**

```bash
git add sciti/decide/rules.py sciti/runner.py configs/rules.yaml tests/test_rules.py
git commit -m "feat: rule-based payback policy, used as fallback for all agent policies

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 14: LLM policy with spend caps and fallback

**Files:**
- Create: `sciti/decide/llm.py`, `sciti/decide/prompts/v1_system.md`, `configs/mvp_llm.yaml`
- Modify: `sciti/runner.py` (`make_policy`: `llm`)
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `Brief`, `Reply`, `RulesPolicy`, `DecisionCfg` fields `model, max_tokens, max_llm_calls, max_spend_usd, price_per_mtok_in, price_per_mtok_out, max_consecutive_failures`.
- Produces:
  - `sciti.decide.llm.PROMPT_VERSION = "v1"`; `load_system_prompt() -> str`; `render_brief(brief: Brief) -> str`
  - `SpendTracker(max_calls, max_usd, price_in, price_out)` with `.calls`, `.usd`, `.cost(tokens_in, tokens_out) -> float`, `.can_call(est_in=3000, est_out=600) -> bool`, `.record(tokens_in, tokens_out)`
  - `LLMPolicy(decision_cfg, fallback, client=None, sleep=time.sleep)` with `name = "llm"`, `decide(brief, feedback=None) -> Reply`, `stats() -> dict` (`prompt_version, model, calls, usd, fallbacks, disabled_reason`)
  - `client` must expose `client.messages.create(model=, max_tokens=, system=, messages=)` returning an object with `.content` (items with `.type`, `.text`) and `.usage.input_tokens/.output_tokens`. When `client` is None, `anthropic.Anthropic()` is built (reads `ANTHROPIC_API_KEY` from the environment).

- [ ] **Step 1: Write the failing test**

`tests/test_llm.py`:

```python
import json
from types import SimpleNamespace

import anthropic
import httpx
import numpy as np
import pytest

from sciti.config import Config, DecisionCfg
from sciti.decide.interface import Brief
from sciti.decide.llm import LLMPolicy, SpendTracker, render_brief
from sciti.decide.rules import RulesPolicy
from sciti.runner import run

FAKE_KEY = "sk-ant-api03-FAKEFAKEFAKEFAKE1234567890"


class FakeClient:
    def __init__(self, texts=None, errors=0):
        self.texts, self.errors, self.calls = list(texts or []), errors, []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if self.errors:
            self.errors -= 1
            raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://example.invalid"))
        text = self.texts.pop(0) if self.texts else '{"decisions": []}'
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=1000, output_tokens=100))


def cfg(**kw):
    return DecisionCfg(policy="llm", model="test-model", price_per_mtok_in=1.0, price_per_mtok_out=5.0, **kw)


def b():
    return Brief("Retail_1", "Retail", 14, 2, "proposal", {"you": {"persona": {"risk": "bold", "budget_share": 0.1,
            "horizon_weeks": 52}}, "last_quarter": {"costs": {}}, "budget_available": 0,
            "eligible_technologies": [], "held": [], "partners": [], "rules": {"max_new_adoptions": 1}})


def test_spend_tracker():
    t = SpendTracker(max_calls=2, max_usd=1.0, price_in=1.0, price_out=5.0)
    assert t.cost(1_000_000, 0) == 1.0
    assert t.can_call(1000, 100)
    t.record(1000, 100)
    t.record(1000, 100)
    assert not t.can_call(1000, 100)


def test_call_passes_model_system_and_brief():
    c = FakeClient(['{"decisions": []}'])
    p = LLMPolicy(cfg(), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: None)
    r = p.decide(b(), feedback="bad json")
    kw = c.calls[0]
    assert kw["model"] == "test-model" and "JSON" in kw["system"]
    assert "bad json" in kw["messages"][0]["content"]
    assert r.tokens_in == 1000 and r.fallback is False
    assert p.stats()["usd"] == pytest.approx((1000 * 1 + 100 * 5) / 1e6)


def test_spend_cap_falls_back_without_calling():
    c = FakeClient()
    p = LLMPolicy(cfg(max_llm_calls=0), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: None)
    r = p.decide(b())
    assert r.fallback and "cap" in r.error and c.calls == []
    assert p.stats()["disabled_reason"].startswith("spend cap")


def test_transient_errors_retry_then_disable():
    c = FakeClient(errors=100)
    p = LLMPolicy(cfg(max_consecutive_failures=2), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: None)
    r1, r2, r3 = p.decide(b()), p.decide(b()), p.decide(b())
    assert r1.fallback and r2.fallback and r3.fallback
    assert len(c.calls) == 6  # 3 attempts × 2 decisions, then disabled
    assert "failures" in p.stats()["disabled_reason"]


def test_render_is_json_block():
    assert '"agent": "Retail_1"' in render_brief(b())


def test_llm_run_logs_and_never_writes_key(baseline_path, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    reply = json.dumps({"decisions": [{"tech": "routing", "action": "adopt", "partners": [], "reason": FAKE_KEY}]})
    c = Config(name="llm", seed=1, weeks=14, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=cfg(max_spend_usd=5.0))
    out = run(c, run_dir=tmp_path / "r", client=FakeClient([reply] * 200))
    for f in out.iterdir():
        assert FAKE_KEY not in f.read_text(), f.name
    man = json.loads((out / "manifest.json").read_text())
    assert man["policy_stats"]["calls"] > 0 and man["policy_stats"]["prompt_version"] == "v1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_llm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.decide.llm'`

- [ ] **Step 3: Write `sciti/decide/prompts/v1_system.md`**

```markdown
You are the decision-maker for one firm in a simulated supply chain (Ridge Line). Each quarter you
receive a JSON briefing about your firm: role, persona, last quarter's results, your budget, your
partners and their technologies, and the technologies you may adopt.

Decide whether to adopt supply chain technologies, alone or together with partners.

- `adopt`: adopt a technology on your own.
- `propose_group`: invite partners to adopt together. `partners` is a list of your direct partner ids,
  or ["chain"] (your whole upstream and downstream chain) or ["network"] (every eligible firm).
  Groups share the one-time cost and get a group bonus. Some technologies only work if partners also adopt.
- `skip`: do nothing about a technology.
- `drop`: stop using a technology you hold (running cost stops; one-time cost is not refunded).
- In a response briefing, answer each proposal with `accept_group` or `decline_group` and its `group_id`.

Act in character for your persona. Respect your budget and the limits in `rules`.
All effect sizes are illustrative simulation parameters.

Reply with JSON only, no other text, in exactly this shape:

{"decisions": [{"tech": "<technology id>", "action": "<action>", "partners": [], "reason": "<at most 40 words>", "group_id": "<only in response pass>"}]}

An empty list {"decisions": []} is a valid reply.
```

- [ ] **Step 4: Implement `sciti/decide/llm.py`**

```python
"""Claude-backed agent policy with spend caps and fallback (spec §7.5, §9.2, §9.3)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from sciti.decide.interface import Brief, Reply

PROMPT_VERSION = "v1"
PROMPT_DIR = Path(__file__).with_name("prompts")


def load_system_prompt() -> str:
    return (PROMPT_DIR / f"{PROMPT_VERSION}_system.md").read_text()


def render_brief(brief: Brief) -> str:
    payload = {"agent": brief.agent, "week": brief.week, "quarter": brief.quarter, "pass": brief.pass_,
               "briefing": brief.data}
    return "Quarterly briefing:\n```json\n" + json.dumps(payload, indent=1, sort_keys=True) + "\n```"


class SpendTracker:
    def __init__(self, max_calls: int, max_usd: float, price_in: float, price_out: float):
        self.max_calls, self.max_usd = max_calls, max_usd
        self.price_in, self.price_out = price_in, price_out
        self.calls, self.usd = 0, 0.0

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return (tokens_in * self.price_in + tokens_out * self.price_out) / 1e6

    def can_call(self, est_in: int = 3000, est_out: int = 600) -> bool:
        return self.calls + 1 <= self.max_calls and self.usd + self.cost(est_in, est_out) <= self.max_usd

    def record(self, tokens_in: int, tokens_out: int) -> None:
        self.calls += 1
        self.usd += self.cost(tokens_in, tokens_out)


class LLMPolicy:
    name = "llm"

    def __init__(self, decision_cfg, fallback, client=None, sleep=time.sleep):
        import anthropic
        self._transient = (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError)
        self._api_error = anthropic.APIError
        self.cfg = decision_cfg
        self.fallback = fallback
        self.client = client if client is not None else anthropic.Anthropic()
        self.sleep = sleep
        self.system = load_system_prompt()
        self.spend = SpendTracker(decision_cfg.max_llm_calls, decision_cfg.max_spend_usd,
                                  decision_cfg.price_per_mtok_in, decision_cfg.price_per_mtok_out)
        self.failures = 0
        self.fallbacks = 0
        self.disabled_reason: str | None = None

    def _fallback(self, brief: Brief, why: str) -> Reply:
        self.fallbacks += 1
        r = self.fallback.decide(brief)
        return Reply(brief.agent, r.raw, fallback=True, error=why)

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        if self.disabled_reason is None and not self.spend.can_call(est_out=self.cfg.max_tokens):
            self.disabled_reason = f"spend cap reached after {self.spend.calls} calls (${self.spend.usd:.4f})"
        if self.disabled_reason:
            return self._fallback(brief, self.disabled_reason)
        content = render_brief(brief)
        if feedback:
            content += f"\n\nYour previous reply was invalid: {feedback}\nReply again with valid JSON only."
        start = time.monotonic()
        resp, last = None, None
        for attempt in range(3):
            try:
                resp = self.client.messages.create(model=self.cfg.model, max_tokens=self.cfg.max_tokens,
                                                   system=self.system, messages=[{"role": "user", "content": content}])
                break
            except self._transient as e:
                last = e
                self.sleep(2 ** attempt)
            except self._api_error as e:
                last = e
                break
        if resp is None:
            self.failures += 1
            if self.failures >= self.cfg.max_consecutive_failures:
                self.disabled_reason = f"{self.failures} consecutive API failures; last: {type(last).__name__}"
            return self._fallback(brief, f"API error: {type(last).__name__}")
        self.failures = 0
        tin, tout = resp.usage.input_tokens, resp.usage.output_tokens
        self.spend.record(tin, tout)
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
        return Reply(brief.agent, text, tokens_in=tin, tokens_out=tout, latency_s=round(time.monotonic() - start, 3))

    def stats(self) -> dict:
        return {"prompt_version": PROMPT_VERSION, "model": self.cfg.model, "calls": self.spend.calls,
                "usd": round(self.spend.usd, 6), "fallbacks": self.fallbacks, "disabled_reason": self.disabled_reason}
```

Note: `latency_s` differs between runs by design; it lives only in `decisions.jsonl`, which is not one of `DETERMINISTIC_FILES`.

- [ ] **Step 5: Modify `make_policy` in `sciti/runner.py`**

Add before the final `raise`:

```python
    if kind == "llm":
        from sciti.decide.llm import LLMPolicy
        return LLMPolicy(cfg.decision, fallback, client=client), fallback
```

`configs/mvp_llm.yaml` (the model id and prices are the user's choice; confirm current values before a paid run):

```yaml
# LLM agents decide quarterly. Run `sciti estimate configs/mvp_llm.yaml` first.
name: mvp_llm
seed: 1
weeks: 156
decision:
  policy: llm
  model: claude-haiku-4-5-20251001
  max_llm_calls: 1500
  max_spend_usd: 10.0
  price_per_mtok_in: 0.0    # set to the model's current input price per million tokens
  price_per_mtok_out: 0.0   # set to the model's current output price per million tokens
  visibility: partners
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_llm.py -v`
Expected: 6 passed. No network access happens (FakeClient).

- [ ] **Step 7: Commit**

```bash
git add sciti/decide/llm.py sciti/decide/prompts/v1_system.md sciti/runner.py configs/mvp_llm.yaml tests/test_llm.py
git commit -m "feat: LLM agent policy with spend cap, retries, disable-on-failure, key scrubbing

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 15: Replay policy and `sciti replay`

**Files:**
- Create: `sciti/decide/replay.py`
- Modify: `sciti/runner.py` (`make_policy`: `replay`; add `replay_run`), `sciti/cli.py` (add `replay`)
- Test: `tests/test_replay.py`

**Interfaces:**
- Consumes: `decisions.jsonl` record format (Task 12), `DETERMINISTIC_FILES`, manifest `config`.
- Produces:
  - `sciti.decide.replay.ReplayError(Exception)`; `ReplayPolicy(path: str | Path)` with `name = "replay"`, `decide(brief, feedback=None) -> Reply` returning `{"decisions": parsed}` for key `(week, pass, agent)`; raises `ReplayError` when a key is missing (the run has diverged)
  - `sciti.runner.replay_run(original: Path, out_dir: Path) -> list[str]` — loads `manifest.json` config, sets `decision.policy="replay"`, `decision.replay_from=<original>/decisions.jsonl`, runs into `out_dir`, returns the names of `DETERMINISTIC_FILES` that differ (empty list = exact replication)
  - CLI: `sciti replay RUN_DIR [--out DIR]` → prints `replication: exact` and exits 0, or lists mismatched files and exits 1

- [ ] **Step 1: Write the failing test**

`tests/test_replay.py`:

```python
import json

import pytest

from sciti.cli import main
from sciti.config import Config, DecisionCfg
from sciti.decide.interface import Brief
from sciti.decide.replay import ReplayError, ReplayPolicy
from sciti.runner import replay_run, run


def rules_run(baseline_path, tmp_path):
    c = Config(name="rp", seed=9, weeks=40, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    return run(c, run_dir=tmp_path / "orig")


def test_replay_reproduces_exactly(baseline_path, tmp_path):
    orig = rules_run(baseline_path, tmp_path)
    assert json.loads((orig / "summary.json").read_text())["adoptions"] > 0
    assert replay_run(orig, tmp_path / "again") == []


def test_replay_detects_divergence(baseline_path, tmp_path):
    orig = rules_run(baseline_path, tmp_path)
    p = ReplayPolicy(orig / "decisions.jsonl")
    with pytest.raises(ReplayError):
        p.decide(Brief("Retail_1", "Retail", 999, 77, "proposal", {}))


def test_cli_replay(baseline_path, tmp_path, capsys):
    orig = rules_run(baseline_path, tmp_path)
    assert main(["replay", str(orig), "--out", str(tmp_path / "cli")]) == 0
    assert "replication: exact" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_replay.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.decide.replay'`

- [ ] **Step 3: Implement `sciti/decide/replay.py`**

```python
"""Replays logged decisions so a run can be reproduced with no API calls (spec §9.1)."""
from __future__ import annotations

import json
from pathlib import Path

from sciti.decide.interface import Brief, Reply


class ReplayError(Exception):
    pass


class ReplayPolicy:
    name = "replay"

    def __init__(self, path: str | Path):
        self.log = {}
        for line in Path(path).read_text().splitlines():
            rec = json.loads(line)
            self.log[(rec["week"], rec["pass"], rec["agent"])] = rec["parsed"]

    def decide(self, brief: Brief, feedback: str | None = None) -> Reply:
        key = (brief.week, brief.pass_, brief.agent)
        if key not in self.log:
            raise ReplayError(f"no logged decision for {key}; the replay has diverged from the original run")
        return Reply(brief.agent, json.dumps({"decisions": self.log[key]}))
```

- [ ] **Step 4: Modify `sciti/runner.py`**

In `make_policy`, add before the final `raise`:

```python
    if kind == "replay":
        from sciti.decide.replay import ReplayPolicy
        return ReplayPolicy(cfg.decision.replay_from), fallback
```

Add at the end of the file:

```python
def replay_run(original: Path, out_dir: Path) -> list[str]:
    from sciti.config import Config
    from sciti.outputs import DETERMINISTIC_FILES
    original = Path(original)
    data = json.loads((original / "manifest.json").read_text())["config"]
    data["decision"]["policy"] = "replay"
    data["decision"]["replay_from"] = str(original / "decisions.jsonl")
    out = run(Config.model_validate(data), run_dir=Path(out_dir))
    return [f for f in DETERMINISTIC_FILES if (original / f).read_bytes() != (out / f).read_bytes()]
```

- [ ] **Step 5: Modify `sciti/cli.py`**

After the `run` subparser add:

```python
    rp = sub.add_parser("replay", help="re-run from logged decisions and compare outputs")
    rp.add_argument("run_dir")
    rp.add_argument("--out", default=None)
```

Before `return 1` add:

```python
    if args.cmd == "replay":
        from sciti.runner import replay_run
        src = Path(args.run_dir)
        out = Path(args.out) if args.out else src.with_name(src.name + "_replay")
        diffs = replay_run(src, out)
        if diffs:
            print("replication: MISMATCH in " + ", ".join(diffs))
            return 1
        print(f"replication: exact ({out})")
        return 0
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_replay.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add sciti/decide/replay.py sciti/runner.py sciti/cli.py tests/test_replay.py
git commit -m "feat: replay policy and sciti replay with exact-output comparison

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 16: Batch runs and `sciti estimate`

**Files:**
- Create: `sciti/batch.py`, `configs/classroom_shanghai_tower.yaml`
- Modify: `sciti/cli.py` (add `batch`, `estimate`)
- Test: `tests/test_batch.py`

**Interfaces:**
- Consumes: `run`, `Config`, `config_hash`, `DecisionCfg` price fields.
- Produces:
  - `sciti.batch.EST_TOKENS_IN = 3000`, `EST_TOKENS_OUT = 400`
  - `estimate(cfg) -> dict` with `rounds, calls_expected, calls_max, usd_expected, usd_max, note` (`rounds = ceil(weeks / 13)`; expected calls = `48 · rounds · 1.3`; max calls = `min(max_llm_calls, 48 · rounds · 2 · 2)` (both passes, each with one retry); usd uses the configured prices; `note` warns when prices are 0; for policies other than `llm` all counts are 0)
  - `SpendConfirmationRequired(Exception)`
  - `parse_seeds(text: str) -> list[int]` (`"1-3,7"` → `[1, 2, 3, 7]`)
  - `flatten(summary: dict) -> dict` (nested dicts become `parent_child` keys)
  - `run_batch(cfg, seeds: list[int], out_dir: Path, with_baseline=False, confirm_spend=False, client=None) -> Path` — writes each run to `out_dir/<policy>_s<seed>/` and `out_dir/results.csv` (one row per run: `seed, policy, config_hash, run_dir` + flattened summary). Raises `SpendConfirmationRequired` when policy is `llm` and `usd_max · len(seeds) > confirm_spend_threshold_usd` and not `confirm_spend`.
  - CLI: `sciti estimate CONFIG`; `sciti batch CONFIG --seeds 1-30 [--with-baseline] [--confirm-spend] [--out DIR]`

- [ ] **Step 1: Write the failing test**

`tests/test_batch.py`:

```python
import csv

import pytest

from sciti.batch import SpendConfirmationRequired, estimate, flatten, parse_seeds, run_batch
from sciti.config import Config, DecisionCfg


def test_parse_seeds():
    assert parse_seeds("1-3,7") == [1, 2, 3, 7]


def test_flatten():
    assert flatten({"a": 1, "b": {"c": 2, "d": None}}) == {"a": 1, "b_c": 2, "b_d": None}


def test_estimate_llm_and_rules():
    llm = Config(name="e", seed=1, decision=DecisionCfg(policy="llm", model="m", price_per_mtok_in=1, price_per_mtok_out=5))
    e = estimate(llm)
    assert e["rounds"] == 12 and e["calls_expected"] == round(48 * 12 * 1.3)
    assert e["usd_max"] == pytest.approx(e["calls_max"] * (3000 * 1 + 400 * 5) / 1e6)
    assert estimate(Config(name="e", seed=1))["calls_max"] == 0
    assert "price" in estimate(Config(name="e", seed=1, decision=DecisionCfg(policy="llm", model="m")))["note"]


def test_batch_writes_results_with_baseline(baseline_path, tmp_path):
    c = Config(name="b", seed=0, weeks=26, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="rules"))
    out = run_batch(c, [1, 2], tmp_path / "batch", with_baseline=True)
    rows = list(csv.DictReader(open(out / "results.csv")))
    assert [(r["policy"], r["seed"]) for r in rows] == [("rules", "1"), ("none", "1"), ("rules", "2"), ("none", "2")]
    assert "costs_shipping" in rows[0] and "bullwhip_DC" in rows[0]


def test_batch_llm_requires_spend_confirmation(baseline_path, tmp_path):
    c = Config(name="b", seed=0, weeks=26, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=DecisionCfg(policy="llm", model="m", price_per_mtok_in=100, price_per_mtok_out=100,
                                    confirm_spend_threshold_usd=0.01))
    with pytest.raises(SpendConfirmationRequired):
        run_batch(c, [1], tmp_path / "batch")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_batch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sciti.batch'`

- [ ] **Step 3: Implement `sciti/batch.py`**

```python
"""Many runs → one tidy results table; spend estimate (spec §4.1, §8, §9.3)."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from sciti.config import config_hash
from sciti.runner import run

EST_TOKENS_IN = 3000
EST_TOKENS_OUT = 400
AGENTS = 48


class SpendConfirmationRequired(Exception):
    pass


def estimate(cfg) -> dict:
    rounds = math.ceil(cfg.weeks / 13)
    D = cfg.decision
    if D.policy != "llm":
        return {"rounds": rounds, "calls_expected": 0, "calls_max": 0, "usd_expected": 0.0, "usd_max": 0.0,
                "note": f"policy {D.policy} makes no API calls"}
    per_call = (EST_TOKENS_IN * D.price_per_mtok_in + EST_TOKENS_OUT * D.price_per_mtok_out) / 1e6
    expected = round(AGENTS * rounds * 1.3)
    worst = min(D.max_llm_calls, AGENTS * rounds * 2 * 2)
    note = ("set decision.price_per_mtok_in/out to the model's current prices to estimate spend"
            if D.price_per_mtok_in == 0 and D.price_per_mtok_out == 0 else
            f"spend is also capped at ${D.max_spend_usd} per run")
    return {"rounds": rounds, "calls_expected": expected, "calls_max": worst,
            "usd_expected": round(expected * per_call, 4), "usd_max": round(worst * per_call, 4), "note": note}


def parse_seeds(text: str) -> list[int]:
    seeds = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))
    return seeds


def flatten(summary: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in summary.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "_"))
        else:
            out[key] = v
    return out


def run_batch(cfg, seeds, out_dir: Path, with_baseline=False, confirm_spend=False, client=None) -> Path:
    out_dir = Path(out_dir)
    if cfg.decision.policy == "llm":
        total = estimate(cfg)["usd_max"] * len(seeds)
        if total > cfg.decision.confirm_spend_threshold_usd and not confirm_spend:
            raise SpendConfirmationRequired(
                f"worst-case spend ${total:.2f} exceeds ${cfg.decision.confirm_spend_threshold_usd}; pass --confirm-spend")
    rows = []
    for seed in seeds:
        variants = [cfg.model_copy(update={"seed": seed}, deep=True)]
        if with_baseline and cfg.decision.policy != "none":
            base = cfg.model_copy(update={"seed": seed}, deep=True)
            base.decision.policy = "none"
            variants.append(base)
        for c in variants:
            d = run(c, run_dir=out_dir / f"{c.decision.policy}_s{seed}", client=client)
            summary = json.loads((d / "summary.json").read_text())
            rows.append({"seed": seed, "policy": c.decision.policy, "config_hash": config_hash(c),
                         "run_dir": str(d), **flatten(summary)})
    columns = list(dict.fromkeys(k for r in rows for k in r))
    with open(out_dir / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    return out_dir
```

- [ ] **Step 4: Modify `sciti/cli.py`**

Add subparsers after `replay`:

```python
    es = sub.add_parser("estimate", help="estimated LLM calls and spend; makes no calls")
    es.add_argument("config")
    bt = sub.add_parser("batch", help="run many seeds and write results.csv")
    bt.add_argument("config")
    bt.add_argument("--seeds", required=True)
    bt.add_argument("--with-baseline", action="store_true")
    bt.add_argument("--confirm-spend", action="store_true")
    bt.add_argument("--out", default=None)
```

Add handlers before `return 1`:

```python
    if args.cmd == "estimate":
        import json as _json
        from sciti.batch import estimate
        from sciti.config import load_config
        print(_json.dumps(estimate(load_config(args.config)), indent=1))
        return 0
    if args.cmd == "batch":
        from sciti.batch import SpendConfirmationRequired, parse_seeds, run_batch
        from sciti.config import load_config
        cfg = load_config(args.config)
        out = Path(args.out) if args.out else Path(cfg.output_dir) / f"batch_{cfg.name}"
        try:
            print(run_batch(cfg, parse_seeds(args.seeds), out, args.with_baseline, args.confirm_spend) / "results.csv")
        except SpendConfirmationRequired as e:
            print(e)
            return 2
        return 0
```

`configs/classroom_shanghai_tower.yaml`:

```yaml
# Classroom preset: the Shanghai chain adopts a control tower in week 1; glass supply is disrupted in
# week 20; other firms decide with the payback rule. Compare with the same seed under configs/baseline.yaml.
name: classroom_shanghai_tower
seed: 11
weeks: 104
decision:
  policy: rules
forced_adoptions:
  - week: 1
    tech: control_tower
    members: [DC_Shanghai, Retail_5, Retail_6, Retail_7, Retail_8]
disruptions:
  - target: CM_4
    start_week: 20
    weeks: 6
    capacity_mult: 0.25
    extra_lead_days: 7
```

- [ ] **Step 5: Run tests and the full suite**

Run: `.venv/bin/pytest -v`
Expected: all tests pass.

Then on real data (no API calls):

```bash
.venv/bin/sciti estimate configs/mvp_llm.yaml
.venv/bin/sciti batch configs/rules.yaml --seeds 1-3 --with-baseline
```

Expected: estimate prints JSON with a price note; batch prints a `results.csv` path with 6 rows.

- [ ] **Step 6: Commit**

```bash
git add sciti/batch.py sciti/cli.py configs/classroom_shanghai_tower.yaml tests/test_batch.py
git commit -m "feat: batch runs with paired baselines, spend estimate, classroom preset

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

**Paid LLM run (not part of automated steps):** before running `sciti run configs/mvp_llm.yaml`, stop and ask the user to (1) confirm the model id and current prices in the config, (2) confirm `ANTHROPIC_API_KEY` is set in their shell, and (3) approve the estimated spend. Then run it, then `sciti replay` on the result and report `replication: exact`.
