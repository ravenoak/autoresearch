"""Integration tests for LM Studio adapter with realistic Autoresearch workloads.

This test uses mocked responses to simulate LM Studio behavior without requiring
a live LM Studio instance. The tests verify that the adapter handles requests
correctly and performs within expected time bounds.

Note: These tests were previously live integration tests but were converted to
mocked tests to prevent CI timeouts and ensure reliable testing without external
dependencies.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from autoresearch.llm.adapters import LMStudioAdapter


@pytest.mark.llm_simple
@pytest.mark.timeout(20)
@patch('autoresearch.llm.adapters.requests.Session.post')
def test_lmstudio_simple_query(mock_post):
    """Verify LM Studio adapter handles simple queries correctly."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Python is a programming language"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    adapter = LMStudioAdapter()

    start = time.time()
    result = adapter.generate("What is Python?", model="test-model", max_tokens=100)
    duration = time.time() - start

    assert duration < 5.0  # Should be very fast with mocked response
    assert result is not None
    assert "Python is a programming language" in result

    # Verify the HTTP call was made correctly
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert "http://localhost:1234/v1/chat/completions" in call_args[0][0]


@pytest.mark.llm_medium
@pytest.mark.timeout(60)
@patch('autoresearch.llm.adapters.requests.Session.post')
def test_lmstudio_research_synthesis(mock_post):
    """Verify LM Studio adapter handles research synthesis correctly."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Python's key characteristics include being a high-level programming language that emphasizes code readability and supports multiple programming paradigms."}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    adapter = LMStudioAdapter()

    prompt = """Based on these sources, synthesize an answer:
Source 1: Python is a high-level programming language.
Source 2: It emphasizes code readability.
Source 3: Python supports multiple paradigms.

Question: What are Python's key characteristics?"""

    start = time.time()
    result = adapter.generate(prompt, model="test-model", max_tokens=300)
    duration = time.time() - start

    assert duration < 5.0  # Should be very fast with mocked response
    assert result is not None
    assert "high-level programming language" in result

    # Verify the HTTP call was made correctly
    mock_post.assert_called_once()


@pytest.mark.llm_complex
@pytest.mark.timeout(120)
@pytest.mark.slow
@patch('autoresearch.llm.adapters.requests.Session.post')
def test_lmstudio_large_context(mock_post):
    """Verify LM Studio adapter handles large context correctly."""
    # Mock successful response for large context
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Computational efficiency insights synthesized from documents..."}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    adapter = LMStudioAdapter()

    # Simulate realistic document analysis
    prompt = f"""You are analyzing research documents. Here are summaries:

Document 1 (1500 words): {'Deep learning overview. ' * 50}
Document 2 (1200 words): {'Healthcare ML applications. ' * 40}
Document 3 (1800 words): {'Programming language evolution. ' * 60}

Question: Synthesize insights about computational efficiency."""

    start = time.time()
    result = adapter.generate(prompt, model="test-model", max_tokens=500)
    duration = time.time() - start

    assert duration < 5.0  # Should be very fast with mocked response
    assert result is not None
    assert "Computational efficiency insights" in result

    # Verify the HTTP call was made correctly
    mock_post.assert_called_once()


@pytest.mark.llm_workflow
@pytest.mark.timeout(180)
@pytest.mark.slow
@patch('autoresearch.llm.adapters.requests.Session.post')
def test_lmstudio_multi_agent_workflow(mock_post):
    """Verify multi-agent sequential workflow adapter behavior."""
    # Mock responses for each step
    responses = [
        MagicMock(),  # Planning
        MagicMock(),  # Research
        MagicMock()   # Synthesis
    ]

    responses[0].json.return_value = {"choices": [{"message": {"content": "Planning step response"}}]}
    responses[1].json.return_value = {"choices": [{"message": {"content": "Research step response"}}]}
    responses[2].json.return_value = {"choices": [{"message": {"content": "Synthesis step response"}}]}

    for response in responses:
        response.raise_for_status.return_value = None

    # Return responses in sequence
    mock_post.side_effect = responses

    adapter = LMStudioAdapter()
    model = "test-model"
    workflow_start = time.time()

    # Step 1: Planning
    plan = adapter.generate(
        "Create a research plan for Python type hints", model=model, max_tokens=150
    )
    assert plan is not None

    # Step 2: Research
    research = adapter.generate("Research type hints benefits...", model=model, max_tokens=200)
    assert research is not None

    # Step 3: Synthesis
    synthesis = adapter.generate("Synthesize findings...", model=model, max_tokens=150)
    assert synthesis is not None

    workflow_duration = time.time() - workflow_start

    assert workflow_duration < 5.0  # Should be very fast with mocked responses
    assert mock_post.call_count == 3  # Three HTTP calls made


@pytest.mark.llm_workflow
@pytest.mark.timeout(180)
@pytest.mark.slow
@patch('autoresearch.llm.adapters.requests.Session.post')
def test_lmstudio_parallel_agents(mock_post):
    """Verify parallel agent execution adapter behavior."""
    import concurrent.futures

    # Mock responses for each agent
    responses = [
        MagicMock(),
        MagicMock(),
        MagicMock()
    ]

    responses[0].json.return_value = {"choices": [{"message": {"content": "Agent 0 analysis"}}]}
    responses[1].json.return_value = {"choices": [{"message": {"content": "Agent 1 analysis"}}]}
    responses[2].json.return_value = {"choices": [{"message": {"content": "Agent 2 analysis"}}]}

    for response in responses:
        response.raise_for_status.return_value = None

    # Return responses in sequence (parallel requests will be mocked)
    mock_post.side_effect = responses

    adapter = LMStudioAdapter()
    model = "test-model"

    def agent_task(agent_id):
        return adapter.generate(
            f"Agent {agent_id}: Analyze aspect {agent_id}", model=model, max_tokens=150
        )

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(agent_task, i) for i in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    duration = time.time() - start

    assert len(results) == 3
    assert all(r is not None for r in results)
    assert duration < 5.0  # Should be very fast with mocked responses
    assert mock_post.call_count == 3  # Three HTTP calls made for three agents
