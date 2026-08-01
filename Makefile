# Description: Entry points for the Weaver schema workflow and the Docker Compose stack.
# Created by: Mustafa Can Caliskan
# Date: 2026-08-01

SHELL := /usr/bin/env bash
ROOT  := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

include .env
export

# Weaver runs from its official image, so nothing has to be installed locally.
# HOME is redirected into .weaver-home/ so the registry dependency cache
# (the OpenTelemetry semantic conventions) survives between runs.
WEAVER := docker run --rm \
	-u $(shell id -u):$(shell id -g) \
	-e HOME=/tmp/weaver \
	-v "$(ROOT)/.weaver-home:/tmp/weaver" \
	-v "$(ROOT):/work" \
	-w /work \
	otel/weaver:$(WEAVER_VERSION)

COMPOSE := docker compose

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# --- Weaver: the telemetry schema workflow -----------------------------------

# Docker creates a missing bind-mount source as root, which the container's
# non-root user then cannot write to. Creating it here keeps it owned by the
# caller, so a fresh clone works without a manual mkdir.
.PHONY: weaver-home
weaver-home:
	@mkdir -p "$(ROOT)/.weaver-home"

.PHONY: check
check: weaver-home ## Validate the registry and enforce the Acme governance policies
	$(WEAVER) registry check -r semconv -p semconv/policies

.PHONY: generate
generate: weaver-home ## Regenerate the Python bindings and the schema reference docs
	$(WEAVER) registry generate -r semconv --templates weaver/templates python generated/python
	$(WEAVER) registry generate -r semconv --templates weaver/templates markdown generated/docs

.PHONY: generate-check
generate-check: generate ## Fail if the committed generated code is stale
	@git diff --exit-code generated/ \
		|| { echo "generated/ is stale — run 'make generate' and commit the result"; exit 1; }

.PHONY: diff
diff: weaver-home ## Report schema changes between semconv-baseline (0.1.0) and semconv (0.2.0)
	$(WEAVER) registry diff -r semconv --baseline-registry semconv-baseline

.PHONY: resolve
resolve: weaver-home ## Write the fully resolved registry to generated/resolved-registry.json
	$(WEAVER) registry resolve -r semconv --format json -o generated/resolved-registry.json

# Runs on the lab's own network so the sample signals enter through the very
# same sidecar agent the gateway service uses.
.PHONY: emit
emit: weaver-home ## Send registry-conformant sample signals through the pipeline
	docker run --rm \
		-u $(shell id -u):$(shell id -g) \
		-e HOME=/tmp/weaver \
		--network acme-observability-lab_default \
		-v "$(ROOT)/.weaver-home:/tmp/weaver" \
		-v "$(ROOT):/work" \
		-w /work \
		otel/weaver:$(WEAVER_VERSION) \
		registry emit -r semconv --endpoint http://agent-gateway:4317

# Asking live-check for its report ends the session; the container's restart
# policy immediately brings up a fresh one that starts grading from zero.
.PHONY: live-check-report
live-check-report: ## Stop the live-check session and summarize the conformance report
	@mkdir -p report
	@curl -sS -X POST "http://localhost:$(WEAVER_ADMIN_PORT)/stop" -o report/live-check.json \
		|| { echo "live-check admin port not reachable — is the stack up?"; exit 1; }
	@python3 scripts/live_check_summary.py report/live-check.json

# --- Docker Compose: the distributed system ----------------------------------

.PHONY: up
up: ## Build and start the whole stack
	$(COMPOSE) up -d --build

.PHONY: down
down: ## Stop the stack and delete its volumes
	$(COMPOSE) --profile bindplane down -v --remove-orphans

.PHONY: ps
ps: ## Show container status
	$(COMPOSE) ps

.PHONY: logs
logs: ## Follow the logs of every service
	$(COMPOSE) logs -f

.PHONY: bindplane-up
bindplane-up: ## Start the stack with the self-hosted Bindplane server (needs a license)
	$(COMPOSE) --profile bindplane up -d --build

.PHONY: order
order: ## Place a single order against the gateway
	@curl -sS -X POST "http://localhost:$(GATEWAY_PORT)/checkout" \
		-H 'content-type: application/json' \
		-d '{"item_count": 3, "customer_tier": "plus"}' \
		| python3 -m json.tool

.PHONY: clean
clean: down ## Stop everything and remove the Weaver dependency cache
	rm -rf .weaver-home report
