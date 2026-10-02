#!/bin/bash
# Air-gap proof for apertus-qa:local. Everything below runs with --network none.
set -u
IMG=${IMAGE:-apertus-qa:local}
echo "\$ docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'"
docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'
echo "\$ docker image inspect $IMG --format '{{.Id}}'"
docker image inspect $IMG --format '{{.Id}}'
echo
echo "## 1. Interfaces inside a --network none container (only loopback expected)"
echo "\$ docker run --rm --network none $IMG python -c \"import socket;print(sorted(n for _,n in socket.if_nameindex()))\""
docker run --rm --network none $IMG python -c "import socket;print(sorted(n for _,n in socket.if_nameindex()))"
echo
echo "## 2. Egress and DNS are impossible"
P='import socket
for h,p in [("1.1.1.1",443),("8.8.8.8",53)]:
    try:
        socket.create_connection((h,p),timeout=3); print(h,p,"CONNECTED (unexpected)")
    except OSError as e: print(h,p,"->",type(e).__name__,e)
try:
    socket.getaddrinfo("api.github.com",443); print("DNS resolved (unexpected)")
except OSError as e: print("DNS api.github.com ->",type(e).__name__,e)'
echo "\$ docker run --rm --network none $IMG python -c '<connect 1.1.1.1:443, 8.8.8.8:53; resolve api.github.com>'"
docker run --rm --network none $IMG python -c "$P"
echo
echo "## 3. Full app served and queried inside the same air-gapped container"
echo "\$ docker run -d --name aqa-offline --network none $IMG   # default CMD: serve on :8080"
docker run -d --name aqa-offline --network none $IMG >/dev/null && sleep 4
Q='import json,urllib.request as u
h=json.load(u.urlopen("http://127.0.0.1:8080/health")); print("health:",{k:h[k] for k in ("ok","model_mode","entries","snapshot")})
for q in ["¿Cuál fue la inflación mensual de agosto de 2026?","¿Cuál será el dólar blue en diciembre?"]:
    r=u.Request("http://127.0.0.1:8080/api/ask",data=json.dumps({"q":q}).encode(),headers={"Content-Type":"application/json"})
    d=json.load(u.urlopen(r)); print("Q:",q); print("  refused:",d["refused"],"| answer:",d["answer"]); print("  cite:",(d.get("citation_text") or "-")[:120])'
echo "\$ docker exec aqa-offline python -c '<GET /health; POST /api/ask x2>'"
docker exec aqa-offline python -c "$Q"
echo "\$ docker inspect aqa-offline --format '{{.HostConfig.NetworkMode}}'"
docker inspect aqa-offline --format '{{.HostConfig.NetworkMode}}'
docker rm -f aqa-offline >/dev/null
echo
echo "## 4. Test suite and both eval sets, no network"
echo "\$ make test   (docker run --rm --network none ... unittest)"
docker run --rm --network none $IMG python -m unittest discover -s tests -t . 2>&1 | tail -3
for s in main heldout; do for m in stub off; do
  echo "\$ docker run --rm --network none -e LLM_MODE=$m $IMG python -m eval.run_eval --mode $m --set $s --out /tmp/x"
  docker run --rm --network none -e LLM_MODE=$m $IMG python -m eval.run_eval --mode $m --set $s --out /tmp/x | python3 -c "
import sys,json,re
t=sys.stdin.read(); j=json.loads(t[t.rindex('{\n'):])
print('  ',{k:j[k] for k in ('set','overall_ok','refusal_correct','false_refusals','grounding_violations','official_checks_ok') if k in j})"
done; done
echo
echo "## 5. The ONLY network use is the model call: real mode with no network degrades safely"
echo "\$ docker run --rm --network none -e LLM_MODE=real -e LLM_BASE_URL=https://example.invalid/v1 -e LLM_NAME=placeholder -e LLM_API_KEY=dummy -e LLM_TIMEOUT_S=3 $IMG python -m apertus_qa ask --json '¿Cuál fue la inflación mensual de agosto de 2026?'"
docker run --rm --network none -e LLM_MODE=real -e LLM_BASE_URL=https://example.invalid/v1 -e LLM_NAME=placeholder -e LLM_API_KEY=dummy -e LLM_TIMEOUT_S=3 $IMG python -m apertus_qa ask --json '¿Cuál fue la inflación mensual de agosto de 2026?' 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read()
try:
    d=json.loads(t); print('  answer:',d['answer']); print('  trace:',json.dumps(d.get('trace'),ensure_ascii=False)[:400])
except Exception: print(t[:1500])"
