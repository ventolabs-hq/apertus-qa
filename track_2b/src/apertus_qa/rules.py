"""Deterministic keyword router: the fallback when the model is unavailable or its plan is rejected, and the
no-model baseline in the evaluation. Deliberately simple; it handles common phrasings only."""
from __future__ import annotations

import re
import unicodedata

from .catalog import Catalog
from .fmt import MESES

IPC = "148.3_INIVELNAL_DICI_M_26"


def _n(s: str) -> str:
    s = unicodedata.normalize("NFD", s.casefold())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


REFUSE = [
    ("pronostico", r"\b(sera|seran|va a ser|van a|pronostic|proyeccion|predec|predic|el ano que viene|proximo ano|proximo mes|en 20(2[7-9]|[3-9]\d))"),
    ("consejo", r"\b(conviene|deberia|recomend|invertir|inversion|comprar dolares|plazo fijo|impuesto)"),
    ("otro", r"(ignora|olvida).{0,30}(instruccion|regla)|system prompt|sos un|actua como"),
    ("fuera_de_alcance", r"\b(blue|desempleo|desocupacion|pobreza|indigencia|pbi|riesgo pais|bcra|reservas|tasa de interes|"
                         r"merval|bitcoin|salario minimo|jubilacion)"),
]

TOPICS = [  # (pattern, series id or special); order matters
    (r"subte|premetro", "302.3_TRANSP_PASSAJ_0_S_38"),
    (r"turis", "turismo"),
    (r"export", "expo"),
    (r"salari|sueldo", "salarios"),
    (r"poblacion|habitantes", "9.1_POB_2004_A_9"),
    (r"tipo de cambio|dolar", "9.1_TU_2004_A_17"),
    (r"solar", "367.1_POTENCIA_ILAR__24"),
    (r"eolic", "367.1_POTENCIA_IICA__25"),
    (r"potencia", "367.1_POTENCIA_ITAL__24"),
    (r"petroleo|crudo", "363.3_PRODUCCIONUDO__28"),
    (r"naci(mientos|dos|eron)|natalidad", "deis_nacidos_vivos_total_pais"),
    (r"ruta|cabotaje", "anac_2025_vuelos_cabotaje_por_ruta"),
    (r"aeropuerto|vuelo", "anac_2025_movimientos_regulares_por_aeropuerto"),
    (r"siniestr|muertes viales|victimas", "vial"),
    (r"inflacion|ipc|precios|ajust|equival|actualiz", IPC),
]

VEHICLES = {r"\bmoto": "Motocicleta", r"\bauto": "Automóvil", r"peaton": "Peatón", r"bici": "Bicicleta"}
DEST = {"brasil": 5, "chile": 3, "uruguay": 9, "bolivia": 1, "paraguay": 4, "europa": 2, "estados unidos": 6}


def _periods(q: str) -> list[str]:
    out = []
    for m in re.finditer(r"(" + "|".join(MESES) + r")\s+(?:de|del)?\s*(\d{4})", q):
        out.append((m.start(), f"{m.group(2)}-{MESES.index(m.group(1)) + 1:02d}"))
    taken = {m.group(2) for m in re.finditer(r"(" + "|".join(MESES) + r")\s+(?:de|del)?\s*(\d{4})", q)}
    for m in re.finditer(r"\b(19\d{2}|20\d{2})\b", q):
        if m.group(1) not in taken:
            out.append((m.start(), m.group(1)))
    return [p for _, p in sorted(out)]


def _amount(q: str):
    m = re.search(r"\$\s*([\d.]+(?:,\d+)?)|([\d.]+(?:,\d+)?)\s*pesos", q)
    if not m:
        return None
    x = (m.group(1) or m.group(2)).replace(".", "").replace(",", ".")
    try:
        v = float(x)
        return int(v) if v.is_integer() else v
    except ValueError:
        return None


