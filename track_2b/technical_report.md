# Technical report — Apertus QA: grounded Spanish answers over official statistics

> **DRAFT (round 2, 2 Oct 2026).** All results below come from the **STUB** (replayed outputs written by the build agent,
> not by Apertus) or from the **no-model baseline**. Every Apertus number is a placeholder of the form `[[APERTUS_…]]` and
> will be filled from real runs once the CSCS key is available. Placeholders must be gone before the PDF is exported.

- **Track:** `Track 2B — Apertus QA (own project)`
- **Event:** Online
- **Team:** Vento Labs — `[[ENTRANT_LEGAL_NAME as on Devpost]]`
- **Demo:** `[[VIDEO_URL]]` (≤ 2 min, screen capture + captions, no voice)
- **Repository / commit:** `[[PUBLIC_REPO_URL]]` @ `[[COMMIT]]`

## 1. Summary

People ask statistical questions in plain language ("how much did prices rise last month?"). General-purpose chatbots
answer fluently, but the figure is often unsourced, out of date or wrong. For a newsroom, a public office or a school that
is worse than no answer. **Apertus QA** answers Spanish questions over a local, licence-checked snapshot of official
Argentine open data (47 series and tables from INDEC and other agencies, CC BY 4.0). Apertus does the two jobs that need
language understanding: it **plans** the query (which series, which operation, which period) and it **phrases** the answer.
It never produces a number, and it never sees one. A deterministic data layer computes every figure, and code attaches the
citation (publisher, series id, period, licence). If the snapshot cannot answer, the system says so, and it refuses
forecasts and financial advice. Everything except the model call runs with no network (`docker run --network none`), and
the model endpoint can be a self-hosted Apertus inside the same isolated network. **Headline (STUB / baseline, to be
replaced):** main set 31/31, held-out paraphrases 8/13, 0 grounding violations, 5/5 INDEC cross-checks.
**Apertus 8B:** main `[[APERTUS_MAIN]]`, held-out `[[APERTUS_HELDOUT]]`, grounding violations `[[APERTUS_GV]]`.

## 2. Architecture

```
question ─▶ input guard ─▶ [P1 router: Apertus] ─▶ plan JSON ─▶ validate_plan (catalog ids, period, op/kind,
                                │ invalid / timeout / no model            amount must appear in the question)
                                └──▶ rules router (fallback + baseline) ──┤ valid
                                                                          ▼
                      ops.run: 13 deterministic operations over data/snapshot (sha256 + licence verified at start)
                                                                          │ figures, placeholder slots, citations
                                                                          │ (no data ─▶ "no tengo ese dato", with coverage)
                                                                          ▼
          [P2 phrasing: Apertus — sees placeholder NAMES and direction hints, never values] ─▶ validate_phrase
                                │ invalid / timeout / no model                    (no digits, no number words,
                                └──▶ per-operation template ──────────────────────┤ known placeholders, banned words)
                                                                                  ▼
                            render slots ─▶ grounding re-check ─▶ answer + citation + figures table + trace
                                         Web UI (/) · JSON API (/api/ask, /api/catalog, /health) · CLI
```

**One container, one process.** Python 3.12 standard library only: no third-party packages, no `pip install`, no
database. The snapshot (≈0.3 MB of CSV plus `catalog.json`) ships inside the image. The Spanish web UI is a single HTML
file with no CDN, fonts or other external assets (a test asserts this).

**Components** (`src/apertus_qa/`): `catalog.py` (loads the snapshot and checks sha256 and licence for every file),
`ops.py` (13 operations: value, latest, change, monthly change, year-on-year, max, min, annual total, ranking, inflation
adjustment, comparison, table top-n, table value), `gateway.py` (LLM gateway), `providers.py` (OpenAI-compatible client,
stub replay, recorder), `prompts.py`, `validate.py`, `rules.py`, `pipeline.py`, `server.py`, `__main__.py`.

**LLM gateway.** The gateway never throws. It enforces a per-minute and per-day request budget, a timeout and a circuit
breaker (transport failures only; invalid content does not trip it). It parses JSON tolerantly, including fenced output,
validates it against a schema and semantic rules, and otherwise returns a deterministic fallback with a machine-readable
reason (for example `network_error`, `http_error`, `bad_response`, `budget_exhausted`, `breaker_open`, or a validator rejection). The reason appears in
the trace and in the UI.

