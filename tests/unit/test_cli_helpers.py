from autoresearch.cli_helpers import (
    find_similar_commands,
    parse_agent_groups,
    handle_command_not_found,
)
import typer
import pytest
from pathlib import Path


pytestmark = pytest.mark.usefixtures("dummy_storage")


def test_find_similar_commands_basic():
    cmds = ["search", "serve", "backup"]
    matches = find_similar_commands("serch", cmds)
    assert "search" in matches


def test_parse_agent_groups_parses_nested_lists():
    groups = ["alpha,beta", "gamma , delta ,", " "]
    assert parse_agent_groups(groups) == [["alpha", "beta"], ["gamma", "delta"]]


def test_handle_command_not_found_suggests_similar(capsys):
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


def test_install_help_text_in_readme():
    readme = Path(__file__).resolve().parents[2] / "README.md"
    text = readme.read_text()
    assert "dev-minimal` and `test` extras" in text
