"""Unit tests for specialized agents."""

import json
from unittest.mock import MagicMock, patch

import pytest

from autoresearch.agents.specialized.researcher import ResearcherAgent
from autoresearch.agents.specialized.critic import CriticAgent
from autoresearch.agents.specialized.summarizer import SummarizerAgent
from autoresearch.agents.specialized.planner import PlannerAgent
from autoresearch.orchestration.state import QueryState
from autoresearch.agents.feedback import FeedbackEvent
from autoresearch.config.models import ConfigModel


@pytest.fixture
def mock_llm_adapter():
    """Create a mock LLM adapter for testing."""
    # Create a proper mock of the LLMAdapter class
    with patch(
        "autoresearch.agents.base.LLMAdapter", autospec=True
    ) as mock_adapter_class:
        # Create an instance of the mocked class
        adapter = mock_adapter_class.return_value
        adapter.generate.return_value = "Mock response from LLM"
        yield adapter


@pytest.fixture
def mock_state():
    """Create a mock query state for testing."""
    state = QueryState(query="Test query")
    state.claims = [
        {"id": "1", "type": "thesis", "content": "This is a thesis claim"},
        {"id": "2", "type": "antithesis", "content": "This is an antithesis claim"},
        {
            "id": "3",
            "type": "research_findings",
            "content": "These are research findings",
        },
    ]
    return state


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock(spec=ConfigModel)
    config.max_results_per_query = 3
    config.search = MagicMock(max_results_per_query=3)
    config.default_model = "test-model"

    # Add agent_config attribute with get method
    config.agent_config = MagicMock()
    config.agent_config.get.return_value = None

    return config


def test_researcher_agent_execute(mock_llm_adapter, mock_state, mock_config):
    """Test that the ResearcherAgent executes correctly."""
    # Arrange
    agent = ResearcherAgent(name="Researcher", llm_adapter=mock_llm_adapter)

    # Mock the search functionality
    with patch("autoresearch.search.Search.external_lookup") as mock_search:
        mock_search.return_value = [
            {"title": "Source 1", "content": "Content 1"},
            {"title": "Source 2", "content": "Content 2"},
        ]

        # Act
        result = agent.execute(mock_state, mock_config)

        # Assert
        assert result is not None
        assert "claims" in result
        assert len(result["claims"]) == 1
        assert result["claims"][0]["type"] == "research_findings"
        assert "results" in result
        assert "research_findings" in result["results"]
        assert result["results"]["research_findings"] == "Mock response from LLM"
        assert "sources" in result
        assert len(result["sources"]) == 2

        # Verify the search was called with the correct parameters
        mock_search.assert_called_once_with(
            mock_state.query,
            max_results=mock_config.search.max_results_per_query * 2,
        )

        # Verify the LLM adapter was called with the correct parameters
        mock_llm_adapter.generate.assert_called_once()
        args, kwargs = mock_llm_adapter.generate.call_args
        assert (
            "You are a Researcher agent responsible for conducting in-depth research on a topic"
            in args[0]
        )
        assert "Your research findings should be thorough, well-organized" in args[0]
        assert kwargs["model"] == "test-model"


def test_critic_agent_execute(mock_llm_adapter, mock_state, mock_config):
    """Test that the CriticAgent executes correctly."""
    # Arrange
    agent = CriticAgent(name="Critic", llm_adapter=mock_llm_adapter)

    # Act
    result = agent.execute(mock_state, mock_config)

    # Assert
    assert result is not None
    assert "claims" in result
    assert len(result["claims"]) == 1
    assert result["claims"][0]["type"] == "critique"
    assert "results" in result
    assert "critique" in result["results"]
    assert result["results"]["critique"] == "Mock response from LLM"
    assert "metadata" in result
    assert "evaluated_claims" in result["metadata"]
    assert (
        len(result["metadata"]["evaluated_claims"]) == 2
    )  # thesis and research_findings

    # Verify the LLM adapter was called with the correct parameters
    mock_llm_adapter.generate.assert_called_once()
    args, kwargs = mock_llm_adapter.generate.call_args
    assert (
        "You are a Critic agent responsible for evaluating the quality of research"
        in args[0]
    )
    assert (
        "Your critique should be balanced, highlighting both strengths and areas for improvement"
        in args[0]
    )
    assert kwargs["model"] == "test-model"


def test_summarizer_agent_execute(mock_llm_adapter, mock_state, mock_config):
    """Test that the SummarizerAgent executes correctly."""
    # Arrange
    agent = SummarizerAgent(name="Summarizer", llm_adapter=mock_llm_adapter)

    # Act
    result = agent.execute(mock_state, mock_config)

    # Assert
    assert result is not None
    assert "claims" in result
    assert len(result["claims"]) == 1
    assert result["claims"][0]["type"] == "summary"
    assert "results" in result
    assert "summary" in result["results"]
    assert result["results"]["summary"] == "Mock response from LLM"
    assert "metadata" in result
    assert "summarized_items" in result["metadata"]
    assert result["metadata"]["summarized_items"] == 3  # All claims

    # Verify the LLM adapter was called with the correct parameters
    mock_llm_adapter.generate.assert_called_once()
    args, kwargs = mock_llm_adapter.generate.call_args
    assert (
        "You are a Summarizer agent responsible for generating concise, clear summaries"
        in args[0]
    )
    assert (
        "Your summary should be significantly shorter than the original content"
        in args[0]
    )
    assert kwargs["model"] == "test-model"


