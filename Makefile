TYPST           ?= typst
PODMAN          ?= podman
IMAGE           ?= ghcr.io/typst/typst:v0.14.2
CHECK_IMAGE     ?= quay.io/centos/centos:stream10-minimal
OUT             := dist
FONT_DIR        := assets/fonts/inter

MAIN            := src/leitfaden.typ
HEX             := src/leitfaden-hex-nex.typ

SRC             := $(wildcard src/*.typ) $(wildcard src/chapters/*.typ)
THEME           := $(wildcard theme/*.typ)

VERSION         := $(shell scripts/get_version.sh --full)
$(if $(VERSION),,$(error Could not extract version — scripts/get_version.sh failed))

TYPST_FLAGS     := --root . --font-path $(FONT_DIR)

.DEFAULT_GOAL := pdf

.PHONY: pdf clean podman-pdf check-text podman-check-text test podman-test podman-ci help

# ── Native builds (requires `typst` on PATH) ─────────────────────────────────

pdf: $(OUT)/qv-leitfaden-$(VERSION).pdf $(OUT)/qv-leitfaden-hex-nex-$(VERSION).pdf ## Compile both PDFs

$(OUT)/qv-leitfaden-$(VERSION).pdf: $(MAIN) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(MAIN) $@

$(OUT)/qv-leitfaden-hex-nex-$(VERSION).pdf: $(HEX) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(HEX) $@

$(OUT):
	mkdir -p $(OUT)

clean: ## Remove built PDFs
	rm -f $(OUT)/*.pdf

# ── Container builds (no host dependencies beyond Podman) ─────────────────────

podman-pdf: ## Compile PDFs in container
	mkdir -p $(OUT)
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(MAIN) $(OUT)/qv-leitfaden-$(VERSION).pdf
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(HEX) $(OUT)/qv-leitfaden-hex-nex-$(VERSION).pdf

# ── Text quality (spelling + grammar) ────────────────────────────────────────

check-text: ## Run spelling + grammar checks (requires .venv)
	SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" .venv/bin/python3 scripts/check_text.py

test: ## Run Python tests (requires .venv)
	.venv/bin/python3 -m pytest scripts/ -v

podman-test: ## Run Python tests in container
	$(PODMAN) run --rm \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		microdnf install -y python3 python3-pip >/dev/null && \
		python3 -m pip install -q --root-user-action=ignore -r requirements.txt >/dev/null && \
		python3 -m pytest scripts/ -v'

podman-check-text: ## Run text checks in container
	$(PODMAN) run --rm \
		-e SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" \
		$(if $(strip $(HUNSPELL_LANG)),-e HUNSPELL_LANG="$(HUNSPELL_LANG)") \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		microdnf install -y python3 hunspell hunspell-de >/dev/null && \
		python3 scripts/check_text.py'

podman-ci: podman-test podman-check-text ## Run full CI suite in containers

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
