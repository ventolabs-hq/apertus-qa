"""Period parsing for plans ('2026-08', '2026') -> ISO keys used in the snapshot ('2026-08-01', '2026-01-01')."""
from __future__ import annotations

import re

_M = re.compile(r"^(\d{4})-(\d{2})$")
_Y = re.compile(r"^(\d{4})$")


def to_iso(p: str | None, freq: str) -> str | None:
    """Return the snapshot key for a plan period, or None if it is malformed / incompatible with the frequency."""
    if p is None:
        return None
    p = str(p).strip()
    m = _M.match(p)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if not 1 <= mo <= 12:
            return None
        return f"{y:04d}-{mo:02d}-01" if freq == "month" else None
    m = _Y.match(p)
    if m:
        return f"{int(m.group(1)):04d}-01-01" if freq == "year" else None
    return None


def shift(iso: str, freq: str, n: int) -> str:
    y, mo = int(iso[:4]), int(iso[5:7])
    if freq == "year":
        return f"{y + n:04d}-01-01"
    k = y * 12 + (mo - 1) + n
    return f"{k // 12:04d}-{k % 12 + 1:02d}-01"


def year_of(p: str) -> int | None:
    m = re.match(r"^(\d{4})", str(p or ""))
    return int(m.group(1)) if m else None
