"""Minimal HTTP server (stdlib only): serves the Spanish UI and a JSON API. No external assets, no CDN."""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .pipeline import QA

WEB = Path(__file__).resolve().parent / "web"


def make_handler(qa: QA):
    lock = threading.Lock()

    class H(BaseHTTPRequestHandler):
        server_version = "apertus-qa"

        def log_message(self, fmt, *args):  # quiet; no question logging by default (privacy)
            if os.environ.get("QA_ACCESS_LOG") == "1":
                super().log_message(fmt, *args)

        def _send(self, code, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
            if self.path == "/health":
                st = qa.gateway.status()
                return self._json(200, {"ok": True, "model_mode": qa.mode, "model": os.environ.get("LLM_NAME") if qa.mode in ("real", "record") else None,
                                        "model_available": st["available"], "model_status": st.get("reason"),
                                        "snapshot": qa.catalog.built_at, "entries": len(qa.catalog.doc["entries"])})
            if self.path == "/api/catalog":
                return self._json(200, {"snapshot": qa.catalog.built_at, "attribution": qa.catalog.doc["attribution"],
                                        "entries": qa.catalog.compact()})
            self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/ask":
                return self._json(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > 4096:
                return self._json(413, {"error": "too large"})
            try:
                q = json.loads(self.rfile.read(n) or b"{}").get("q", "")
            except (json.JSONDecodeError, AttributeError):
                return self._json(400, {"error": "bad json"})
            with lock:
                out = qa.answer(str(q))
            self._json(200, out)

    return H


def serve(host: str = "0.0.0.0", port: int = 8080, qa: QA | None = None):
    qa = qa or QA.from_env()
    httpd = ThreadingHTTPServer((host, port), make_handler(qa))
    print(f"apertus-qa: http://{host}:{port}  model_mode={qa.mode}  snapshot={qa.catalog.built_at}", flush=True)
    httpd.serve_forever()
