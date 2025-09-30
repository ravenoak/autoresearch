import pytest
from fastapi.testclient import TestClient

from autoresearch.agents.prompts import PromptTemplate, PromptTemplateRegistry
from autoresearch.api import app
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.errors import SearchError
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.orchestration.state import QueryState
from autoresearch.search import Search
from autoresearch.storage import StorageManager


class DummyAgent:
    def can_execute(self, state, config):
        return False


def test_prompt_registry_unknown() -> None:
    """PromptTemplateRegistry.get raises KeyError for unknown template."""
    with pytest.raises(KeyError):
        PromptTemplateRegistry.get("missing")


def test_prompt_render_missing_variable() -> None:
    """PromptTemplate.render raises KeyError when a variable is missing."""
    tmpl = PromptTemplate(template="Hello ${name}", description="d")
    with pytest.raises(KeyError):
        tmpl.render()


def test_check_agent_can_execute_false() -> None:
    """_check_agent_can_execute returns False when the agent skips execution."""
    cfg = ConfigModel()
    state = QueryState(query="q")
    agent = DummyAgent()
    assert not OrchestrationUtils.check_agent_can_execute(agent, "Dummy", state, cfg)


def test_external_lookup_unknown_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown search backend triggers SearchError."""
    cfg = ConfigModel()
    cfg.search.backends = ["missing"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr(
        "autoresearch.search.core.get_cached_results",
        lambda *_, **__: (_ for _ in ()).throw(
            AssertionError("cache lookup should not occur for unknown backends")
        ),
    )
    with pytest.raises(SearchError):
        Search.external_lookup("q")


def test_vector_search_vss_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Vector search returns an empty list when VSS is unavailable."""
    monkeypatch.setattr(StorageManager, "has_vss", lambda: False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    monkeypatch.setattr(StorageManager.context, "db_backend", object())
    assert StorageManager.vector_search([0.1, 0.2, 0.3]) == []


def test_query_endpoint_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """/query returns 422 when required fields are missing."""
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.api.routing.get_config", lambda: cfg)
    client = TestClient(app)
    resp = client.post("/query", json={})
    assert resp.status_code == 422
