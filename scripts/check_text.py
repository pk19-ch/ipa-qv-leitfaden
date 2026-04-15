#!/usr/bin/env python3
"""Spell-check (hunspell) and grammar/style check (LanguageTool public API).

Exit codes: 0 = clean, 1 = issues found, 2 = infrastructure error (``InfrastructureError``).
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

from extract_text import build_corpus

ROOT = Path(__file__).resolve().parent.parent


class InfrastructureError(Exception):
    """Missing tool or broken setup; ``main()`` maps this to exit code 2."""


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

# ── LanguageTool ignore-list ──────────────────────────────────────────────────
def load_lt_ignore_rules(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    rules: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            rules.add(stripped)
    return rules


# ── Hunspell ──────────────────────────────────────────────────────────────────
def resolve_hunspell_lang(cli_value: str | None) -> str:
    """CLI ``--hunspell-lang`` overrides ``HUNSPELL_LANG``; empty values use ``de_CH``."""
    if cli_value is not None:
        s = cli_value.strip()
        if s:
            return s
    env = (os.environ.get("HUNSPELL_LANG") or "").strip()
    return env or "de_CH"


def hunspell_executable() -> str:
    found = shutil.which("hunspell")
    if not found:
        raise InfrastructureError(
            "hunspell not found; install hunspell and a dictionary for your language",
        )
    return found


def ensure_hunspell_dictionary(hunspell: str, lang: str) -> None:
    """Confirm that hunspell can load the dictionary for ``lang``; raise on failure."""
    proc = subprocess.run(
        [hunspell, "-d", lang, "-i", "utf-8", "-l"],
        input="",
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        msg = (
            f"hunspell cannot load dictionary -d {lang!r} "
            "(install the matching hunspell / dictionary package)"
        )
        if detail:
            msg = f"{msg}\n{detail}"
        raise InfrastructureError(msg)


def hunspell_check(hunspell: str, corpus: str, lang: str, personal: Path) -> list[str]:
    cmd = [hunspell, "-d", lang, "-i", "utf-8", "-l"]
    if personal.is_file():
        cmd.extend(["-p", str(personal)])

    proc = subprocess.run(cmd, input=corpus, capture_output=True, text=True, check=False)
    if proc.returncode not in (0, 1):
        detail = (proc.stderr or proc.stdout or "").strip()
        raise InfrastructureError(detail or f"hunspell exited with code {proc.returncode}")

    words = [w.strip() for w in proc.stdout.splitlines() if w.strip()]
    return sorted({w for w in words if not re.fullmatch(r"[\d./:-]+", w) and len(w) > 1})


# ── LanguageTool (HTTP API) ───────────────────────────────────────────────────

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


def _lt_request(req: urllib.request.Request, max_retries: int = 2) -> dict | None:
    """Send a LanguageTool API request with retries; return parsed JSON or ``None``."""
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except json.JSONDecodeError:
            print("warning: LanguageTool returned malformed JSON", file=sys.stderr)
            return None
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                wait = 2**attempt
                print(f"LanguageTool HTTP {exc.code} — retrying in {wait}s …", file=sys.stderr)
                time.sleep(wait)
                continue
            body = exc.read().decode("utf-8", errors="replace")
            print(f"warning: LanguageTool HTTP {exc.code}: {body}", file=sys.stderr)
            return None
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                wait = 2**attempt
                print(f"LanguageTool request failed — retrying in {wait}s …", file=sys.stderr)
                time.sleep(wait)
                continue
            print(f"warning: LanguageTool unreachable: {exc}", file=sys.stderr)
            return None


def lt_check_chunk(
    text: str,
    *,
    ignore_rules: set[str],
    disabled_categories: str | None,
) -> list[LTMatch] | None:
    """Check a text chunk via LanguageTool; return ``None`` when the API is unreachable."""
    params: dict[str, str] = {"text": text, "language": LT_LANG}
    if disabled_categories:
        params["disabledCategories"] = disabled_categories
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        LT_URL, data=data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
    )
    payload = _lt_request(req)
    if payload is None:
        return None
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


def _run_lt_checks(corpus: str, args: argparse.Namespace) -> tuple[list[str], bool]:
    """Run LanguageTool on the corpus unless skipped.

    Returns ``(formatted_issues, lt_reachable)``.  ``lt_reachable`` is ``False``
    when every chunk failed, so callers can distinguish "clean" from "not checked".
    """
    if args.skip_lt:
        return [], True
    print(f"note: sending corpus to {LT_URL} for grammar checking", file=sys.stderr)
    ignore_rules = load_lt_ignore_rules(ROOT / "dict" / "languagetool-ignore-rules.txt")
    disabled = args.lt_disable_categories.strip() or None
    chunks = lt_chunks(corpus, CHUNK_CHARS)
    issues: list[str] = []
    chunks_ok = 0
    for i, chunk in enumerate(chunks):
        if i:
            time.sleep(CHUNK_PAUSE)
        matches = lt_check_chunk(chunk, ignore_rules=ignore_rules, disabled_categories=disabled)
        if matches is None:
            continue
        chunks_ok += 1
        for m in matches:
            issues.append(format_lt_match(m, chunk))
    return issues, chunks_ok > 0


# ── Main ──────────────────────────────────────────────────────────────────────
def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Spell/grammar check for QV-Leitfaden sources.",
    )
    ap.add_argument(
        "--hunspell-lang",
        default=None,
        help="Overrides HUNSPELL_LANG; default is de_CH when unset or empty.",
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
    args.hunspell_lang = resolve_hunspell_lang(args.hunspell_lang)
    if os.environ.get("SKIP_LANGUAGETOOL", "").strip() in ("1", "true", "yes"):
        args.skip_lt = True
    return args


def main() -> None:
    args = _parse_args()

    try:
        corpus = build_corpus(ROOT)
        if not corpus.strip():
            raise InfrastructureError("empty corpus — no prose files found")

        hunspell = hunspell_executable()
        ensure_hunspell_dictionary(hunspell, args.hunspell_lang)
        bad_words = hunspell_check(hunspell, corpus, args.hunspell_lang, args.personal_dict)
        if bad_words:
            print(f"Spelling — {len(bad_words)} unknown word(s):", file=sys.stderr)
            for w in bad_words:
                print(f"  {w}", file=sys.stderr)
            print("  (add to dict/ipa-personal.pws if correct)", file=sys.stderr)

        lt_issues, lt_reachable = _run_lt_checks(corpus, args)

        if lt_issues:
            print(f"\nLanguageTool — {len(lt_issues)} issue(s):", file=sys.stderr)
            for line in lt_issues:
                print(line, file=sys.stderr)

        if bad_words or lt_issues:
            sys.exit(1)

        checks = "hunspell"
        if not args.skip_lt:
            if lt_reachable:
                checks += " + LanguageTool"
            else:
                print(
                    "warning: LanguageTool was unreachable — grammar check incomplete",
                    file=sys.stderr,
                )
        print(f"OK ({checks})")
    except InfrastructureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
