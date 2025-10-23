# mypy: ignore-errors
import importlib

import pytest
from typer.testing import CliRunner

from autoresearch.cli_utils import (
    get_console,
    render_metrics_panel,
    set_bare_mode,
    summary_table,
)

pytestmark = pytest.mark.usefixtures("dummy_storage")


def test_render_metrics_panel_bare_mode(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_BARE_MODE", "1")
    set_bare_mode(True)
    try:
        renderable = render_metrics_panel({"a": 1, "b": 2})
        assert isinstance(renderable, str)
        assert "a" in renderable
        assert "#" in renderable
    finally:
        monkeypatch.delenv("AUTORESEARCH_BARE_MODE", raising=False)
        set_bare_mode(False)


def test_summary_table_render():
    table = summary_table({"x": 1})
    console = get_console(force_refresh=True)
    with console.capture() as capture:
        console.print(table)
    output = capture.get()
    assert "x" in output
    assert "1" in output


def test_search_visualize_option(monkeypatch, dummy_storage):
    """Test that the search command includes the visualize option in its help."""
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.config.models import ConfigModel

    def _load(self):
        return ConfigModel.model_construct(loops=1)

    monkeypatch.setattr(ConfigLoader, "load_config", _load)
    main = importlib.import_module("autoresearch.main")

    runner = CliRunner()
    result = runner.invoke(main.app, ["search", "--help"])
    assert result.exit_code == 0
    assert "--visualize" in result.stdout
