# Despliegue soberano / air-gapped

**Arquitectura objetivo (Track 2B):** **b) Air-gapped**. También sirve para **a) On-premise** y **c) Sovereign Swiss cloud**,
porque la imagen no depende de ningún servicio externo.

## Qué necesita la red, y cuándo

| Etapa | Red externa | Detalle |
|---|---|---|
| Construir la imagen | Solo para bajar `python:3.12-slim` | No hay `pip install`: el código usa solo la biblioteca estándar de Python. En un sitio aislado: `make image-save` en una máquina conectada, copiar `apertus-qa.tar`, `docker load -i apertus-qa.tar`. |
| Datos | **Ninguna** | `data/snapshot/` (≈0,3 MB, CSV + `catalog.json` con sha256) va dentro de la imagen. La integridad y la licencia se verifican al arrancar. |
| Ejecución: UI, API, cálculo, citas, rechazos | **Ninguna** | Todo es local. `make eval` corre con `docker run --network none`. |
| Ejecución: modelo | Solo hacia `LLM_BASE_URL` | Puede ser el endpoint de CSCS (Suiza) o un Apertus **autoalojado** en la misma red aislada (vLLM / Ollama / llama.cpp, API estilo OpenAI). |
| Si el modelo no responde | Ninguna | El gateway cae a un router por reglas + plantillas; la respuesta sigue siendo correcta y citada, y la UI muestra el modo. |

## Modos (`LLM_MODE`)

- `real`: endpoint OpenAI-compatible definido por `LLM_NAME`, `LLM_BASE_URL`, `LLM_API_KEY` (la clave es opcional para servidores locales).
- `stub`: repite salidas grabadas (`src/apertus_qa/stub/`); determinístico, sin red. Se etiqueta **STUB** en la UI y en la evaluación.
- `record`: como `real`, y además guarda las salidas del modelo en `stub/recorded.json`, para que un jurado sin clave pueda reproducir una corrida real sin red.
- `off`: sin modelo (reglas + plantillas). Es el modo "sin conexión total".

## Apertus autoalojado (sin internet)

`docs/deploy/docker-compose.airgap.yml` es un ejemplo con vLLM sirviendo `swiss-ai/Apertus-v1.5-8B` desde pesos locales
(`HF_HUB_OFFLINE=1`) en una red Docker `internal: true` (sin salida). **No probado en esta etapa** (no hay GPU ni Docker en
la máquina de desarrollo). Requisitos: los pesos descargados de antemano (modelo con acceso condicionado en Hugging Face:
hay que aceptar sus condiciones), GPU con memoria suficiente para el 8B, o una versión cuantizada vía llama.cpp/Ollama en CPU (lenta).

## Actualizar datos sin internet en el sitio

Los datos se actualizan **fuera** del sitio aislado: `make snapshot` (mantenedores) regenera `data/snapshot/` desde descargas
crudas verificadas; se reconstruye la imagen y se transfiere. El sitio nunca descarga nada.
