#!/usr/bin/env python3
"""Extract plain text from Typst files for spelling/grammar checks.

Only prose-bearing files are processed (chapter sources, body content).
Layout, theme, and entry-point `.typ` wrappers are excluded so that Typst
syntax does not pollute the corpus.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Typst helpers
# ---------------------------------------------------------------------------

_TYP_DIRECTIVE = re.compile(
    r"^\s*#(?:import|include|let|set|show|outline|pagebreak|counter|image|"
    r"table|rect|line|block|align|v|matter|cover_page|chapter_opener)\b.*$",
    re.MULTILINE,
)
_TYP_HEADING = re.compile(r"(?m)^=+\s+(.+)$")


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
    if c.startswith("#") and len(c) < 30 and "/" not in c:
        return True
    return False


def extract_typst(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    raw = _TYP_DIRECTIVE.sub("\n", raw)

    parts: list[str] = []

    for m in _TYP_HEADING.finditer(raw):
        parts.append(m.group(1).strip())

    depth = 0
    start: int | None = None
    for i, ch in enumerate(raw):
        if ch == "[":
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = raw[start:i]
                if not _skip_bracket_chunk(chunk):
                    parts.append(chunk.strip())
                start = None

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
