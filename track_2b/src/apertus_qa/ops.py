"""Deterministic operations over the snapshot. The ONLY place numbers are produced.

Each op returns a Result: figures (raw value + formatted string + series id + period), the placeholder map handed
to the phrasing step, and the citation records. Ops raise NoData when the snapshot can't answer."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import fmt
from .catalog import Catalog, Series, Table
from .periods import shift, to_iso

OPS = ("valor", "ultimo", "variacion", "variacion_mensual", "interanual", "maximo", "minimo", "total_anual",
       "ranking", "ajuste", "comparar", "tabla_top", "tabla_valor")
MEASURES = ("nivel", "variacion_mensual", "interanual")
IPC = "148.3_INIVELNAL_DICI_M_26"


class NoData(Exception):
    def __init__(self, msg: str, entry: dict | None = None, hint: dict | None = None):
        super().__init__(msg)
        self.entry, self.hint = entry, hint


@dataclass
class Result:
    op: str
    figures: list[dict] = field(default_factory=list)
    slots: dict[str, str] = field(default_factory=dict)      # placeholder -> formatted text
    citations: list[dict] = field(default_factory=list)


def _fig(r: Result, slot: str, value: float, text: str, s, period_iso: str | None, label: str):
    r.figures.append({"slot": slot, "label": label, "value": value, "text": text, "series_id": s.id,
                      "period": period_iso[:7] if (period_iso and getattr(s, "freq", "year") == "month") else (period_iso or "")[:4]})
    r.slots[slot] = text


def _cite(r: Result, s, periods: list[str]):
    m = s.meta
    freq = m.get("frequency", "year")
    lab = " a ".join(fmt.period(p, freq) for p in sorted({p for p in periods if p})) or m.get("period", "")
    if not any(c["series_id"] == m["id"] for c in r.citations):
        r.citations.append({"series_id": m["id"], "title": m["title"], "source": m["source"], "dataset": m.get("dataset"),
                            "dataset_url": m.get("dataset_url"), "licence": m["licence"], "period": lab,
                            "retrieved_from": m.get("retrieved_from"), "notes": m.get("notes", [])})


def _pt(s: Series, iso: str | None, label: str = "período") -> float:
    if iso is None:
        raise NoData(f"{label} inválido para la frecuencia de la serie", s.meta)
    if iso not in s.points:
        raise NoData(f"sin dato para {fmt.period(iso, s.freq)}", s.meta,
                     {"desde": s.first, "hasta": s.last})
    return s.points[iso]


def _series(cat: Catalog, sid: str) -> Series:
    s = cat.series.get(sid)
    if s is None:
        raise NoData(f"serie desconocida: {sid}")
    return s


def _measure(s: Series, iso: str, measure: str) -> float | None:
    if measure == "nivel":
        return s.points.get(iso)
    k = 1 if measure == "variacion_mensual" else (12 if s.freq == "month" else 1)
    prev = s.points.get(shift(iso, s.freq, -k))
    cur = s.points.get(iso)
    if prev in (None, 0) or cur is None:
        return None
    return cur / prev - 1


def _show(s: Series, v: float) -> str:
    return fmt.pct(v) if s.kind == "pct" else fmt.value(v, s.unit)


def run(cat: Catalog, plan: dict) -> Result:
    op = plan["op"]
    r = Result(op)
    ids = plan.get("series") or []
    if op in ("tabla_top", "tabla_valor"):
        t = cat.tables.get(ids[0]) if ids else None
        if not isinstance(t, Table):
            raise NoData("tabla desconocida")
        u = t.meta["unit"]
        lab = t.meta.get("labels") or {}

        def name(k: str) -> str:
            parts = k.split("-")
            if lab and all(x in lab for x in parts):
                return "–".join(lab[x] for x in parts) + f" ({k})"
            return k
        if op == "tabla_top":
            n = max(1, min(int(plan.get("n") or 3), 10))
            for i, (k, v) in enumerate(t.rows[:n], 1):
                r.slots[f"clave_{i}"] = name(k)    # keys are labels, not figures
                _fig(r, f"valor_{i}", v, fmt.value(v, u), t, t.meta["period"], name(k))
        else:
            key = str(plan.get("key") or "").upper()
            row = next(((k, v) for k, v in t.rows if k.upper() == key or "-".join(sorted(k.split("-"))) == "-".join(sorted(key.split("-")))), None)
            if row is None:
                raise NoData(f"clave no encontrada: {key}", t.meta)
            r.slots["clave"] = name(row[0])
            _fig(r, "valor", row[1], fmt.value(row[1], u), t, t.meta["period"], name(row[0]))
        r.slots["periodo"] = t.meta["period"]
        r.slots["serie"] = t.meta["title"]
        _cite(r, t, [])
        r.citations[-1]["period"] = t.meta["period"]
        return r

    if op in ("ranking",):
        g = cat.groups().get(plan.get("group") or "")
        if not g:
            raise NoData("grupo desconocido")
        ss = [cat.series[i] for i in g]
        f = ss[0].freq
        y = str(plan.get("period") or "")[:4]
        vals = []
        for s in ss:
            if f == "month":
                months = [shift(f"{y}-01-01", "month", k) for k in range(12)]
                if not all(m in s.points for m in months):
                    raise NoData(f"año {y} incompleto en {s.id}", s.meta, {"desde": s.first, "hasta": s.last})
                vals.append((s, sum(s.points[m] for m in months)))
            else:
                vals.append((s, _pt(s, to_iso(y, "year"))))
        vals.sort(key=lambda t: -t[1])
        n = max(1, min(int(plan.get("n") or 3), 10))
        for i, (s, v) in enumerate(vals[:n], 1):
            r.slots[f"serie_{i}"] = s.meta["title"]
            _fig(r, f"valor_{i}", v, _show(s, v), s, f"{y}-01-01" if f == "year" else None, s.meta["title"])
            r.figures[-1]["period"] = y
            _cite(r, s, [f"{y}-01-01"] if f == "year" else [])
            if f == "month":
                r.citations[-1]["period"] = f"enero a diciembre de {y}"
        r.slots["periodo"] = y if f == "year" else f"{y} (enero a diciembre)"
        return r

    s = _series(cat, ids[0]) if ids else None
    if s is None:
        raise NoData("falta la serie")
    r.slots["serie"] = s.meta["title"]
    if op == "valor":
        iso = to_iso(plan.get("period"), s.freq)
        v = _pt(s, iso)
        _fig(r, "valor", v, _show(s, v), s, iso, s.meta["title"])
        r.slots["periodo"] = fmt.period(iso, s.freq)
        _cite(r, s, [iso])
    elif op == "ultimo":
        iso = s.last
        v = s.points[iso]
        _fig(r, "valor", v, _show(s, v), s, iso, s.meta["title"])
        r.slots["periodo"] = fmt.period(iso, s.freq)
        _cite(r, s, [iso])
    elif op in ("variacion", "variacion_mensual", "interanual"):
        if op == "variacion":
            a, b = to_iso(plan.get("from"), s.freq), to_iso(plan.get("to"), s.freq)
        else:
            b = to_iso(plan.get("period"), s.freq) if plan.get("period") else s.last
            if b is None:
                raise NoData("período inválido", s.meta)
            k = 1 if op == "variacion_mensual" else (12 if s.freq == "month" else 1)
            a = shift(b, s.freq, -k)
        va, vb = _pt(s, a, "desde"), _pt(s, b, "hasta")
        if s.kind == "pct":
            raise NoData("la serie ya es una variación; usar 'valor'", s.meta)
        if va == 0:
            raise NoData("variación indefinida (valor inicial 0)", s.meta)
        ch = vb / va - 1
        _fig(r, "desde_valor", va, _show(s, va), s, a, "valor inicial")
        _fig(r, "hasta_valor", vb, _show(s, vb), s, b, "valor final")
        _fig(r, "variacion", ch, fmt.pct(ch), s, b, "variación")
        r.slots.update(desde=fmt.period(a, s.freq), hasta=fmt.period(b, s.freq), periodo=fmt.period(b, s.freq))
        _cite(r, s, [a, b])
    elif op in ("maximo", "minimo"):
        meas = plan.get("measure") or "nivel"
        if meas not in MEASURES:
            raise NoData("medida inválida")
        lo = to_iso(plan.get("from"), s.freq) if plan.get("from") else s.first
        hi = to_iso(plan.get("to"), s.freq) if plan.get("to") else s.last
        if lo is None or hi is None:
            raise NoData("rango inválido", s.meta)
        cand = [(d, _measure(s, d, meas)) for d in s.order if lo <= d <= hi]
        cand = [(d, v) for d, v in cand if v is not None]
        if not cand:
            raise NoData("sin datos en el rango", s.meta, {"desde": s.first, "hasta": s.last})
        d, v = (max if op == "maximo" else min)(cand, key=lambda t: t[1])
        txt = fmt.pct(v) if meas != "nivel" or s.kind == "pct" else fmt.value(v, s.unit)
        _fig(r, "valor", v, txt, s, d, s.meta["title"])
        r.slots.update(periodo=fmt.period(d, s.freq), rango_desde=fmt.period(cand[0][0], s.freq),
                       rango_hasta=fmt.period(cand[-1][0], s.freq))
        _cite(r, s, [cand[0][0], cand[-1][0]])
        r.citations[-1]["period"] = f"{fmt.period(cand[0][0], s.freq)} a {fmt.period(cand[-1][0], s.freq)}"
    elif op == "total_anual":
        if s.freq != "month" or not s.meta.get("aggregation_ok"):
            raise NoData("la serie no admite suma anual", s.meta)
        y = str(plan.get("period") or "")[:4]
        months = [shift(f"{y}-01-01", "month", k) for k in range(12)] if y.isdigit() else []
        missing = [m for m in months if m not in s.points]
        if not months or missing:
            raise NoData(f"año {y} incompleto", s.meta, {"desde": s.first, "hasta": s.last})
        v = sum(s.points[m] for m in months)
        _fig(r, "valor", v, fmt.value(v, s.unit), s, None, s.meta["title"])
        r.figures[-1]["period"] = y
        r.slots["periodo"] = y
        _cite(r, s, [])
        r.citations[-1]["period"] = f"enero a diciembre de {y}"
    elif op == "ajuste":
        if s.id != IPC:
            raise NoData("el ajuste por inflación usa solo el IPC")
        amount = plan.get("amount")
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise NoData("monto inválido")
        a = to_iso(plan.get("from"), "month")
        b = to_iso(plan.get("to"), "month") if plan.get("to") else s.last
        ia, ib = _pt(s, a, "desde"), _pt(s, b, "hasta")
        v = amount * ib / ia
        r.slots["monto"] = fmt.money(amount)
        r.figures.append({"slot": "monto", "label": "monto de la pregunta", "value": amount, "text": fmt.money(amount),
                          "series_id": None, "period": a[:7]})
        _fig(r, "valor", v, fmt.money(v), s, b, "monto ajustado")
        _fig(r, "variacion", ib / ia - 1, fmt.pct(ib / ia - 1), s, b, "inflación acumulada")
        r.slots.update(desde=fmt.period(a, "month"), hasta=fmt.period(b, "month"), periodo=fmt.period(b, "month"))
        _cite(r, s, [a, b])
    elif op == "comparar":
        if len(ids) != 2:
            raise NoData("comparar requiere dos series")
        s2 = _series(cat, ids[1])
        if s.freq != s2.freq or s.unit != s2.unit:
            raise NoData("las series no son comparables (frecuencia o unidad distinta)")
        iso = to_iso(plan.get("period"), s.freq)
        v1, v2 = _pt(s, iso), _pt(s2, iso)
        r.slots.update(serie_1=s.meta["title"], serie_2=s2.meta["title"], periodo=fmt.period(iso, s.freq))
        _fig(r, "valor_1", v1, _show(s, v1), s, iso, s.meta["title"])
        _fig(r, "valor_2", v2, _show(s2, v2), s2, iso, s2.meta["title"])
        r.slots["mayor"] = s.meta["title"] if v1 > v2 else s2.meta["title"] if v2 > v1 else "ninguna (iguales)"
        _cite(r, s, [iso])
        _cite(r, s2, [iso])
    else:
        raise NoData(f"operación desconocida: {op}")
    return r