def plan(question: str, cat: Catalog) -> dict | None:
    q = _n(question)
    for reason, pat in REFUSE:
        if re.search(pat, q):
            return {"action": "refuse", "reason": reason}
    topic = next((t for pat, t in TOPICS if re.search(pat, q)), None)
    if topic is None:
        return {"action": "refuse", "reason": "fuera_de_alcance"}
    ps = _periods(q)
    p0 = ps[0] if ps else None
    years = [p[:4] for p in ps]
    base = {"action": "answer"}

    if topic == "turismo":
        via = "aerea" if "aere" in q or "avion" in q else "terrestre" if "terrestre" in q else "aerea"
        dest = next((k for k in DEST if k in q), None)
        if dest is None or re.search(r"(que|cual).{0,20}(destino|pais)", q):
            return {**base, "op": "ranking", "group": f"turismo_emisivo_{via}", "period": years[0] if years else None, "n": 3}
        idx = DEST[dest] + {"aerea": 0, "terrestre": 9, "maritima_fluvial": 18}[via]
        sid = f"te_turistas_{idx}"
        if p0 and len(p0) == 7:
            return {**base, "op": "valor", "series": [sid], "period": p0}
        return {**base, "op": "total_anual", "series": [sid], "period": years[0] if years else None}
    if topic == "expo":
        if re.search(r"rubro|que (tipo|sector)|mas export", q):
            return {**base, "op": "ranking", "group": "exportaciones_rubros", "period": years[0] if years else None, "n": 4}
        topic = "350.1_TOTAL_EXPONES__39"
    if topic == "salarios":
        return {**base, "op": "comparar", "series": ["149.1_TL_REGIADO_OCTU_0_16", "148.3_INIVELNAL_DICI_M_26@dic_dic"],
                "period": years[0] if years else None}
    if topic == "vial":
        veh = next((v for k, v in VEHICLES.items() if re.search(k, q)), None)
        if veh:
            return {**base, "op": "tabla_valor", "series": ["snic_sat_mv_victimas_por_vehiculo_2024"], "key": veh}
        if re.search(r"vehiculo", q):
            return {**base, "op": "tabla_top", "series": ["snic_sat_mv_victimas_por_vehiculo_2024"], "n": 3}
        topic = "snic_sat_mv_victimas_anual"
    if topic in cat.tables:
        return {**base, "op": "tabla_top", "series": [topic], "n": 3}

    sid = topic
    s = cat.series[sid]
    if sid == IPC:
        amt = _amount(question)
        if amt is not None and re.search(r"ajust|equival|actualiz|necesit|hoy", q) and p0:
            to = ps[1] if len(ps) > 1 and len(ps[1]) == 7 else None
            return {**base, "op": "ajuste", "series": [IPC], "amount": amt, "from": p0 if len(p0) == 7 else f"{p0}-12",
                    "to": to}
        if re.search(r"(mas alta|maxima|mayor)", q):
            return {**base, "op": "maximo", "series": [IPC], "measure": "variacion_mensual" if "mensual" in q else "interanual"}
        if re.search(r"diciembre a diciembre|anual de|inflacion de (19|20)\d{2}\b|en (19|20)\d{2}\??$", q) and p0 and len(p0) == 4:
            return {**base, "op": "valor", "series": ["148.3_INIVELNAL_DICI_M_26@dic_dic"], "period": p0}
        if len(ps) >= 2:
            return {**base, "op": "variacion", "series": [IPC], "from": ps[0], "to": ps[1]}
        if "interanual" in q:
            return {**base, "op": "interanual", "series": [IPC], "period": p0}
        return {**base, "op": "variacion_mensual", "series": [IPC], "period": p0}
    if len(ps) >= 2:
        return {**base, "op": "variacion", "series": [sid], "from": ps[0], "to": ps[1]}
    if "interanual" in q or "respecto del ano anterior" in q:
        return {**base, "op": "interanual", "series": [sid], "period": p0}
    if re.search(r"(mas alt|maxim|mayor)", q):
        return {**base, "op": "maximo", "series": [sid]}
    if p0:
        if s.freq == "month" and len(p0) == 4 and s.meta.get("aggregation_ok"):
            return {**base, "op": "total_anual", "series": [sid], "period": p0}
        if s.freq == "year":
            p0 = p0[:4]
        return {**base, "op": "valor", "series": [sid], "period": p0}
    return {**base, "op": "ultimo", "series": [sid]}
