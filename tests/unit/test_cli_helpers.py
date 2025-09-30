import inspect
import io
from pathlib import Path

import pytest
import typer
from fastapi import HTTPException
from rich.console import Console

from autoresearch.cli_helpers import (
    find_similar_commands,
    parse_agent_groups,
    handle_command_not_found,
    report_missing_tables,
    require_api_key,
)


pytestmark = pytest.mark.usefixtures("dummy_storage")


def test_find_similar_commands_basic() -> None:
    cmds = ["search", "serve", "backup"]
    matches = find_similar_commands("serch", cmds)
    assert "search" in matches


def test_find_similar_commands_default_threshold() -> None:
    sig = inspect.signature(find_similar_commands)
    assert sig.parameters["threshold"].default == 0.6


def test_parse_agent_groups_parses_nested_lists() -> None:
    groups = ["alpha,beta", "gamma , delta ,", " "]
    assert parse_agent_groups(groups) == [["alpha", "beta"], ["gamma", "delta"]]


def test_find_similar_commands_respects_threshold() -> None:
    cmds = ["search"]
    assert find_similar_commands("serch", cmds, threshold=0.95) == []


def test_parse_agent_groups_discards_empty_groups() -> None:
    assert parse_agent_groups([" ", ", ,"]) == []


def test_require_api_key_missing_header() -> None:
    with pytest.raises(HTTPException) as excinfo:
        require_api_key({})
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Missing API key"
    assert excinfo.value.headers == {"WWW-Authenticate": "API-Key"}


def test_require_api_key_accepts_present_header() -> None:
    # Should not raise when the header is available.
    require_api_key({"X-API-Key": "secret"})


def test_report_missing_tables_sorts_and_prints(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    from autoresearch import cli_utils

    monkeypatch.setattr(cli_utils, "VERBOSITY", cli_utils.Verbosity.VERBOSE)
    report_missing_tables(["b", "a"])
    out = capsys.readouterr().out
    assert "a, b" in out


def test_report_missing_tables_uses_console() -> None:
    buf = io.StringIO()
    console = Console(file=buf)
    report_missing_tables(["b", "a"], console)
    assert "a, b" in buf.getvalue()


def test_handle_command_not_found_suggests_similar(capsys: pytest.CaptureFixture[str]) -> None:
    import click

    @click.group()
    def app() -> None:  # pragma: no cover - no logic needed
        pass

    @app.command()
    def search() -> None:  # pragma: no cover - no logic needed
        pass

    ctx = typer.Context(app)
    with pytest.raises(typer.Exit):
        handle_command_not_found(ctx, "serch")
    output = capsys.readouterr().out
    assert "Did you mean" in output
    assert "search" in output


def test_install_help_text_in_readme() -> None:
    readme = Path(__file__).resolve().parents[2] / "README.md"
    text = readme.read_text()
    assert "dev-minimal` and `test` extras" in text
