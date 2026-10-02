# Technical report — Apertus QA (DRAFT, round 1)

> Draft written at the first checkpoint (2 Oct 2026). Numbers marked STUB come from replayed, agent-written model outputs,
> not from Apertus. They will be replaced by real Apertus runs once the CSCS key is available.

- **Track:** `Track 2B — Apertus QA: grounded Spanish Q&A over official statistics`
- **Event:** Online
- **Team:** `TBD`
- **Demo:** `TBD (≤ 2 min, screen capture + captions)`

## 1. Summary

Citizens, journalists and civil servants ask statistical questions in natural language, and general-purpose chatbots answer
with plausible but unsourced or wrong figures. Apertus QA answers Spanish questions over a local, licence-checked snapshot of
official Argentine open data (47 series/tables: prices, wages, population, births, trade, tourism, energy, oil, subway,
flights, road deaths). Apertus does two narrow jobs — choose the series and operation, and phrase the answer with
placeholders — while a deterministic data layer computes every number and code attaches the citation. Everything except the
model call runs offline; the model endpoint can be a self-hosted Apertus inside an air-gapped network. Round-1 result (STUB):
31/31 on the main eval set, 0 grounding violations; held-out paraphrases 8/13 for the no-model baseline (to be measured with Apertus).

## 2. Architecture

```
question ─▶ [P1 router: Apertus] ─▶ plan JSON ─▶ validator (catalog ids, periods, ops, amount ∈ question)
                 │ invalid/timeout/no model                       │ valid
                 └──▶ rules router (fallback/baseline) ───────────┤
                                                                  ▼
                              deterministic ops over data/snapshot (sha256 + licence verified at start)
                                                                  │ figures + placeholder slots + citations
                                                                  ▼
             [P2 phrasing: Apertus, sees placeholders only, never numbers] ─▶ validator (no digits/number words,
                 │ invalid/timeout/no model                                   known placeholders, banned words)
                 └──▶ template ───────────────────────────────────────────────┤
                                                                              ▼
                                      render slots ─▶ grounding re-check ─▶ answer + citations (UI / JSON API / CLI)
```

Single stateless Python process (stdlib only), Spanish web UI with no external assets, JSON API (`/api/ask`, `/api/catalog`,
`/health`), CLI. LLM gateway: never throws; budgets, timeout, circuit breaker, fallback with machine-readable reason.

### Target architecture (mandatory)

**b) Air-gapped** (also a and c). Build time: base image pull only (no pip). Runtime: no external dependency except
`LLM_BASE_URL`, which can point to a self-hosted Apertus in the same isolated network. See `docs/OFFLINE.md`.

## 3. Use of Apertus

- **Model:** `swiss-ai/Apertus-v1.5-8B` (70B optional), via the CSCS free inference API or self-hosted vLLM.
- **How it is used:** inference; tool-use-style planning (structured JSON plan) + constrained generation (placeholder phrasing).
- **Where it runs:** hosted endpoint (CSCS) or local weights; OpenAI-compatible `/chat/completions`, temperature 0.
- Prompts: `src/apertus_qa/prompts.py`. No other model is used at runtime or for evaluation.

## 4. Data

CC BY 4.0 datasets only, from datos.gob.ar / apis.datos.gob.ar (INDEC, Ministerio de Economía, Secretaría de Energía,
CAMMESA, Subsecretaría de Turismo, DEIS/Ministerio de Salud, ANAC, SNIC/Ministerio de Seguridad). Microdata are reduced to
aggregates; no personal data in the repository. Full table: `docs/DATA.md`.

## 5. Evaluation

Task: Spanish questions with expected answers computed independently from the snapshot (`src/eval/make_expected.py`);
IPC answers additionally cross-checked against INDEC's published one-decimal figures. Metrics: decision (answer vs refuse),
value match, citation (series + period), grounding (every number in the text comes from a computed figure).

| Setup | Set | Overall | Answers | Refusals | Grounding violations |
|----------|--------|--------|--------|--------|--------|
| No-model baseline (rules + templates) | main (31) | 31/31 | 23/23 | 8/8 | 0 |
| STUB replay (not Apertus) | main (31) | 31/31 | 23/23 | 8/8 | 0 |
| No-model baseline | held-out paraphrases (13) | 8/13 | 6/11 | 2/2 | 0 |
| Apertus 8B | main / held-out | TBD | TBD | TBD | TBD |

Caveat: the rules router was written while looking at the main set, so its 31/31 is not a blind score; the held-out set is
the fair baseline.

## 6. Limitations

Snapshot coverage is fixed (47 series/tables); many official statistics (unemployment, poverty, GDP) are not included yet.
A wrong plan that still validates yields a correct-but-irrelevant cited figure (seen in the baseline on 1/13 held-out
questions). The real-model numbers are pending.

## 7. Reproducibility

`make run` / `make test` / `make eval` from `track_2b/`. Deterministic in STUB/off modes. Snapshot sha256 values in
`data/snapshot/catalog.json`. Real runs: `LLM_MODE=record make eval` stores the model outputs for offline replay.

## 8. Next steps

Real Apertus runs (8B and 70B), prompt iteration on the held-out set, more series (labour market, GDP), BFS/opendata.swiss
adapter to show portability to another national statistics office.

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References

- Apertus v1.5: huggingface.co/swiss-ai/Apertus-v1.5-8B · Series de Tiempo API: datosgobar.github.io/series-tiempo-ar-api
