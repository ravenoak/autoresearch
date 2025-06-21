"""Unit tests for the A2A interface module."""

import pytest
from unittest.mock import patch, MagicMock, call

from autoresearch.a2a_interface import (
    A2AInterface,
    A2AClient,
    get_a2a_client,
    requires_a2a,
    A2A_AVAILABLE,
)


# Skip all tests if A2A SDK is not available
pytestmark = pytest.mark.skipif(not A2A_AVAILABLE, reason="A2A SDK not available")


@pytest.fixture
def mock_a2a_server():
    """Create a mock A2A server."""
    with patch("autoresearch.a2a_interface.A2AServer") as mock_server:
        mock_instance = MagicMock()
        mock_server.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_a2a_client():
    """Create a mock A2A client."""
    with patch("autoresearch.a2a_interface.A2AClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_a2a_message():
    """Create a mock A2A message."""
    with patch("autoresearch.a2a_interface.A2AMessage") as mock_message_class:
        mock_message = MagicMock()
        mock_message_class.return_value = mock_message
        yield mock_message


@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator."""
    with patch("autoresearch.a2a_interface.Orchestrator") as mock_orch:
        mock_instance = MagicMock()
        mock_orch.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config():
    """Create a mock config."""
    with patch("autoresearch.a2a_interface.get_config") as mock_get_config:
        from autoresearch.config import ConfigModel

        cfg = ConfigModel()
        mock_get_config.return_value = cfg
        yield cfg


class TestA2AInterface:
    """Tests for the A2AInterface class."""

    def test_init(self, mock_a2a_server):
        """Test initialization of A2AInterface."""
        interface = A2AInterface(host="test_host", port=1234)

        assert interface.host == "test_host"
        assert interface.port == 1234
        assert interface.server == mock_a2a_server

        # Check that handlers were registered
        assert mock_a2a_server.register_handler.call_count == 3
        mock_a2a_server.register_handler.assert_has_calls(
            [
                call("query", interface._handle_query),
                call("command", interface._handle_command),
                call("info", interface._handle_info),
            ]
        )

    def test_start(self, mock_a2a_server):
        """Test starting the A2A interface."""
        interface = A2AInterface()
        interface.start()

        mock_a2a_server.start.assert_called_once()

    def test_stop(self, mock_a2a_server):
        """Test stopping the A2A interface."""
        interface = A2AInterface()
        interface.stop()

        mock_a2a_server.stop.assert_called_once()

    def test_handle_query(self, mock_a2a_server, mock_a2a_message, mock_orchestrator):
        """Test handling a query message."""
        # Setup
        interface = A2AInterface()
        mock_a2a_message.content = {"query": "test query"}
        mock_orchestrator.run_query.return_value.answer = "test answer"

        # Execute
        result = interface._handle_query(mock_a2a_message)

        # Verify
        assert result["status"] == "success"
        assert result["message"]["role"] == "agent"
        mock_orchestrator.run_query.assert_called_once()

    def test_handle_command_get_capabilities(self, mock_a2a_server, mock_a2a_message):
        """Test handling a get_capabilities command."""
        interface = A2AInterface()
        mock_a2a_message.content = {"command": "get_capabilities"}

        with patch("autoresearch.a2a_interface.capabilities_endpoint") as cap:
            cap.return_value = {"version": "1"}
            result = interface._handle_command(mock_a2a_message)

        assert result == {"status": "success", "result": {"version": "1"}}
        cap.assert_called_once()

    def test_handle_command_get_config(self, mock_a2a_server, mock_a2a_message, mock_config):
        """Test handling a get_config command."""
        interface = A2AInterface()
        mock_a2a_message.content = {"command": "get_config"}

        result = interface._handle_command(mock_a2a_message)

        assert result["status"] == "success"
        assert "llm_backend" in result["result"]

    def test_handle_command_set_config(self, mock_a2a_server, mock_a2a_message, mock_config):
        """Test handling a set_config command."""
        interface = A2AInterface()
        mock_a2a_message.content = {"command": "set_config", "args": {"loops": 3}}

        result = interface._handle_command(mock_a2a_message)

        assert result["status"] == "success"
        assert result["result"]["loops"] == 3

    def test_handle_command_unknown(self, mock_a2a_server, mock_a2a_message):
        """Test handling an unknown command."""
        # Setup
        interface = A2AInterface()
        mock_a2a_message.content = {"command": "unknown_command"}

        # Execute
        result = interface._handle_command(mock_a2a_message)

        # Verify
        assert result == {
            "status": "error",
            "error": "Unknown command: unknown_command",
        }

    def test_handle_info(self, mock_a2a_server, mock_a2a_message):
        """Test handling an info message."""
        # Setup
        interface = A2AInterface()
        mock_a2a_message.content = {"info_type": "test_info"}

        # Execute
        result = interface._handle_info(mock_a2a_message)

        # Verify
        assert "status" in result
        assert result["status"] == "success"
        assert "agent_info" in result
        assert "version" in result["agent_info"]
        assert "name" in result["agent_info"]


class TestA2AClient:
    """Tests for the A2AClient class."""

    def test_init(self):
        """Test initialization of A2AClient."""
        with patch(
            "autoresearch.a2a_interface.A2AClient.__init__", return_value=None
        ) as mock_init:
            A2AClient()
            mock_init.assert_called_once()

    def test_query_agent(self, mock_a2a_client):
        """Test querying an agent."""
        # Setup
        with patch(
            "autoresearch.a2a_interface.A2AClient", return_value=mock_a2a_client
        ):
            client = A2AClient()
            mock_a2a_client.send_message.return_value = {
                "status": "success",
                "result": {"answer": "test answer"},
            }

            # Execute
            result = client.query_agent("http://test-agent", "test query")

            # Verify
            assert result == {"answer": "test answer"}
            mock_a2a_client.send_message.assert_called_once()

    def test_get_agent_capabilities(self, mock_a2a_client):
        """Test getting agent capabilities."""
        # Setup
        with patch(
            "autoresearch.a2a_interface.A2AClient", return_value=mock_a2a_client
        ):
            client = A2AClient()
            mock_a2a_client.send_message.return_value = {
                "status": "success",
                "result": {"capabilities": "test"},
            }

            # Execute
            result = client.get_agent_capabilities("http://test-agent")

            # Verify
            assert result == {"capabilities": "test"}
            mock_a2a_client.send_message.assert_called_once()

    def test_get_agent_config(self, mock_a2a_client):
        """Test getting agent config."""
        # Setup
        with patch(
            "autoresearch.a2a_interface.A2AClient", return_value=mock_a2a_client
        ):
            client = A2AClient()
            mock_a2a_client.send_message.return_value = {
                "status": "success",
                "result": {"config": "test"},
            }

            # Execute
            result = client.get_agent_config("http://test-agent")

            # Verify
            assert result == {"config": "test"}
            mock_a2a_client.send_message.assert_called_once()

    def test_set_agent_config(self, mock_a2a_client):
        """Test setting agent config."""
        # Setup
        with patch(
            "autoresearch.a2a_interface.A2AClient", return_value=mock_a2a_client
        ):
            client = A2AClient()
            mock_a2a_client.send_message.return_value = {
                "status": "success",
                "result": {"updated": True},
            }

            # Execute
            result = client.set_agent_config("http://test-agent", {"key": "value"})

            # Verify
            assert result == {"updated": True}
            mock_a2a_client.send_message.assert_called_once()


def test_get_a2a_client():
    """Test getting an A2A client."""
    with patch("autoresearch.a2a_interface.A2AClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = get_a2a_client()

        assert client == mock_client
        mock_client_class.assert_called_once()


def test_requires_a2a_decorator_available():
    """Test the requires_a2a decorator when A2A is available."""
    # Setup
    with patch("autoresearch.a2a_interface.A2A_AVAILABLE", True):

        @requires_a2a
        def test_func():
            return "success"

        # Execute
        result = test_func()

        # Verify
        assert result == "success"


def test_requires_a2a_decorator_not_available():
    """Test the requires_a2a decorator when A2A is not available."""
    # Setup
    with patch("autoresearch.a2a_interface.A2A_AVAILABLE", False):

        @requires_a2a
        def test_func():
            return "success"

        # Execute and Verify
        with pytest.raises(ImportError) as excinfo:
            test_func()

        assert "A2A SDK is not available" in str(excinfo.value)
