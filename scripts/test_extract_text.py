#!/usr/bin/env python3
"""Minimal tests for extract_text.py — guards against silent regressions."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from extract_text import build_corpus, corpus_files, extract_typst


def test_extract_typst_strips_directives() -> None:
    with TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.typ"
        p.write_text(
            '#import "foo.typ": bar\n'
            "#set text(size: 10pt)\n"
            "\n"
            "= Kapitel Eins\n"
            "\n"
            "Dies ist ein Absatz mit [wichtigem Inhalt zum Testen].\n",
            encoding="utf-8",
        )
        result = extract_typst(p)
        assert "import" not in result
        assert "set text" not in result
        assert "Kapitel Eins" in result
        assert "wichtigem Inhalt zum Testen" in result


def test_extract_typst_skips_short_and_colour_chunks() -> None:
    with TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.typ"
        p.write_text(
            "= Titel\n"
            "\n"
            "Ein Aufruf mit [kurz] und [rgb(#0070B4)] dazwischen.\n"
            "\n"
            "Dann ein Block mit [Dies ist ein ausreichend langer deutscher Textblock].\n",
            encoding="utf-8",
        )
        result = extract_typst(p)
        assert "0070B4" not in result
        assert "kurz" not in result
        assert "ausreichend langer deutscher Textblock" in result


def test_corpus_files_finds_chapters_and_body(tmp_path: Path) -> None:
    ch = tmp_path / "src" / "chapters"
    ch.mkdir(parents=True)
    (ch / "ch01.typ").write_text("= Eins\n", encoding="utf-8")
    (ch / "ch02.typ").write_text("= Zwei\n", encoding="utf-8")
    body = tmp_path / "src" / "body-hex-nex.typ"
    body.write_text("= HEX\n", encoding="utf-8")
    layout = tmp_path / "src" / "layout.typ"
    layout.write_text('#let x = 1\n', encoding="utf-8")

    found = corpus_files(tmp_path)
    names = [p.name for p in found]
    assert "ch01.typ" in names
    assert "ch02.typ" in names
    assert "body-hex-nex.typ" in names
    assert "layout.typ" not in names


def test_build_corpus_normalises_whitespace(tmp_path: Path) -> None:
    ch = tmp_path / "src" / "chapters"
    ch.mkdir(parents=True)
    (ch / "ch01.typ").write_text(
        "= Test\n\n"
        "#term_block[Sende eine E Mail an die  Fachkraft für Informatik.]\n",
        encoding="utf-8",
    )
    result = build_corpus(tmp_path)
    assert "E-Mail" in result
    assert "  " not in result


if __name__ == "__main__":
    import subprocess, sys

    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "pytest", __file__, "-v"],
        )
    )
