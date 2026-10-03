# Despliegue soberano / air-gapped

**Arquitectura objetivo (Track 2B):** **b) Air-gapped**. También sirve para **a) On-premise** y **c) Sovereign Swiss cloud**,
porque la imagen no depende de ningún servicio externo.

## Qué necesita la red, y cuándo

| Etapa | Red externa | Detalle |
|---|---|---|
| Construir la imagen | Solo para bajar `python:3.12-slim` (lo hace el daemon); los pasos `RUN` corren con `docker build --network none` | No hay `pip install`: el código usa solo la biblioteca estándar de Python. En un sitio aislado: `make image-save` en una máquina conectada, copiar `apertus-qa.tar`, `docker load -i apertus-qa.tar`. |
| Datos | **Ninguna** | `data/snapshot/` (≈0,3 MB, CSV + `catalog.json` con sha256) va dentro de la imagen. La integridad y la licencia se verifican al arrancar. |
| Ejecución: UI, API, cálculo, citas, rechazos | **Ninguna** | Todo es local. `make eval` corre con `docker run --network none`. |
| Ejecución: modelo | Solo hacia `LLM_BASE_URL` | Puede ser el endpoint de CSCS (Suiza) o un Apertus **autoalojado** en la misma red aislada (vLLM / Ollama / llama.cpp, API estilo OpenAI). |
| Si el modelo no responde | Ninguna | El gateway cae a un router por reglas + plantillas; la respuesta sigue siendo correcta y citada, y la UI muestra el modo. |

## Modos (`LLM_MODE`)

- `real`: endpoint OpenAI-compatible definido por `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` (la clave es opcional para servidores locales).
- `stub`: repite salidas grabadas (`src/apertus_qa/stub/`); determinístico, sin red. Se etiqueta **STUB** en la UI (banner superior + badges) y en la evaluación (`STUB (canned replay, not real Apertus)`).
- `record`: como `real`, y además guarda las salidas del modelo en `stub/recorded.json`, para que un jurado sin clave pueda reproducir una corrida real sin red.
- `off`: sin modelo (reglas + plantillas). Es el modo "sin conexión total".

## Apertus autoalojado (sin internet)

`docs/deploy/docker-compose.airgap.yml` es un ejemplo con vLLM sirviendo `swiss-ai/Apertus-v1.5-8B` desde pesos locales
(`HF_HUB_OFFLINE=1`) en una red Docker `internal: true` (sin salida). **No probado en esta etapa** (no hay GPU en la máquina de
desarrollo; la imagen de la app sí está verificada, ver abajo). Requisitos: los pesos descargados de antemano (modelo con acceso condicionado en Hugging Face:
hay que aceptar sus condiciones), GPU con memoria suficiente para el 8B, o una versión cuantizada vía llama.cpp/Ollama en CPU (lenta).

## Actualizar datos sin internet en el sitio

Los datos se actualizan **fuera** del sitio aislado: `make snapshot` (mantenedores) regenera `data/snapshot/` desde descargas
crudas verificadas; se reconstruye la imagen y se transfiere. El sitio nunca descarga nada.

## Prueba verificada: todo funciona con `--network none` (3 oct 2026; re-verificado tras polish STUB DEMO)

Entorno: Docker Engine 29.8.2 (Debian 13, x86-64), imagen `apertus-qa:local` construida con
`docker build --no-cache --network none -t apertus-qa:local .` (7 pasos OK; la única descarga es la imagen base, que hace
el daemon, no el contenedor). Reproducir con **`make offline-proof`** (script: `scripts/offline_proof.sh`; falla si algún paso no cumple: solo `lo`, egress/DNS bloqueados, banner STUB en la UI, 35 tests, evals con 0 grounding violations).

Qué demuestra:
1. Dentro del contenedor solo existe la interfaz `lo`.
2. No hay salida a internet ni DNS (`Network is unreachable`, fallo de resolución).
3. La app completa (UI/API, cálculo, citas, rechazos) responde dentro del mismo contenedor aislado.
4. Los 35 tests y las dos evaluaciones (principal y held-out; modos STUB y `off`) pasan sin red. Las cifras son las mismas
   que en `docs/eval/` (31/31 principal; 8/13 held-out; 0 violaciones de grounding; 5/5 cotejos con INDEC).
5. La **única** dependencia de red es la llamada al modelo: en modo `real` sin red, el gateway registra
   `network_error` y cae a reglas + plantillas, y la respuesta sigue siendo correcta y citada.

Salida literal de `make offline-proof`:

