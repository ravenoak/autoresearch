"""Unit tests for orchestration token utilities."""

from __future__ import annotations

import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.token_utils import (
    AdapterProtocol,
    _execute_with_adapter,
    is_agent_execution_result,
    supports_adapter_mutation,
    supports_adapter_setter,
)


class RecordingAdapter:
    """Adapter stub capturing prompts passed through generate."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate(self, prompt: str, model: str | None = None, **_: object) -> str:
        self.calls.append(prompt)
        return "response"


class KwargAgent:
    """Agent exposing adapter injection through ``execute`` kwargs."""

    def __init__(self) -> None:
        self.adapter: AdapterProtocol | None = None

    def execute(self, state: QueryState, config: ConfigModel, *, adapter: AdapterProtocol) -> dict[str, object]:
        self.adapter = adapter
        return {"agent": "kwarg", "query": state.query, "backend": config.llm_backend}


class MutableAgent:
    """Agent toggling adapters via setter/getter hooks."""

    def __init__(self) -> None:
        self._adapter: AdapterProtocol = RecordingAdapter()

    def set_adapter(self, adapter: AdapterProtocol) -> None:
        self._adapter = adapter

    def get_adapter(self) -> AdapterProtocol:
        return self._adapter

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, object]:
        return {
            "agent": "mutable",
            "adapter_id": id(self._adapter),
            "query": state.query,
            "backend": config.llm_backend,
        }


class StatelessAgent:
    """Agent lacking adapter mutation hooks."""

    def execute(self, state: QueryState, config: ConfigModel) -> dict[str, object]:
        return {"agent": "stateless", "query": state.query, "backend": config.llm_backend}


class InvalidResultAgent:
    """Agent returning a non-mapping result."""

    def execute(self, state: QueryState, config: ConfigModel) -> object:  # pragma: no cover - negative path
        return [state.query, config.llm_backend]


@pytest.fixture()
def query_state() -> QueryState:
    return QueryState(query="test-query")


@pytest.fixture()
def config_model() -> ConfigModel:
    return ConfigModel()


def test_execute_with_adapter_kwarg(query_state: QueryState, config_model: ConfigModel) -> None:
    agent = KwargAgent()
    adapter = RecordingAdapter()

    result = _execute_with_adapter(agent, query_state, config_model, adapter)

    assert result["agent"] == "kwarg"
    assert agent.adapter is adapter


def test_execute_with_mutation_hooks_restores_original(query_state: QueryState, config_model: ConfigModel) -> None:
    agent = MutableAgent()
    original_adapter = agent.get_adapter()
    replacement = RecordingAdapter()

    result = _execute_with_adapter(agent, query_state, config_model, replacement)

    assert result["agent"] == "mutable"
    assert agent.get_adapter() is original_adapter


def test_execute_without_adapter_hooks(query_state: QueryState, config_model: ConfigModel) -> None:
    agent = StatelessAgent()
    adapter = RecordingAdapter()

    result = _execute_with_adapter(agent, query_state, config_model, adapter)

    assert result["agent"] == "stateless"


def test_execute_raises_for_non_mapping_result(query_state: QueryState, config_model: ConfigModel) -> None:
    agent = InvalidResultAgent()
    adapter = RecordingAdapter()

    with pytest.raises(TypeError):
        _execute_with_adapter(agent, query_state, config_model, adapter)


def test_type_guards_detect_adapter_features() -> None:
    mutable = MutableAgent()
    stateless = StatelessAgent()

    assert supports_adapter_setter(mutable)
    assert supports_adapter_mutation(mutable)
    assert not supports_adapter_setter(stateless)
    assert not supports_adapter_mutation(stateless)


def test_is_agent_execution_result_guard() -> None:
    mapping_result = {"key": "value"}
    non_mapping_result = ["value"]

    assert is_agent_execution_result(mapping_result)
    assert not is_agent_execution_result(non_mapping_result)
