// Headless demo recorder (DEMO.md appendix: real-Apertus cut). Chrome DevTools Protocol (Node >= 22 global WebSocket, or Node 20 with --experimental-websocket;
// zero deps) drives the running app; each step is captured with Page.captureScreenshot and held for a set duration;
// ffmpeg's concat demuxer turns the stills into a constant 30 fps H.264 MP4 with a silent AAC track. Captions are an
// overlay drawn in the page at capture time (burned in). The recorder never sees secrets: it only talks to the app URL.
//   node scripts/record_demo.mjs <appUrl> <outDir> [--probe]
// Inputs: docs/eval/eval_{main,heldout}_record.json (verified numbers) and an offline-proof transcript at $PROOF_LOG.
import { spawn, execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const [APP = 'http://127.0.0.1:8080', OUTARG = '/tmp/aqa-demo', ...flags] = process.argv.slice(2);
const PROBE = flags.includes('--probe');
const OUT = path.resolve(OUTARG); const FR = path.join(OUT, 'frames'); fs.rmSync(FR, { recursive: true, force: true }); fs.mkdirSync(FR, { recursive: true });
const W = 1920, H = 1080, CHROME = process.env.CHROME || '/usr/bin/google-chrome';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------- CDP ----------
const port = 9300 + Math.floor(Math.random() * 300);
const prof = fs.mkdtempSync(path.join(os.tmpdir(), 'aqa-demo-'));
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${prof}`, '--no-first-run', '--no-sandbox',
  '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1', `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 80 && !target; i++) { try { target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((x) => x.type === 'page'); } catch { /* starting */ } if (!target) await sleep(250); }
if (!target) throw new Error('chrome did not start');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
let seq = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { const { res, rej } = pending.get(d.id); pending.delete(d.id); d.error ? rej(new Error(d.error.message)) : res(d.result); } };
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++seq; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(`${expr.slice(0, 90)}: ${r.exceptionDetails.text}`); return r.result.value; };
const waitFor = async (expr, ms = 60000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr)) return; await sleep(100); } throw new Error(`timeout: ${expr}`); };
await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
async function go(url) { await send('Page.navigate', { url }); await sleep(300); await waitFor('document.readyState === "complete"'); await sleep(500); }

// ---------- timeline ----------
const timeline = []; let n = 0; let caption = '';
const OVERLAY = `(() => { let c = document.getElementById('demoCap'); if (!c) { c = document.createElement('div'); c.id = 'demoCap';
  Object.assign(c.style, { position: 'fixed', left: '50%', bottom: '54px', transform: 'translateX(-50%)', maxWidth: '1500px', zIndex: 99999,
    background: 'rgba(10,10,10,.82)', color: '#fff', font: '600 38px/1.3 DejaVu Sans, sans-serif', padding: '14px 28px', borderRadius: '10px',
    textAlign: 'center', pointerEvents: 'none' }); document.body.appendChild(c); } return true; })()`;
async function cap(text) { caption = text; }
async function shot(sec) {
  await ev(OVERLAY);
  await ev(`(() => { const c = document.getElementById('demoCap'); c.textContent = ${JSON.stringify(caption)}; c.style.display = ${JSON.stringify(caption)} ? 'block' : 'none'; return true; })()`);
  const { data } = await send('Page.captureScreenshot', { format: 'png' });
  const f = path.join(FR, `f${String(n++).padStart(4, '0')}.png`); fs.writeFileSync(f, Buffer.from(data, 'base64'));
  timeline.push({ f, sec, caption });
}
const total = () => timeline.reduce((a, b) => a + b.sec, 0);

// ---------- app helpers ----------
const ZOOM = `document.querySelector('main').style.zoom = '1.45'; true`;
async function typeAndAsk(q, typeSec = 2.0) {
  await ev(`(() => { const i = document.querySelector('#q'); i.value = ''; i.focus(); document.querySelector('#out').innerHTML = ''; return true; })()`);
  const steps = Math.min(q.length, 24);
  for (let k = 1; k <= steps; k++) { const part = q.slice(0, Math.round(q.length * k / steps)); await ev(`document.querySelector('#q').value = ${JSON.stringify(part)}; true`); await shot(typeSec / steps); }
  const t0 = Date.now();
  await ev(`(() => { document.querySelector('#f').requestSubmit(); return true; })()`);
  await waitFor(`!!document.querySelector('#out .ans')`, 90000);
  await sleep(300);
  const ans = await ev(`({ answer: document.querySelector('#out .ans').textContent, cite: (document.querySelector('#out .cite:not([style])')||{}).textContent || '', modes: document.querySelector('#out details summary').textContent })`);
  ans.ms = Date.now() - t0; ans.q = q; return ans;
}

