#!/usr/bin/env python3
"""Check the version bump of a PR against its base branch.

Usage: check_version.py BASE_DIR [HEAD_DIR]   (HEAD_DIR defaults to the repo root)

Errors (exit 1): wrong version format or number, top row of src/changelog.typ
not matching the version, older history rows removed.
Warning only: guide text changed but the version was not raised (raising it is
a deliberate, manual decision).
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from extract_text import corpus_files, extract_typst

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r'#let\s+version\s*=\s*"([^"]*)"')
VERSION_FORMAT = re.compile(r"(\d{4})\.([1-9]\d*)")
ROW_RE = re.compile(r"^\s*\[(\d{4}\.\d+)\],\s*\[([^\]]*)\],\s*\[(.*)\],?\s*$", re.MULTILINE)
QV_YEAR_SWITCH_MONTH = 8  # from 1 August, editions are for the next QV year


def read_version(root: Path) -> str:
    m = VERSION_RE.search((root / "src" / "meta.typ").read_text(encoding="utf-8"))
    return m.group(1) if m else ""


def changelog_rows(root: Path) -> list[tuple[str, str, str]]:
    """(version, date, summary) rows of the Änderungshistorie, top first."""
    text = (root / "src" / "changelog.typ").read_text(encoding="utf-8")
    return [(v, d.strip(), s.strip()) for v, d, s in ROW_RE.findall(text)]


def qv_year(today: date) -> int:
    return today.year + (today.month >= QV_YEAR_SWITCH_MONTH)


def expected_next(base_version: str, today: date) -> str:
    year, n = (int(x) for x in base_version.split("."))
    cycle = qv_year(today)
    return f"{cycle}.1" if cycle > year else f"{year}.{n + 1}"


def guide_text(root: Path) -> str:
    """Prose of both editions without the history table (which changes with every bump)."""
    return "\n".join(extract_typst(p) for p in corpus_files(root) if p.name != "changelog.typ")


def check(base: Path, head: Path, today: date) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    base_v, head_v = read_version(base), read_version(head)

    if not VERSION_FORMAT.fullmatch(head_v):
        return [f'src/meta.typ: version "{head_v}" must look like 2027.2'], warnings

    rows = changelog_rows(head)
    if not rows or rows[0][0] != head_v:
        top = rows[0][0] if rows else "none"
        errors.append(f"src/changelog.typ: top row must be version {head_v} (found {top})")
    elif not rows[0][1] or not rows[0][2]:
        errors.append(f"src/changelog.typ: row {head_v} needs a date and a summary")

    missing = [v for v, _, _ in changelog_rows(base) if v not in {r[0] for r in rows}]
    if missing:
        errors.append(f"src/changelog.typ: keep the older rows, missing: {', '.join(missing)}")

    if head_v != base_v:
        want = expected_next(base_v, today)
        if head_v != want:
            errors.append(f"src/meta.typ: after {base_v} the next version is {want}, not {head_v}")
    elif guide_text(base) != guide_text(head):
        warnings.append(
            f"Text changed but the version is still {base_v}. To publish it as a new "
            f"edition, raise it to {expected_next(base_v, today)} (see README)."
        )
    return errors, warnings


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: check_version.py BASE_DIR [HEAD_DIR]")
    base = Path(sys.argv[1])
    head = Path(sys.argv[2]) if len(sys.argv) == 3 else ROOT
    today = datetime.now(ZoneInfo("Europe/Zurich")).date()
    errors, warnings = check(base, head, today)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    for kind, msgs in (("error", errors), ("warning", warnings)):
        for msg in msgs:
            print(f"::{kind}::{msg}" if gha else f"{kind}: {msg}")
    if errors:
        sys.exit(1)
    print(f"Version OK ({read_version(head)})")


if __name__ == "__main__":
    main()
