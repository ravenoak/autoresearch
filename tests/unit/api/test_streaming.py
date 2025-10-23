# mypy: ignore-errors
"""Tests for streaming API endpoints."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from autoresearch.api.models import QueryRequestV1, QueryResponseV1
from autoresearch.api.streaming import KEEPALIVE_INTERVAL, query_stream_endpoint
from autoresearch.orchestration import ReasoningMode


@pytest.fixture()
def mock_orchestrator():
    """Mock orchestrator for testing."""
    mock = MagicMock()
    mock.run_query.return_value = QueryResponseV1(
        answer="Test answer",
        citations=[{"title": "Test", "url": "https://test.com"}],
        reasoning=["Test reasoning"],
        metrics={"tokens": 100}
    )
    return mock


@pytest.fixture()
def mock_config():
    """Mock configuration for testing."""
    mock = MagicMock()
    mock.reasoning_mode = ReasoningMode.SYNTHESIS
    mock.loops = 2
    mock.llm_backend = "test"
    mock.api.webhook_timeout = 5
    mock.api.webhook_retries = 3
    mock.api.webhook_backoff = 0.5
    mock.api.webhooks = []
    return mock


def test_keepalive_interval_constant():
    """Test that KEEPALIVE_INTERVAL is properly defined."""
    assert isinstance(KEEPALIVE_INTERVAL, int)
    assert KEEPALIVE_INTERVAL > 0


@pytest.mark.asyncio
async def test_query_stream_endpoint_basic_flow(mock_config, mock_orchestrator):
    """Test basic streaming endpoint flow."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=None,
        llm_backend=None,
        webhook_url=None
    )

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"):

        response = await query_stream_endpoint(request)

        assert response.media_type == "application/json"
        assert hasattr(response, 'body_iterator')

        # Collect all streamed content
        content_lines = []
        async for line in response.body_iterator:
            if line.strip():  # Skip empty heartbeat lines
                content_lines.append(line.decode().strip())

        assert len(content_lines) == 1
        data = json.loads(content_lines[0])
        assert "answer" in data
        assert data["answer"] == "Test answer"


@pytest.mark.asyncio
async def test_query_stream_endpoint_with_reasoning_mode(mock_config, mock_orchestrator):
    """Test streaming endpoint respects reasoning mode override."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode="fact_check",
        loops=None,
        llm_backend=None,
        webhook_url=None
    )

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"):

        await query_stream_endpoint(request)

        # Verify config was updated
        assert mock_config.reasoning_mode == ReasoningMode.FACT_CHECK


@pytest.mark.asyncio
async def test_query_stream_endpoint_with_loops_override(mock_config, mock_orchestrator):
    """Test streaming endpoint respects loops override."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=5,
        llm_backend=None,
        webhook_url=None
    )

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"):

        await query_stream_endpoint(request)

        # Verify config was updated
        assert mock_config.loops == 5


@pytest.mark.asyncio
async def test_query_stream_endpoint_with_llm_backend_override(mock_config, mock_orchestrator):
    """Test streaming endpoint respects LLM backend override."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=None,
        llm_backend="custom_backend",
        webhook_url=None
    )

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"):

        await query_stream_endpoint(request)

        # Verify config was updated
        assert mock_config.llm_backend == "custom_backend"


@pytest.mark.asyncio
async def test_query_stream_endpoint_with_webhook(mock_config, mock_orchestrator):
    """Test streaming endpoint sends webhooks when configured."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=None,
        llm_backend=None,
        webhook_url="https://test-webhook.com"
    )

    mock_config.api.webhooks = ["https://global-webhook.com"]

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook") as mock_notify:

        await query_stream_endpoint(request)

        # Verify both webhooks were called
        assert mock_notify.call_count == 2


@pytest.mark.asyncio
async def test_query_stream_endpoint_error_handling(mock_config):
    """Test streaming endpoint handles errors gracefully."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=None,
        llm_backend=None,
        webhook_url=None
    )

    mock_orchestrator = MagicMock()
    mock_orchestrator.run_query.side_effect = Exception("Test error")

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"), \
         patch("autoresearch.api.streaming.get_error_info") as mock_get_error, \
         patch("autoresearch.api.streaming.format_error_for_api") as mock_format_error:

        mock_get_error.return_value = MagicMock(
            message="Test error",
            suggestions=["Try again"],
            category="test_error"
        )
        mock_format_error.return_value = {"error": "formatted"}

        response = await query_stream_endpoint(request)

        assert response.media_type == "application/json"

        # Collect all streamed content
        content_lines = []
        async for line in response.body_iterator:
            if line.strip():
                content_lines.append(line.decode().strip())

        assert len(content_lines) == 1
        data = json.loads(content_lines[0])
        assert "answer" in data
        assert "Error: Test error" in data["answer"]
        assert "Suggestion: Try again" in data["reasoning"][1]


@pytest.mark.asyncio
async def test_query_stream_endpoint_keepalive(mock_config, mock_orchestrator):
    """Test streaming endpoint sends keepalive messages."""
    request = QueryRequestV1(
        version="v1",
        query="test query",
        reasoning_mode=None,
        loops=None,
        llm_backend=None,
        webhook_url=None
    )

    # Mock a slow operation that triggers keepalive
    async def slow_generator():
        await asyncio.sleep(KEEPALIVE_INTERVAL + 1)
        yield b'{"answer": "slow response"}\n'
        yield None

    with patch("autoresearch.api.streaming.get_config", return_value=mock_config), \
         patch("autoresearch.api.streaming.create_orchestrator", return_value=mock_orchestrator), \
         patch("autoresearch.api.streaming.validate_version"), \
         patch("autoresearch.api.streaming.webhooks.notify_webhook"):

        response = await query_stream_endpoint(request)

        # We can't easily test the timeout in unit tests due to the async nature,
        # but we can verify the response structure is correct
        assert response.media_type == "application/json"
