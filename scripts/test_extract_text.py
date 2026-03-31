#!/usr/bin/env python3
"""Minimal tests for extract_text.py — guards against silent regressions."""

from __future__ import annotations

from pathlib import Path

from extract_text import build_corpus, corpus_files, extract_typst


def test_extract_typst_strips_directives(tmp_path: Path) -> None:
    p = tmp_path / "sample.typ"
    p.write_text(
        '#import "foo.typ": bar\n'
        "#set text(size: 10pt)\n"
        "\n"
        "= Kapitel Eins\n"
        "\n"
        "Dies ist ein Absatz mit normalem Text.\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "import" not in result
    assert "set text" not in result
    assert "Kapitel Eins" in result
    assert "normalem Text" in result


def test_extract_typst_captures_paragraph_prose(tmp_path: Path) -> None:
    """Paragraph text outside of brackets must appear in the corpus."""
    p = tmp_path / "ch_test.typ"
    p.write_text(
        '#import "../../theme/zh-mba.typ": callout\n'
        "\n"
        "= Grundsätzliche Idee\n"
        "\n"
        "Die Wegleitung des Staatssekretariats bildet die Grundlage.\n"
        "\n"
        "- geschätzte Ausführungsdauer\n"
        "- geplanter Ausführungszeitraum\n"
        "\n"
        "#callout[\n"
        "  Die Erfahrung zeigt bewährte Ansätze.\n"
        "]\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "Grundsätzliche Idee" in result
    assert "Wegleitung des Staatssekretariats" in result
    assert "geschätzte Ausführungsdauer" in result
    assert "Erfahrung zeigt bewährte Ansätze" in result


def test_extract_typst_strips_inline_functions(tmp_path: Path) -> None:
    p = tmp_path / "sample.typ"
    p.write_text(
        "= Titel\n"
        "\n"
        "#strong[Plattformentwicklung]: \\\n"
        "Zuständig für den Aufbau der Infrastruktur.\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "strong" not in result
    assert "Plattformentwicklung" in result
    assert "Zuständig für den Aufbau" in result


def test_extract_typst_timeline_entry_preserves_label_and_body(tmp_path: Path) -> None:
    """#timeline_entry([label])[body] must extract both label and body prose."""
    p = tmp_path / "sample.typ"
    p.write_text(
        "#timeline_entry([November – Dezember])[\n"  # noqa: RUF001
        "  Orientierung über das Qualifikationsverfahren.\n"
        "]\n"
        "\n"
        "#timeline_entry([März – Juni], last: true)[\n"  # noqa: RUF001
        "  Korrektur und Notengebung durch Fachkraft.\n"
        "]\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "November – Dezember" in result  # noqa: RUF001
    assert "Orientierung über das Qualifikationsverfahren" in result
    assert "Korrektur und Notengebung durch Fachkraft" in result
    assert "timeline_entry" not in result
    assert "last" not in result


def test_extract_typst_nested_parens_in_label(tmp_path: Path) -> None:
    """Brackets inside parenthesized args with nested parens must not corrupt depth."""
    p = tmp_path / "sample.typ"
    p.write_text(
        "#term_block([Am dritten Besuch (Präsentation und Demonstration)])[\n"
        "  Das Expertenteam bewertet die Arbeit.\n"
        "]\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "Präsentation und Demonstration" in result
    assert "Expertenteam bewertet die Arbeit" in result
    assert "term_block" not in result


def test_extract_typst_skips_short_and_colour_chunks(tmp_path: Path) -> None:
    p = tmp_path / "sample.typ"
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


def test_extract_typst_cleans_nested_strong_in_bracket(tmp_path: Path) -> None:
    """#strong[...] nested inside a bracket should be cleaned to prose."""
    p = tmp_path / "sample.typ"
    p.write_text(
        "[#strong[Total Pauschale aller Beträge]]\n",
        encoding="utf-8",
    )
    result = extract_typst(p)
    assert "Total Pauschale aller Beträge" in result
    assert "#strong" not in result


def test_corpus_files_finds_chapters_body_and_changelog(tmp_path: Path) -> None:
    ch = tmp_path / "src" / "chapters"
    ch.mkdir(parents=True)
    (ch / "ch01.typ").write_text("= Eins\n", encoding="utf-8")
    (ch / "ch02.typ").write_text("= Zwei\n", encoding="utf-8")
    body = tmp_path / "src" / "body-hex-nex.typ"
    body.write_text("= HEX\n", encoding="utf-8")
    changelog = tmp_path / "src" / "changelog.typ"
    changelog.write_text("#heading(numbering: none)[Änderungshistorie]\n", encoding="utf-8")
    layout = tmp_path / "src" / "layout.typ"
    layout.write_text("#let x = 1\n", encoding="utf-8")

    found = corpus_files(tmp_path)
    names = [p.name for p in found]
    assert "ch01.typ" in names
    assert "ch02.typ" in names
    assert "body-hex-nex.typ" in names
    assert "changelog.typ" in names
    assert "layout.typ" not in names


def test_build_corpus_normalises_whitespace(tmp_path: Path) -> None:
    ch = tmp_path / "src" / "chapters"
    ch.mkdir(parents=True)
    (ch / "ch01.typ").write_text(
        "= Test\n\n#term_block[Sende eine E Mail an die  Fachkraft für Informatik.]\n",
        encoding="utf-8",
    )
    result = build_corpus(tmp_path)
    assert "E-Mail" in result
    assert "  " not in result


def test_build_corpus_includes_paragraph_prose(tmp_path: Path) -> None:
    """Regression guard: plain paragraphs must appear in the final corpus."""
    ch = tmp_path / "src" / "chapters"
    ch.mkdir(parents=True)
    (ch / "ch01.typ").write_text(
        '#import "../../theme/zh-mba.typ": callout\n'
        "\n"
        "= Kapitel\n"
        "\n"
        "Die vorgesetzte Fachkraft formuliert die Aufgabenstellung.\n"
        "\n"
        "#callout[\n"
        "  Wichtige Hinweise zur Prüfung.\n"
        "]\n",
        encoding="utf-8",
    )
    result = build_corpus(tmp_path)
    assert "vorgesetzte Fachkraft formuliert" in result
    assert "Wichtige Hinweise zur Prüfung" in result


def test_corpus_files_includes_entrypoints(tmp_path: Path) -> None:
    """Entrypoint .typ files contain prose that should be spell-checked."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "chapters").mkdir()
    (src / "chapters" / "ch01.typ").write_text("= Eins\n", encoding="utf-8")
    (src / "leitfaden.typ").write_text(
        '#import "layout.typ": cover_page\n\nWir wünschen ein gutes Gelingen!\n',
        encoding="utf-8",
    )
    (src / "leitfaden-hex-nex.typ").write_text(
        '#import "layout.typ": cover_page\n\nErgänzung zum allgemeinen Leitfaden.\n',
        encoding="utf-8",
    )

    found = corpus_files(tmp_path)
    names = [p.name for p in found]
    assert "leitfaden.typ" in names
    assert "leitfaden-hex-nex.typ" in names


