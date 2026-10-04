"""Model providers. All speak the same interface: available() and generate(system, user, task, key) -> str.

- StubProvider: deterministic replay of canned outputs (no network). Used for tests/eval until the key arrives.
- OpenAICompatProvider: any OpenAI-style /chat/completions endpoint (CSCS-hosted Apertus, or self-hosted vLLM /
  Ollama / llama.cpp server). Python stdlib only (urllib), so the image has no third-party dependencies.
- RecordingProvider: wraps a real provider and saves its outputs (LLM_MODE=record) to a SEPARATE replay file.
- ReplayProvider: replays that file offline (LLM_MODE=replay), e.g. for judges without a key. The STUB never loads it."""
from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

from .gateway import ProviderError


def norm_key(q: str) -> str:
    q = unicodedata.normalize("NFC", q).casefold().strip()
    q = re.sub(r"\s+", " ", q)
    return q.strip(" ¿?¡!.")


class StubProvider:
    name = "stub-replay"

    def __init__(self, *paths: str | Path):
        self.canned: dict[str, dict[str, object]] = {}
        for p in paths:
            p = Path(p)
            if not p.exists():
                continue
            d = json.loads(p.read_text())
            for task, items in d.items():
                if task.startswith("_"):
                    continue
                for k, v in items.items():
                    self.canned.setdefault(task, {})[norm_key(k)] = v

    def available(self) -> bool:
        return True

    def generate(self, *, system: str, user: str, task: str, key: str) -> str:
        v = self.canned.get(task, {}).get(norm_key(key))
        if v is None:
            raise ProviderError(f"no canned output for {task}:{key!r}", code="stub_miss")
        if isinstance(v, dict) and "__raise__" in v:          # scripted failure for tests
            raise ProviderError(v["__raise__"], code=v["__raise__"], status=v.get("status"))
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


class ReplayProvider(StubProvider):
    """Replays REAL model outputs recorded with LLM_MODE=record (separate file; the STUB never loads it). Offline."""
    name = "replay"

    def __init__(self, path: str | Path):
        super().__init__(path)
        p = Path(path)
        d = json.loads(p.read_text()) if p.exists() else {}
        self.meta = {k: v for k, v in d.items() if k.startswith("_")}
        self.model = self.meta.get("_model")


class OpenAICompatProvider:
    """Retries (opt-in, `retries` > 0) only on HTTP 429 / 5xx, with exponential backoff (honours a numeric
    Retry-After). Error messages never include the URL, headers or key. Token usage (if the server reports it) is
    accumulated in `usage` so the eval can report it."""
    RETRY_STATUS = {429, 500, 502, 503, 504}

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 30.0, json_mode: bool = False,
                 max_tokens: int = 400, retries: int = 0, backoff_s: float = 2.0, sleep=time.sleep):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key, self.model, self.timeout_s = api_key or "", model or "", timeout_s
        self.json_mode, self.max_tokens = json_mode, max_tokens
        self.retries, self.backoff_s, self._sleep = max(0, int(retries)), backoff_s, sleep
        self.name = f"openai-compat:{self.model}"
        self._lock = threading.Lock()
        self.usage = {"calls": 0, "attempts": 0, "retries": 0, "prompt_tokens": 0, "completion_tokens": 0,
                      "total_tokens": 0, "errors": {}}

    def max_wall_s(self) -> float:
        """Worst-case wall time of one generate() call incl. retries (the gateway timeout must cover it)."""
        return self.timeout_s * (self.retries + 1) + sum(min(30.0, self.backoff_s * 2 ** i) for i in range(self.retries))

    def available(self) -> bool:
        return bool(self.base_url and self.model)

    def request_body(self, system: str, user: str) -> dict:
        body = {"model": self.model, "temperature": 0, "max_tokens": self.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        return body

    def _count(self, field: str, n: int = 1, err: str | None = None):
        with self._lock:
            if err:
                self.usage["errors"][err] = self.usage["errors"].get(err, 0) + 1
            else:
                self.usage[field] += n

    def _once(self, url: str, data: bytes, headers: dict) -> dict:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        self._count("attempts")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            ra = e.headers.get("Retry-After") if e.headers else None
            err = ProviderError(f"HTTP {e.code}", code="http_error", status=e.code)
            err.retry_after = float(ra) if ra and ra.strip().isdigit() else None
            raise err from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"network: {type(e).__name__}", code="network_error") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ProviderError("unexpected response shape", code="bad_response") from None

    def generate(self, *, system: str, user: str, task: str, key: str) -> str:
        url = self.base_url + "/chat/completions"
        data = json.dumps(self.request_body(system, user)).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "apertus-qa/0.1 (Vento Labs)"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        self._count("calls")
        for attempt in range(self.retries + 1):
            try:
                doc = self._once(url, data, headers)
                break
            except ProviderError as e:
                retryable = e.status in self.RETRY_STATUS   # not DNS/connection errors: air-gapped runs fall back at once
                self._count("", err=f"{e.status or e.code}")
                if not retryable or attempt >= self.retries:
                    raise
                self._count("retries")
                wait = getattr(e, "retry_after", None) or self.backoff_s * 2 ** attempt
                self._sleep(min(30.0, wait))
        u = doc.get("usage") if isinstance(doc, dict) else None
        if isinstance(u, dict):
            for f in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if isinstance(u.get(f), int):
                    self._count(f, u[f])
        try:
            return doc["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError("unexpected response shape", code="bad_response") from None


class RecordingProvider:
    def __init__(self, inner, path: str | Path):
        self.inner, self.path = inner, Path(path)
        self.name = f"record({inner.name})"
        self._lock = threading.Lock()

    def available(self) -> bool:
        return self.inner.available()

    def max_wall_s(self) -> float:
        return self.inner.max_wall_s() if hasattr(self.inner, "max_wall_s") else 30.0

    @property
    def usage(self):
        return getattr(self.inner, "usage", None)

    def generate(self, *, system: str, user: str, task: str, key: str) -> str:
        out = self.inner.generate(system=system, user=user, task=task, key=key)
        with self._lock:   # only model ids and raw model text are stored: never the endpoint URL, headers or key
            d = json.loads(self.path.read_text()) if self.path.exists() else {
                "_about": "REAL model outputs recorded with LLM_MODE=record; replayed offline with LLM_MODE=replay"}
            d["_model"] = getattr(self.inner, "model", None)
            d["_recorded_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            d.setdefault(task, {})[key] = out
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        return out
