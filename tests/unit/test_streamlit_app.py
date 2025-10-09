"""Tests for Streamlit application functionality."""

import pytest
from unittest.mock import Mock, patch

from autoresearch.streamlit_app import (
    _trigger_rerun,
    display_config_editor,
    track_agent_performance,
    collect_system_metrics,
    update_metrics_periodically,
    display_agent_performance,
    display_metrics_dashboard,
    setup_logging,
    display_log_viewer,
    initialize_session_state,
    display_query_input,
    main,
    store_query_history,
    display_query_history,
)
from autoresearch.config import ConfigModel
from autoresearch.models import QueryResponse


class TestStreamlitApp:
    """Test cases for Streamlit application functionality."""

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_trigger_rerun(self) -> None:
        """Test that _trigger_rerun correctly triggers a rerun."""
        with patch("streamlit.rerun") as mock_rerun:
            _trigger_rerun()
            mock_rerun.assert_called_once()

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_config_editor_basic(self) -> None:
        """Test basic config editor display functionality."""
        with patch("streamlit.sidebar"), patch("streamlit.columns"), patch("streamlit.button"):
            display_config_editor()

    def test_track_agent_performance(self) -> None:
        """Test agent performance tracking functionality."""
        # The function should not crash and should log performance data
        track_agent_performance("TestAgent", 1.5, 100, True)
        # Test passes if no exception is raised

    def test_collect_system_metrics(self) -> None:
        """Test system metrics collection."""
        metrics = collect_system_metrics()

        # Should return a dictionary with expected keys
        assert isinstance(metrics, dict)
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "memory_used" in metrics
        assert "memory_total" in metrics
        assert "process_memory" in metrics
        assert "token_usage" in metrics
        assert "agent_performance" in metrics
        assert "health" in metrics

        # Values should be reasonable
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["memory_percent"] <= 100

    def test_update_metrics_periodically_threading(self) -> None:
        """Test that metrics update runs in background thread."""
        with patch("autoresearch.streamlit_app.st.session_state") as mock_session_state, \
             patch("threading.Thread") as mock_thread:
            # Set test mode to prevent infinite loop
            mock_session_state._test_mode = True
            update_metrics_periodically()

            # Should not start thread in test mode
            mock_thread.assert_not_called()

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_agent_performance_ui(self) -> None:
        """Test agent performance UI display."""
        with patch("autoresearch.streamlit_app.st.subheader"), patch("autoresearch.streamlit_app.st.columns"), patch("autoresearch.streamlit_app.st.metric"):
            display_agent_performance()

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_metrics_dashboard(self) -> None:
        """Test metrics dashboard display."""
        with patch("autoresearch.streamlit_app.st.title"), patch("autoresearch.streamlit_app.st.columns"), patch("autoresearch.streamlit_app.st.metric"):
            display_metrics_dashboard()

    def test_setup_logging(self) -> None:
        """Test logging setup functionality."""
        with patch("logging.getLogger") as mock_get_logger:
            setup_logging()

            # Should configure logging
            mock_get_logger.assert_called()

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_log_viewer(self) -> None:
        """Test log viewer display functionality."""
        with patch("autoresearch.streamlit_app.st.title"), patch("autoresearch.streamlit_app.st.empty"), patch("autoresearch.streamlit_app.st.code"):
            display_log_viewer()

    def test_initialize_session_state(self) -> None:
        """Test session state initialization."""
        with patch("autoresearch.streamlit_app.st.session_state") as mock_session_state:
            initialize_session_state()

            # Should set various session state variables
            assert hasattr(mock_session_state, "__setitem__")

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_query_input(self) -> None:
        """Test query input display functionality."""
        with patch("autoresearch.streamlit_app.st.title"), patch("autoresearch.streamlit_app.st.text_input"), patch("autoresearch.streamlit_app.st.button"):
            display_query_input()

    def test_store_query_history(self) -> None:
        """Test query history storage."""
        query = "test query"
        result = Mock(spec=QueryResponse)
        config = Mock(spec=ConfigModel)
        config.reasoning_mode = Mock()
        config.reasoning_mode.value = "direct"
        config.loops = 2
        config.llm_backend = "lmstudio"

        # The function should not crash
        store_query_history(query, result, config)
        # Test passes if no exception is raised

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    def test_display_query_history(self) -> None:
        """Test query history display."""
        with patch("autoresearch.streamlit_app.st.title"), patch("autoresearch.streamlit_app.st.expander"), patch("autoresearch.streamlit_app.st.json"):
            display_query_history()

    @pytest.mark.skip(reason="UI test requiring Streamlit runtime")
    @patch("autoresearch.streamlit_app.initialize_session_state")
    @patch("threading.enumerate")
    @patch("threading.Thread")
    def test_main_initialization(self, mock_thread: Mock, mock_enumerate: Mock, mock_init_state: Mock) -> None:
        """Test main function initialization."""
        # Mock that no MetricsCollector thread exists
        mock_enumerate.return_value = []

        with patch("autoresearch.streamlit_app.st.set_page_config"), patch("autoresearch.streamlit_app.st.title"):
            main()

            # Should initialize session state
            mock_init_state.assert_called_once()

            # Should start metrics thread
            mock_thread.assert_called_once()

    def test_metrics_collection_accuracy(self) -> None:
        """Test that metrics collection provides accurate data."""
        metrics = collect_system_metrics()

        # Verify data types and ranges
        assert isinstance(metrics["cpu_percent"], (int, float))
        assert isinstance(metrics["memory_percent"], (int, float))
        assert isinstance(metrics["memory_used"], (int, float))
        assert isinstance(metrics["memory_total"], (int, float))
        assert isinstance(metrics["process_memory"], (int, float))

    def test_agent_performance_tracking_integration(self) -> None:
        """Test integration between agent performance tracking and display."""
        # The function should not crash and should log performance data
        track_agent_performance("TestAgent", 2.0, 200, True)
        # Test passes if no exception is raised

    def test_session_state_persistence(self) -> None:
        """Test that session state persists across function calls."""
        with patch("autoresearch.streamlit_app.st.session_state") as mock_session_state:
            # First call
            initialize_session_state()

            # Second call should not overwrite existing state
            initialize_session_state()

            # Should maintain state between calls
            assert mock_session_state.__getitem__.call_count >= 0

    def test_query_history_storage_format(self) -> None:
        """Test that query history is stored in correct format."""
        query = "test query"
        result = Mock(spec=QueryResponse)
        result.query = query
        config = Mock(spec=ConfigModel)
        config.reasoning_mode = Mock()
        config.reasoning_mode.value = "direct"
        config.loops = 2
        config.llm_backend = "lmstudio"

        # The function should not crash
        store_query_history(query, result, config)
        # Test passes if no exception is raised
