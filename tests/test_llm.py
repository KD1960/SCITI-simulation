import json
from types import SimpleNamespace

import anthropic
import httpx2 as httpx  # installed anthropic 1.5.0 depends on httpx2, not httpx (see task-14-report.md)
import numpy as np
import pytest

from sciti.config import Config, DecisionCfg, load_config
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


class FakeStatusClient:
    """Raises a queued list of exceptions (e.g. SDK status errors) before succeeding."""

    def __init__(self, errors):
        self.errors, self.calls = list(errors), []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if self.errors:
            raise self.errors.pop(0)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"decisions": []}')],
                               usage=SimpleNamespace(input_tokens=1000, output_tokens=100))


def _status_error(cls, status_code):
    req = httpx.Request("POST", "https://example.invalid")
    return cls(cls.__name__, response=httpx.Response(status_code, request=req), body=None)


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


def test_zero_price_refuses_construction():
    zero_cfg = DecisionCfg(policy="llm", model="test-model", price_per_mtok_in=0.0, price_per_mtok_out=0.0)
    with pytest.raises(ValueError, match="price"):
        LLMPolicy(zero_cfg, RulesPolicy(np.random.default_rng(0)), client=FakeClient())


def test_mvp_llm_config_still_loads_with_zero_prices():
    c = load_config("configs/mvp_llm.yaml")
    assert c.decision.price_per_mtok_in == 0.0 and c.decision.price_per_mtok_out == 0.0


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        LLMPolicy(cfg(), RulesPolicy(np.random.default_rng(0)))


def test_missing_api_key_run_creates_no_run_dir(baseline_path, tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = Config(name="llm", seed=1, weeks=14, baseline_path=str(baseline_path), output_dir=str(tmp_path),
               decision=cfg())
    run_dir = tmp_path / "r"
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        run(c, run_dir=run_dir)
    assert not run_dir.exists()


def test_real_client_gets_timeout_and_no_sdk_retries(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    captured = {}

    class StubAnthropic:
        def __init__(self, **kw):
            captured.update(kw)

    monkeypatch.setattr(anthropic, "Anthropic", StubAnthropic)
    LLMPolicy(cfg(request_timeout_s=12.5), RulesPolicy(np.random.default_rng(0)))
    assert captured["timeout"] == 12.5
    assert captured["max_retries"] == 0


def test_overloaded_529_is_transient_then_succeeds():
    c = FakeStatusClient([_status_error(anthropic.OverloadedError, 529), _status_error(anthropic.OverloadedError, 529)])
    slept = []
    p = LLMPolicy(cfg(), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: slept.append(s))
    r = p.decide(b())
    assert r.fallback is False
    assert len(c.calls) == 3 and slept


def test_authentication_error_disables_immediately_without_retrying():
    c = FakeStatusClient([_status_error(anthropic.AuthenticationError, 401)])
    p = LLMPolicy(cfg(), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: None)
    r1 = p.decide(b())
    assert r1.fallback is True
    assert "authentication" in p.stats()["disabled_reason"]
    calls_after_first = len(c.calls)
    r2 = p.decide(b())
    assert r2.fallback is True
    assert len(c.calls) == calls_after_first


def test_reply_budget_leaves_room_for_thinking_and_json():
    # E5: max_tokens 600 with thinking on truncated replies, forcing retries and rule fallbacks.
    assert DecisionCfg(policy="llm", model="m", price_per_mtok_in=1, price_per_mtok_out=5).max_tokens == 2000


def test_request_asks_for_the_reply_schema():
    from sciti.decide.llm import REPLY_SCHEMA
    c = FakeClient()
    p = LLMPolicy(cfg(), RulesPolicy(np.random.default_rng(0)), client=c, sleep=lambda s: None)
    p.decide(b())
    fmt = c.calls[0]["output_config"]["format"]
    assert fmt["type"] == "json_schema" and fmt["schema"] == REPLY_SCHEMA
    decision = REPLY_SCHEMA["properties"]["decisions"]["items"]
    assert REPLY_SCHEMA["required"] == ["decisions"]
    assert set(decision["required"]) == {"tech", "action", "partners", "reason"}
    assert "group_id" in decision["properties"] and decision["additionalProperties"] is False
