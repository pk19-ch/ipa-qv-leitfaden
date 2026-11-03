# QV-Leitfaden für Informatikerinnen und Informatiker

This repository contains the text of the QV-Leitfaden of Prüfungskommission 19 (Kanton Zürich). Two PDFs are built from it:

| PDF | Audience | Source files |
|-----|----------|--------------|
| `qv-leitfaden-YYYY.N.pdf` | Candidates (KAND) and vorgesetzte Fachkräfte (VF) | `src/leitfaden.typ` + `src/chapters/ch01–ch06.typ` |
| `qv-leitfaden-hex-nex-YYYY.N.pdf` | Experts (HEX/NEX) | `src/leitfaden-hex-nex.typ` + `src/body-hex-nex.typ` |

The text is written in [Typst](https://typst.app/), a simple markup language similar to Markdown. `YYYY.N` is the edition number, e.g. `2027.1`.

## Where is which text?

| File | Content |
|------|---------|
| `src/chapters/ch01.typ` | Grundsätzliche Idee der IPA |
| `src/chapters/ch02.typ` | Zeitplan und Organisatorisches |
| `src/chapters/ch03.typ` | Facharbeit: IPA-Bericht |
| `src/chapters/ch04.typ` | Facharbeit: Präsentation und Demonstration |
| `src/chapters/ch05.typ` | Facharbeit: Fachgespräch |
| `src/chapters/ch06.typ` | Hinweise für VF |
| `src/body-hex-nex.typ` | Whole text of the HEX/NEX edition |
| `src/changelog.typ` | "Änderungshistorie" table at the start of both PDFs |
| `src/meta.typ` | Edition number (`version`) |

Some rules appear in both editions. If you change one, check whether the other edition says the same thing.

## Changing text (no installation needed)

All changes go through a pull request (PR). Nobody can change `main` directly.

1. Open the file on GitHub and click the pencil icon (Edit).
2. Make your change.
3. Click **Commit changes…**, choose **Create a new branch** and give a short description, e.g. `content: Abgabefrist präzisiert`.
4. Click **Propose changes**, then **Create pull request**.
5. Wait a few minutes. The automatic checks run (see below), and a comment **PDF preview ready** appears with a download link. Open both PDFs and check your change.
6. Ask another CEX or maintainer to review. As soon as one person approves and all checks are green, the PR can be merged with **Squash and merge**.

To fix something after the review, edit the file again on the same branch. The checks run again.

### Typst in 30 seconds

```typst
= Chapter title
== Section title

A normal paragraph. An empty line starts a new paragraph.

*bold text*  ·  _italic text_  ·  #strong[bold text]

- list item
- another item

Line break inside a paragraph \
continues here.

#tip_block[A highlighted tip box.]
```

Copy the style of the text around your change. If the PDF build fails, the check output shows the file and line.

## Automatic checks on every PR

| Check | What it does | If it fails |
|-------|--------------|-------------|
| `typst` (Build PDFs) | Builds both PDFs and checks that the current edition number appears in `src/changelog.typ` | Open **Details**. Usually a markup typo (e.g. a missing `]`) or a missing row in `changelog.typ` |
| `lint-text` (spelling & grammar) | Spell check (Swiss German) and grammar check (LanguageTool) on the whole text, plus tests for the check scripts | Open **Details** and scroll to the end: the flagged word or sentence is shown |

**The spell checker flags a correct word** (e.g. a new abbreviation): add the word on its own line to `dict/ipa-personal.pws` in the same PR.

**The grammar checker flags something that is correct**: first try to rephrase the sentence. If the rule is wrong for this text in general, add its ID (shown in brackets, e.g. `[DE_CASE]`) to `dict/languagetool-ignore-rules.txt`.

## Publishing a new edition

In the same PR as your text changes, or in a separate one:

1. Increase `version` in `src/meta.typ`: next number in the same year (`2027.1` → `2027.2`), or `.1` for a new year.
2. Add a new row **at the top** of the table in `src/changelog.typ` with version, month and a short summary. Keep the older rows.
3. Do not edit `CHANGELOG.md`. It is generated automatically.

After the merge, GitHub creates a tag and a [release](../../releases) with both PDFs attached.

## Commit and PR titles

Start the title with one of these words so the generated changelog is sorted correctly:

| Prefix | Use for |
|--------|---------|
| `content:` | Text changes (new rules, rewording) |
| `fix:` | Typos and corrections |
| `design:` | Layout and appearance |
| `docs:` | This README |
| `ci:`, `build:`, `chore:`, `refactor:`, `feat:` | Technical changes (maintainers) |

## Working on your own computer (optional)

You only need this to build the PDFs locally or for technical changes.

**Install:** [Typst](https://typst.app/) 0.14.2 or newer, Python 3, and `hunspell` with the Swiss German dictionary (`de_CH`). Alternatively only [Podman](https://podman.io/) (or Docker with `PODMAN=docker`).

```bash
git clone https://github.com/pk19-ch/ipa-qv-leitfaden.git
cd ipa-qv-leitfaden
make pdf                 # builds both PDFs into dist/

# once, for checks and tests:
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

make check-text          # spelling + grammar (same as the PR check)
make test                # tests for the check scripts
make lint                # Python code style
```

| Without local Typst/Python | Command |
|----------------------------|---------|
| Build PDFs | `make podman-pdf` |
| Spelling + grammar | `make podman-check-text` (uses the German `de_DE` dictionary, so Swiss spellings may be flagged) |
| All checks | `make podman-ci` |

`make help` lists all commands. `SKIP_LANGUAGETOOL=1 make check-text` skips the online grammar check.

## For maintainers

| Path | Purpose |
|------|---------|
| `src/layout.typ`, `theme/zh-mba.typ` | Cover page, page layout, Kanton Zürich colours and text blocks (`tip_block`, `callout`, …) |
| `scripts/` | `extract_text.py` turns the Typst files into plain text, `check_text.py` runs hunspell and LanguageTool on it, plus tests |
| `dict/` | Spell-check word list and ignored LanguageTool rules |
| `assets/fonts/` | Inter font (SIL OFL) |
| `.github/workflows/` | `build-pdf.yml` (PDFs + preview comment), `text-check.yml` (spelling/grammar/tests), `release.yml` (tag + GitHub Release when `version` in `src/meta.typ` changes on `main`) |
| `cliff.toml` | Configuration for the generated `CHANGELOG.md` (git-cliff) |

`main` is protected: changes only via PR, one approval, and the `lint-text` check must pass. `release.yml` commits the generated `CHANGELOG.md` back to `main`, so it needs a way past this protection (a bot bypass or a changelog PR). Otherwise the release job fails.
