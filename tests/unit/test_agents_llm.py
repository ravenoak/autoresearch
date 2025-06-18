from unittest.mock import patch

from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.agents.dialectical.contrarian import ContrarianAgent
from autoresearch.agents.dialectical.fact_checker import FactChecker
from autoresearch.agents.registry import AgentFactory
from autoresearch.orchestration.state import QueryState
from autoresearch.config import ConfigModel
from autoresearch.llm.adapters import LLMAdapter


class MockAdapter(LLMAdapter):
    """Mock LLM adapter for testing."""

    # Include common model names for testing
    available_models = ["mock-model", "gpt-3.5-turbo", "gpt-4", "llama2", "mistral"]

    def generate(self, prompt: str, model: str | None = None, **kwargs):
        # For testing, we'll accept any model name
        if model is None:
            model = self.available_models[0]
        return f"mocked:{prompt}"

    def validate_model(self, model: str | None) -> str:
        """Override to accept any model name for testing."""
        if model is None:
            return self.available_models[0]
        return model


# Tests using dependency injection (new approach)
def test_synthesizer_with_injected_adapter():
    """Test SynthesizerAgent with an injected adapter."""
    state = QueryState(query="q")
    cfg = ConfigModel()
    mock_adapter = MockAdapter()
    agent = SynthesizerAgent(name="Synthesizer", llm_adapter=mock_adapter)
    result = agent.execute(state, cfg)
    assert result["claims"][0]["content"].startswith("mocked:")


def test_contrarian_with_injected_adapter():
    """Test ContrarianAgent with an injected adapter."""
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "thesis", "content": "a"}],
    )
    cfg = ConfigModel()
    mock_adapter = MockAdapter()
    agent = ContrarianAgent(name="Contrarian", llm_adapter=mock_adapter)
    result = agent.execute(state, cfg)
    assert result["claims"][0]["type"] == "antithesis"
    assert result["claims"][0]["content"].startswith("mocked:")


@patch("autoresearch.agents.dialectical.fact_checker.Search.external_lookup")
def test_fact_checker_with_injected_adapter(mock_search):
    """Test FactChecker with an injected adapter."""
    mock_search.return_value = [{"title": "t", "url": "u"}]
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "thesis", "content": "a"}],
    )
    cfg = ConfigModel()
    mock_adapter = MockAdapter()
    agent = FactChecker(name="FactChecker", llm_adapter=mock_adapter)
    result = agent.execute(state, cfg)
    assert result["sources"][0]["checked_claims"] == ["1"]
    assert result["metadata"]["source_count"] == 1


# Tests using AgentFactory with injected adapters
def test_agent_factory_with_injected_adapter():
    """Test creating agents through the factory with injected adapters."""
    # Register the agent classes if not already registered
    AgentFactory.register("Synthesizer", SynthesizerAgent)
    AgentFactory.register("Contrarian", ContrarianAgent)
    AgentFactory.register("FactChecker", FactChecker)

    # Create a mock adapter
    mock_adapter = MockAdapter()

    # Create agents through the factory with the injected adapter
    synthesizer = AgentFactory.create("Synthesizer", llm_adapter=mock_adapter)
    contrarian = AgentFactory.create("Contrarian", llm_adapter=mock_adapter)
    fact_checker = AgentFactory.create("FactChecker", llm_adapter=mock_adapter)

    # Verify that the adapters were injected
    assert synthesizer.llm_adapter is mock_adapter
    assert contrarian.llm_adapter is mock_adapter
    assert fact_checker.llm_adapter is mock_adapter

    # Test that the agents work with the injected adapter
    state = QueryState(
        query="q", claims=[{"id": "1", "type": "thesis", "content": "a"}]
    )
    cfg = ConfigModel()

    # Test synthesizer
    result = synthesizer.execute(state, cfg)
    assert result["claims"][0]["content"].startswith("mocked:")

    # Test contrarian
    result = contrarian.execute(state, cfg)
    assert result["claims"][0]["type"] == "antithesis"
    assert result["claims"][0]["content"].startswith("mocked:")


# Legacy tests using patching (kept for backward compatibility)
@patch("autoresearch.agents.base.Agent.get_adapter")
def test_synthesizer_dynamic(mock_get_adapter):
    mock_get_adapter.return_value = MockAdapter()
    state = QueryState(query="q")
    cfg = ConfigModel()
    agent = SynthesizerAgent(name="Synthesizer")
    result = agent.execute(state, cfg)
    assert result["claims"][0]["content"].startswith("mocked:")


@patch("autoresearch.agents.base.Agent.get_adapter")
def test_contrarian_dynamic(mock_get_adapter):
    mock_get_adapter.return_value = MockAdapter()
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "thesis", "content": "a"}],
    )
    cfg = ConfigModel()
    agent = ContrarianAgent(name="Contrarian")
    result = agent.execute(state, cfg)
    assert result["claims"][0]["type"] == "antithesis"
    assert result["claims"][0]["content"].startswith("mocked:")


@patch("autoresearch.agents.base.Agent.get_adapter")
@patch("autoresearch.agents.dialectical.fact_checker.Search.external_lookup")
def test_fact_checker_sources(mock_search, mock_get_adapter):
    mock_get_adapter.return_value = MockAdapter()
    mock_search.return_value = [{"title": "t", "url": "u"}]
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "thesis", "content": "a"}],
    )
    cfg = ConfigModel()
    agent = FactChecker(name="FactChecker")
    result = agent.execute(state, cfg)
    assert result["sources"][0]["checked_claims"] == ["1"]
    assert result["metadata"]["source_count"] == 1
