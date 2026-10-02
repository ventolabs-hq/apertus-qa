"""Score grounded answers on eval/questions.jsonl.

Usage: python3 -m eval.run_eval [--mode stub|off|real|record] [--out reports/]
Metrics per question: decision (answer vs refuse) correct; every expected value matched by the pipeline figure in the
same slot (relative tol); citations include the expected series id + period; grounding (every number in the answer text
comes from a computed figure); plus mode breakdown (model vs fallback). Labels the run STUB when mode=stub."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from apertus_qa.pipeline import QA  # noqa: E402
from apertus_qa.validate import grounded  # noqa: E402


def close(a, b, tol):
    return abs(a - b) <= tol * max(1.0, abs(b))


def score_one(item, out):
    ex = item["expect"]
    r = {"id": item["id"], "q": item["q"], "answer": out["answer"], "refused": out["refused"], "reason": out["reason"],
         "router": out["trace"].get("router", {}).get("mode"), "router_reason": out["trace"].get("router", {}).get("reason"),
         "phrase": (out["trace"].get("phrase") or {}).get("mode"), "phrase_reason": (out["trace"].get("phrase") or {}).get("reason")}
    if ex["refuse"]:
        r["decision_ok"] = out["refused"] and (not ex["reasons"] or out["reason"] in ex["reasons"])
        r["values_ok"] = r["citation_ok"] = None
        r["grounded"] = grounded(out["answer"], out.get("slots") or {})
        r["ok"] = r["decision_ok"]
        return r
    r["decision_ok"] = not out["refused"]
    figs = {f["slot"]: f for f in out["figures"]}
    vals = []
    for v in ex["values"]:
        f = figs.get(v["slot"])
        vals.append(bool(f) and close(f["value"], v["value"], v["tol"]))
    r["values_ok"] = r["decision_ok"] and all(vals)
    cited = {c["series_id"] for c in out["citations"]}
    r["citation_ok"] = r["decision_ok"] and set(ex["series"]) <= cited and all(c.get("period") for c in out["citations"])
    r["grounded"] = grounded(out["answer"], out.get("slots") or {})
    oc = item.get("official_check")
    if oc and r["values_ok"]:
        slot = ex["values"][0]["slot"]
        pct = figs[slot]["value"] * 100
        r["official_ok"] = abs(pct - oc["value_pct"]) <= oc["tol_pp"]
    r["ok"] = bool(r["decision_ok"] and r["values_ok"] and r["citation_ok"] and r["grounded"])
    return r



def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default=os.environ.get("LLM_MODE") or "stub")
    ap.add_argument("--out", default=str(HERE.parents[1] / "docs" / "eval"))
    ap.add_argument("--set", default="main", choices=["main", "heldout"])
    a = ap.parse_args(argv)
    qa = QA.from_env(a.mode)
    items = [json.loads(l) for l in (HERE / ("questions.jsonl" if a.set == "main" else "questions_heldout.jsonl")).read_text().splitlines() if l.strip()]
    t0 = time.time()
    rows = [score_one(it, qa.answer(it["q"])) for it in items]
    n = len(rows)
    ans = [r for r in rows if r["values_ok"] is not None]
    ref = [r for r in rows if r["values_ok"] is None]
    label = {"stub": "STUB (canned replay, not real Apertus)", "off": "NO-MODEL baseline (rules + templates)",
             "real": "REAL model", "record": "REAL model (recording)"}.get(qa.mode, qa.mode)
    summ = {
        "label": label, "mode": qa.mode, "model": os.environ.get("LLM_NAME") if qa.mode in ("real", "record") else None,
        "questions": n, "answerable": len(ans), "must_refuse": len(ref),
        "overall_ok": sum(r["ok"] for r in rows),
        "answer_correct": sum(bool(r["values_ok"]) for r in ans),
        "citation_ok": sum(bool(r["citation_ok"]) for r in ans),
        "refusal_correct": sum(bool(r["decision_ok"]) for r in ref),
        "false_refusals": sum(r["refused"] for r in ans),
        "grounding_violations": sum(not r["grounded"] for r in rows),
        "official_checks_ok": f"{sum(1 for r in rows if r.get('official_ok'))}/{sum(1 for r in rows if 'official_ok' in r)}",
        "router_model": sum(r["router"] == "llm" for r in rows), "router_fallback": sum(r["router"] == "fallback" for r in rows),
        "phrase_model": sum(r["phrase"] == "llm" for r in rows), "phrase_fallback": sum(r["phrase"] == "fallback" for r in rows),
        "seconds": round(time.time() - t0, 2), "snapshot": qa.catalog.built_at,
    }
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"eval_{a.set}_{qa.mode}.json").write_text(json.dumps({"summary": summ, "rows": rows}, ensure_ascii=False, indent=1))
    summ["set"] = a.set
    lines = [f"# Eval ({a.set}) — {label}", "", "| métrica | valor |", "|---|---|"] + [f"| {k} | {v} |" for k, v in summ.items()]
    lines += ["", "| id | ok | decisión | valores | cita | router | redacción | respuesta |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {'✔' if r['ok'] else '✘'} | {r['decision_ok']} | {r['values_ok']} | {r['citation_ok']} | "
                     f"{r['router']}{' (' + str(r['router_reason']) + ')' if r['router_reason'] else ''} | "
                     f"{r['phrase']}{' (' + str(r['phrase_reason']) + ')' if r['phrase_reason'] else ''} | {r['answer'][:140].replace('|', '/')} |")
    (out / f"eval_{a.set}_{qa.mode}.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return 0 if summ["grounding_violations"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
