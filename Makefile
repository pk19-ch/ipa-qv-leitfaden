TYPST           ?= typst
PODMAN          ?= podman
IMAGE           ?= ghcr.io/typst/typst:0.15.1
VERAPDF_IMAGE   ?= docker.io/verapdf/cli:v1.30.3
CHECK_IMAGE     ?= quay.io/centos/centos:stream10-minimal
OUT             := dist
FONT_DIR        := assets/fonts/inter

MAIN            := src/leitfaden.typ
HEX             := src/leitfaden-hex-nex.typ

SRC             := $(wildcard src/*.typ) $(wildcard src/chapters/*.typ)
THEME           := $(wildcard theme/*.typ)

VERSION         := $(shell scripts/get_version.sh --full)
$(if $(VERSION),,$(error Could not extract version — scripts/get_version.sh failed))

# Accessible (PDF/UA-1) and archivable (PDF/A-2a) output
PDF_STANDARDS   := --pdf-standard ua-1 --pdf-standard a-2a
TYPST_FLAGS     := --root . --font-path $(FONT_DIR) $(PDF_STANDARDS)

.DEFAULT_GOAL := pdf

.PHONY: pdf clean podman-pdf podman-check-pdf check-text podman-check-text test lint podman-lint podman-test podman-ci help

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

# Containers use python3.14 to match CI (Stream 10's default python3 is 3.12).
# ── Container builds (no host dependencies beyond Podman) ─────────────────────

podman-pdf: ## Compile PDFs in container
	mkdir -p $(OUT)
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(PDF_STANDARDS) $(MAIN) $(OUT)/qv-leitfaden-$(VERSION).pdf
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(PDF_STANDARDS) $(HEX) $(OUT)/qv-leitfaden-hex-nex-$(VERSION).pdf

podman-check-pdf: ## Validate the PDFs in dist/ (PDF/UA-1, PDF/A-2a) with veraPDF
	for f in $(OUT)/qv-leitfaden-$(VERSION).pdf $(OUT)/qv-leitfaden-hex-nex-$(VERSION).pdf; do \
		for fl in ua1 2a; do \
			$(PODMAN) run --rm -v "$$(pwd):/data:Z" $(VERAPDF_IMAGE) --flavour $$fl --format text /data/$$f | grep -q '^PASS' \
				|| { echo "FAIL $$f ($$fl)"; exit 1; }; \
		done; \
	done; echo "PDF/UA-1 + PDF/A-2a OK"

# ── Text quality (spelling + grammar) ────────────────────────────────────────

check-text: ## Run spelling + grammar checks (requires .venv)
	SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" .venv/bin/python3 scripts/check_text.py

test: ## Run Python tests (requires .venv)
	.venv/bin/python3 -m pytest scripts/ -v

lint: ## Run Python linter (requires .venv)
	.venv/bin/python3 -m ruff check scripts/

podman-lint: ## Run ruff lint in a container
	$(PODMAN) run --rm \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		microdnf install -y python3.14 python3.14-pip >/dev/null && \
		python3.14 -m pip install -q --root-user-action=ignore -r requirements.txt && \
		python3.14 -m ruff check scripts/'

podman-test: ## Run Python tests in container
	$(PODMAN) run --rm \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		microdnf install -y python3.14 python3.14-pip >/dev/null && \
		python3.14 -m pip install -q --root-user-action=ignore -r requirements.txt >/dev/null && \
		python3.14 -m pytest scripts/ -v'

podman-check-text: ## Run text checks in container
	$(PODMAN) run --rm \
		-e SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" \
		-e HUNSPELL_LANG="$(or $(HUNSPELL_LANG),de_CH)" \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		microdnf install -y python3.14 hunspell hunspell-de >/dev/null && \
		python3.14 scripts/check_text.py'

podman-ci: podman-lint podman-test podman-check-text ## Run full CI suite in containers

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
