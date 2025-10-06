# mypy: ignore-errors
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator

pytestmark = pytest.mark.slow


def _setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel(loops=1))

    def dummy_run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: dict[str, Any] | None = None,
        **kwargs: object,
    ) -> QueryResponse:
        return QueryResponse(
            answer="ok",
            citations=["c"],
            reasoning=["r"],
            metrics={
                "m": 1,
                "knowledge_graph": {
                    "summary": {"entity_count": 1, "relation_count": 1},
                    "exports": {"graphml": True, "graph_json": True},
                },
            },
        )

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.export_knowledge_graph_graphml",
        lambda: "<graphml/>",
    )
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.export_knowledge_graph_json",
        lambda: '{"graph": []}',
    )


def test_search_visualize_option_integration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _setup(monkeypatch)
    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "q", "--visualize"])
    assert result.exit_code == 0
    assert "Knowledge Graph" in result.stdout
    assert "m" in result.stdout


def test_visualize_command_integration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _setup(monkeypatch)
    saved: dict[str, str] = {}

    def fake_save(
        result: QueryResponse, path: Path, layout: str = "spring"
    ) -> None:
        saved["path"] = str(path)

    monkeypatch.setattr("autoresearch.visualization.save_knowledge_graph", fake_save)
    runner = CliRunner()
    out_file = tmp_path / "graph.png"
    result = runner.invoke(cli_app, ["visualize", "q", str(out_file)])
    assert result.exit_code == 0
    assert saved.get("path") == str(out_file)
    assert "Graph written" in result.stdout
    assert "Metrics Summary" in result.stdout


def test_graph_export_options(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _setup(monkeypatch)
    runner = CliRunner()
    graphml_path = tmp_path / "graph.graphml"
    graphjson_path = tmp_path / "graph.json"
    result = runner.invoke(
        cli_app,
        [
            "search",
            "q",
            "--graphml",
            str(graphml_path),
            "--graph-json",
            str(graphjson_path),
        ],
    )
    assert result.exit_code == 0
    assert graphml_path.read_text() == "<graphml/>"
    assert graphjson_path.read_text() == '{"graph": []}'
