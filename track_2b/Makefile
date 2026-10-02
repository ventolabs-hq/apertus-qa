# Apertus QA. Judges: `make run` (Docker), then open http://localhost:8080
# Model: set LLM_NAME, LLM_BASE_URL, LLM_API_KEY (see .env.example). Without them the app runs in STUB mode
# (replayed outputs) and says so in the UI. LLM_MODE=off runs with no model at all (rules + templates).
IMAGE   ?= apertus-qa:local
PORT    ?= 8080
DOCKER  ?= docker
PYTHON  ?= python3
LLM_MODE ?=
# How `make run` publishes the UI. Default: normal Docker port mapping. On hosts whose daemon runs with
# --bridge=none (e.g. our build box), use: make run RUN_NET="--network host -e HOST=127.0.0.1"
RUN_NET ?= -p $(PORT):8080
# Network for building the report image (apt). Default Docker networking; on a daemon without a bridge use --network host.
REPORT_BUILD_NET ?=
-include .env
export LLM_NAME LLM_BASE_URL LLM_API_KEY LLM_MODE LLM_JSON_MODE LLM_TIMEOUT_S
ENV_FLAGS = -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e LLM_MODE -e LLM_JSON_MODE -e LLM_TIMEOUT_S
# stub/off evaluation runs with NO network at all, proving there is no runtime internet dependency
NET_EVAL = $(if $(filter real record,$(LLM_MODE)),,--network none)
EVAL_MODE = $(if $(LLM_MODE),$(LLM_MODE),stub)

.PHONY: report report-image offline-proof run build test eval eval-heldout run-local test-local eval-local snapshot image-save help check-docker

help:
	@echo "make run | test | eval | eval-heldout | offline-proof | report   (Docker)"
	@echo "make run-local | test-local | eval-local (host Python >= 3.10, no Docker)"
	@echo "make image-save  -> apertus-qa.tar for air-gapped transfer (docker load -i apertus-qa.tar)"

check-docker:
	@command -v $(DOCKER) >/dev/null 2>&1 || { echo "Docker not found. Install Docker, or use 'make run-local' (Python >= 3.10)."; exit 1; }

build: check-docker
	$(DOCKER) build --network none -t $(IMAGE) .   # RUN steps need no network (stdlib only)

run: build
	$(DOCKER) run --rm $(RUN_NET) $(ENV_FLAGS) $(IMAGE)

test: build
	$(DOCKER) run --rm --network none $(IMAGE) python -m unittest discover -s tests -t . -v

eval: build
	$(DOCKER) run --rm $(NET_EVAL) $(ENV_FLAGS) -v "$(CURDIR)/docs/eval:/app/docs/eval" --user "$$(id -u):$$(id -g)" \
	  $(IMAGE) python -m eval.run_eval --mode $(EVAL_MODE) --set main

eval-heldout: build
	$(DOCKER) run --rm $(NET_EVAL) $(ENV_FLAGS) -v "$(CURDIR)/docs/eval:/app/docs/eval" --user "$$(id -u):$$(id -g)" \
	  $(IMAGE) python -m eval.run_eval --mode $(EVAL_MODE) --set heldout

# Air-gap proof: interfaces, blocked egress/DNS, app + tests + evals under --network none, model-call fallback
offline-proof: build
	IMAGE=$(IMAGE) bash scripts/offline_proof.sh

# Technical report PDF (template: TeamName_Report.pdf, max 6 pages). Separate builder image (pandoc + WeasyPrint from
# Debian); it does not touch the app image. Rendering runs with --network none.
REPORT_IMAGE ?= apertus-qa-report:local
report-image: check-docker
	$(DOCKER) build $(REPORT_BUILD_NET) -t $(REPORT_IMAGE) -f docs/report/Dockerfile docs/report

report: check-docker
	@$(DOCKER) image inspect $(REPORT_IMAGE) >/dev/null 2>&1 || $(MAKE) report-image   # build once; rendering is offline
	$(DOCKER) run --rm --network none --user "$$(id -u):$$(id -g)" -v "$(CURDIR):/work" -w /work $(REPORT_IMAGE) sh docs/report/render.sh

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
