import pytest
from fastapi.testclient import TestClient

from autoresearch.agents.prompts import PromptTemplate, PromptTemplateRegistry
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.config.models import ConfigModel, APIConfig
from autoresearch.orchestration.state import QueryState
from autoresearch.search import Search
from autoresearch.storage import StorageManager
from autoresearch.api import app
from autoresearch.errors import SearchError, StorageError


class DummyAgent:
    def can_execute(self, state, config):
        return False


def test_prompt_registry_unknown():
    """PromptTemplateRegistry.get raises KeyError for unknown template."""
    with pytest.raises(KeyError):
        PromptTemplateRegistry.get("missing")


def test_prompt_render_missing_variable():
    """PromptTemplate.render raises KeyError when a variable is missing."""
    tmpl = PromptTemplate(template="Hello ${name}", description="d")
    with pytest.raises(KeyError):
        tmpl.render()


def test_check_agent_can_execute_false():
    """_check_agent_can_execute returns False when the agent skips execution."""
    cfg = ConfigModel()
    state = QueryState(query="q")
    agent = DummyAgent()
    assert not Orchestrator._check_agent_can_execute(agent, "Dummy", state, cfg)


def test_external_lookup_unknown_backend(monkeypatch):
    """Unknown search backend triggers SearchError."""
    cfg = ConfigModel()
    cfg.search.backends = ["missing"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    with pytest.raises(SearchError):
        Search.external_lookup("q")


def test_vector_search_vss_unavailable(monkeypatch):
    """StorageManager.vector_search raises StorageError when VSS is missing."""
    monkeypatch.setattr(StorageManager, "has_vss", lambda: False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    monkeypatch.setattr(StorageManager.context, "db_backend", object())
    with pytest.raises(StorageError):
        StorageManager.vector_search([0.1, 0.2, 0.3])


def test_query_endpoint_validation_error(monkeypatch):
    """/query returns 422 when required fields are missing."""
    cfg = ConfigModel(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr("autoresearch.api.get_config", lambda: cfg)
    client = TestClient(app)
    resp = client.post("/query", json={})
    assert resp.status_code == 422
