"""Tests for check_version.py."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from check_version import check, expected_next, qv_year

NOV_2026 = date(2026, 11, 3)


def _repo(
    root: Path,
    version: str,
    rows: list[str],
    text: str = "Ein Satz im Leitfaden.",
) -> Path:
    (root / "src" / "chapters").mkdir(parents=True)
    (root / "src" / "meta.typ").write_text(f'#let version      = "{version}"\n', encoding="utf-8")
    table = "\n".join(f"  {r}," for r in rows)
    (root / "src" / "changelog.typ").write_text(
        "#table(\n  columns: (auto, auto, 1fr),\n"
        f"  [Version], [Datum], [Änderungen],\n{table}\n)\n",
        encoding="utf-8",
    )
    (root / "src" / "chapters" / "ch01.typ").write_text(f"= Titel\n\n{text}\n", encoding="utf-8")
    return root


ROW_2027_1 = "[2027.1], [Nov 2026], [Eigenleistung überprüfen]"
ROW_2026_1 = "[2026.1], [März 2026], [Erstausgabe]"
ROW_2027_2 = "[2027.2], [Nov 2026], [Abgabefrist präzisiert]"


@pytest.mark.parametrize(
    ("today", "year"),
    [
        (date(2027, 7, 31), 2027),
        (date(2027, 8, 1), 2028),
        (date(2026, 11, 3), 2027),
        (date(2026, 4, 2), 2026),
    ],
)
def test_qv_year_switches_on_1_august(today: date, year: int) -> None:
    assert qv_year(today) == year


def test_expected_next_same_and_new_qv_year() -> None:
    assert expected_next("2027.1", NOV_2026) == "2027.2"
    assert expected_next("2027.3", date(2027, 9, 15)) == "2028.1"


def test_valid_bump_passes(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1, ROW_2026_1])
    head = _repo(
        tmp_path / "head", "2027.2", [ROW_2027_2, ROW_2027_1, ROW_2026_1], text="Neuer Satz."
    )
    assert check(base, head, NOV_2026) == ([], [])


def test_skipped_number_fails(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1])
    head = _repo(tmp_path / "head", "2027.3", ["[2027.3], [Nov 2026], [X]", ROW_2027_1])
    errors, _ = check(base, head, NOV_2026)
    assert any("next version is 2027.2" in e for e in errors)


def test_bad_format_fails(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1])
    head = _repo(tmp_path / "head", "2027.02", [ROW_2027_1])
    errors, _ = check(base, head, NOV_2026)
    assert errors and "must look like" in errors[0]


def test_top_row_must_match_version(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1])
    head = _repo(tmp_path / "head", "2027.2", [ROW_2027_1])
    errors, _ = check(base, head, NOV_2026)
    assert any("top row must be version 2027.2" in e for e in errors)


def test_removed_history_row_fails(tmp_path: Path) -> None:
    """The mistake from PR #20: the new row replaced the old one."""
    base = _repo(tmp_path / "base", "2026.1", [ROW_2026_1])
    head = _repo(tmp_path / "head", "2027.1", [ROW_2027_1])
    errors, _ = check(base, head, NOV_2026)
    assert any("missing: 2026.1" in e for e in errors)


def test_text_change_without_bump_only_warns(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1])
    head = _repo(tmp_path / "head", "2027.1", [ROW_2027_1], text="Geänderter Satz.")
    errors, warnings = check(base, head, NOV_2026)
    assert errors == []
    assert warnings and "raise it to 2027.2" in warnings[0]


def test_no_text_change_no_bump_is_silent(tmp_path: Path) -> None:
    base = _repo(tmp_path / "base", "2027.1", [ROW_2027_1])
    head = _repo(tmp_path / "head", "2027.1", [ROW_2027_1])
    assert check(base, head, NOV_2026) == ([], [])
