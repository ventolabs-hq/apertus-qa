# Demo video plan (≤ 2:00): shot list and caption script

**Recording readiness: STUB DEMO only.** Nothing has been recorded yet. This document is the shot list for a
**clearly labelled STUB** screen-capture (agent-written replay, not real Apertus). Do **not** present STUB numbers as
model results. A real-Apertus cut is deferred until CSCS key + live eval exist (see appendix); placeholders like
`[[A8_MAIN]]` must stay empty until then — **do not invent live results**.

**Format.** Screen capture of the local app and a terminal only. No face, no voice, no music with lyrics. English
captions burned in (the UI is in Spanish, so captions translate the question and answer). 1920×1080, 30 fps, MP4 (H.264),
target 1:50–1:58. Captions: white text with a dark box, bottom third, ≥ 2.5 s each, ≤ 2 lines of about 42 characters.
**Team:** Vento Labs. **Hosting:** YouTube, **unlisted** (the rules ask only for a URL and no visibility requirement was
found; re-check the submission form before upload). If unlisted is not accepted, upload as public on the experiment's
YouTube channel.

**STUB labels (mandatory on every model shot).** The UI shows a top banner
`STUB DEMO — respuestas grabadas … · NO es salida real de Apertus`, a yellow `modelo: STUB (…)` badge, amber
`planificación: stub` / `redacción: stub` badges, and a per-answer line `STUB · no es salida real de Apertus`.
If any of those is missing on camera, stop and fix before cutting.

**Capture setup (no accounts, no network needed for the app):**
```bash
cd track_2b
LLM_MODE=stub make run RUN_NET="--network host -e HOST=127.0.0.1"   # this box (no bridge); judges: LLM_MODE=stub make run
```
Open `http://127.0.0.1:8080` in the box browser. Confirm the STUB banner is visible **before** shot 1. Use a clean
terminal with a large font. Hide bookmarks, tabs and notifications; show no personal names, emails or keys. Never run
`env` or `cat .env` on camera.

## Shot list (STUB DEMO — recordable now)

| # | Time | Screen | Action |
|---|---|---|---|
| 1 | 0:00–0:08 | Title card + UI with STUB banner visible | Hold; banner and yellow STUB badge must be readable |
| 2 | 0:08–0:24 | UI (STUB) | Type "¿Cuál fue la inflación mensual de agosto de 2026?" → Enter → answer 1,7 %, citation, figures table; STUB tag under the answer |
| 3 | 0:24–0:40 | Same answer, expand details | Badges show `planificación: stub` / `redacción: stub` (not "llm") and the plan JSON. Optional cut to `prompts.py` `{placeholder}` contract |
| 4 | 0:40–0:54 | UI (STUB) | "¿Cuánto equivalen hoy 1.000 pesos de enero de 2020?" → adjusted amount + citation |
| 5 | 0:54–1:06 | UI (STUB) | "¿Cuántos nacimientos hubo en 2024?" → "la serie llega a 2022" |
| 6 | 1:06–1:16 | UI (STUB) | "¿Cuál será la inflación de diciembre de 2026?" → refusal; then "¿Conviene comprar dólares?" → refusal |
| 7 | 1:16–1:36 | Terminal | `make offline-proof` (sped up 4–6× with a visible "×5" tag): `['lo']`, `Network is unreachable`, eval summary lines |
| 8 | 1:36–1:48 | Terminal | STUB eval summary only: main **31/31**, held-out **8/13**, grounding 0 — label on screen: `STUB (canned replay, not real Apertus)`. Then flash `docs/deploy/docker-compose.airgap.yml` (`internal: true`) |
| 9 | 1:48–1:56 | End card | Hold; include "STUB DEMO · real Apertus pending CSCS key" |

## Caption script (English, burned in) — STUB cut

