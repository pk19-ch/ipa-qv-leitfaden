# QV-Leitfaden für Informatikerinnen und Informatiker

This repository contains the text of the QV-Leitfaden of Prüfungskommission 19 (Kanton Zürich). Two PDFs are built from it:

| PDF | For |
|-----|-----|
| `qv-leitfaden-YYYY.N.pdf` | Candidates (KAND) and vorgesetzte Fachkräfte (VF) |
| `qv-leitfaden-hex-nex-YYYY.N.pdf` | Experts (HEX/NEX) |

`YYYY.N` is the version number, e.g. `2027.1`.

**In short:**

- You change the text directly on GitHub, in your browser. You need a GitHub account, nothing else.
- Every change is a *pull request* (PR). A maintainer checks it and puts it into the guide.
- A new version with new PDFs is published only when someone raises the version number.
- Maintainers are the members of [pk19-ch](https://github.com/pk19-ch).

## Words used here

| Word | Meaning |
|------|---------|
| `main` | The current, approved text. |
| Pull request (PR) | A proposed change. It waits for approval. |
| Branch / fork | A working copy that GitHub creates for your change. You don't have to manage it. |
| Check | An automatic test on every PR: green ✓ is fine, red ✗ needs a fix. |
| Release | A published version on the [Releases](../../releases) page, with both PDFs. |
| Maintainer | A member of pk19-ch. Only maintainers can approve and merge PRs. |

## Where is which text?

| File | Content |
|------|---------|
| `src/chapters/ch01.typ` | Grundsätzliche Idee der IPA |
| `src/chapters/ch02.typ` | Zeitplan und Organisatorisches |
| `src/chapters/ch03.typ` | Facharbeit: IPA-Bericht |
| `src/chapters/ch04.typ` | Facharbeit: Präsentation und Demonstration |
| `src/chapters/ch05.typ` | Facharbeit: Fachgespräch |
| `src/chapters/ch06.typ` | Hinweise für VF |
| `src/body-hex-nex.typ` | Gesamter Leitfaden für HEX/NEX |
| `src/changelog.typ` | Änderungshistorie (in beiden PDFs) |
| `src/meta.typ` | Versionsnummer |

Many rules (deadlines, durations) are in both editions. When you change a rule, change it in both editions in the same PR. To find all places: type a word of the rule into the search field at the top of the repository page and press Enter. GitHub lists every file that contains it.

## Change the text

1. Open the file on GitHub.
2. Click the pencil icon (**Edit**). If you are not a maintainer, GitHub first shows **Fork this repository**: click it.
3. Make your change.
4. Click **Commit changes…**.
5. Enter a short title. Start it with `content:` for a change of content or `fix:` for a typo, e.g. `fix: Tippfehler in Kapitel 3`.
6. Maintainers: choose **Create a new branch**. (Non-members don't see this choice.)
7. Click **Propose changes**.
8. Click **Create pull request**.
9. Wait a few minutes until the checks are green.
10. Check the PDFs (see [Check the PDFs](#check-the-pdfs)).
11. GitHub asks the maintainers for a review automatically. You don't need to do anything.

You don't need to raise the version number. A maintainer does that when publishing.

### Check the PDFs

1. In your PR, open the `typst` check: click **Details**.
2. Click **Summary** on the left.
3. Scroll down to **Artifacts** and download the ZIP.
4. Open the two PDFs in the ZIP and look at your change.

Maintainers also get a comment **PDF preview ready** with a direct link.

## Review a PR (maintainers)

1. Open the PR.
2. If you see **Approve and run workflows**, click it. This starts the checks for a first-time contributor.
3. Click **Files changed** and read the change.
4. Check:
   - Is the text correct and clear?
   - If the rule is in both editions: were both changed?
   - If the version number was raised: is the new row in `changelog.typ` correct?
   - Did only text files change? If a PR from outside pk19-ch changes files in `.github/` or `scripts/`, don't approve it yourself: ask the repository admins.
   - Does `lint-text` show the warning *Text changed but the version is still …*? Then decide whether to publish a new version (see [New version](#new-version)).
5. Look at the PDFs (see [Check the PDFs](#check-the-pdfs)).
6. Click **Review changes** → **Approve** → **Submit review**.
7. When all checks are green, click **Squash and merge** → **Confirm squash and merge**.

## New version

A new version is published only when the version number is raised. Maintainers raise it, in the text PR before merging or in a separate PR. We recommend a new version for every change to the text, including typo fixes. Changes to colours or layout alone need no new version.

### Which number?

The number is `YEAR.COUNT`, e.g. `2027.2`.

- **YEAR** is the QV year: until 31 July the current year, from 1 August the current year + 1.
- **COUNT**: if the current number already has this YEAR, add 1. Otherwise start at 1.

| Today | Current number | New number |
|-------|----------------|------------|
| 3 November 2026 | `2027.1` | `2027.2` |
| 10 January 2027 | `2027.2` | `2027.3` |
| 15 September 2027 | `2027.3` | `2028.1` |

### How

Make two changes, in your text PR or in a separate PR:

1. In `src/meta.typ`, change the number between the quotes: `#let version = "2027.2"`.
2. In `src/changelog.typ`, add a new row directly below the header row `[Version], [Datum], [Änderungen],`. Write the month short and in German (`Jan`, `Feb`, `März`, `Apr`, `Mai`, `Juni`, `Juli`, `Aug`, `Sept`, `Okt`, `Nov`, `Dez`). Keep all other rows:

   `[2027.2], [Nov 2026], [Abgabefrist für Anhänge präzisiert],`

The check `lint-text` tells you if the number is wrong, the new row is missing, or an old row was deleted.

After the merge, the new version appears on the [Releases](../../releases) page within a few minutes.

## Working on your own computer

Optional. You only need this to build the PDFs or run the checks on your computer. Requirements: Git, Make and [Podman](https://podman.io/).

On macOS and Windows, Podman runs in a small virtual machine. Create it once, and start it again after every restart of your computer:

```bash
podman machine init    # once
podman machine start   # after every restart
```

Clone the project into your home folder (the Podman machine can only see files there):

```bash
cd ~
git clone https://github.com/pk19-ch/ipa-qv-leitfaden.git
cd ipa-qv-leitfaden
make podman-pdf          # build both PDFs into dist/
make podman-check-text   # spelling and grammar
make podman-ci           # all checks: lint, tests, spelling and grammar
```

`SKIP_LANGUAGETOOL=1 make podman-check-text` skips the online grammar check.
