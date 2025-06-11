from unittest.mock import patch

from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
from autoresearch.agents.dialectical.contrarian import ContrarianAgent
from autoresearch.agents.dialectical.fact_checker import FactChecker
from autoresearch.orchestration.state import QueryState
from autoresearch.config import ConfigModel


class MockAdapter:
    def generate(self, prompt: str, model: str | None = None, **kwargs):
        return f"mocked:{prompt}"


@patch("autoresearch.agents.dialectical.synthesizer.get_llm_adapter")
def test_synthesizer_dynamic(mock_get):
    mock_get.return_value = MockAdapter()
    state = QueryState(query="q")
    cfg = ConfigModel()
    agent = SynthesizerAgent(name="Synthesizer")
    result = agent.execute(state, cfg)
    assert result["claims"][0]["content"].startswith("mocked:")


@patch("autoresearch.agents.dialectical.contrarian.get_llm_adapter")
def test_contrarian_dynamic(mock_get):
    mock_get.return_value = MockAdapter()
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "thesis", "content": "a"}],
    )
    cfg = ConfigModel()
    agent = ContrarianAgent(name="Contrarian")
    result = agent.execute(state, cfg)
    assert result["claims"][0]["type"] == "antithesis"
    assert result["claims"][0]["content"].startswith("mocked:")


@patch("autoresearch.agents.dialectical.fact_checker.get_llm_adapter")
@patch("autoresearch.agents.dialectical.fact_checker.Search.external_lookup")
def test_fact_checker_sources(mock_search, mock_get):
    mock_get.return_value = MockAdapter()
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
