#!/usr/bin/env python3
"""Extract plain text from Typst files for spelling/grammar checks.

Only prose-bearing files are processed (chapter sources, body content,
changelog).  Layout, theme, and entry-point ``.typ`` wrappers are excluded
so that Typst syntax does not pollute the corpus.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Typst helpers
# ---------------------------------------------------------------------------

# Full-line directives: layout/meta commands that never contain prose.
# ── CONTRACT ──
# When adding new layout helpers to src/layout.typ or theme/*.typ that
# start lines with ``#name(...)``, add the name here so Typst syntax
# does not leak into the spell-check corpus.
_TYP_DIRECTIVE = re.compile(
    r"^\s*#(?:import|include|let|set|show|outline|pagebreak|counter|image|"
    r"table|rect|line|block|align|v|matter|cover_page)\b.*$",
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


def _clean_chunk(chunk: str) -> str:
    """Strip inline Typst function names and stray brackets from bracket content."""
    text = _INLINE_FUNC.sub("", chunk)
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


def extract_typst(path: Path) -> str:
    """Extract prose from a Typst file using a state machine.

    Walks character-by-character, tracking three states:
    - **depth-0 prose** (bracket_depth == 0, paren_depth == 0): paragraph text
    - **inside function args** (paren_depth > 0): skipped, but brackets
      inside args are still extracted as prose
    - **inside brackets** (bracket_depth > 0): content extracted as-is
    """
    raw = path.read_text(encoding="utf-8")
    raw = _TYP_DIRECTIVE.sub("\n", raw)

    parts: list[str] = []
    bracket_depth = 0
    paren_depth = 0
    bracket_start: int | None = None
    prose_buf: list[str] = []
    i = 0
    n = len(raw)

    while i < n:
        ch = raw[i]

        if bracket_depth > 0:
            if ch == "[":
                bracket_depth += 1
            elif ch == "]":
                bracket_depth -= 1
                if bracket_depth == 0 and bracket_start is not None:
                    _emit_bracket(raw[bracket_start:i], parts)
                    bracket_start = None
            i += 1

        elif paren_depth > 0:
            if ch == "(":
                paren_depth += 1
                i += 1
            elif ch == ")":
                paren_depth -= 1
                i += 1
            elif ch == "[":
                bracket_depth = 1
                bracket_start = i + 1
                i += 1
            else:
                i += 1

        elif ch == "#" and i + 1 < n and (raw[i + 1].isalpha() or raw[i + 1] == "_"):
            _emit_prose(prose_buf, parts)
            prose_buf = []
            j = i + 1
            while j < n and (raw[j].isalnum() or raw[j] == "_"):
                j += 1
            k = j
            while k < n and raw[k] in " \t":
                k += 1
            if k < n and raw[k] == "(":
                paren_depth = 1
                i = k + 1
            elif k < n and raw[k] == "[":
                bracket_depth = 1
                bracket_start = k + 1
                i = k + 1
            else:
                i = j

        elif ch == "[":
            _emit_prose(prose_buf, parts)
            prose_buf = []
            bracket_depth = 1
            bracket_start = i + 1
            i += 1

        else:
            prose_buf.append(ch)
            i += 1

    _emit_prose(prose_buf, parts)

    return "\n".join(p for p in parts if p)


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
