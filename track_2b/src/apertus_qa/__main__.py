"""CLI:  python -m apertus_qa ask "pregunta"  |  serve [--port 8080]  |  catalog"""
from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="apertus_qa", description="Preguntas sobre estadísticas oficiales argentinas")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask")
    a.add_argument("question", nargs="+")
    a.add_argument("--json", action="store_true")
    s = sub.add_parser("serve")
    s.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    s.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    sub.add_parser("catalog")
    args = ap.parse_args(argv)
    from .pipeline import QA
    if args.cmd == "serve":
        from .server import serve
        serve(args.host, args.port)
        return 0
    qa = QA.from_env()
    if args.cmd == "catalog":
        for e in qa.catalog.compact():
            print(f"{e['id']:<45} {e['titulo']}  [{e.get('desde', e.get('periodo'))}–{e.get('hasta', '')}]")
        return 0
    out = qa.answer(" ".join(args.question))
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(out["answer"])
        if out["citation_text"]:
            print(out["citation_text"])
        r, p = out["trace"].get("router", {}), out["trace"].get("phrase") or {}
        print(f"[modelo: {qa.mode} · router: {r.get('mode')} · redacción: {p.get('mode', '-')} · snapshot {out['snapshot']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