def test_planner_agent_execute(mock_llm_adapter, mock_state, mock_config):
    """Test that the PlannerAgent executes correctly."""
    # Arrange
    agent = PlannerAgent(name="Planner", llm_adapter=mock_llm_adapter)

    # Act
    result = agent.execute(mock_state, mock_config)

    # Assert
    assert result is not None
    assert "claims" in result
    assert len(result["claims"]) == 1
    assert result["claims"][0]["type"] == "research_plan"
    assert "results" in result
    assert "research_plan" in result["results"]
    assert result["results"]["research_plan"] == "Mock response from LLM"
    graph = result["results"].get("task_graph")
    assert graph is not None
    assert graph["tasks"], "planner must surface structured tasks"
    assert mock_state.task_graph["tasks"], "state should store planner task graph"

    # Verify the LLM adapter was called with the correct parameters
    mock_llm_adapter.generate.assert_called_once()
    args, kwargs = mock_llm_adapter.generate.call_args
    assert (
        "You are a Planner agent responsible for structuring complex research tasks"
        in args[0]
    )
    assert "Your research plan should be comprehensive, well-organized" in args[0]
    assert kwargs["model"] == "test-model"


def test_planner_agent_parses_json_plan(mock_config):
    """Planner normalises JSON plans into the state task graph."""

    class StubAdapter:
        def generate(self, prompt: str, model: str | None = None) -> str:
            return json.dumps(
                {
                    "tasks": [
                        {
                            "id": "t1",
                            "question": "Collect baseline data",
                            "tools": ["search"],
                        },
                        {
                            "id": "t2",
                            "question": "Synthesize findings",
                            "depends_on": ["t1"],
                            "tools": ["analysis"],
                            "criteria": ["cite sources"],
                        },
                    ],
                }
            )

    state = QueryState(query="Structured task graph demo")
    agent = PlannerAgent(name="Planner", llm_adapter=StubAdapter())
    result = agent.execute(state, mock_config)

    graph = result["results"]["task_graph"]
    assert graph["tasks"][1]["depends_on"] == ["t1"]
    assert graph["tasks"][1]["tools"] == ["analysis"]
    assert state.task_graph["edges"], "edges should capture dependencies"


def test_researcher_agent_can_execute(mock_state, mock_config):
    """Test that the ResearcherAgent can_execute method works correctly."""
    # Arrange
    agent = ResearcherAgent(name="Researcher")

    # Act & Assert
    assert agent.can_execute(mock_state, mock_config) is True

    # Test with disabled agent
    agent.enabled = False
    assert agent.can_execute(mock_state, mock_config) is False


def test_critic_agent_can_execute(mock_state, mock_config):
    """Test that the CriticAgent can_execute method works correctly."""
    # Arrange
    agent = CriticAgent(name="Critic")

    # Act & Assert
    assert agent.can_execute(mock_state, mock_config) is True

    # Test with no claims
    empty_state = QueryState(query="Test query")
    assert agent.can_execute(empty_state, mock_config) is False

    # Test with disabled agent
    agent.enabled = False
    assert agent.can_execute(mock_state, mock_config) is False


def test_summarizer_agent_can_execute(mock_state, mock_config):
    """Test that the SummarizerAgent can_execute method works correctly."""
    # Arrange
    agent = SummarizerAgent(name="Summarizer")

    # Act & Assert
    assert agent.can_execute(mock_state, mock_config) is True

    # Test with no claims
    empty_state = QueryState(query="Test query")
    assert agent.can_execute(empty_state, mock_config) is False

    # Test with disabled agent
    agent.enabled = False
    assert agent.can_execute(mock_state, mock_config) is False


def test_planner_agent_can_execute(mock_state, mock_config):
    """Test that the PlannerAgent can_execute method works correctly."""
    # Arrange
    agent = PlannerAgent(name="Planner")

    # Act & Assert
    # Should return True because mock_state has cycle 0 (even though it has claims)
    assert agent.can_execute(mock_state, mock_config) is True

    # Test with empty state (beginning of process)
    empty_state = QueryState(query="Test query")
    assert agent.can_execute(empty_state, mock_config) is True

    # Test with non-zero cycle and claims
    mock_state.cycle = 1
    assert agent.can_execute(mock_state, mock_config) is False

    # Test with disabled agent
    agent.enabled = False
    assert agent.can_execute(mock_state, mock_config) is False


def test_researcher_agent_processes_feedback(mock_llm_adapter, mock_state, mock_config):
    """Verify feedback influences ResearcherAgent prompts."""
    agent = ResearcherAgent(name="Researcher", llm_adapter=mock_llm_adapter)
    mock_config.enable_feedback = True
    mock_state.add_feedback_event(
        FeedbackEvent(
            source="Critic", target="Researcher", content="More stats", cycle=0
        )
    )

    with patch("autoresearch.search.Search.external_lookup") as mock_search:
        mock_search.return_value = []
        agent.execute(mock_state, mock_config)

        args, _ = mock_llm_adapter.generate.call_args
        assert "More stats" in args[0]
