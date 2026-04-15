#!/usr/bin/env python3
"""Integration tests for check_text.main() — exit codes and output."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from check_text import InfrastructureError, main


@patch("check_text.build_corpus", return_value="")
def test_main_exit_2_empty_corpus(
    _mock_corpus: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_text", "--skip-lt"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


@patch("check_text.build_corpus", return_value="Ein Satz mit genug Worten hier.")
@patch(
    "check_text.hunspell_executable",
    side_effect=InfrastructureError("simulated missing hunspell"),
)
def test_main_exit_2_infrastructure_error(
    _mock_exe: MagicMock,
    _mock_corpus: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_text", "--skip-lt"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2


@patch("check_text.build_corpus", return_value="Korpus Text.")
@patch("check_text.hunspell_executable", return_value="/usr/bin/hunspell")
@patch("check_text.subprocess.run")
def test_main_exits_1_when_hunspell_lists_unknown_words(
    mock_run: MagicMock,
    _mock_exe: MagicMock,
    _mock_corpus: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_text", "--skip-lt"])
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="Unbekanntwort\n", stderr=""),
    ]
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


@patch("check_text.build_corpus", return_value="Alles in Ordnung hier.")
@patch("check_text.hunspell_executable", return_value="/usr/bin/hunspell")
@patch("check_text.subprocess.run")
def test_main_ok_hunspell_only_when_skip_lt(
    mock_run: MagicMock,
    _mock_exe: MagicMock,
    _mock_corpus: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_text", "--skip-lt"])
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
    ]
    main()
    assert mock_run.call_count == 2
    out = capsys.readouterr().out
    assert "OK (hunspell)" in out


@patch("check_text.build_corpus", return_value="Ein kurzer Text.")
@patch("check_text.hunspell_executable", return_value="/usr/bin/hunspell")
@patch("check_text.subprocess.run")
@patch("check_text.lt_check_chunk", return_value=[])
def test_main_ok_with_languagetool_when_lt_clean(
    _mock_lt: MagicMock,
    mock_run: MagicMock,
    _mock_exe: MagicMock,
    _mock_corpus: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["check_text"])
    mock_run.side_effect = [
        MagicMock(returncode=0, stdout="", stderr=""),
        MagicMock(returncode=0, stdout="", stderr=""),
    ]
    main()
    out = capsys.readouterr().out
    assert "OK (hunspell + LanguageTool)" in out