### 2.1 Grounding guarantees (by construction, each covered by tests)

1. **Numbers come only from `ops.py`**, computed from the verified snapshot.
2. **The phrasing model never receives a figure.** It gets placeholder names (`{variacion}`, `{periodo}`) and qualitative
   hints (`direccion: subió`). A test against a fake OpenAI-style server asserts that the computed figure never appears in the phrasing request.
3. **Any digit or number word in model text is rejected**, and the template is used instead.
4. **The router cannot invent inputs.** Series must exist in the catalog, periods must be well-formed, and an amount to
   adjust for inflation must appear literally in the question.
5. **The final text is re-checked.** Every numeric token in the rendered answer must come from a computed slot value.
6. **Citations are written by code, not by the model**: publisher, series id, period range, licence and portal.

These guarantees bound the failure mode: a bad plan that still validates can give a *correct, cited figure for the wrong
question* (Section 6), but it cannot give an invented figure. Users can spot that case because the UI shows the series
and period used, next to the answer.

### 2.2 Target architecture (mandatory): **b) Air-gapped** (also a) on-premise and c) sovereign Swiss cloud)

| Stage | External network | Notes |
|---|---|---|
| Build | Base image only (`python:3.12-slim`, pulled by the daemon) | All `RUN` steps execute with `docker build --network none`. Isolated sites: `make image-save` → copy `apertus-qa.tar` → `docker load`. |
| Data | None | Snapshot inside the image; integrity (sha256) and licence verified at start-up. Refreshes are built *outside* the site and shipped as a new image. |
| Runtime: UI, API, computation, citations, refusals | None | Verified with `--network none` (Section 2.3). |
| Runtime: model | Only `LLM_BASE_URL` | CSCS-hosted Apertus (Switzerland) or a self-hosted Apertus (vLLM, Ollama or llama.cpp; OpenAI-style API) on the same isolated network. The API key is optional for local servers. |
| Model unreachable | None | Falls back to rules and templates. Answers stay correct and cited, and the UI shows the mode. |

`docs/deploy/docker-compose.airgap.yml` sketches the fully isolated set-up: app and vLLM serving local Apertus weights
(`HF_HUB_OFFLINE=1`) on a Docker network with `internal: true`, so there is no route out. *(Not run by us: no GPU was
available. `[[SELF_HOST_RESULT or "untested"]]`.)*

### 2.3 Air-gap proof

`make offline-proof` (script in `scripts/offline_proof.sh`, full output in `docs/OFFLINE.md`) runs the image with
`--network none` and shows the following:

- Only `lo` exists inside the container.
- Connecting to `1.1.1.1:443` or `8.8.8.8:53` fails with `Network is unreachable`, and DNS resolution fails.
- The server, started with its default command, answers `/health` and `/api/ask` from inside the same container, with
  correct cited answers and refusals.
- The 35 tests and all four evaluation runs (main and held-out × STUB and off) pass with identical scores.
- In `real` mode with no network, the trace records `router: fallback (network_error)` and the answer is still correct and
  cited. This shows the model call is the **only** network dependency.

## 3. Use of Apertus

- **Model:** `swiss-ai/Apertus-v1.5-8B` `[[confirm exact LLM_NAME from CSCS]]`; 70B `[[if time]]`.
- **How it is used:** inference in two roles. (P1) **tool-use-style planning**: the model emits one JSON plan over a catalog
  of 47 entries. (P2) **constrained generation**: Spanish phrasing with placeholders only.
- **Where it runs:** CSCS inference endpoint (OpenAI-compatible `/chat/completions`, temperature 0) via `LLM_BASE_URL`,
  `LLM_NAME` and `LLM_API_KEY`. The same code runs against any self-hosted OpenAI-style server.
- **P1 router prompt** (`prompts.ROUTER_SYSTEM`): Spanish instructions plus a compact catalog (ids, titles, units,
  frequency and coverage, **no values**; ≈4k tokens). The output is either
  `{action, op, series|group, period|from|to, measure, amount, n, key}` or `{action: "refuse", reason}`. Refusal reasons
  are `fuera_de_alcance | pronostico | consejo | otro`. Periods outside coverage are passed through so code can explain the
  coverage instead of guessing.
