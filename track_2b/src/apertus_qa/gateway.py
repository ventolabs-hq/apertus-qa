"""LLM gateway: never raises to the caller; any failure returns the caller's deterministic fallback.

Adapted (ported JS -> Python) from this team's earlier `llm-gateway` component (RC1, written 2026-10-02 for another
prototype): same contract — status(), budgets per day and per minute, circuit breaker, timeout, JSON parse,
schema + semantic validation, fallback with a machine-readable reason. Disclosed in docs/DISCLOSURE.md."""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable


class ProviderError(Exception):
    def __init__(self, msg: str, code: str = "provider_error", status: int | None = None):
        super().__init__(msg)
        self.code, self.status = code, status


@dataclass
class GatewayResult:
    mode: str                    # "llm" | "fallback"
    data: Any
    reason: str | None = None
    raw: str | None = None
    latency_ms: int = 0


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.S)


def parse_json(text: str) -> Any:
    """Strict JSON, tolerating a single markdown fence or leading prose before the first '{'."""
    t = _FENCE.sub("", text.strip())
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            return json.loads(t[i:j + 1])
        raise


@dataclass
class Gateway:
    provider: Any = None
    daily_budget: int = 2000
    rpm_budget: int = 30
    timeout_s: float = 30.0
    breaker_failures: int = 3
    breaker_window_s: float = 600.0
    breaker_cooldown_s: float = 300.0
    now: Callable[[], float] = time.time
    log: list = field(default_factory=list)

    def __post_init__(self):
        self._day = self._today()
        self._used = 0
        self._minute: list[float] = []
        self._failures: list[float] = []
        self._open_until = 0.0
        self._pool = cf.ThreadPoolExecutor(max_workers=2)

    def _today(self):
        return time.strftime("%Y-%m-%d", time.gmtime(self.now()))

    def status(self) -> dict:
        if self._today() != self._day:
            self._day, self._used = self._today(), 0
        base = {"used_today": self._used, "daily_budget": self.daily_budget}
        if self.provider is None:
            return {"available": False, "reason": "no_provider", **base}
        if not self.provider.available():
            return {"available": False, "reason": "no_key", **base}
        if self._open_until > self.now():
            return {"available": False, "reason": "breaker_open", **base}
        if self._used >= self.daily_budget:
            return {"available": False, "reason": "budget_exhausted", **base}
        return {"available": True, **base}

    def _fail(self):
        t = self.now()
        self._failures = [x for x in self._failures if t - x < self.breaker_window_s] + [t]
        if len(self._failures) >= self.breaker_failures:
            self._open_until, self._failures = t + self.breaker_cooldown_s, []

    def generate_json(self, *, task: str, system: str, user: str, key: str, fallback: Callable[[], Any],
                      validate: Callable[[Any], str | None] | None = None) -> GatewayResult:
        t0 = self.now()

        def done(reason: str, raw: str | None = None) -> GatewayResult:
            try:
                data = fallback()
            except Exception as e:  # the fallback itself must never take the request down
                data, reason = None, f"{reason}+fallback_error:{type(e).__name__}"
            res = GatewayResult("fallback", data, reason, raw, int((self.now() - t0) * 1000))
            self.log.append({"task": task, "mode": "fallback", "reason": reason})
            return res

        st = self.status()
        if not st["available"]:
            return done(st["reason"])
        t = self.now()
        self._minute = [x for x in self._minute if t - x < 60]
        if len(self._minute) >= self.rpm_budget:
            return done("rpm_budget")
        self._minute.append(t)
        self._used += 1
        fut = self._pool.submit(self.provider.generate, system=system, user=user, task=task, key=key)
        try:
            text = fut.result(timeout=self.timeout_s)
        except cf.TimeoutError:
            self._fail()
            return done("timeout")
        except ProviderError as e:
            self._fail()
            return done("rate_limited" if e.status == 429 else e.code)
        except Exception as e:  # noqa: BLE001 - never raise to caller
            self._fail()
            return done(f"provider_error:{type(e).__name__}")
        try:
            data = parse_json(text) if isinstance(text, str) else text
        except Exception:
            return done("bad_json", text if isinstance(text, str) else None)
        if validate:
            try:
                err = validate(data)
            except Exception as e:  # validator bug -> treat as invalid output
                err = f"validator_error:{type(e).__name__}"
            if err:   # invalid content is logged and falls back, but does not trip the breaker (transport failures do)
                return done(f"invalid:{err}", text if isinstance(text, str) else None)
        self.log.append({"task": task, "mode": "llm"})
        return GatewayResult("llm", data, None, text if isinstance(text, str) else None, int((self.now() - t0) * 1000))
