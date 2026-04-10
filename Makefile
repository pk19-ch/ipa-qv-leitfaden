TYPST           ?= typst
PODMAN          ?= podman
IMAGE           ?= ghcr.io/typst/typst:v0.14.2
CHECK_IMAGE     ?= docker.io/library/ubuntu:24.04
OUT             := dist
FONT_DIR        := assets/fonts/inter

MAIN            := src/leitfaden.typ
HEX             := src/leitfaden-hex-nex.typ

SRC             := $(wildcard src/*.typ) $(wildcard src/chapters/*.typ)
THEME           := $(wildcard theme/*.typ)

YEAR            := $(shell scripts/get_version.sh --year)
$(if $(YEAR),,$(error Could not extract year — scripts/get_version.sh failed))

TYPST_FLAGS     := --root . --font-path $(FONT_DIR)

.DEFAULT_GOAL := pdf

.PHONY: pdf clean podman-pdf check-text podman-check-text test lint podman-test podman-ci help

# ── Native builds (requires `typst` on PATH) ─────────────────────────────────

pdf: $(OUT)/qv-leitfaden-$(YEAR).pdf $(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf ## Compile both PDFs

$(OUT)/qv-leitfaden-$(YEAR).pdf: $(MAIN) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(MAIN) $@

$(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf: $(HEX) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(HEX) $@

$(OUT):
	mkdir -p $(OUT)

clean: ## Remove built PDFs
	rm -f $(OUT)/*.pdf

# ── Container builds (no host dependencies beyond Podman) ─────────────────────

podman-pdf: ## Compile PDFs in container
	mkdir -p $(OUT)
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(MAIN) $(OUT)/qv-leitfaden-$(YEAR).pdf
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(HEX) $(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf

# ── Text quality (spelling + grammar) ────────────────────────────────────────

check-text: ## Run spelling + grammar checks (requires .venv)
	SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" .venv/bin/python3 scripts/check_text.py

test: ## Run Python tests (requires .venv)
	.venv/bin/python3 -m pytest scripts/ -v

lint: ## Run Python linter (requires .venv)
	.venv/bin/python3 -m ruff check scripts/

podman-test: ## Run Python tests in container
	$(PODMAN) run --rm \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		export DEBIAN_FRONTEND=noninteractive && \
		apt-get update -qq && apt-get install -y -qq python3-pytest >/dev/null && \
		python3 -m pytest scripts/ -v'

podman-check-text: ## Run text checks in container
	$(PODMAN) run --rm \
		-e SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		export DEBIAN_FRONTEND=noninteractive && \
		apt-get update -qq && apt-get install -y -qq python3 hunspell hunspell-de-ch >/dev/null && \
		python3 scripts/check_text.py'

podman-ci: podman-test podman-check-text ## Run full CI suite in containers

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