- **P2 phrasing prompt** (`prompts.PHRASE_SYSTEM`): input is the question, the operation, placeholder descriptions,
  required placeholders and direction hints. Output is `{"texto": …}`, one or two Spanish sentences.
- **JSON handling:** optional `response_format: json_object` (`LLM_JSON_MODE=1`) when the endpoint supports it; otherwise
  tolerant parsing.
- **Record and replay:** `LLM_MODE=record` stores real Apertus outputs (`stub/recorded.json`), so judges can replay a real
  run without a key or network. Replayed runs are labelled as such.
- **Observed behaviour:** `[[APERTUS_OBSERVATIONS: JSON validity rate, typical plan errors, phrase rejections by reason,
  latency p50/p95, effect of prompt iterations]]`.

No other model is used at runtime or for evaluation (scoring is deterministic code; there is no LLM judge).

## 4. Data

| Domain | Content | Publisher |
|---|---|---|
| Prices | CPI national level (monthly, Dec 2016 → Aug 2026); Dec–Dec inflation | INDEC |
| Wages | Registered wage index, Dec–Dec change | INDEC |
| Population, births | Population 2004–2025; live births (to 2022, declared) | INDEC; DEIS / Ministerio de Salud |
| Exchange rate, trade | Nominal annual exchange rate; exports, total and 4 categories | INDEC / Ministerio de Economía |
| Tourism | Resident tourist trips by destination and mode (27 series) | Subsecretaría de Turismo |
| Energy | Installed solar, wind and total capacity; crude oil production | CAMMESA; Secretaría de Energía |
| Transport | Subway passengers; 2025 regular flights by airport and route (counts only) | INDEC; ANAC |
| Road safety | Road deaths by year and by vehicle | SNIC / Ministerio de Seguridad |

**Licence.** All data are **third-party** open data under **CC BY 4.0**, obtained from datos.gob.ar /
apis.datos.gob.ar, respecting robots.txt and its crawl delay, and only at build time. We redistribute them under their
original licence with attribution (`data/README.md`, `docs/DATA.md`, and the citation line on every answer). We do not
relicense them, and we do not publish them as our own dataset on any hub. **Transformations:** time-window trimming;
microdata (flights, road deaths) reduced to aggregate counts; no personal data enters the repository. A per-file sha256
is recorded in `catalog.json` and checked at start-up.

## 5. Evaluation

**Task.** Spanish questions answered end to end. **Main set:** 31 questions (23 answerable, 8 that must be refused:
missing period, forecast, out of scope, financial advice, prompt injection). **Held-out set:** 13 paraphrases written
separately (colloquial wording, ellipsis), not used to write the rules router or prompts.

**Ground truth.** Expected values are computed directly from the snapshot by independent code (`src/eval/make_expected.py`,
which does not import the app). Five CPI answers are also cross-checked against INDEC's published one-decimal figures.

**Metrics.** *Decision* (answer vs refuse, with reason); *value* (the figure matches the expected value within tolerance);
*citation* (correct series and period); *grounding violations* (numbers in the text that do not come from a computed figure,
target 0); *false refusals*; *fallback rates* for router and phrasing, by reason.

| Setup | Set | Overall | Answers | Refusals | False refusals | Grounding viol. |
|---|---|---|---|---|---|---|
| No-model baseline (rules + templates) | main (31) | 31/31 | 23/23 | 8/8 | 0 | 0 |
| STUB replay (agent-written, **not Apertus**) | main (31) | 31/31 | 23/23 | 8/8 | 0 | 0 |
| No-model baseline | held-out (13) | 8/13 | 6/11 | 2/2 | 4 | 0 |
| **Apertus 8B** | main (31) | `[[A8_MAIN]]` | `[[ ]]` | `[[ ]]` | `[[ ]]` | `[[ ]]` |
| **Apertus 8B** | held-out (13) | `[[A8_HO]]` | `[[ ]]` | `[[ ]]` | `[[ ]]` | `[[ ]]` |
| Apertus 70B (optional) | held-out (13) | `[[A70_HO]]` | | | | |

