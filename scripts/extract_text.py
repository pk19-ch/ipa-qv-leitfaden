#!/usr/bin/env python3
"""Extract plain text from Typst files for spelling/grammar checks.

Only prose-bearing files are processed (chapter sources, body content,
changelog).  Layout, theme, and entry-point ``.typ`` wrappers are excluded
so that Typst syntax does not pollute the corpus.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Typst helpers
# ---------------------------------------------------------------------------

# Single-line directives that never contain prose.
# Multi-line functions (table, align, matter, cover_page, …) are handled
# by the state machine's paren/bracket tracking instead — listing them
# here would strip only the first line and orphan continuation lines.
_TYP_DIRECTIVE = re.compile(
    r"^\s*#(?:import|include|let|set|show|outline|pagebreak|v|line)\b.*$",
    re.MULTILINE,
)

_HEADING_MARKER = re.compile(r"(?m)^=+\s+")
_LIST_MARKER = re.compile(r"(?m)^\s*-\s+")
_TYPST_LINE_BREAK = re.compile(r"\\\s*$", re.MULTILINE)
_INLINE_FUNC = re.compile(r"#\w+")

_HAS_LETTERS = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


def _skip_bracket_chunk(chunk: str) -> bool:
    c = chunk.strip()
    if len(c) < 12:
        return True
    if re.fullmatch(r"[\d.\s%ptcm]+", c):
        return True
    if re.fullmatch(r"#?[0-9a-fA-F]{3,8}", c):
        return True
    if "rgb(" in c or "cmyk(" in c:
        return True
    return c.startswith("#") and len(c) < 30 and "/" not in c and "[" not in c


_INLINE_FUNC_CALL = re.compile(r"#\w+\s*\([^)]*\)")


def _clean_chunk(chunk: str) -> str:
    """Strip inline Typst function calls and stray brackets from bracket content."""
    text = _INLINE_FUNC_CALL.sub("", chunk)
    text = _INLINE_FUNC.sub("", text)
    text = text.replace("[", "").replace("]", "")
    return text.strip()


def _clean_prose(text: str) -> str:
    """Strip remaining Typst syntax from depth-0 text, keeping readable prose."""
    text = _HEADING_MARKER.sub("", text)
    text = _LIST_MARKER.sub("", text)
    text = _TYPST_LINE_BREAK.sub("", text)
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not _HAS_LETTERS.search(stripped):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _emit_bracket(chunk: str, parts: list[str]) -> None:
    """Clean and append a bracket chunk if it contains meaningful prose."""
    if _skip_bracket_chunk(chunk):
        return
    cleaned = _clean_chunk(chunk)
    if cleaned and _HAS_LETTERS.search(cleaned):
        parts.append(cleaned)


def _emit_prose(prose_buf: list[str], parts: list[str]) -> None:
    prose = "".join(prose_buf)
    cleaned = _clean_prose(prose)
    if cleaned:
        parts.append(cleaned)


@dataclass
class _ParserState:
    """Mutable state container for the character-by-character Typst parser."""

    raw: str
    i: int = 0
    bracket_depth: int = 0
    paren_depth: int = 0
    bracket_start: int | None = None
    prose_buf: list[str] = field(default_factory=list)
    parts: list[str] = field(default_factory=list)


def _step_bracket(s: _ParserState) -> None:
    ch = s.raw[s.i]
    if ch == "[":
        s.bracket_depth += 1
    elif ch == "]":
        s.bracket_depth -= 1
        if s.bracket_depth == 0 and s.bracket_start is not None:
            _emit_bracket(s.raw[s.bracket_start : s.i], s.parts)
            s.bracket_start = None
    s.i += 1


def _step_paren(s: _ParserState) -> None:
    ch = s.raw[s.i]
    if ch == "(":
        s.paren_depth += 1
    elif ch == ")":
        s.paren_depth -= 1
    elif ch == "[":
        s.bracket_depth = 1
        s.bracket_start = s.i + 1
    s.i += 1


def _enter_func(s: _ParserState, n: int) -> None:
    """Skip ``#func_name`` and enter paren/bracket tracking if followed by ``(`` or ``[``."""
    j = s.i + 1
    while j < n and (s.raw[j].isalnum() or s.raw[j] == "_"):
        j += 1
    k = j
    while k < n and s.raw[k] in " \t":
        k += 1
    if k < n and s.raw[k] == "(":
        s.paren_depth = 1
        s.i = k + 1
    elif k < n and s.raw[k] == "[":
        s.bracket_depth = 1
        s.bracket_start = k + 1
        s.i = k + 1
    else:
        s.i = j


def _step_depth0(s: _ParserState, n: int) -> None:
    ch = s.raw[s.i]
    if ch == "#" and s.i + 1 < n and (s.raw[s.i + 1].isalpha() or s.raw[s.i + 1] == "_"):
        _emit_prose(s.prose_buf, s.parts)
        s.prose_buf = []
        _enter_func(s, n)
    elif ch == "[":
        _emit_prose(s.prose_buf, s.parts)
        s.prose_buf = []
        s.bracket_depth = 1
        s.bracket_start = s.i + 1
        s.i += 1
    else:
        s.prose_buf.append(ch)
        s.i += 1


def extract_typst(path: Path) -> str:
    """Extract prose from a Typst file using a state machine.

    Walks character-by-character, tracking three states via ``_ParserState``:
    depth-0 prose, function args (paren), and bracket content.
    """
    raw = path.read_text(encoding="utf-8")
    raw = _TYP_DIRECTIVE.sub("\n", raw)
    s = _ParserState(raw)
    n = len(raw)
    while s.i < n:
        if s.bracket_depth > 0:
            _step_bracket(s)
        elif s.paren_depth > 0:
            _step_paren(s)
        else:
            _step_depth0(s, n)
    _emit_prose(s.prose_buf, s.parts)
    return "\n".join(p for p in s.parts if p)


# ---------------------------------------------------------------------------
# Corpus assembly
# ---------------------------------------------------------------------------


def corpus_files(root: Path) -> list[Path]:
    """Collect only prose-bearing source files."""
    paths: list[Path] = []
    ch = root / "src" / "chapters"
    if ch.is_dir():
        paths.extend(sorted(ch.glob("*.typ")))
    hex_body = root / "src" / "body-hex-nex.typ"
    if hex_body.is_file():
        paths.append(hex_body)
    changelog = root / "src" / "changelog.typ"
    if changelog.is_file():
        paths.append(changelog)
    for entry in ("leitfaden.typ", "leitfaden-hex-nex.typ"):
        entry_path = root / "src" / entry
        if entry_path.is_file():
            paths.append(entry_path)
    return paths


def build_corpus(root: Path) -> str:
    chunks: list[str] = []
    for path in corpus_files(root):
        chunks.append(extract_typst(path))

    text = "\n\n".join(c.strip() for c in chunks if c and c.strip())
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+:", ":", text)
    text = re.sub(r"(?i)E\s+Mail(s)?", r"E-Mail\1", text)
    text = re.sub(r"(?<=\d)-(?=[A-Za-zÄÖÜäöüß])", " ", text)
    return text.strip()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    sys.stdout.write(build_corpus(root))


if __name__ == "__main__":
    main()
