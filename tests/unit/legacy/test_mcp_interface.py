# mypy: ignore-errors
from types import MethodType

import pytest

from autoresearch import mcp_interface
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError
from autoresearch.models import QueryResponse


def _mock_load_config() -> ConfigModel:
    return ConfigModel()


@pytest.mark.unit
@pytest.mark.a2a_mcp
@pytest.mark.requires_distributed
def test_client_server_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_interface._config_loader, "load_config", _mock_load_config)

    server = mcp_interface.create_server()

    def success(
        self,
        query: str,
        config: ConfigModel,
        callbacks=None,
        **_kwargs: object,
    ) -> QueryResponse:
        return QueryResponse(
            answer="ok",
            citations=[],
            reasoning=["Socratic check: Did we challenge the initial hypothesis?"],
            metrics={"m": 1},
        )

    monkeypatch.setattr(
        server.orchestrator,
        "run_query",
        MethodType(success, server.orchestrator),
    )

    result = mcp_interface.query("hello", transport=server)

    assert result["answer"] == "ok", (
        "Socratic check: Did the MCP transport return successful results?"
    )
    assert any("Socratic check" in step for step in result["reasoning"]), (
        "Socratic check: Are reflective prompts surfaced on success?"
    )
    assert result["metrics"]["m"] == 1, (
        "Socratic check: Were metrics preserved across the handshake?"
    )


@pytest.mark.unit
@pytest.mark.a2a_mcp
@pytest.mark.requires_distributed
def test_client_server_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mcp_interface._config_loader, "load_config", _mock_load_config)

    server = mcp_interface.create_server()

    def fail(
        self,
        query: str,
        config: ConfigModel,
        **_kwargs: object,
    ) -> QueryResponse:
        raise AgentError("boom", context={"agent": "Stub"})

    monkeypatch.setattr(
        server.orchestrator,
        "run_query",
        MethodType(fail, server.orchestrator),
    )

    result = mcp_interface.query("hello", transport=server)

    assert result["answer"].startswith("Error:"), (
        "Socratic check: Did failure cases propagate structured responses?"
    )
    assert any(step.startswith("Socratic check") for step in result["reasoning"]), (
        "Socratic check: Are diagnostic prompts included on failure?"
    )
    assert result["metrics"].get("error"), (
        "Socratic check: Do metrics expose the failure details?"
    )