```text
$ docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}'
client 29.8.2 / server 29.8.2
$ docker image inspect apertus-qa:local --format '{{.Id}}'
sha256:206e98232ae16b33651b284fd616002690c58347a7d679341ca07c9459e91cd9

## 1. Interfaces inside a --network none container (only loopback expected)
$ docker run --rm --network none apertus-qa:local python -c "import socket;print(sorted(n for _,n in socket.if_nameindex()))"
['lo']

## 2. Egress and DNS are impossible
$ docker run --rm --network none apertus-qa:local python -c '<connect 1.1.1.1:443, 8.8.8.8:53; resolve api.github.com>'
1.1.1.1 443 -> OSError [Errno 101] Network is unreachable
8.8.8.8 53 -> OSError [Errno 101] Network is unreachable
DNS api.github.com -> gaierror [Errno -3] Temporary failure in name resolution

## 3. Full app served and queried inside the same air-gapped container
$ docker run -d --name aqa-offline --network none apertus-qa:local   # default CMD: serve on :8080
$ docker exec aqa-offline python -c '<GET /health; POST /api/ask x2>'
health: {'ok': True, 'model_mode': 'stub', 'entries': 47, 'snapshot': '2026-10-02T14:20:15+00:00'}
Q: ¿Cuál fue la inflación mensual de agosto de 2026?
  refused: False | answer: En agosto de 2026, la inflación mensual fue de 1,7 % respecto de julio de 2026.
  cite: Fuente: Instituto Nacional de Estadística y Censos (INDEC) — IPC Nivel General Nacional (base dic-2016 = 100) (serie 148
Q: ¿Cuál será el dólar blue en diciembre?
  refused: True | answer: No hago pronósticos: solo informo datos oficiales ya publicados que están en el snapshot local.
  cite: -
$ docker exec aqa-offline python -c '<check STUB banner marker in UI HTML>'
UI STUB banner marker: OK
$ docker inspect aqa-offline --format '{{.HostConfig.NetworkMode}}'
none

## 4. Test suite and both eval sets, no network
$ make test   (docker run --rm --network none ... unittest)
Ran 35 tests in 1.165s

OK
$ docker run --rm --network none -e LLM_MODE=stub apertus-qa:local python -m eval.run_eval --mode stub --set main --out /tmp/x
   {'set': 'main', 'overall_ok': 31, 'refusal_correct': 8, 'false_refusals': 0, 'grounding_violations': 0, 'official_checks_ok': '5/5'}
$ docker run --rm --network none -e LLM_MODE=off apertus-qa:local python -m eval.run_eval --mode off --set main --out /tmp/x
   {'set': 'main', 'overall_ok': 31, 'refusal_correct': 8, 'false_refusals': 0, 'grounding_violations': 0, 'official_checks_ok': '5/5'}
$ docker run --rm --network none -e LLM_MODE=stub apertus-qa:local python -m eval.run_eval --mode stub --set heldout --out /tmp/x
   {'set': 'heldout', 'overall_ok': 8, 'refusal_correct': 2, 'false_refusals': 4, 'grounding_violations': 0, 'official_checks_ok': '0/0'}
$ docker run --rm --network none -e LLM_MODE=off apertus-qa:local python -m eval.run_eval --mode off --set heldout --out /tmp/x
   {'set': 'heldout', 'overall_ok': 8, 'refusal_correct': 2, 'false_refusals': 4, 'grounding_violations': 0, 'official_checks_ok': '0/0'}

## 5. The ONLY network use is the model call: real mode with no network degrades safely
$ docker run --rm --network none -e LLM_MODE=real -e LLM_BASE_URL=https://example.invalid/v1 -e LLM_NAME=placeholder -e LLM_API_KEY=dummy -e LLM_TIMEOUT_S=3 apertus-qa:local python -m apertus_qa ask --json '¿Cuál fue la inflación mensual de agosto de 2026?'
  answer: IPC Nivel General Nacional (base dic-2016 = 100): variación mensual de 1,7 % en agosto de 2026 (respecto de julio de 2026).
  trace: {"model_mode": "real", "router": {"mode": "fallback", "reason": "network_error", "plan": {"action": "answer", "op": "variacion_mensual", "series": ["148.3_INIVELNAL_DICI_M_26"], "period": "2026-08"}}, "phrase": {"mode": "fallback", "reason": "network_error"}}
```

Nota sobre el modo `real` con red: el contenedor necesita salida **solo** hacia `LLM_BASE_URL` (CSCS o un Apertus
autoalojado en la misma red aislada). Se puede limitar con una red Docker `internal: true` que contenga solo la app y el
servidor del modelo (ver `deploy/docker-compose.airgap.yml`).
