# QV-Leitfaden für Informatikerinnen und Informatiker

The printable PDFs are generated from [Typst](https://typst.app/) sources in [`src/`](src/). Edition metadata lives in [`src/meta.typ`](src/meta.typ); brand tokens in [`theme/zh-mba.typ`](theme/zh-mba.typ).

### Build

| What | Command | Requires |
|------|---------|----------|
| PDFs (container) | `make podman-pdf` | Podman |
| PDFs (native) | `make pdf` | [Typst](https://typst.app/) ≥ 0.14.2 |
| Spell/grammar (container) | `make podman-check-text` | Podman |
| Spell/grammar (native) | `make check-text` | Python 3, hunspell, hunspell-de-ch |

Set `SKIP_LANGUAGETOOL=1` to skip the LanguageTool API call (offline). Override the container runtime with `PODMAN=docker`.

### CI

All workflows run on pushes and PRs to `main` (path-filtered):

- [build-pdf.yml](.github/workflows/build-pdf.yml) -- compiles PDFs, uploads as `qv-leitfaden-pdf` artifact
- [text-check.yml](.github/workflows/text-check.yml) -- hunspell + LanguageTool on prose changes
- [release.yml](.github/workflows/release.yml) -- on `main` only: auto-tags, changelog, GitHub Release with PDFs (triggered by `version` change in [`src/meta.typ`](src/meta.typ))

### Versioning

Uses CalVer `YYYY.N` (e.g. `2026.1`, `2026.2`). Bump `version` in [`src/meta.typ`](src/meta.typ) as part of your PR to `main`.

### Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) so the changelog groups changes meaningfully:

| Prefix | Use for |
|--------|---------|
| `content:` | Text changes (new sections, rewording) |
| `design:` | Visual / layout changes |
| `fix:` | Typo fixes, corrections |
| `ci:` | Pipeline changes |
| `chore:` | Maintenance, dependency updates |

Other standard types are grouped per [`cliff.toml`](cliff.toml).

### Output

- `dist/qv-leitfaden-YYYY.pdf` -- main (KAND/VF)
- `dist/qv-leitfaden-hex-nex-YYYY.pdf` -- experts (HEX/NEX)

The year is derived automatically from `version` in [`src/meta.typ`](src/meta.typ).