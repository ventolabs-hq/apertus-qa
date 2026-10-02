"""Model providers. All speak the same interface: available() and generate(system, user, task, key) -> str.

- StubProvider: deterministic replay of canned outputs (no network). Used for tests/eval until the key arrives.
- OpenAICompatProvider: any OpenAI-style /chat/completions endpoint (CSCS-hosted Apertus, or self-hosted vLLM /
  Ollama / llama.cpp server). Python stdlib only (urllib), so the image has no third-party dependencies.
- RecordingProvider: wraps a real provider and saves its outputs in the stub format, so a real Apertus run can be
  replayed offline (e.g. by judges without a key)."""
from __future__ import annotations

import json
import re
import threading
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


class OpenAICompatProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 30.0, json_mode: bool = False,
                 max_tokens: int = 400):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key, self.model, self.timeout_s = api_key or "", model or "", timeout_s
        self.json_mode, self.max_tokens = json_mode, max_tokens
        self.name = f"openai-compat:{self.model}"

    def available(self) -> bool:
        return bool(self.base_url and self.model)

    def request_body(self, system: str, user: str) -> dict:
        body = {"model": self.model, "temperature": 0, "max_tokens": self.max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        return body

    def generate(self, *, system: str, user: str, task: str, key: str) -> str:
        url = self.base_url + "/chat/completions"
        data = json.dumps(self.request_body(system, user)).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                doc = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise ProviderError(f"HTTP {e.code}", code="http_error", status=e.code) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ProviderError(f"network: {type(e).__name__}", code="network_error") from None
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

    def generate(self, *, system: str, user: str, task: str, key: str) -> str:
        out = self.inner.generate(system=system, user=user, task=task, key=key)
        with self._lock:
            d = json.loads(self.path.read_text()) if self.path.exists() else {"_about": "recorded real model outputs"}
            d.setdefault(task, {})[key] = out
            self.path.write_text(json.dumps(d, ensure_ascii=False, indent=1))
        return out
