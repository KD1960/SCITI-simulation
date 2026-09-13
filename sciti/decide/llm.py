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
