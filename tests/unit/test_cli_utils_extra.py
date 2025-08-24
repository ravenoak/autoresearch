from autoresearch.cli_utils import (
    format_error,
    format_success,
    format_warning,
    format_info,
    print_error,
    set_verbosity,
    get_verbosity,
    print_verbose,
    Verbosity,
    ascii_bar_graph,
    summary_table,
)
from rich.console import Console
import os


def test_print_error_suggestion(monkeypatch):
    records = []
    monkeypatch.setattr(
        "autoresearch.cli_utils.console.print",
        lambda m: records.append(str(m)),
    )
    set_verbosity(Verbosity.VERBOSE)
    print_error("msg", suggestion="do this", code_example="run")
    assert any("do this" in r for r in records)
    assert any("run" in r for r in records)


def test_verbosity_roundtrip(monkeypatch):
    set_verbosity(Verbosity.VERBOSE)
    assert get_verbosity() == Verbosity.VERBOSE
    records = []
    monkeypatch.setattr("autoresearch.cli_utils.console.print", lambda m: records.append(m))
    print_verbose("hi")
    assert any("hi" in r for r in records)


def test_set_verbosity_sets_env(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_VERBOSITY", raising=False)
    set_verbosity(Verbosity.QUIET)
    assert os.environ["AUTORESEARCH_VERBOSITY"] == "quiet"
    assert get_verbosity() == Verbosity.QUIET


def test_ascii_and_table_empty():
    assert ascii_bar_graph({}) == "(no data)"
    table = summary_table({})
    console = Console(record=True, color_system=None)
    console.print(table)
    out = console.export_text()
    assert "(empty)" in out


def test_format_functions():
    assert "✓" in format_success("ok")
    assert "✗" in format_error("bad")
    assert "⚠" in format_warning("warn")
    assert "ℹ" in format_info("info")
