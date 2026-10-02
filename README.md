# Apertus QA — grounded Spanish Q&A over official statistics

Hack Apertus 2026 · **Track 2B — Own project** · project root: [`track_2b/`](track_2b/)

Ask in Spanish ("¿Cuál fue la inflación mensual de agosto de 2026?") and get a one-sentence answer where **every number
comes from a verified local snapshot of official open data** (INDEC and other agencies via datos.gob.ar, CC BY 4.0), with
the series id, period and licence cited. Apertus plans the query and phrases the answer; it never produces or even sees a
figure. If the snapshot can't answer, it says so.

```bash
cd track_2b
make run            # Docker; then open http://localhost:8080
make test           # offline unit + integration tests (container runs with --network none)
make eval           # scores grounded answers on 31 Spanish questions (+ `make eval-heldout`, 13 paraphrases)
```

Model configuration (template convention): `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` — any OpenAI-compatible endpoint
(CSCS-hosted Apertus, or self-hosted vLLM/Ollama). Without them the app runs in clearly labelled **STUB** mode.

- Architecture, evaluation, limitations: [`track_2b/technical_report.md`](track_2b/technical_report.md)
- Air-gapped / sovereign deployment: [`track_2b/docs/OFFLINE.md`](track_2b/docs/OFFLINE.md)
- Data sources and licences: [`track_2b/docs/DATA.md`](track_2b/docs/DATA.md)
- Reuse and AI-assistance disclosure: [`track_2b/docs/DISCLOSURE.md`](track_2b/docs/DISCLOSURE.md)

Created from [`HackApertus/project-template`](https://github.com/HackApertus/project-template) (commit `7f23822`); the
other track directories were deleted as the template instructs. Code: Apache-2.0 (`LICENSE`). Docs: CC-BY-4.0. Data: CC BY 4.0
from the original publishers (attribution in `docs/DATA.md`).
