"""Write docs/DATA.md from data/snapshot/catalog.json (sources, licences, coverage, notes)."""
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
cat = json.loads((ROOT / "data/snapshot/catalog.json").read_text())
L = ["# Datos: snapshot local", "",
     f"Snapshot construido: {cat['built_at']} (UTC). {cat['built_from']}.", "",
     f"**Política de licencias:** {cat['licence_policy']}", "", f"**Atribución (CC BY 4.0):** {cat['attribution']}", "",
     "**Cómo se obtuvo (solo en tiempo de construcción, nunca en ejecución):** API de Series de Tiempo "
     "(`apis.datos.gob.ar/series/api/series/?ids=...&metadata=full`; robots.txt sin restricciones) y archivos de recursos "
     "enlazados desde páginas de dataset de `datos.gob.ar` (robots.txt: `/api/` prohibido, `Crawl-Delay: 10`; respetados). "
     "La evidencia de licencia es el campo `dataset.license` del metadato de la API o el campo «Licencia» de la página del dataset. "
     "`src/tools/build_snapshot.py` verifica el sha256 de cada archivo crudo y descarta lo que no sea CC BY 4.0.", "",
     "**Transformaciones:** variaciones calculadas (IPC dic–dic), agregados anuales/por categoría de microdatos (ANAC, SNIC) "
     "y corrección documentada de unidades (subte). Los microdatos crudos (víctimas individuales, vuelos individuales) **no** se incluyen.", "",
     "| id | título | fuente | cobertura | licencia | notas |", "|---|---|---|---|---|---|"]
for e in cat["entries"]:
    cov = (f"{e['coverage']['start'][:7]} → {e['coverage']['end'][:7]}" if e["kind"] != "table" else e["period"])
    notes = " ".join(e.get("notes") or [])
    L.append(f"| `{e['id']}` | {e['title']} | {e['source']} | {cov} | {e['licence']} | {notes} |")
L += ["", "Cada respuesta del sistema cita la serie (`id`), el período y la licencia. Las URL exactas de obtención y los sha256 "
      "están en `data/snapshot/catalog.json`."]
(ROOT / "docs" / "DATA.md").write_text("\n".join(L) + "\n")
print("docs/DATA.md", len(cat["entries"]), "entries")
