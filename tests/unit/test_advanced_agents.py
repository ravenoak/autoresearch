import pytest
from unittest.mock import MagicMock, patch

from autoresearch.agents.specialized.domain_specialist import DomainSpecialistAgent
from autoresearch.agents.specialized.moderator import ModeratorAgent
from autoresearch.agents.specialized.user_agent import UserAgent
from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.phases import DialoguePhase
from autoresearch.config.models import ConfigModel
from typing import Any


@pytest.fixture
def mock_llm_adapter() -> Any:
    with patch("autoresearch.agents.base.LLMAdapter", autospec=True) as m:
        adapter = m.return_value
        adapter.generate.return_value = "LLM response"
        yield adapter


@pytest.fixture
def mock_config() -> Any:
    cfg = MagicMock(spec=ConfigModel)
    cfg.default_model = "test-model"
    cfg.max_results_per_query = 3
    cfg.agent_config = MagicMock()
    cfg.agent_config.get.return_value = None
    return cfg


@pytest.fixture
def medical_state() -> Any:
    state = QueryState(query="How does a doctor treat flu?")
    state.claims = [
        {"id": "1", "type": "thesis", "content": "Doctors prescribe medicine"},
        {"id": "2", "type": "research_findings", "content": "Studies on flu"},
    ]
    return state


@pytest.fixture
def dialogue_state() -> Any:
    state = QueryState(query="Discuss climate change")
    state.claims = [
        {"id": "1", "agent": "A", "type": "thesis", "content": "It is warming"},
        {"id": "2", "agent": "B", "type": "antithesis", "content": "However it cools"},
        {"id": "3", "agent": "A", "type": "research_findings", "content": "Data shows trends"},
    ]
    return state


def test_domain_specialist_execute(mock_llm_adapter: Any, medical_state: Any, mock_config: Any) -> None:
    agent = DomainSpecialistAgent(name="Spec", llm_adapter=mock_llm_adapter)
    with patch("autoresearch.search.Search.external_lookup") as mock_search:
        mock_search.return_value = [{"title": "t", "content": "c", "url": "u"}]
        result = agent.execute(medical_state, mock_config)
    assert result["claims"][0]["type"] == "domain_analysis"
    assert result["claims"][1]["type"] == "domain_recommendations"
    assert result["metadata"]["domain"] == "medicine"
    assert result["metadata"]["phase"] == DialoguePhase.ANALYSIS
    assert set(result["metadata"]["analyzed_claims"]) == {"1"}
    assert mock_llm_adapter.generate.call_count == 2


def test_domain_specialist_can_execute(mock_config: Any) -> None:
    agent = DomainSpecialistAgent(name="Spec")
    state = QueryState(query="medical health treatment for patient disease")
    agent.domain = "medicine"
    assert agent.can_execute(state, mock_config)
    agent.domain = "finance"
    assert not agent.can_execute(state, mock_config)
    mock_config.specialist_domains = ["finance"]
    assert agent.can_execute(state, mock_config)


def test_moderator_execute(mock_llm_adapter: Any, dialogue_state: Any, mock_config: Any) -> None:
    agent = ModeratorAgent(name="Mod", llm_adapter=mock_llm_adapter)
    result = agent.execute(dialogue_state, mock_config)
    assert result["claims"][0]["type"] == "moderation"
    assert result["claims"][1]["type"] == "guidance"
    assert result["metadata"]["phase"] == DialoguePhase.MODERATION
    assert result["metadata"]["conflicts_identified"]
    assert mock_llm_adapter.generate.call_count == 2


def test_moderator_can_execute(dialogue_state: Any, mock_config: Any) -> None:
    agent = ModeratorAgent(name="Mod")
    assert agent.can_execute(dialogue_state, mock_config)
    small = QueryState(query="q", claims=dialogue_state.claims[:2])
    assert not agent.can_execute(small, mock_config)
    single_agent = QueryState(query="q", claims=[
        {"id": "1", "agent": "A", "type": "thesis"},
        {"id": "2", "agent": "A", "type": "antithesis"},
        {"id": "3", "agent": "A", "type": "statement"},
    ])
    assert not agent.can_execute(single_agent, mock_config)


def test_user_agent_execute(mock_llm_adapter: Any, medical_state: Any, mock_config: Any) -> None:
    state = medical_state
    state.cycle = 1
    state.results = {"summary": "s"}
    agent = UserAgent(name="User", llm_adapter=mock_llm_adapter)
    result = agent.execute(state, mock_config)
    assert result["claims"][0]["type"] == "user_feedback"
    assert result["claims"][1]["type"] == "user_requirements"
    assert result["metadata"]["phase"] == DialoguePhase.FEEDBACK
    assert "user_preferences" in result["metadata"]
    assert mock_llm_adapter.generate.call_count == 2


def test_user_agent_can_execute(medical_state: Any, mock_config: Any) -> None:
    agent = UserAgent(name="User")
    medical_state.cycle = 1
    assert agent.can_execute(medical_state, mock_config)
    empty = QueryState(query="q")
    empty.cycle = 1
    assert not agent.can_execute(empty, mock_config)
    medical_state.cycle = 0
    assert not agent.can_execute(medical_state, mock_config)


def test_planner_metadata(mock_llm_adapter: Any, mock_config: Any) -> None:
    state = QueryState(query="q")
    agent = PlannerAgent(name="Planner", llm_adapter=mock_llm_adapter)
    result = agent.execute(state, mock_config)
    assert result["metadata"]["phase"] == DialoguePhase.PLANNING
    assert result["claims"][0]["type"] == "research_plan"
    assert mock_llm_adapter.generate.called