```text
1  0:00.0 → 0:04.0  Apertus QA — STUB DEMO (canned replay, not real Apertus)
2  0:04.0 → 0:08.0  Team Vento Labs · Hack Apertus 2026 · Track 2B
3  0:08.0 → 0:13.0  Q: "What was monthly inflation in August 2026?"
4  0:13.0 → 0:19.0  A: 1.7% vs July 2026, with source, series id, period and licence
5  0:19.0 → 0:24.0  Every number comes from a verified local snapshot (INDEC, CC BY 4.0)
6  0:24.0 → 0:31.0  STUB replay picks the series and the operation (a JSON plan)…
7  0:31.0 → 0:40.0  …and writes the sentence with placeholders. Figures come only from code.
8  0:40.0 → 0:47.0  Q: "What are 1,000 pesos of January 2020 worth today?"
9  0:47.0 → 0:54.0  Inflation adjustment computed by code, not by the model, and cited
10 0:54.0 → 1:00.0  Q: "How many births were there in 2024?"
11 1:00.0 → 1:06.0  The series ends in 2022, so it says so instead of guessing
12 1:06.0 → 1:11.0  Q: "What will inflation be in December 2026?" → no forecasts
13 1:11.0 → 1:16.0  Q: "Should I buy dollars?" → no financial advice
14 1:16.0 → 1:24.0  Air-gapped: the container runs with no network at all (--network none)
15 1:24.0 → 1:30.0  No internet, no DNS: only the loopback interface
16 1:30.0 → 1:36.0  App, 35 tests and the full evaluation still pass offline
17 1:36.0 → 1:42.0  STUB eval (not Apertus): 31/31 main · 8/13 held-out · 0 invented numbers
18 1:42.0 → 1:48.0  Real Apertus is a drop-in later: point LLM_* at CSCS or self-hosted
19 1:48.0 → 1:56.0  Open source · Apache-2.0 · Data CC BY 4.0 · STUB DEMO · [[REPO_URL]]
```

Notes:
- Caption 4 must match the figure on screen (currently 1.7% from the snapshot to Aug 2026).
- Caption 17 uses the **committed STUB** scores from `docs/eval/` (`STUB (canned replay, not real Apertus)`). Never swap in
  made-up "live" numbers. When real Apertus exists, replace this caption with the appendix version and re-record shot 8.
- Production (later round): record with the box's screen recorder (ffmpeg x11grab on the agent's own display), cut and
  caption with ffmpeg (`subtitles=` filter from an `.srt` generated from the table above). No external services.

## Shot readiness checklist (STUB)

- [ ] `LLM_MODE=stub make run` (or host equivalent); `/health` → `model_mode: stub`
- [ ] Top STUB banner visible at 1920×1080 without cropping
- [ ] Yellow STUB model badge + per-answer STUB tag visible on shots 2–6
- [ ] Expanded details show `planificación: stub` / `redacción: stub` (not `llm`)
- [ ] Shot 7: `make offline-proof` completes; only `lo`; egress/DNS fail; 35 tests OK
- [ ] Shot 8: on-screen text says STUB / not real Apertus; figures match `docs/eval/eval_*_stub.md`
- [ ] No secrets, no `.env`, no personal identifiers, no invented live-Apertus claims
- [ ] Captions match the STUB script above; title/end cards say STUB DEMO

## Appendix — real Apertus cut (NOT ready; do not record yet)

Record only after a real CSCS (or self-hosted) run and filled `[[REAL_RESULTS]]` in the report.

| # | Change vs STUB cut |
|---|---|
| 1 / banner | Remove STUB banner; show real model id badge |
| 3 | Badges may show `planificación: llm` / `redacción: llm` from the live gateway |
| 8 | Replace STUB summary with real numbers; fill captions 17: `[[A8_MAIN]]` / `[[A8_HO]]` |
| End | Drop "STUB DEMO · real Apertus pending" |

Until then: keep every public or draft cut labelled STUB, and leave `[[A8_*]]` / `[[REAL_RESULTS]]` unfilled.
