import json
from types import SimpleNamespace

import anthropic
import httpx2 as httpx  # installed anthropic 1.5.0 depends on httpx2, not httpx (see task-14-report.md)
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