// ---------- cards & terminal pages (local HTML) ----------
const card = (title, sub) => `data:text/html;charset=utf-8,${encodeURIComponent(`<html><body style="margin:0;background:#14213d;color:#fff;font-family:DejaVu Sans,sans-serif;display:flex;height:100vh;align-items:center;justify-content:center;flex-direction:column"><div style="font-size:84px;font-weight:700">${title}</div><div style="font-size:40px;margin-top:28px;opacity:.85;text-align:center;line-height:1.5">${sub}</div></body></html>`)}`;
const term = (lines, tag = '') => `data:text/html;charset=utf-8,${encodeURIComponent(`<html><body style="margin:0;background:#101418;color:#d8dee9;font:26px/1.42 DejaVu Sans Mono,monospace;padding:40px 60px;height:100vh;box-sizing:border-box;overflow:hidden">${tag ? `<div style="position:fixed;top:30px;right:50px;background:#ebcb8b;color:#111;font:700 34px DejaVu Sans;padding:6px 18px;border-radius:8px">${tag}</div>` : ''}<pre id="t" style="margin:0;white-space:pre-wrap">${lines.map((l) => l.replace(/&/g, '&amp;').replace(/</g, '&lt;')).join('\n')}</pre></body></html>`)}`;

const log = { app: APP, answers: [] };
// 1. title + UI
await go(card('Apertus QA', 'Grounded Spanish answers over official Argentine statistics<br>Team Vento Labs · Hack Apertus 2026 · Track 2B'));
await cap('Apertus QA — live Apertus v1.5-70B on the CSCS endpoint'); await shot(4);
await go(APP); await ev(ZOOM); await waitFor(`document.querySelector('#st').textContent.includes('modelo')`);
log.badge = await ev(`document.querySelector('#st').textContent`);
await cap('Team Vento Labs · Hack Apertus 2026 · Track 2B'); await shot(4);
if (PROBE) { fs.writeFileSync(path.join(OUT, 'probe.json'), JSON.stringify(log, null, 1)); ws.close(); chrome.kill(); process.exit(0); }
// 2-3. inflation question + details
await cap('Q: "What was monthly inflation in August 2026?"');
let a = await typeAndAsk('¿Cuál fue la inflación mensual de agosto de 2026?'); log.answers.push(a);
await shot(3);
await cap('A: 1.7% vs July 2026, with source, series id, period and licence'); await shot(6);
await cap('Every number comes from a verified local snapshot (INDEC, CC BY 4.0)'); await shot(5);
await ev(`(() => { document.querySelector('#out details').open = true; return true; })()`); await sleep(200);
await ev(`window.scrollTo(0, document.querySelector('#out details').getBoundingClientRect().top + scrollY - 220); true`);
await cap('Apertus picks the series and the operation (a JSON plan)…'); await shot(7);
const fallback = a.modes.includes('fallback');
await cap(fallback ? 'Model text rejected by a validator → safe template. No invented numbers.' : '…and writes the sentence with placeholders. Figures come only from code.'); await shot(9);
await ev('window.scrollTo(0,0); true');
// 4. adjustment
await cap('Q: "What are 1,000 pesos of January 2020 worth today?"');
a = await typeAndAsk('¿Cuánto equivalen hoy 1.000 pesos de enero de 2020?'); log.answers.push(a); await shot(3);
await cap('Inflation adjustment computed by code, not by the model, and cited'); await shot(7);
// 5. held-out paraphrase
await cap('Q: "How many people lived in the country in 2015?"');
a = await typeAndAsk('¿Cuánta gente vivía en el país en 2015?'); log.answers.push(a); await shot(2);
await cap("Rules alone can't parse this paraphrase; Apertus maps it to the population series"); await shot(6);
// 6. refusals
await cap('Q: "What will inflation be in December 2026?" → no forecasts');
a = await typeAndAsk('¿Cuál será la inflación de diciembre de 2026?', 1.5); log.answers.push(a); await shot(3.5);
await cap('Q: "Should I buy dollars?" → no financial advice');
a = await typeAndAsk('¿Conviene comprar dólares?', 1.0); log.answers.push(a); await shot(4);
// 7. offline proof (terminal transcript, sped up)
const proof = fs.readFileSync(process.env.PROOF_LOG, 'utf8').split('\n').filter((l) => !/^#\d+ |^\s*$/.test(l) || l.startsWith('## '));
const start = proof.findIndex((l) => l.startsWith('$ docker version'));
const P = proof.slice(start).map((l) => (l.length > 118 ? l.slice(0, 115) + '…' : l));
const caps7 = ['Air-gapped: the container runs with no network at all (--network none)', 'No internet, no DNS: only the loopback interface',
  'App, 41 tests and the full evaluation still pass offline', 'Recorded real outputs replay offline too (LLM_MODE=replay)'];
const pages = 8; const per = Math.ceil(P.length / pages);
for (let k = 0; k < pages; k++) {
  const upto = Math.min(P.length, (k + 1) * per); const view = P.slice(Math.max(0, upto - 24), upto);
  await go(term(['$ make offline-proof', ...view], '×5')); await cap(caps7[Math.min(3, Math.floor(k / 2))]); await shot(2.5);
}
// 8. verified eval summary
const S = (s) => JSON.parse(fs.readFileSync(path.join(ROOT, 'docs', 'eval', `eval_${s}_record.json`), 'utf8')).summary;
const m = S('main'), h = S('heldout');
log.eval = { main: m.overall_ok, heldout: h.overall_ok, gm: m.grounding_violations, gh: h.grounding_violations, p50: [m.latency_ms_p50, h.latency_ms_p50], model: m.model };
const L = [`$ python3 -c 'print summaries of docs/eval/eval_{main,heldout}_record.json'`, '',
  `label: ${m.label}    model: ${m.model}`, '',
  `set        overall   answers   refusals   false refusals   grounding violations   p50 latency`,
  `main       ${m.overall_ok}/${m.questions}     ${m.answer_correct}/${m.answerable}     ${m.refusal_correct}/${m.must_refuse}        ${m.false_refusals}                ${m.grounding_violations}                      ${(m.latency_ms_p50 / 1000).toFixed(1)} s`,
  `held-out   ${h.overall_ok}/${h.questions}     ${h.answer_correct}/${h.answerable}     ${h.refusal_correct}/${h.must_refuse}        ${h.false_refusals}                ${h.grounding_violations}                      ${(h.latency_ms_p50 / 1000).toFixed(1)} s`, '',
  `no-model baseline (rules only), held-out: 8/13      STUB replay (agent-written): 31/31 · 8/13`];
await go(term(L));
await cap(`Apertus v1.5-70B: ${m.overall_ok}/${m.questions} main · ${h.overall_ok}/${h.questions} held-out (rules alone: 8/13) · 0 invented numbers`); await shot(6);
await cap('~2.5 s per question · air-gapped by design: point LLM_* at a self-hosted Apertus'); await shot(6);
// 9. end card
await go(card('Apertus QA', 'Team Vento Labs<br>Open source · Apache-2.0 · Data CC BY 4.0 (INDEC, datos.gob.ar)'));
await cap('Open source · Apache-2.0 · Data CC BY 4.0'); await shot(8);

ws.close(); chrome.kill();
log.total_s = total();
fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify({ timeline: timeline.map((t) => ({ f: path.basename(t.f), sec: t.sec, caption: t.caption })), ...log }, null, 1));
const list = timeline.map((t) => `file '${t.f}'\nduration ${t.sec.toFixed(3)}`).join('\n') + `\nfile '${timeline.at(-1).f}'\n`;
fs.writeFileSync(path.join(OUT, 'concat.txt'), list);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(OUT, 'concat.txt'), '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
  '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-c:a', 'aac', '-b:a', '64k', '-t', log.total_s.toFixed(3), '-shortest', '-movflags', '+faststart',
  path.join(OUT, 'apertus-qa-demo.mp4')]);
console.log(JSON.stringify({ total_s: log.total_s, answers: log.answers.map((x) => ({ q: x.q, ms: x.ms, modes: x.modes, answer: x.answer.slice(0, 120) })), eval: log.eval, badge: log.badge }, null, 1));
