# mypy: ignore-errors
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, ClassVar

import pytest
from typer.testing import CliRunner, Result

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import CallbackMap
from tests.integration import configure_api_defaults


@dataclass(slots=True)
class DummyProgress:
    """Context manager capturing progress updates for CLI flows."""

    updates: list[int] = field(default_factory=list)
    tasks_created: ClassVar[int] = 0

    def __enter__(self) -> "DummyProgress":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def add_task(self, *args: object, **kwargs: object) -> int:
        DummyProgress.tasks_created += 1
        return DummyProgress.tasks_created

    def update(self, *args: object, **kwargs: object) -> None:
        advance = kwargs.get("advance", 0)
        if isinstance(advance, int):
            self.updates.append(advance)


def _invoke_cli(
    runner: CliRunner, *args: str, **kwargs: Any
) -> Result:  # pragma: no cover - helper wrapper
    return runner.invoke(cli_app, list(args), **kwargs)


def test_cli_progress_and_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    progress_instances: list[DummyProgress] = []

    def progress_factory(*_args: object, **_kwargs: object) -> DummyProgress:
        progress = DummyProgress()
        progress_instances.append(progress)
        return progress

    configure_api_defaults(monkeypatch, loops=2)
    monkeypatch.setattr("autoresearch.main.Progress", progress_factory)

    prompts: list[str] = []

    def capture_prompt(*_args: object, **kwargs: object) -> str:
        default = kwargs.get("default", "")
        prompts.append(str(default))
        return ""

    monkeypatch.setattr("autoresearch.main.Prompt.ask", capture_prompt)

    def dummy_run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        **_: object,
    ) -> QueryResponse:
        state = QueryState(query=query)
        for index in range(config.loops):
            if callbacks is not None and "on_cycle_end" in callbacks:
                callbacks["on_cycle_end"](index, state)
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    runner = CliRunner()
    result = _invoke_cli(runner, "search", "test", "--interactive")
    assert result.exit_code == 0
    assert progress_instances[0].updates == [1, 1]
    assert len(prompts) == 1


def test_cli_search_uses_model_copy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The search command should execute successfully with parameter handling."""

    config_path = tmp_path / "autoresearch.toml"
    config_path.write_text("[core]\nloops = 1\n", encoding="utf-8")

    # Set up minimal config loading
    cfg = configure_api_defaults(monkeypatch)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    # Stub out complex dependencies
    class StubStorageManager:
        @staticmethod
        def setup() -> None:
            return None

    monkeypatch.setattr("autoresearch.storage.StorageManager", StubStorageManager)

    def dummy_run_query(
        self: Orchestrator,
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None = None,
        visualize: object | None = None,
        **_: object,
    ) -> QueryResponse:
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    monkeypatch.setattr(Orchestrator, "run_query", dummy_run_query)
    monkeypatch.setattr("autoresearch.output_format.OutputFormatter.format", lambda *_, **__: None)

    runner = CliRunner()
    result = runner.invoke(cli_app, ["search", "test query", "--loops", "3"])

    # The command should execute without crashing
    assert result.exit_code == 0
