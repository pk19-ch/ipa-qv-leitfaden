#!/usr/bin/env python3
"""Spell-check (hunspell) and grammar/style check (LanguageTool public API).

Exit codes:
  0 — no issues
  1 — spelling or grammar issues found
  2 — tool/infrastructure error (hunspell missing, empty corpus, etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent


class _LTRuleCategory(TypedDict, total=False):
    id: str


class _LTRule(TypedDict, total=False):
    id: str
    category: _LTRuleCategory


class LTMatch(TypedDict, total=False):
    offset: int
    length: int
    message: str
    rule: _LTRule


LT_URL = os.environ.get("LANGUAGETOOL_URL", "https://api.languagetool.org/v2/check")
LT_LANG = os.environ.get("LANGUAGETOOL_LANG", "de-CH")
CHUNK_CHARS = int(os.environ.get("LANGUAGETOOL_CHUNK", "12000"))
CHUNK_PAUSE = float(os.environ.get("LANGUAGETOOL_PAUSE", "1.25"))

# ---------------------------------------------------------------------------
# LanguageTool ignore-list
# ---------------------------------------------------------------------------


def load_lt_ignore_rules(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    rules: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            rules.add(stripped)
    return rules


# ---------------------------------------------------------------------------
# Hunspell
# ---------------------------------------------------------------------------


def hunspell_check(corpus: str, lang: str, personal: Path) -> list[str]:
    hunspell = shutil.which("hunspell")
    if not hunspell:
        print("error: hunspell not found; install hunspell + hunspell-de-ch", file=sys.stderr)
        sys.exit(2)

    cmd = [hunspell, "-d", lang, "-i", "utf-8", "-l"]
    if personal.is_file():
        cmd.extend(["-p", str(personal)])

    proc = subprocess.run(cmd, input=corpus, capture_output=True, text=True, check=False)
    if proc.returncode not in (0, 1):
        print(proc.stderr or proc.stdout, file=sys.stderr)
        sys.exit(2)

    words = [w.strip() for w in proc.stdout.splitlines() if w.strip()]
    return sorted({w for w in words if not re.fullmatch(r"[\d./:-]+", w) and len(w) > 1})


# ---------------------------------------------------------------------------
# LanguageTool (HTTP API)
# ---------------------------------------------------------------------------


def lt_chunks(text: str, max_len: int) -> list[str]:
    """Split text into paragraph-aligned chunks that fit the API size limit."""
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    buf: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if size + len(p) + 2 > max_len and buf:
            parts.append("\n\n".join(buf))
            buf = [p]
            size = len(p)
        else:
            buf.append(p)
            size += len(p) + 2
    if buf:
        parts.append("\n\n".join(buf))
    return parts


def lt_check_chunk(
    text: str,
    *,
    ignore_rules: set[str],
    disabled_categories: str | None,
) -> list[LTMatch]:
    data = urllib.parse.urlencode(
        {
            "text": text,
            "language": LT_LANG,
            **({"disabledCategories": disabled_categories} if disabled_categories else {}),
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        LT_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                wait = 2**attempt
                print(
                    f"LanguageTool HTTP {exc.code} — retrying in {wait}s …",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            print(f"warning: LanguageTool HTTP {exc.code}: {body}", file=sys.stderr)
            return []
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                wait = 2**attempt
                print(
                    f"LanguageTool request failed — retrying in {wait}s …",
                    file=sys.stderr,
                )
                time.sleep(wait)
                continue
            print(f"warning: LanguageTool unreachable: {exc}", file=sys.stderr)
            return []
    out: list[LTMatch] = []
    for m in payload.get("matches") or []:
        rid = str(m.get("rule", {}).get("id") or "")
        if rid in ignore_rules:
            continue
        cat_id = str((m.get("rule") or {}).get("category", {}).get("id") or "")
        if cat_id in ("TYPOS", "TYPOGRAPHY"):
            continue
        out.append(m)
    return out


def format_lt_match(m: LTMatch, chunk: str) -> str:
    offset = int(m.get("offset", 0))
    length = int(m.get("length", 0))
    msg = m.get("message", "")
    rid = m.get("rule", {}).get("id", "")
    ctx = chunk[max(0, offset - 40) : min(len(chunk), offset + length + 40)]
    ctx = re.sub(r"\s+", " ", ctx)
    frag = chunk[offset : offset + length] if length else ""
    return f'[{rid}] {msg}\n  … {ctx} …\n  ^ "{frag}"'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Spell/grammar check for QV-Leitfaden sources.",
    )
    ap.add_argument(
        "--hunspell-lang",
        default=os.environ.get("HUNSPELL_LANG", "de_CH"),
    )
    ap.add_argument(
        "--personal-dict",
        type=Path,
        default=ROOT / "dict" / "ipa-personal.pws",
    )
    ap.add_argument(
        "--lt-disable-categories",
        default=os.environ.get("LANGUAGETOOL_DISABLE_CATEGORIES", ""),
    )
    ap.add_argument(
        "--skip-lt",
        action="store_true",
        help="Skip LanguageTool (offline / no network).",
    )
    args = ap.parse_args()

    if os.environ.get("SKIP_LANGUAGETOOL", "").strip() in ("1", "true", "yes"):
        args.skip_lt = True

    from extract_text import build_corpus

    corpus = build_corpus(ROOT)
    if not corpus.strip():
        print("error: empty corpus — no prose files found", file=sys.stderr)
        sys.exit(2)

    bad_words = hunspell_check(corpus, args.hunspell_lang, args.personal_dict)
    if bad_words:
        print(f"Spelling — {len(bad_words)} unknown word(s):", file=sys.stderr)
        for w in bad_words:
            print(f"  {w}", file=sys.stderr)
        print("  (add to dict/ipa-personal.pws if correct)", file=sys.stderr)

    lt_issues: list[str] = []
    if not args.skip_lt:
        ignore_rules = load_lt_ignore_rules(ROOT / "dict" / "languagetool-ignore-rules.txt")
        disabled = args.lt_disable_categories.strip() or None
        chunks = lt_chunks(corpus, CHUNK_CHARS)
        for i, chunk in enumerate(chunks):
            if i:
                time.sleep(CHUNK_PAUSE)
            for m in lt_check_chunk(chunk, ignore_rules=ignore_rules, disabled_categories=disabled):
                lt_issues.append(format_lt_match(m, chunk))

    if lt_issues:
        print(f"\nLanguageTool — {len(lt_issues)} issue(s):", file=sys.stderr)
        for line in lt_issues:
            print(line, file=sys.stderr)

    if bad_words or lt_issues:
        sys.exit(1)

    checks = "hunspell"
    if not args.skip_lt:
        checks += " + LanguageTool"
    print(f"OK ({checks})")


if __name__ == "__main__":
    main()
