#!/usr/bin/env python3
"""Tests for check_text.py."""

from __future__ import annotations

import json
import os
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from check_text import (
    InfrastructureError,
    ensure_hunspell_dictionary,
    format_lt_match,
    hunspell_check,
    hunspell_executable,
    load_lt_ignore_rules,
    lt_check_chunk,
    lt_chunks,
    resolve_hunspell_lang,
)


def test_load_lt_ignore_rules_skips_comments_and_blanks(tmp_path: Path) -> None:
    p = tmp_path / "rules.txt"
    p.write_text("# comment\n\nDE_CASE\n  \n# another\nSOME_RULE\n", encoding="utf-8")
    assert load_lt_ignore_rules(p) == {"DE_CASE", "SOME_RULE"}


def test_load_lt_ignore_rules_missing_file(tmp_path: Path) -> None:
    assert load_lt_ignore_rules(tmp_path / "nonexistent.txt") == set()


def test_resolve_hunspell_lang_defaults_when_unset() -> None:
    with patch.dict(os.environ, {}, clear=True):
        assert resolve_hunspell_lang(None) == "de_CH"


def test_resolve_hunspell_lang_from_env() -> None:
    with patch.dict(os.environ, {"HUNSPELL_LANG": "de_DE"}):
        assert resolve_hunspell_lang(None) == "de_DE"


def test_resolve_hunspell_lang_cli_overrides_env() -> None:
    with patch.dict(os.environ, {"HUNSPELL_LANG": "de_DE"}):
        assert resolve_hunspell_lang("de_AT") == "de_AT"


def test_resolve_hunspell_lang_empty_env_falls_back() -> None:
    with patch.dict(os.environ, {"HUNSPELL_LANG": ""}):
        assert resolve_hunspell_lang(None) == "de_CH"


def test_resolve_hunspell_lang_empty_cli_falls_back_to_env() -> None:
    with patch.dict(os.environ, {"HUNSPELL_LANG": "de_DE"}):
        assert resolve_hunspell_lang("") == "de_DE"
        assert resolve_hunspell_lang("  ") == "de_DE"


def test_resolve_hunspell_lang_empty_cli_without_env() -> None:
    with patch.dict(os.environ, {}, clear=True):
        assert resolve_hunspell_lang("") == "de_CH"


def test_lt_chunks_short_text_single_chunk() -> None:
    text = "Ein kurzer Text."
    assert lt_chunks(text, 100) == [text]


def test_lt_chunks_splits_at_paragraph_boundary() -> None:
    para_a = "Absatz eins mit ausreichend Inhalt."
    para_b = "Absatz zwei mit weiterem Inhalt hier."
    text = f"{para_a}\n\n{para_b}"
    chunks = lt_chunks(text, len(para_a) + 5)
    assert len(chunks) == 2
    assert para_a in chunks[0]
    assert para_b in chunks[1]


def test_format_lt_match_includes_context_and_rule() -> None:
    chunk = "Dies ist ein Beispielsatz mit einem Fehler darin."
    match = {
        "offset": 34,
        "length": 6,
        "message": "Möglicher Fehler gefunden.",
        "rule": {"id": "TEST_RULE", "category": {"id": "GRAMMAR"}},
    }
    result = format_lt_match(match, chunk)
    assert "TEST_RULE" in result
    assert "Möglicher Fehler gefunden." in result
    assert "Fehler" in result


@patch("check_text.subprocess.run")
def test_hunspell_check_filters_dedupes_and_sorts(mock_run: MagicMock, tmp_path: Path) -> None:
    """Exercises numeric/short filtering, deduplication, and sorted output."""
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Zzz\n12.5\na\nAaa\n3:00\nZzz\n",
        stderr="",
    )
    result = hunspell_check("/usr/bin/hunspell", "dummy", "de_CH", tmp_path / "dict.pws")
    assert result == ["Aaa", "Zzz"]


@patch("check_text.shutil.which", return_value=None)
def test_hunspell_executable_raises_when_not_found(_mock_which: MagicMock) -> None:
    with pytest.raises(InfrastructureError, match="hunspell not found"):
        hunspell_executable()


@patch("check_text.subprocess.run")
def test_hunspell_check_raises_if_hunspell_errors(
    mock_run: MagicMock,
    tmp_path: Path,
) -> None:
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="hunspell failure")
    with pytest.raises(InfrastructureError, match="hunspell failure"):
        hunspell_check("/usr/bin/hunspell", "x", "de_CH", tmp_path / "dict.pws")


