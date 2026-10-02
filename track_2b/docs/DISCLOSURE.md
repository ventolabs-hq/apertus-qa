# Disclosure: reuse, pre-existing work and AI assistance

**Project start:** 2 October 2026 (inside the Hack Apertus period, 1–16 Oct 2026). All application code in `src/apertus_qa/`,
`src/eval/`, `src/tests/` and `src/tools/` was written from 2 October 2026 onward. The git history records this.

## Reused components (adapted, written by the same team earlier on 2 October 2026 for another prototype)
- **LLM gateway** (`src/apertus_qa/gateway.py`): ported from JavaScript to Python from an earlier `llm-gateway` component
  (contract: never throws, per-day/per-minute budgets, circuit breaker, timeout, JSON parsing, schema and semantic
  validation, deterministic fallback with a reason). Changes: Python stdlib threads for timeouts; invalid content no longer
  trips the breaker (only transport failures do); tolerant JSON parsing of fenced output.
- **Container pattern** (single stateless web process, env-var configuration, health endpoint), adapted from the same
  prototype's hosting notes.

## Pre-existing data work reused
- Raw downloads and licence evidence cached on 1–2 October 2026 by the team's open-data pipeline (INDEC/datos.gob.ar series
  used for short statistical explainers). This project re-reads those caches at build time (`src/tools/build_snapshot.py`),
  re-verifies sha256 and licence, and writes its own snapshot. Aggregation recipes for ANAC flight counts and SNIC road
  deaths follow the same definitions as that pipeline (counts only; no passenger columns; "siniestros viales").
- The IPC adjustment matches a previously QA'd inflation calculator from the same team (cross-checked against INDEC's
  published one-decimal figures).

## Third-party material
- `LICENSE`, `.gitignore`, `track_2b/README.md`, `track_2b/technical_report.md` skeleton and `track_2b/Makefile` skeleton come
  from `HackApertus/project-template` at commit `7f23822` (Apache-2.0), fetched as a tarball through the GitHub REST API.
- Data: CC BY 4.0, see `docs/DATA.md` for per-dataset attribution.

## AI assistance
The code, tests and documents were produced by AI coding agents directed by the entrant. The **runtime** model is Apertus
(via `LLM_BASE_URL`). No other model is used at runtime. Until the CSCS key is available, tests and evaluation use a **STUB**
that replays outputs **written by the build agent** (they are not real Apertus outputs and are labelled STUB everywhere).
