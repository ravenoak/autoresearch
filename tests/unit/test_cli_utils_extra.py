from autoresearch.cli_utils import (
    format_error,
    format_success,
    format_warning,
    format_info,
    print_error,
    print_warning,
    set_verbosity,
    get_verbosity,
    print_verbose,
    Verbosity,
    ascii_bar_graph,
    summary_table,
)
from rich.console import Console
import os
import pytest
from typing import Any


pytestmark = pytest.mark.usefixtures("dummy_storage")


def test_print_error_suggestion(monkeypatch: pytest.MonkeyPatch) -> None:
    records = []
    monkeypatch.setattr(
        "autoresearch.cli_utils.console.print",
        lambda m: records.append(str(m)),
    )
    set_verbosity(Verbosity.VERBOSE)
    print_error("msg", suggestion="do this", code_example="run")
    assert any("do this" in r for r in records)
    assert any("run" in r for r in records)


def test_verbosity_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    set_verbosity(Verbosity.VERBOSE)
    assert get_verbosity() == Verbosity.VERBOSE
    records = []
    monkeypatch.setattr("autoresearch.cli_utils.console.print", lambda m: records.append(m))
    print_verbose("hi")
    assert any("hi" in r for r in records)


def test_set_verbosity_sets_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTORESEARCH_VERBOSITY", raising=False)
    set_verbosity(Verbosity.QUIET)
    assert os.environ["AUTORESEARCH_VERBOSITY"] == "quiet"
    assert get_verbosity() == Verbosity.QUIET


@pytest.mark.parametrize(
    "level",
    [Verbosity.QUIET, Verbosity.NORMAL, Verbosity.VERBOSE],
)
def test_print_error_emits_at_quiet_threshold(level: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    records: list[str] = []
    monkeypatch.setattr(
        "autoresearch.cli_utils.console.print",
        lambda message: records.append(str(message)),
    )
    previous = get_verbosity()
    set_verbosity(level)
    try:
        print_error("boom", min_verbosity=Verbosity.QUIET)
    finally:
        set_verbosity(previous)

    assert records, f"print_error should emit output for level {level}"


def test_print_error_suppressed_when_threshold_higher(monkeypatch: pytest.MonkeyPatch) -> None:
    records: list[str] = []
    monkeypatch.setattr(
        "autoresearch.cli_utils.console.print",
        lambda message: records.append(str(message)),
    )
    previous = get_verbosity()
    set_verbosity(Verbosity.NORMAL)
    try:
        print_error("quiet", min_verbosity=Verbosity.VERBOSE)
    finally:
        set_verbosity(previous)

    assert not records


@pytest.mark.parametrize(
    "level, expected",
    [
        (Verbosity.QUIET, False),
        (Verbosity.NORMAL, True),
        (Verbosity.VERBOSE, True),
    ],
)
def test_print_warning_respects_minimum(level: Any, expected: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    records: list[str] = []
    monkeypatch.setattr(
        "autoresearch.cli_utils.console.print",
        lambda message: records.append(str(message)),
    )
    previous = get_verbosity()
    set_verbosity(level)
    try:
        print_warning("heads up")
    finally:
        set_verbosity(previous)

    assert bool(records) is expected


def test_ascii_and_table_empty() -> None:
    assert ascii_bar_graph({}) == "(no data)"
    table = summary_table({})
    console = Console(record=True, color_system=None)
    console.print(table)
    out = console.export_text()
    assert "(empty)" in out


def test_format_functions() -> None:
    assert "✓" in format_success("ok")
    assert "✗" in format_error("bad")
    assert "⚠" in format_warning("warn")
    assert "ℹ" in format_info("info")
