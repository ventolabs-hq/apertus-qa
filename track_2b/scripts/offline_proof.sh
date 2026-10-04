#!/bin/bash
# Air-gap proof for apertus-qa:local. Everything below runs with --network none.
# Hygiene: fail fast on any step; always remove the ephemeral aqa-offline container.
set -eu
IMG=${IMAGE:-apertus-qa:local}
cleanup() { docker rm -f aqa-offline >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "\$ docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'"
docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'
echo "\$ docker image inspect $IMG --format '{{.Id}}'"
docker image inspect $IMG --format '{{.Id}}'
echo
echo "## 1. Interfaces inside a --network none container (only loopback expected)"
echo "\$ docker run --rm --network none $IMG python -c \"import socket;print(sorted(n for _,n in socket.if_nameindex()))\""
IFACES=$(docker run --rm --network none $IMG python -c "import socket;print(sorted(n for _,n in socket.if_nameindex()))")
echo "$IFACES"
test "$IFACES" = "['lo']"
echo
echo "## 2. Egress and DNS are impossible"
P='import socket,sys
bad=0
for h,p in [("1.1.1.1",443),("8.8.8.8",53)]:
    try:
        socket.create_connection((h,p),timeout=3); print(h,p,"CONNECTED (unexpected)"); bad=1
    except OSError as e: print(h,p,"->",type(e).__name__,e)
try:
    socket.getaddrinfo("api.github.com",443); print("DNS resolved (unexpected)"); bad=1
except OSError as e: print("DNS api.github.com ->",type(e).__name__,e)
sys.exit(bad)'
echo "\$ docker run --rm --network none $IMG python -c '<connect 1.1.1.1:443, 8.8.8.8:53; resolve api.github.com>'"
docker run --rm --network none $IMG python -c "$P"
echo
echo "## 3. Full app served and queried inside the same air-gapped container"
cleanup
echo "\$ docker run -d --name aqa-offline --network none $IMG   # default CMD: serve on :8080"
docker run -d --name aqa-offline --network none $IMG >/dev/null
sleep 4
Q='import json,urllib.request as u,sys
h=json.load(u.urlopen("http://127.0.0.1:8080/health")); print("health:",{k:h[k] for k in ("ok","model_mode","entries","snapshot")})
assert h.get("ok") is True
assert h.get("model_mode") in ("stub","off","real","record")
for q in ["¿Cuál fue la inflación mensual de agosto de 2026?","¿Cuál será el dólar blue en diciembre?"]:
    r=u.Request("http://127.0.0.1:8080/api/ask",data=json.dumps({"q":q}).encode(),headers={"Content-Type":"application/json"})
    d=json.load(u.urlopen(r)); print("Q:",q); print("  refused:",d["refused"],"| answer:",d["answer"]); print("  cite:",(d.get("citation_text") or "-")[:120])
    assert "answer" in d'
echo "\$ docker exec aqa-offline python -c '<GET /health; POST /api/ask x2>'"
docker exec aqa-offline python -c "$Q"
# STUB hygiene: default image mode is stub; confirm the UI source carries the DEMO STUB banner marker.
echo "\$ docker exec aqa-offline python -c '<check STUB banner marker in UI HTML>'"
docker exec aqa-offline python -c "from pathlib import Path; t=Path('/app/src/apertus_qa/web/index.html').read_text(); assert 'STUB DEMO' in t and 'id=\"stubBanner\"' in t; print('UI STUB banner marker: OK')"
echo "\$ docker inspect aqa-offline --format '{{.HostConfig.NetworkMode}}'"
NET=$(docker inspect aqa-offline --format '{{.HostConfig.NetworkMode}}')
echo "$NET"
test "$NET" = "none"
cleanup
echo
echo "## 4. Test suite and both eval sets, no network"
echo "\$ make test   (docker run --rm --network none ... unittest)"
OUT=$(docker run --rm --network none $IMG python -m unittest discover -s tests -t . 2>&1)
echo "$OUT" | tail -3
N=$(echo "$OUT" | sed -n 's/^Ran \([0-9]*\) tests.*/\1/p'); test "${N:-0}" -ge 35   # at least the original 35
echo "$OUT" | grep -q '^OK$'
for s in main heldout; do for m in stub off; do
  echo "\$ docker run --rm --network none -e LLM_MODE=$m $IMG python -m eval.run_eval --mode $m --set $s --out /tmp/x"
  docker run --rm --network none -e LLM_MODE=$m $IMG python -m eval.run_eval --mode $m --set $s --out /tmp/x | python3 -c "
import sys,json
t=sys.stdin.read(); j=json.loads(t[t.index('{'):])   # the summary is the only JSON printed
print('  ',{k:j[k] for k in ('set','overall_ok','refusal_correct','false_refusals','grounding_violations','official_checks_ok','label','mode') if k in j})
assert j.get('grounding_violations', 1) == 0
if j.get('mode') == 'stub':
    assert 'STUB' in (j.get('label') or '') and 'not real Apertus' in (j.get('label') or '')
if j.get('set') == 'main':
    assert j.get('overall_ok') == 31
"
done; done
echo
echo "## 5. The ONLY network use is the model call: real mode with no network degrades safely"
echo "\$ docker run --rm --network none -e LLM_MODE=real -e LLM_BASE_URL=https://example.invalid/v1 -e LLM_NAME=placeholder -e LLM_API_KEY=dummy -e LLM_TIMEOUT_S=3 $IMG python -m apertus_qa ask --json '¿Cuál fue la inflación mensual de agosto de 2026?'"
docker run --rm --network none -e LLM_MODE=real -e LLM_BASE_URL=https://example.invalid/v1 -e LLM_NAME=placeholder -e LLM_API_KEY=dummy -e LLM_TIMEOUT_S=3 $IMG python -m apertus_qa ask --json '¿Cuál fue la inflación mensual de agosto de 2026?' 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read()
d=json.loads(t)
print('  answer:',d['answer']); print('  trace:',json.dumps(d.get('trace'),ensure_ascii=False)[:400])
assert d.get('answer')
tr=d.get('trace') or {}
assert (tr.get('router') or {}).get('reason') == 'network_error' or (tr.get('router') or {}).get('mode') == 'fallback'
"
echo
echo "## 6. Recorded REAL Apertus outputs replay with no network (LLM_MODE=replay; separate file, never loaded by the STUB)"
if [ -f src/apertus_qa/replay/apertus_real.json ] && [ -f docs/eval/eval_main_record.json ]; then
  for s in main heldout; do
    echo "\$ docker run --rm --network none -e LLM_MODE=replay $IMG python -m eval.run_eval --mode replay --set $s --out /tmp/x"
    docker run --rm --network none -e LLM_MODE=replay $IMG sh -c "python -m eval.run_eval --mode replay --set $s --out /tmp/x >/dev/null && cat /tmp/x/eval_${s}_replay.json" | python3 -c "
import sys,json
rep=json.load(sys.stdin); rec=json.load(open('docs/eval/eval_${s}_record.json'))
a,b=rep['summary'],rec['summary']
print('  ',{k:a[k] for k in ('set','overall_ok','grounding_violations','router_model','phrase_model','label','model') if k in a} if 'set' in a else {k:a[k] for k in ('overall_ok','grounding_violations','router_model','phrase_model','label','model')})
same=[(x['id'],x['answer'],x['ok'],x['router'],x['phrase']) for x in rep['rows']]==[(x['id'],x['answer'],x['ok'],x['router'],x['phrase']) for x in rec['rows']]
print('   identical to the recorded real run (answers, scores, router/phrasing modes):', same)
assert same and a['overall_ok']==b['overall_ok'] and a['grounding_violations']==0
"
  done
else
  echo "  (no replay file / recorded run in this checkout: skipped)"
fi

echo
echo "offline-proof: OK (air-gap + STUB UI marker + tests/evals + safe real-mode fallback)"
