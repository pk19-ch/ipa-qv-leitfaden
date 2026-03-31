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

YEAR            := $(shell sed -n 's/.*version[[:space:]]*=[[:space:]]*"\([0-9]*\)\..*/\1/p' src/meta.typ)
$(if $(YEAR),,$(error Could not extract year from src/meta.typ — check version format))

TYPST_FLAGS     := --root . --font-path $(FONT_DIR)

.DEFAULT_GOAL := pdf

.PHONY: pdf clean podman-pdf check-text podman-check-text test podman-test

# ── Native builds (requires `typst` on PATH) ─────────────────────────────────

pdf: $(OUT)/qv-leitfaden-$(YEAR).pdf $(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf

$(OUT)/qv-leitfaden-$(YEAR).pdf: $(MAIN) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(MAIN) $@

$(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf: $(HEX) $(SRC) $(THEME) | $(OUT)
	$(TYPST) compile $(TYPST_FLAGS) $(HEX) $@

$(OUT):
	mkdir -p $(OUT)

clean:
	rm -f $(OUT)/*.pdf

# ── Container builds (no host dependencies beyond Podman) ─────────────────────

podman-pdf:
	mkdir -p $(OUT)
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(MAIN) $(OUT)/qv-leitfaden-$(YEAR).pdf
	$(PODMAN) run --rm -v "$$(pwd):/work:Z" -w /work $(IMAGE) \
		compile --root /work --font-path /work/$(FONT_DIR) $(HEX) $(OUT)/qv-leitfaden-hex-nex-$(YEAR).pdf

# ── Text quality (spelling + grammar) ────────────────────────────────────────

check-text:
	SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" python3 scripts/check_text.py

test:
	python3 -m pytest scripts/test_extract_text.py -v

podman-test:
	$(PODMAN) run --rm \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		export DEBIAN_FRONTEND=noninteractive && \
		apt-get update -qq && apt-get install -y -qq python3-pytest >/dev/null && \
		python3 -m pytest scripts/test_extract_text.py -v'

podman-check-text:
	$(PODMAN) run --rm \
		-e SKIP_LANGUAGETOOL="$(SKIP_LANGUAGETOOL)" \
		-v "$$(pwd):/work:Z" -w /work $(CHECK_IMAGE) bash -lc '\
		export DEBIAN_FRONTEND=noninteractive && \
		apt-get update -qq && apt-get install -y -qq python3 hunspell hunspell-de-ch >/dev/null && \
		python3 scripts/check_text.py'
