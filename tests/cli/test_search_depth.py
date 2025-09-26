import pytest
from typer.testing import CliRunner

from autoresearch.main.app import app as cli_app
from autoresearch.models import QueryResponse

pytestmark = pytest.mark.integration


class DummyProgress:
    def __enter__(self) -> "DummyProgress":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def add_task(self, *args: object, **kwargs: object) -> int:
        return 0

    def update(self, *args: object, **kwargs: object) -> None:
        return None


class DummyPrompt:
    @staticmethod
    def ask(*args: object, **kwargs: object) -> str:
        return ""


@pytest.fixture
def cli_environment(monkeypatch: pytest.MonkeyPatch) -> QueryResponse:
    from autoresearch.config.models import ConfigModel

    dummy_response = QueryResponse(
        query="depth test",
        answer="An extended answer about adaptive depth rendering.",
        citations=["Source A", "Source B"],
        reasoning=["Initial reasoning", "Follow-up check"],
        metrics={"tokens": 42, "latency_ms": 12},
        claim_audits=[
            {
                "claim_id": "1",
                "status": "supported",
                "entailment_score": 0.92,
                "sources": [{"title": "Whitepaper"}],
            }
        ],
    )

    class DummyOrchestrator:
        def __init__(self) -> None:  # pragma: no cover - interface shim
            return None

        def run_query(self, *args: object, **kwargs: object) -> QueryResponse:
            return dummy_response

    class DummyStorage:
        @staticmethod
        def setup() -> None:  # pragma: no cover - interface shim
            return None

        @staticmethod
        def load_ontology(*_args: object, **_kwargs: object) -> None:  # pragma: no cover
            return None

    monkeypatch.setattr("autoresearch.main.app.Orchestrator", DummyOrchestrator)
    monkeypatch.setattr("autoresearch.main.app.StorageManager", DummyStorage)
    monkeypatch.setattr(
        "autoresearch.main.app._config_loader.load_config",
        lambda: ConfigModel(),
    )
    monkeypatch.setattr("autoresearch.main.app.Progress", DummyProgress)
    monkeypatch.setattr("autoresearch.main.app.Prompt", DummyPrompt)
    return dummy_response


def test_cli_depth_tldr(cli_runner: CliRunner, cli_environment: QueryResponse) -> None:
    result = cli_runner.invoke(cli_app, ["search", "depth test", "--depth", "tldr"])
    assert result.exit_code == 0
    assert "# TL;DR" in result.stdout
    assert "Key findings are hidden" in result.stdout


def test_cli_depth_trace_json(cli_runner: CliRunner, cli_environment: QueryResponse) -> None:
    result = cli_runner.invoke(
        cli_app,
        ["search", "depth test", "--depth", "trace", "--output", "json"],
    )
    assert result.exit_code == 0
    assert '"raw_response"' in result.stdout
    assert '"key_findings"' in result.stdout
