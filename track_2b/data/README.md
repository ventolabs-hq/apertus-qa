# `data/`: third-party data (CC BY 4.0), not a dataset contributed by this project

Everything under `data/snapshot/` is **third-party open data** published by Argentine public bodies (INDEC, Ministerio de
Economía, Secretaría de Energía, CAMMESA, Subsecretaría de Turismo, Ministerio de Salud/DEIS, ANAC, Ministerio de
Seguridad/SNIC) on datos.gob.ar / apis.datos.gob.ar under the **Creative Commons Attribution 4.0 International** licence
(CC BY 4.0, https://creativecommons.org/licenses/by/4.0/).

- We redistribute it **under its original CC BY 4.0 licence, with attribution**. We do not relicense it (for example under
  CDLA-Permissive-2.0), and we do not claim it as our own dataset. It is **not** uploaded to Hugging Face or any dataset hub.
- Changes made by this project: series trimmed to a time window, microdata reduced to aggregate counts (no personal data),
  and CSV/JSON reformatting. Values are not altered. Every app answer cites the publisher, series id, period and licence.
- Per-dataset source, coverage, licence evidence and sha256: `../docs/DATA.md` and `snapshot/catalog.json`.

Attribution: "Fuente: INDEC y otros organismos del Estado Nacional argentino, vía datos.gob.ar. Licencia CC BY 4.0.
Datos transformados (recortes y agregados) por el proyecto Apertus QA."

What this project itself contributes (eval questions in `../src/eval/`) is our own work and can be licensed as the
competition terms require.
