# Apertus QA. Judges: `make run` (Docker), then open http://localhost:8080
# Model: set LLM_NAME, LLM_BASE_URL, LLM_API_KEY (see .env.example). Without them the app runs in STUB mode
# (replayed outputs) and says so in the UI. LLM_MODE=off runs with no model at all (rules + templates).
IMAGE   ?= apertus-qa:local
PORT    ?= 8080
DOCKER  ?= docker
PYTHON  ?= python3
LLM_MODE ?=
-include .env
export LLM_NAME LLM_BASE_URL LLM_API_KEY LLM_MODE LLM_JSON_MODE LLM_TIMEOUT_S
ENV_FLAGS = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e LLM_MODE -e LLM_JSON_MODE -e LLM_TIMEOUT_S
# stub/off evaluation runs with NO network at all, proving there is no runtime internet dependency
NET_EVAL = $(if $(filter real record,$(LLM_MODE)),,--network none)
EVAL_MODE = $(if $(LLM_MODE),$(LLM_MODE),stub)

.PHONY: run build test eval eval-heldout run-local test-local eval-local snapshot image-save help check-docker

help:
	@echo "make run | test | eval | eval-heldout   (Docker)"
	@echo "make run-local | test-local | eval-local (host Python >= 3.10, no Docker)"
	@echo "make image-save  -> apertus-qa.tar for air-gapped transfer (docker load -i apertus-qa.tar)"

check-docker:
	@command -v $(DOCKER) >/dev/null 2>&1 || { echo "Docker not found. Install Docker, or use 'make run-local' (Python >= 3.10)."; exit 1; }

build: check-docker
	$(DOCKER) build -t $(IMAGE) .

run: build
	$(DOCKER) run --rm -p $(PORT):8080 $(ENV_FLAGS) $(IMAGE)

test: build
	$(DOCKER) run --rm --network none $(IMAGE) python -m unittest discover -s tests -t . -v

eval: build
	$(DOCKER) run --rm $(NET_EVAL) $(ENV_FLAGS) -v "$(CURDIR)/docs/eval:/app/docs/eval" --user "$$(id -u):$$(id -g)" \
	  $(IMAGE) python -m eval.run_eval --mode $(EVAL_MODE) --set main

eval-heldout: build
	$(DOCKER) run --rm $(NET_EVAL) $(ENV_FLAGS) -v "$(CURDIR)/docs/eval:/app/docs/eval" --user "$$(id -u):$$(id -g)" \
	  $(IMAGE) python -m eval.run_eval --mode $(EVAL_MODE) --set heldout

image-save: build
	$(DOCKER) save $(IMAGE) -o apertus-qa.tar

# ---- host fallbacks (no Docker) ----
run-local:
	cd src && $(PYTHON) -m apertus_qa serve --port $(PORT)

test-local:
	cd src && $(PYTHON) -m unittest discover -s tests -t . -v

eval-local:
	cd src && $(PYTHON) -m eval.run_eval --mode $(EVAL_MODE) --set main && $(PYTHON) -m eval.run_eval --mode $(EVAL_MODE) --set heldout

# Maintainers only: rebuild data/snapshot from raw caches (build time; no network). See docs/DATA.md.
snapshot:
	$(PYTHON) src/tools/build_snapshot.py && $(PYTHON) src/eval/make_expected.py && $(PYTHON) src/tools/data_doc.py