@patch("check_text.subprocess.run")
def test_ensure_hunspell_dictionary_raises_when_probe_fails(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr='Can\'t open affix or dictionary files for dictionary named "de_CH".\n',
    )
    with pytest.raises(InfrastructureError, match="cannot load dictionary"):
        ensure_hunspell_dictionary("/usr/bin/hunspell", "de_CH")


@patch("check_text.subprocess.run")
def test_ensure_hunspell_dictionary_passes_on_probe_ok(mock_run: MagicMock) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
    ensure_hunspell_dictionary("/usr/bin/hunspell", "de_CH")
    args, kwargs = mock_run.call_args
    assert args[0] == ["/usr/bin/hunspell", "-d", "de_CH", "-i", "utf-8", "-l"]
    assert kwargs.get("input") == ""


def _mock_lt_response(matches: list[dict[str, object]]) -> MagicMock:
    payload = json.dumps({"matches": matches}).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__ = MagicMock(side_effect=lambda: resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


@patch("check_text.urllib.request.urlopen")
def test_lt_check_chunk_filters_ignored_rules(mock_urlopen: MagicMock) -> None:
    matches = [
        {
            "rule": {"id": "IGNORED_RULE", "category": {"id": "GRAMMAR"}},
            "offset": 0,
            "length": 5,
            "message": "x",
        },
        {
            "rule": {"id": "REAL_ISSUE", "category": {"id": "GRAMMAR"}},
            "offset": 10,
            "length": 3,
            "message": "y",
        },
    ]
    mock_urlopen.return_value = _mock_lt_response(matches)
    result = lt_check_chunk("test text", ignore_rules={"IGNORED_RULE"}, disabled_categories=None)
    assert len(result) == 1
    assert result[0]["rule"]["id"] == "REAL_ISSUE"


@pytest.mark.parametrize("category", ["TYPOS", "TYPOGRAPHY"])
@patch("check_text.urllib.request.urlopen")
def test_lt_check_chunk_filters_hardcoded_categories(
    mock_urlopen: MagicMock, category: str
) -> None:
    matches = [
        {
            "rule": {"id": "SOME_RULE", "category": {"id": category}},
            "offset": 0,
            "length": 5,
            "message": "filtered",
        },
    ]
    mock_urlopen.return_value = _mock_lt_response(matches)
    result = lt_check_chunk("test text", ignore_rules=set(), disabled_categories=None)
    assert len(result) == 0


@patch("check_text.time.sleep")
@patch("check_text.urllib.request.urlopen")
def test_lt_check_chunk_retries_on_429(
    mock_urlopen: MagicMock,
    _mock_sleep: MagicMock,
) -> None:
    error_resp = urllib.error.HTTPError(
        url="http://test",
        code=429,
        msg="Too Many Requests",
        hdrs=MagicMock(),
        fp=BytesIO(b"rate limited"),
    )
    success_resp = _mock_lt_response([])
    mock_urlopen.side_effect = [error_resp, success_resp]
    result = lt_check_chunk("text", ignore_rules=set(), disabled_categories=None)
    assert result == []
    assert mock_urlopen.call_count == 2


@patch("check_text.time.sleep")
@patch("check_text.urllib.request.urlopen")
def test_lt_check_chunk_soft_fails_after_retries(
    mock_urlopen: MagicMock,
    _mock_sleep: MagicMock,
) -> None:
    error_resp = urllib.error.HTTPError(
        url="http://test",
        code=500,
        msg="Server Error",
        hdrs=MagicMock(),
        fp=BytesIO(b"error"),
    )
    mock_urlopen.side_effect = [error_resp, error_resp, error_resp]
    result = lt_check_chunk("text", ignore_rules=set(), disabled_categories=None)
    assert result is None
    assert mock_urlopen.call_count == 3


@patch("check_text.urllib.request.urlopen")
def test_lt_check_chunk_returns_none_on_malformed_json(
    mock_urlopen: MagicMock,
) -> None:
    resp = MagicMock()
    resp.read.return_value = b"not valid json"
    resp.__enter__ = MagicMock(side_effect=lambda: resp)
    resp.__exit__ = MagicMock(return_value=False)
    mock_urlopen.return_value = resp
    result = lt_check_chunk("text", ignore_rules=set(), disabled_categories=None)
    assert result is None
