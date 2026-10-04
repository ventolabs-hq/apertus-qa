"""Spanish (Argentina) formatting: thousands '.', decimal ','. Periods as 'agosto de 2026'."""
from __future__ import annotations

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]


def num(x: float, dec: int = 1) -> str:
    s = f"{abs(x):,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return ("−" if x < 0 and float(f"{abs(x):.{dec}f}") != 0 else "") + s


def pct(x: float, dec: int = 1) -> str:
    """x is a proportion (0.0166 -> '1,7 %')."""
    return num(x * 100, dec) + " %"


def period(iso: str, freq: str) -> str:
    if freq == "year":
        return iso[:4]
    return f"{MESES[int(iso[5:7]) - 1]} de {iso[:4]}"


UNIT_DEC = {"habitantes": 0, "nacimientos": 0, "víctimas": 0, "movimientos": 0, "vuelos": 0, "viajes de turistas": 0,
            "pesos por dólar": 2, "índice (dic-2016=100)": 2, "MW": 1, "miles de m³": 1, "millones de dólares": 1,
            "miles de pasajeros": 1}


def value(x: float, unit: str) -> str:
    d = UNIT_DEC.get(unit, 1)
    return f"{num(x, d)} {unit}"


def money(x: float) -> str:
    return "$ " + num(x, 2)
