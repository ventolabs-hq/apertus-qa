# Demo video: real Apertus cut

- File: `apertus-qa-demo.mp4`, 1920×1080, H.264 30 fps, silent AAC track, **112.0 s** (1:52), 2.9 MB
- sha256: `38ec7372efb109129061c9c067e39bc88fe30fc728922346102092c626c6ea01`
- Recorded 2026-10-04 09:57–09:58 ART, headless, with `scripts/record_demo.mjs`: Chrome DevTools Protocol screenshots
  of the running app plus ffmpeg concat. Follows the real-Apertus appendix of `docs/DEMO.md`. No narration; the
  captions are an on-page overlay.
- App: `LLM_MODE=real`, model `swiss-ai/Apertus-v1.5-70B`. All five questions were asked live during the take, and
  the answers shown are the endpoint's real answers, unedited (`timeline.json` → `answers`). The inflation and
  1.000-pesos answers fell back to the safe template (`invalid:digits_in_text`), so caption 7b is shown. The 2015
  population answer is Apertus' own wording. The forecast and advice questions were refused.
- Terminal shots: the `make offline-proof` transcript (shown at ×5) and the summary of
  `docs/eval/eval_{main,heldout}_record.json`.
- Leak checks on the final MP4, all PASS:
  - OCR (tesseract) of all 144 captured stills plus 56 frames sampled every 2 s: no key, no key fragment of 10+ characters,
    no base URL or host, 0 scope-term hits.
  - `scripts/leak_check.py --path` on the MP4, `timeline.json` and the OCR text.
  - Audio: −91 dB (digital silence). The Whisper (base) transcript contains only the usual silence hallucination
    ("You" ×4); the leak check on it is PASS.
- The secrets env was sourced silently in a subshell and passed to Docker by variable name only. No terminal on screen
  shows env, keys or the endpoint.

Reproduce (app running on :8080): `PROOF_LOG=<offline-proof transcript> node --experimental-websocket scripts/record_demo.mjs http://127.0.0.1:8080 /tmp/aqa-demo`
(drop the flag on Node ≥ 22).
