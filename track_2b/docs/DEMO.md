# Demo video plan (≤ 2:00): shot list and caption script

**Status:** plan only. Nothing has been recorded. Record only after the real Apertus run, so the trace and eval shots show
real model output. A STUB recording would need a visible "STUB" label in every model shot.

**Format.** Screen capture of the local app and a terminal only. No face, no voice, no music with lyrics. English
captions burned in (the UI is in Spanish, so captions translate the question and answer). 1920×1080, 30 fps, MP4 (H.264),
target 1:50–1:58. Captions: white text with a dark box, bottom third, ≥ 2.5 s each, ≤ 2 lines of about 42 characters.
**Team:** Vento Labs. **Hosting:** YouTube, **unlisted** (the rules ask only for a URL and no visibility requirement was
found; re-check the submission form before upload). If unlisted is not accepted, upload as public on the experiment's
YouTube channel.

**Capture setup (no accounts, no network needed for the app):** run `make run` (or the image with `--network none` for
the terminal shots); use the box browser at `http://localhost:8080`; a clean terminal with a large font. Hide bookmarks,
tabs and notifications, and show no personal names, emails or keys anywhere. In real mode, check that `LLM_API_KEY` is
never on screen (do not run `env` or `cat .env`).

## Shot list

| # | Time | Screen | Action |
|---|---|---|---|
| 1 | 0:00–0:07 | Title card (static HTML or a frame from the UI header) | Hold |
| 2 | 0:07–0:24 | UI, empty | Type "¿Cuál fue la inflación mensual de agosto de 2026?" → Enter → answer, citation line, figures table |
| 3 | 0:24–0:40 | Same answer, expand the details under it | Mode badges ("planificación: llm", "redacción: llm") and the plan JSON from Apertus. Optionally cut to `prompts.py` to show the `{placeholder}` phrasing contract |
| 4 | 0:40–0:54 | UI | "¿Cuánto equivalen hoy 1.000 pesos de enero de 2020?" → adjusted amount + citation |
| 5 | 0:54–1:06 | UI | "¿Cuántos nacimientos hubo en 2024?" → "la serie llega a 2022" |
| 6 | 1:06–1:16 | UI | "¿Cuál será la inflación de diciembre de 2026?" → refusal; then "¿Conviene comprar dólares?" → refusal |
| 7 | 1:16–1:36 | Terminal | `make offline-proof` (sped up 4–6× with a visible "×5" tag): `['lo']`, `Network is unreachable`, eval summary lines |
| 8 | 1:36–1:48 | Terminal or editor | Real-mode run: eval summary with real Apertus numbers; then `docker-compose.airgap.yml` (`internal: true`) |
| 9 | 1:48–1:56 | End card | Hold |

## Caption script (English, burned in)

```text
1  0:00.0 → 0:03.5  Apertus QA — official statistics, answered and cited
2  0:03.5 → 0:07.0  Team Vento Labs · Hack Apertus 2026 · Track 2B
3  0:07.0 → 0:12.0  Q: "What was monthly inflation in August 2026?"
4  0:12.0 → 0:18.0  A: 1.7% vs July 2026, with source, series id, period and licence
5  0:18.0 → 0:24.0  Every number comes from a verified local snapshot of official data (INDEC, CC BY 4.0)
6  0:24.0 → 0:31.0  Apertus picks the series and the operation (a JSON plan)…
7  0:31.0 → 0:40.0  …and writes the sentence with placeholders. It never sees a figure, so it can't invent one.
8  0:40.0 → 0:47.0  Q: "What are 1,000 pesos of January 2020 worth today?"
9  0:47.0 → 0:54.0  Inflation adjustment computed by code, not by the model, and cited
10 0:54.0 → 1:00.0  Q: "How many births were there in 2024?"
11 1:00.0 → 1:06.0  The series ends in 2022, so it says so instead of guessing
12 1:06.0 → 1:11.0  Q: "What will inflation be in December 2026?" → no forecasts
13 1:11.0 → 1:16.0  Q: "Should I buy dollars?" → no financial advice
14 1:16.0 → 1:24.0  Air-gapped: the container runs with no network at all (--network none)
15 1:24.0 → 1:30.0  No internet, no DNS: only the loopback interface
16 1:30.0 → 1:36.0  App, 35 tests and the full evaluation still pass offline
17 1:36.0 → 1:42.0  With real Apertus: [[A8_MAIN]] main set · [[A8_HO]] held-out · 0 invented numbers
18 1:42.0 → 1:48.0  The only network call is the model: point it at CSCS or a self-hosted Apertus
19 1:48.0 → 1:56.0  Open source · Code Apache-2.0 · Data CC BY 4.0 (INDEC and others) · [[REPO_URL]]
```

Notes:
- Caption 4 must match the figure on screen (currently 1.7% from the snapshot to Aug 2026).
- Caption 17 is a placeholder. If real numbers are not available, replace it with "Evaluation shown: no-model baseline"
  and do not show STUB numbers as model results.
- Production (later round): record with the box's screen recorder (ffmpeg x11grab on the agent's own display), cut and
  caption with ffmpeg (`subtitles=` filter from an `.srt` generated from the table above). No external services.
