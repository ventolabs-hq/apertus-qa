"""Question -> grounded answer.

1. Router (Apertus, P1) proposes a plan {series, operation, period}; validated against the catalog. Fallback: rules.
2. The deterministic data layer computes every figure (ops.run).
3. Phrasing (Apertus, P2) writes the sentence with placeholders only; validated; fallback: template.
4. Code renders the placeholders, re-checks grounding and appends the citations."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import fmt, ops, prompts, rules
from .catalog import Catalog
from .gateway import Gateway
from .providers import OpenAICompatProvider, RecordingProvider, StubProvider
from .validate import grounded, render, validate_phrase, validate_plan

HERE = Path(__file__).resolve().parent
STUB_FILES = [HERE / "stub" / "canned.json", HERE / "stub" / "recorded.json"]

REQUIRED = {"valor": ["valor"], "ultimo": ["valor"], "variacion": ["variacion"], "variacion_mensual": ["variacion"],
            "interanual": ["variacion"], "maximo": ["valor", "periodo"], "minimo": ["valor", "periodo"],
            "total_anual": ["valor"], "ranking": ["serie_1", "valor_1"], "ajuste": ["valor"],
            "comparar": ["valor_1", "valor_2"], "tabla_top": ["clave_1", "valor_1"], "tabla_valor": ["valor"]}

TEMPLATES = {
    "valor": "{serie}, {periodo}: {valor}.",
    "ultimo": "Último dato disponible de {serie} ({periodo}): {valor}.",
    "variacion": "{serie}: variación de {variacion} entre {desde} ({desde_valor}) y {hasta} ({hasta_valor}).",
    "variacion_mensual": "{serie}: variación mensual de {variacion} en {hasta} (respecto de {desde}).",
    "interanual": "{serie}: variación interanual de {variacion} en {hasta} (respecto de {desde}).",
    "maximo": "{serie}: el valor más alto entre {rango_desde} y {rango_hasta} fue {valor}, en {periodo}.",
    "minimo": "{serie}: el valor más bajo entre {rango_desde} y {rango_hasta} fue {valor}, en {periodo}.",
    "total_anual": "{serie}, total de {periodo}: {valor}.",
    "ajuste": "{monto} de {desde} equivalen a {valor} de {hasta}, según el IPC (inflación acumulada: {variacion}).",
    "comparar": "{periodo}: {serie_1} {valor_1}; {serie_2} {valor_2}. Mayor: {mayor}.",
    "tabla_valor": "{serie}: {clave}, {valor} ({periodo}).",
}

REFUSALS = {
    "fuera_de_alcance": "No puedo responder eso con los datos de este sistema. Cubre: precios (IPC), salarios registrados, "
                        "población, nacimientos, tipo de cambio anual, exportaciones, turismo emisivo, energía, petróleo, "
                        "subte, vuelos y siniestros viales.",
    "pronostico": "No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local.",
    "consejo": "No doy consejos de inversión, impuestos ni compras. Puedo informar datos oficiales publicados.",
    "otro": "No puedo procesar esa pregunta. Probá preguntar por un dato oficial concreto.",
    "no_entendida": "No entendí qué dato oficial buscás. Probá con una serie y un período, por ejemplo: "
                    "«¿Cuál fue la inflación mensual de agosto de 2026?».",
}


def _template(op: str, slots: dict) -> str:
    if op == "ranking":
        n = sum(1 for k in slots if k.startswith("serie_"))
        return "Ranking " + "{periodo}: " + "; ".join(f"{{serie_{i}}}: {{valor_{i}}}" for i in range(1, n + 1)) + "."
    if op == "tabla_top":
        n = sum(1 for k in slots if k.startswith("clave_"))
        return "{serie}: " + "; ".join(f"{{clave_{i}}} {{valor_{i}}}" for i in range(1, n + 1)) + "."
    return TEMPLATES[op]


def _hints(res: ops.Result) -> dict:
    h = {}
    f = {x["slot"]: x["value"] for x in res.figures}
    if "variacion" in f:
        h["direccion"] = "subió" if f["variacion"] > 0 else "bajó" if f["variacion"] < 0 else "sin cambios"
    if res.op == "comparar":
        h["mayor"] = "serie_1" if f["valor_1"] > f["valor_2"] else "serie_2" if f["valor_2"] > f["valor_1"] else "iguales"
    return h


def make_provider(mode: str | None = None):
    mode = (mode or os.environ.get("LLM_MODE") or "").lower()
    real = OpenAICompatProvider(os.environ.get("LLM_BASE_URL", ""), os.environ.get("LLM_API_KEY", ""),
                                os.environ.get("LLM_NAME", ""), float(os.environ.get("LLM_TIMEOUT_S") or 30),
                                (os.environ.get("LLM_JSON_MODE") or "0") == "1")
    if not mode:
        mode = "real" if real.available() else "stub"
    if mode == "off":
        return None, "off"
    if mode == "stub":
        return StubProvider(*STUB_FILES), "stub"
    if mode == "record":
        return RecordingProvider(real, HERE / "stub" / "recorded.json"), "record"
    return real, "real"


@dataclass
class QA:
    catalog: Catalog = field(default_factory=Catalog)
    gateway: Gateway | None = None
    mode: str = "stub"

    @classmethod
    def from_env(cls, mode: str | None = None) -> "QA":
        provider, m = make_provider(mode)
        cat = Catalog()
        rpm = int(os.environ.get("LLM_RPM") or (100000 if m in ("stub", "off") else 60))
        daily = int(os.environ.get("LLM_DAILY_BUDGET") or (10**9 if m in ("stub", "off") else 5000))
        return cls(cat, Gateway(provider=provider, timeout_s=float(os.environ.get("LLM_TIMEOUT_S") or 30),
                                rpm_budget=rpm, daily_budget=daily), m)

    def answer(self, question: str) -> dict:
        t0 = time.time()
        q = " ".join(str(question or "").split())[:300]
        cat = self.catalog
        trace: dict = {"model_mode": self.mode}
        if len(q) < 3:
            return self._refusal(q, "no_entendida", trace, t0)
        rp = self.gateway.generate_json(
            task="router", key=q, system=prompts.router_system(cat.compact()), user=prompts.router_user(q),
            fallback=lambda: rules.plan(q, cat), validate=lambda d: validate_plan(d, cat, q))
        plan = rp.data
        trace["router"] = {"mode": rp.mode, "reason": rp.reason, "plan": plan}
        if rp.mode == "fallback" and (plan is None or validate_plan(plan, cat, q)):
            trace["router"]["rules_invalid"] = True
            return self._refusal(q, "no_entendida", trace, t0)
        if plan["action"] == "refuse":
            return self._refusal(q, plan["reason"], trace, t0)
        try:
            res = ops.run(cat, plan)
        except ops.NoData as e:
            return self._nodata(q, e, trace, t0)
        required = REQUIRED[res.op]
        forbidden = sorted({w for c in res.citations for w in (cat.get(c["series_id"]).meta.get("forbidden_words") or [])})
        tpl = _template(res.op, res.slots)
        pp = self.gateway.generate_json(
            task="phrase", key=q, system=prompts.PHRASE_SYSTEM,
            user=prompts.phrase_user(q, res.op, res.slots, required, _hints(res)),
            fallback=lambda: {"texto": tpl},
            validate=lambda d: validate_phrase(d, res.slots, required, forbidden))
        trace["phrase"] = {"mode": pp.mode, "reason": pp.reason}
        text = render(pp.data["texto"], res.slots)
        if not grounded(text, res.slots):            # belt and braces; cannot happen if validators hold
            text = render(tpl, res.slots)
            trace["phrase"]["grounding_override"] = True
        return {"question": q, "refused": False, "reason": None, "answer": text, "slots": res.slots,
                "citation_text": self._cite_text(res.citations), "figures": res.figures, "citations": res.citations,
                "plan": plan, "trace": trace, "snapshot": cat.built_at[:10],
                "elapsed_ms": int((time.time() - t0) * 1000)}

    def _cite_text(self, cits: list[dict]) -> str:
        return " · ".join(f"Fuente: {c['source']} — {c['title']} (serie {c['series_id']}), {c['period']}. "
                          f"Licencia {c['licence']}, vía datos.gob.ar." for c in cits)

    def _refusal(self, q, reason, trace, t0):
        return {"question": q, "refused": True, "reason": reason, "answer": REFUSALS.get(reason, REFUSALS["otro"]), "slots": {},
                "citation_text": "", "figures": [], "citations": [], "plan": trace.get("router", {}).get("plan"),
                "trace": trace, "snapshot": self.catalog.built_at[:10], "elapsed_ms": int((time.time() - t0) * 1000)}

    def _nodata(self, q, e: ops.NoData, trace, t0):
        out = self._refusal(q, "sin_datos", trace, t0)
        msg = "No tengo ese dato en el snapshot local"
        if e.entry and e.hint:
            f = e.entry.get("frequency", "year")
            out["slots"] = {"desde": fmt.period(e.hint["desde"], f), "hasta": fmt.period(e.hint["hasta"], f),
                            "serie": e.entry["title"]}
            msg += f": la serie «{e.entry['title']}» cubre de {out['slots']['desde']} a {out['slots']['hasta']}"
        elif e.entry:
            msg += f" ({e})"
        out["answer"] = msg + ". No invento cifras."
        if e.entry:
            out["citation_text"] = f"Serie consultada: {e.entry['id']} ({e.entry['source']}). Licencia {e.entry['licence']}."
        trace["nodata"] = str(e)
        return out