INDEC cross-checks: 5/5 (baseline and STUB); Apertus `[[ ]]`.
All rows above were reproduced inside the Docker image with `--network none` (Section 2.3).

**How to read it.** The rules router was written while looking at the main set, so its 31/31 is **not a blind score**. The
held-out set is the fair comparison, and the claim to test is: *Apertus improves held-out coverage over the rules
baseline (8/13) while keeping grounding violations at 0.* The STUB rows only show that the pipeline, validators and
fallbacks work. The STUB also contains four adversarial canned outputs: an unknown series id (rejected, rules fallback), a
markdown-fenced plan (tolerated by the parser), a phrasing that invents a figure (rejected, template) and a phrasing that
uses a banned word, "récord" (rejected, template). All four are handled as designed.
**Error analysis:** `[[APERTUS_ERRORS: per-category breakdown, examples of plan errors caught vs passed, phrasing
rejections]]`.

## 6. Limitations

- **Coverage is fixed** at 47 series and tables. Unemployment, poverty and GDP are not included yet. The snapshot ends at
  the latest data cached at build time (CPI to Aug 2026).
- **Plausible but wrong plans.** A plan can pass validation and still answer a slightly different question (seen once in
  13 held-out cases for the baseline). The figure is still real and cited, and the UI shows the series and period, but the
  user has to notice. Plan–question consistency checks are planned.
- **Spanish only** (Argentine usage); no multi-turn context.
- **Real-model results pending** (`[[ ]]`). Self-hosted Apertus not tested (no GPU).
- **Not tested:** load beyond a single user, accessibility audit of the UI.

## 7. Reproducibility

From `track_2b/`: `make run` (UI at http://localhost:8080), `make test`, `make eval`, `make eval-heldout`,
`make offline-proof`. STUB and off modes are deterministic: the reports in `docs/eval/` regenerate byte-identically.
Verified on Docker Engine 29.8.2 (Linux x86-64), image based on `python:3.12-slim`, CPU only, no GPU. Hosts without Docker
can use `make run-local` / `test-local` / `eval-local` (Python ≥ 3.10). Real runs: set `LLM_BASE_URL`, `LLM_NAME`,
`LLM_API_KEY`, then `LLM_MODE=record make eval` (stores outputs for offline replay). Exact commit: `[[COMMIT]]`.

## 8. Next steps

Real Apertus runs (8B, then 70B) with prompt iteration on the held-out set; plan–question consistency checks; more series
(labour market, GDP, provincial data); a second statistics office (for example BFS / opendata.swiss) through the same
catalog format, to show portability; a measured self-hosted Apertus deployment on an isolated GPU node.

## 9. Disclosures

- **AI-assisted development (plain statement).** This project was built with **closed-weights (proprietary) AI coding
  agents**, directed and reviewed by the entrant. They wrote the code, tests, documentation and this report. They are not
  part of the submitted system, are not called at runtime, and are not used for evaluation. The only runtime model is
  Apertus. (The rules mention open-weights models used to support development; ours were closed-weights, so we state
  their role here explicitly.)
- **STUB.** Until real runs are recorded, the STUB replays outputs written by the build agent. It is labelled STUB in the
  UI, the evaluation reports and this report.
- **Reuse.** The LLM gateway was ported to Python from an earlier prototype by the same team, written on 2 Oct 2026.
  Cached raw downloads and aggregation definitions come from the team's open-data pipeline (1–2 Oct 2026), re-verified at
  build time. The template files come from `HackApertus/project-template` @ `7f23822`. Details: `docs/DISCLOSURE.md`.
- **Data** is third-party CC BY 4.0 with attribution (Section 4).

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced. Code: Apache-2.0 (`LICENSE`).
Data in `data/`: third-party, CC BY 4.0 (original publishers).

## References

- Apertus v1.5 model card: huggingface.co/swiss-ai/Apertus-v1.5-8B
- Series de Tiempo API (datos.gob.ar): datosgobar.github.io/series-tiempo-ar-api
- INDEC, Índice de precios al consumidor (monthly technical reports), indec.gob.ar
- Hack Apertus project template: github.com/HackApertus/project-template (commit `7f23822`)
