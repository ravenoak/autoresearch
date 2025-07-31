"""Unit tests for the A2A interface module."""

import pytest
from unittest.mock import MagicMock, call, patch

from autoresearch.a2a_interface import (
    A2AInterface,
    A2AClient,
    get_a2a_client,
    requires_a2a,
    A2A_AVAILABLE,
)
from a2a.utils.message import new_agent_text_message


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
def mock_send_request():
    """Patch the internal send_request helper."""
    with patch("autoresearch.a2a_interface.A2AClientWrapper._send_request") as mock:
        yield mock


@pytest.fixture
def make_a2a_message():
    """Create a real A2A message for tests."""

    def _make(**metadata):
        msg = new_agent_text_message("")
        msg.metadata = metadata
        return msg

    return _make


@pytest.fixture
def mock_orchestrator():
    """Create a mock Orchestrator."""
    with patch("autoresearch.a2a_interface.Orchestrator") as mock_orch:
        mock_instance = MagicMock()
        mock_orch.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config():
    """Create a mock config and inject it for the duration of the test."""
    from autoresearch.config.models import ConfigModel
    from autoresearch.config.loader import ConfigLoader, temporary_config

    cfg = ConfigModel()

    with temporary_config(cfg):
        with patch.object(ConfigLoader, "load_config", lambda self: cfg):
            ConfigLoader.reset_instance()
            try:
                yield cfg
            finally:
                ConfigLoader.reset_instance()


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
        from autoresearch.a2a_interface import A2AMessageType

        mock_a2a_server.register_handler.assert_has_calls(
            [
                call(A2AMessageType.QUERY, interface._handle_query),
                call(A2AMessageType.COMMAND, interface._handle_command),
                call(A2AMessageType.INFO, interface._handle_info),
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

    def test_handle_query(self, mock_a2a_server, make_a2a_message, mock_orchestrator):
        """Test handling a query message."""
        # Setup
        interface = A2AInterface()
        msg = make_a2a_message(query="test query")
        mock_orchestrator.run_query.return_value.answer = "test answer"

        # Execute
        result = interface._handle_query(msg)

        # Verify
        assert result["status"] == "success"
        assert result["message"]["role"] == "agent"
        mock_orchestrator.run_query.assert_called_once()

    def test_handle_command_get_capabilities(self, mock_a2a_server, make_a2a_message):
        """Test handling a get_capabilities command."""
        interface = A2AInterface()
        msg = make_a2a_message(command="get_capabilities")

        with patch("autoresearch.a2a_interface.capabilities_endpoint") as cap:
            cap.return_value = {"version": "1"}
            result = interface._handle_command(msg)

        assert result == {"status": "success", "result": {"version": "1"}}
        cap.assert_called_once()

    def test_handle_command_get_config(self, mock_a2a_server, make_a2a_message, mock_config):
        """Test handling a get_config command."""
        interface = A2AInterface()
        msg = make_a2a_message(command="get_config")

        result = interface._handle_command(msg)

        assert result["status"] == "success"
        assert "llm_backend" in result["result"]

    def test_handle_command_set_config(self, mock_a2a_server, make_a2a_message, mock_config):
        """Test handling a set_config command."""
        interface = A2AInterface()
        msg = make_a2a_message(command="set_config", args={"loops": 3})

        result = interface._handle_command(msg)

        assert result["status"] == "success"
        assert result["result"]["loops"] == 3

    def test_handle_command_unknown(self, mock_a2a_server, make_a2a_message):
        """Test handling an unknown command."""
        # Setup
        interface = A2AInterface()
        msg = make_a2a_message(command="unknown_command")

        # Execute
        result = interface._handle_command(msg)

        # Verify
        assert result == {
            "status": "error",
            "error": "Unknown command: unknown_command",
        }

    def test_handle_info(self, mock_a2a_server, make_a2a_message):
        """Test handling an info message."""
        # Setup
        interface = A2AInterface()
        msg = make_a2a_message(info_type="test_info")

        # Execute
        result = interface._handle_info(msg)

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
        client = A2AClient()
        assert isinstance(client, A2AClient)

    def test_query_agent(self, mock_send_request):
        """Test querying an agent."""
        client = A2AClient()
        mock_send_request.return_value = {
            "result": {
                "kind": "message",
                "parts": [{"kind": "text", "text": "test answer"}],
            }
        }

        result = client.query_agent("http://test-agent", "test query")

        assert result == {"answer": "test answer"}
        mock_send_request.assert_called_once()

    def test_get_agent_capabilities(self, mock_send_request):
        """Test getting agent capabilities."""
        # Setup
        client = A2AClient()
        mock_send_request.return_value = {"result": {"capabilities": "test"}}

        result = client.get_agent_capabilities("http://test-agent")

        assert result == {"capabilities": "test"}
        mock_send_request.assert_called_once()

    def test_get_agent_config(self, mock_send_request):
        """Test getting agent config."""
        # Setup
        client = A2AClient()
        mock_send_request.return_value = {"result": {"config": "test"}}

        result = client.get_agent_config("http://test-agent")

        assert result == {"config": "test"}
        mock_send_request.assert_called_once()

    def test_set_agent_config(self, mock_send_request):
        """Test setting agent config."""
        # Setup
        client = A2AClient()
        mock_send_request.return_value = {"result": {"updated": True}}

        result = client.set_agent_config("http://test-agent", {"key": "value"})

        assert result == {"updated": True}
        mock_send_request.assert_called_once()


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


def test_handle_query_exception(mock_a2a_server, make_a2a_message, mock_orchestrator):
    interface = A2AInterface()
    msg = make_a2a_message(query="bad")
    mock_orchestrator.run_query.side_effect = RuntimeError("oops")
    result = interface._handle_query(msg)
    assert result["status"] == "error"

    assert "oops" in result["error"]


def test_handle_set_config_invalid(monkeypatch, mock_a2a_server, make_a2a_message, mock_config):
    interface = A2AInterface()
    msg = make_a2a_message(command="set_config", args={"loops": "bad"})
    result = interface._handle_command(msg)
    assert result["result"]["status"] == "error"


class TestA2AClientExtended(TestA2AClient):
    def test_query_agent_error(self, mock_send_request):
        client = A2AClient()
        mock_send_request.return_value = {"error": "bad"}
        result = client.query_agent("http://test-agent", "q")
        assert result == {"error": "bad"}
        mock_send_request.assert_called_once()
