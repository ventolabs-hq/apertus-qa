"""Validators for model output. A rejected output never reaches the user: the gateway falls back."""
from __future__ import annotations

import re

from .catalog import Catalog
from .ops import MEASURES, OPS
from .periods import to_iso

REASONS = ("fuera_de_alcance", "pronostico", "consejo", "otro", "sin_datos")
PLAN_KEYS = {"action", "op", "series", "group", "period", "from", "to", "measure", "amount", "n", "key", "reason"}
NUMBER_WORDS = re.compile(r"\b(cero|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|veinte|treinta|"
                          r"cuarenta|cincuenta|cien|ciento|cientos|mil|miles|millón|millon|millones|billón|billones|"
                          r"doble|triple|cuádruple|mitad|tercio|decena|docena|centenar)\b", re.I)
GLOBAL_FORBIDDEN = ("récord", "record", "histórico", "pronóstico", "te recomiendo", "conviene", "deberías")
PLACEHOLDER = re.compile(r"\{([a-z_0-9]+)\}")


def numbers_in(text: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)*", text)


def validate_plan(d, cat: Catalog, question: str) -> str | None:
    if not isinstance(d, dict):
        return "not_object"
    if set(d) - PLAN_KEYS:
        return "unknown_keys"
    if d.get("action") == "refuse":
        return None if d.get("reason") in REASONS else "bad_reason"
    if d.get("action") != "answer":
        return "bad_action"
    op = d.get("op")
    if op not in OPS:
        return "bad_op"
    ids = d.get("series") or []
    if not isinstance(ids, list) or len(ids) > 2 or not all(isinstance(x, str) for x in ids):
        return "bad_series"
    if op == "ranking":
        if d.get("group") not in cat.groups():
            return "unknown_group"
    else:
        if not ids:
            return "missing_series"
        for sid in ids:
            if cat.get(sid) is None:
                return "unknown_series"
        tbl = op.startswith("tabla_")
        if tbl != all(sid in cat.tables for sid in ids):
            return "op_kind_mismatch"
        if op == "comparar" and len(ids) != 2:
            return "comparar_needs_two"
    freq = None
    if ids and ids[0] in cat.series:
        freq = cat.series[ids[0]].freq
    elif op == "ranking":
        freq = "year"   # ranking periods are always years
    for k in ("period", "from", "to"):
        v = d.get(k)
        if v is None:
            continue
        if not isinstance(v, str):
            return f"bad_{k}"
        if freq and op != "ranking" and op != "total_anual" and to_iso(v, freq) is None:
            return f"bad_{k}_format"
        if (op in ("ranking", "total_anual")) and not re.fullmatch(r"\d{4}", v):
            return f"bad_{k}_format"
    if op in ("valor", "comparar", "total_anual", "ranking") and not d.get("period"):
        return "missing_period"
    if op == "variacion" and not (d.get("from") and d.get("to")):
        return "missing_range"
    if d.get("measure") is not None and d.get("measure") not in MEASURES:
        return "bad_measure"
    if d.get("n") is not None and (not isinstance(d["n"], int) or not 1 <= d["n"] <= 10):
        return "bad_n"
    if d.get("key") is not None and (not isinstance(d["key"], str) or len(d["key"]) > 20):
        return "bad_key"
    if op == "ajuste":
        a = d.get("amount")
        if not isinstance(a, (int, float)) or isinstance(a, bool) or a <= 0:
            return "bad_amount"
        # grounding: the amount must literally appear in the question (the model may not invent it)
        qn = set()
        for x in numbers_in(question):
            try:
                qn.add(float(x.replace(".", "").replace(",", ".")))
            except ValueError:
                pass
        if float(a) not in qn:
            return "amount_not_in_question"
        if not d.get("from"):
            return "missing_from"
    return None


def validate_phrase(d, slots: dict[str, str], required: list[str], forbidden: list[str]) -> str | None:
    if not isinstance(d, dict) or not isinstance(d.get("texto"), str):
        return "not_object"
    t = d["texto"].strip()
    if not 10 <= len(t) <= 400:
        return "length"
    used = PLACEHOLDER.findall(t)
    if any(u not in slots for u in used):
        return "unknown_placeholder"
    if any(r not in used for r in required):
        return "missing_required"
    bare = PLACEHOLDER.sub(" ", t)
    if "{" in bare or "}" in bare:
        return "stray_brace"
    if re.search(r"\d", bare):
        return "digits_in_text"
    if NUMBER_WORDS.search(bare):
        return "number_words"
    low = bare.casefold()
    for w in list(GLOBAL_FORBIDDEN) + list(forbidden):
        if w.casefold() in low:
            return f"forbidden:{w}"
    return None


def render(t: str, slots: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: slots[m.group(1)], t.strip())


def grounded(text: str, slots: dict[str, str]) -> bool:
    """Every numeric token in the final answer must come from a slot value."""
    allowed = set()
    for v in slots.values():
        allowed.update(numbers_in(v))
    return all(n in allowed for n in numbers_in(text))
