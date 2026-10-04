"""Data layer: loads the local snapshot (data/snapshot/), verifies integrity and licence, never uses the network."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


class DataError(Exception):
    pass


@dataclass
class Series:
    meta: dict
    points: dict[str, float]                    # iso date -> value
    order: list[str] = field(default_factory=list)

    @property
    def id(self): return self.meta["id"]
    @property
    def freq(self): return self.meta["frequency"]
    @property
    def unit(self): return self.meta["unit"]
    @property
    def kind(self): return self.meta["kind"]
    @property
    def first(self): return self.order[0]
    @property
    def last(self): return self.order[-1]


@dataclass
class Table:
    meta: dict
    rows: list[tuple[str, float]]

    @property
    def id(self): return self.meta["id"]


class Catalog:
    def __init__(self, directory: str | Path | None = None):
        self.dir = Path(directory or os.environ.get("SNAPSHOT_DIR") or DEFAULT_DIR)
        raw = (self.dir / "catalog.json").read_bytes()
        self.doc = json.loads(raw)
        self.series: dict[str, Series] = {}
        self.tables: dict[str, Table] = {}
        for e in self.doc["entries"]:
            if e.get("licence") != "CC BY 4.0":
                raise DataError(f"{e['id']}: licence is not CC BY 4.0; refusing to load")
            b = (self.dir / e["file"]).read_bytes()
            if hashlib.sha256(b).hexdigest() != e["sha256"]:
                raise DataError(f"{e['file']}: sha256 mismatch (snapshot modified?)")
            rows = list(csv.reader(b.decode().splitlines()))[1:]
            if e["kind"] == "table":
                self.tables[e["id"]] = Table(e, [(k, float(v)) for k, v in rows])
            else:
                pts = {d: float(v) for d, v in rows}
                self.series[e["id"]] = Series(e, pts, sorted(pts))

    @property
    def built_at(self) -> str:
        return self.doc["built_at"]

    def get(self, sid: str):
        return self.series.get(sid) or self.tables.get(sid)

    def groups(self) -> dict[str, list[str]]:
        g: dict[str, list[str]] = {}
        for s in self.series.values():
            if s.meta.get("group"):
                g.setdefault(s.meta["group"], []).append(s.id)
        return g

    def compact(self) -> list[dict]:
        """What the model sees: ids, titles, units, frequency and coverage. No values."""
        out = []
        for e in self.doc["entries"]:
            c = {"id": e["id"], "titulo": e["title"], "tema": e["topic"], "unidad": e["unit"]}
            if e["kind"] == "table":
                c.update({"tipo": "tabla", "periodo": e["period"], "filas": e["rows"]})
            else:
                c.update({"tipo": e["kind"], "frecuencia": "mensual" if e["frequency"] == "month" else "anual",
                          "desde": e["coverage"]["start"][:7 if e["frequency"] == "month" else 4],
                          "hasta": e["coverage"]["end"][:7 if e["frequency"] == "month" else 4]})
                if e.get("group"):
                    c["grupo"] = e["group"]
            out.append(c)
        return out
