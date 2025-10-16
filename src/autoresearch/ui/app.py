"""Refactored Streamlit application using modular components.

This is the main entry point for the Streamlit UI that orchestrates the various
UI components in a clean, maintainable way. This replaces the monolithic
streamlit_app.py with a component-based architecture.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional, cast

try:
    import streamlit as st
except ImportError:
    # For test environments without streamlit
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        import streamlit as st
    else:

        class MockStreamlit:
            def __getattr__(self, name: str) -> Any:
                return lambda *args, **kwargs: None

        st = cast(Any, MockStreamlit())

from ..orchestration.orchestrator import Orchestrator
from ..orchestration import ReasoningMode
from ..error_utils import get_error_info, format_error_for_gui
from .components.config_editor import ConfigEditorComponent
from .components.query_input import QueryInputComponent
from .components.results_display import ResultsDisplayComponent
from .state.session_state import SessionStateManager
from .ui_helpers import (
    apply_theme_settings,
    apply_accessibility_settings,
    display_guided_tour,
    display_help_sidebar,
)


class AutoresearchApp:
    """Main Streamlit application using modular components."""

    def __init__(self) -> None:
        """Initialize the application."""
        self._state_manager = SessionStateManager()
        self._query_input = QueryInputComponent()
        self._results_display = ResultsDisplayComponent()
        self._config_editor = ConfigEditorComponent()

        # Check if we're running in test mode
        self._test_mode = self._get_env_bool("_STREAMLIT_TEST_MODE", False)

    def run(self) -> None:
        """Run the Streamlit application."""
        # Initialize session state
        self._state_manager.initialize()

        # Start background threads if not in test mode
        if not self._test_mode:
            self._start_background_threads()

        # Set up logging
        self._setup_logging()

        # Render the main UI
        self._render_main_ui()

    def _start_background_threads(self) -> None:
        """Start background threads for metrics collection."""
        if not any(thread.name == "MetricsCollector" for thread in threading.enumerate()):
            metrics_thread = threading.Thread(
                target=self._collect_metrics_periodically, daemon=True, name="MetricsCollector"
            )
            metrics_thread.start()

    def _collect_metrics_periodically(self) -> None:
        """Collect system metrics periodically in the background."""
        # Get timeout from environment (default 1 hour, lower for tests)
        timeout_seconds = float(self._get_env("STREAMLIT_METRICS_TIMEOUT", "3600"))
        start_time = time.time()

        while True:
            # Check if we should stop (for graceful shutdown)
            if getattr(st.session_state, "_metrics_thread_stop", False):
                break

            # Check for timeout (prevent infinite loops in tests)
            if time.time() - start_time > timeout_seconds:
                break

            # Collect and store metrics
            self._collect_and_store_metrics()

            # Sleep for 1 second
            time.sleep(1)

    def _collect_and_store_metrics(self) -> None:
        """Collect system metrics and store in session state."""
        try:
            import psutil
            import os

            # Get CPU usage
            cpu_percent_raw = psutil.cpu_percent(interval=0.1)
            cpu_percent = float(
                cpu_percent_raw[0] if isinstance(cpu_percent_raw, list) else cpu_percent_raw
            )

            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = cast(float, getattr(memory, "percent", 0.0))
            memory_used = cast(float, getattr(memory, "used", 0.0)) / (1024 * 1024 * 1024)
            memory_total = cast(float, getattr(memory, "total", 0.0)) / (1024 * 1024 * 1024)

            # Get process information
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB

            # Determine overall health status
            health = "OK"
            if cpu_percent > 90 or memory_percent > 90:
                health = "CRITICAL"
            elif cpu_percent > 80 or memory_percent > 80:
                health = "WARNING"

            # Store metrics in session state
            if "system_metrics" not in st.session_state:
                st.session_state.system_metrics = []

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used": memory_used,
                "memory_total": memory_total,
                "process_memory": process_memory,
                "health": health,
                "timestamp": time.time(),
            }

            # Add current metrics to history (keep last 60 data points)
            st.session_state.system_metrics.append(metrics)
            if len(st.session_state.system_metrics) > 60:
                st.session_state.system_metrics.pop(0)

            # Update current metrics
            st.session_state.current_metrics = metrics

        except Exception as e:
            logging.warning(f"Failed to collect system metrics: {e}")

    def _setup_logging(self) -> None:
        """Set up the logging system."""

        # Create a custom handler for Streamlit logs
        class StreamlitLogHandler(logging.Handler):
            def __init__(self, level: int = logging.INFO) -> None:
                super().__init__(level)
                self.setFormatter(logging.Formatter("%(message)s"))

            def emit(self, record: logging.LogRecord) -> None:
                try:
                    structured_log = self._convert_to_structured_log(record)

                    # Initialize logs list in session state if it doesn't exist
                    logs = cast(list[dict[str, Any]], st.session_state.setdefault("logs", []))

                    # Add the structured log entry to the session state
                    logs.append(structured_log)

                    # Keep only the last 1000 log entries to avoid memory issues
                    if len(logs) > 1000:
                        logs[:] = logs[-1000:]

                except Exception:
                    self.handleError(record)

            def _convert_to_structured_log(self, record: logging.LogRecord) -> dict[str, Any]:
                from datetime import datetime

                correlation_id = getattr(record, "correlation_id", None)

                return {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "correlation_id": correlation_id,
                }

        # Get the root logger
        root_logger = logging.getLogger()

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set the log level
        root_logger.setLevel(logging.INFO)

        # Create and add the custom handler
        handler = StreamlitLogHandler()
        root_logger.addHandler(handler)

        # Add a console handler for debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(console_handler)

        # Log that the logging system is set up
        logging.info("Logging system initialized for Streamlit GUI")

    def _render_main_ui(self) -> None:
        """Render the main user interface."""
        # Set page configuration
        st.set_page_config(
            page_title="Autoresearch",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Add custom CSS
        self._add_custom_css()

        # Header
        st.markdown("<h1 class='main-header'>Autoresearch</h1>", unsafe_allow_html=True)
        st.markdown(
            "<a class='skip-link' href='#main-content' aria-label='Skip to main content'>Skip to main content</a>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "A local-first research assistant that coordinates multiple agents to produce evidence-backed answers."
        )

        # Show guided tour for new users
        display_guided_tour()

        # Sidebar
        self._render_sidebar()

        # Apply theme and accessibility settings
        apply_theme_settings()
        apply_accessibility_settings()

        # Main content
        self._render_main_content()

    def _add_custom_css(self) -> None:
        """Add custom CSS styles."""
        st.markdown(
            """
            <style>
            .main-header {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            .subheader {
                font-size: 1.5rem;
                margin-bottom: 1rem;
            }
            .stAlert {
                margin-top: 1rem;
            }
            .citation {
                background-color: #f0f2f6;
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 0.5rem;
            }
            .reasoning-step {
                margin-bottom: 0.5rem;
            }
            .metrics-container {
                background-color: #f0f2f6;
                border-radius: 0.5rem;
                padding: 1rem;
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            @media (max-width: 1024px) {
                .metrics-container {
                    flex-direction: column;
                }
            }
            .responsive-container {
                display: flex;
                flex-wrap: wrap;
                gap: 1rem;
            }
            .responsive-item {
                flex: 1 1 300px;
            }
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            .skip-link {
                position: absolute;
                left: -1000px;
                top: auto;
                width: 1px;
                height: 1px;
                overflow: hidden;
            }
            .skip-link:focus {
                left: 1rem;
                top: 1rem;
                width: auto;
                height: auto;
                background: #fff;
                padding: 0.5rem;
                z-index: 1000;
            }
            @media (max-width: 768px) {
                .responsive-container, .metrics-container {
                    flex-direction: column;
                }
                .stForm button[type="submit"] {
                    width: 100%;
                }
                .main-header {
                    font-size: 2rem;
                }
                .subheader {
                    font-size: 1.2rem;
                }
            }
            @media (max-width: 480px) {
                .responsive-item {
                    flex-basis: 100%;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def _render_sidebar(self) -> None:
        """Render the sidebar with configuration and settings."""
        with st.sidebar:
            st.markdown("<h2 class='subheader'>Configuration</h2>", unsafe_allow_html=True)

            # Theme and accessibility settings
            st.session_state.high_contrast = st.checkbox(
                "High Contrast Mode",
                value=st.session_state.get("high_contrast", False),
                help="Improve readability with a high contrast color scheme",
            )

            st.session_state.dark_mode = st.checkbox(
                "Dark Mode",
                value=st.session_state.get("dark_mode", False),
                help="Toggle between light and dark themes",
            )

            if st.button("Show Tour", key="show_tour_btn", help="View interface walkthrough"):
                st.session_state.show_tour = True

            # Display current configuration summary
            self._render_config_summary()

            # Configuration editor
            with st.expander("Edit Configuration"):
                self._config_editor.render()

            # Tutorial/help sidebar
            display_help_sidebar()

    def _render_config_summary(self) -> None:
        """Render a summary of current configuration settings."""
        st.markdown("### Current Settings")
        config = self._state_manager.get_config()

        st.markdown(f"**LLM Backend:** {config.llm_backend}")
        st.markdown(f"**Reasoning Mode:** {config.reasoning_mode.value}")
        st.markdown(f"**Loops:** {config.loops}")
        st.markdown(f"**Active Profile:** {config.active_profile or 'None'}")

        if hasattr(config, "user_preferences") and config.user_preferences:
            prefs = config.user_preferences
            st.markdown("### Preferences")
            st.markdown(f"**Detail:** {prefs.get('detail_level', 'balanced')}")
            st.markdown(f"**Perspective:** {prefs.get('perspective', 'neutral')}")

        # Configuration change notification
        if st.session_state.get("config_changed", False):
            st.success("Configuration updated")
            st.session_state.config_changed = False

    def _render_main_content(self) -> None:
        """Render the main content area."""
        # Create tabs for main content, metrics dashboard, logs, and history
        main_tab, metrics_tab, logs_tab, history_tab = st.tabs(
            ["Main", "Metrics Dashboard", "Logs", "History"]
        )

        with main_tab:
            st.markdown(
                "<div id='main-content' aria-live='polite'></div>",
                unsafe_allow_html=True,
            )

            # Query input section
            self._render_query_input()

        with metrics_tab:
            self._render_metrics_dashboard()

        with logs_tab:
            self._render_log_viewer()

        with history_tab:
            self._render_query_history()

    def _render_query_input(self) -> None:
        """Render the query input interface."""
        # Use the modular query input component
        query, reasoning_mode, loops = self._query_input.render()

        # Handle form submission
        if query and reasoning_mode and loops is not None:
            self._handle_query_submission(query, reasoning_mode, loops)

    def _handle_query_submission(self, query: str, reasoning_mode: str, loops: int) -> None:
        """Handle query form submission."""
        # Update config with selected options
        config = self._state_manager.get_config()
        config.reasoning_mode = ReasoningMode(reasoning_mode)
        config.loops = loops

        # Show spinner while processing
        with st.spinner("Processing query..."):
            try:
                # Run the query
                result = Orchestrator().run_query(query, config)

                # Track performance metrics
                # TODO: Implement track_agent_performance function in session_state

                # Update token usage metrics
                if hasattr(result, "metrics") and result.metrics and "tokens" in result.metrics:
                    tokens = result.metrics["tokens"]
                    self._state_manager.update_token_usage(tokens)

                # Store query in history
                self._state_manager.add_to_history(query, result, config)

                # Display results
                self._results_display.render(result)

            except Exception as e:
                # Get error information with suggestions and code examples
                error_info = get_error_info(e)
                formatted_error = format_error_for_gui(error_info)

                # Display error with suggestions and code examples
                st.error(formatted_error)

                # Log the error
                logging.error(f"Error processing query: {str(e)}", exc_info=e)

    def _render_metrics_dashboard(self) -> None:
        """Render the metrics dashboard."""
        try:
            import pandas as pd
        except Exception:
            st.warning("Pandas is required to render the metrics dashboard.")
            return

        # Create tabs for different metrics
        metrics_tab1, metrics_tab2 = st.tabs(["System Metrics", "Agent Performance"])

        with metrics_tab1:
            st.markdown("<h2 class='subheader'>System Metrics</h2>", unsafe_allow_html=True)

            # Get current metrics
            metrics_dict = cast(Dict[str, Any], st.session_state.get("current_metrics", {}))

            if metrics_dict:
                # Display CPU usage
                col1, col2, col3 = st.columns(3)

                with col1:
                    cpu_percent = float(metrics_dict.get("cpu_percent", 0.0))
                    st.markdown("### CPU Usage")
                    st.progress(cpu_percent / 100)
                    st.markdown(f"{cpu_percent:.1f}%")

                # Display memory usage
                with col2:
                    memory_percent = float(metrics_dict.get("memory_percent", 0.0))
                    memory_used = float(metrics_dict.get("memory_used", 0.0))
                    memory_total = float(metrics_dict.get("memory_total", 0.0))
                    st.markdown("### Memory Usage")
                    st.progress(memory_percent / 100)
                    st.markdown(
                        f"{memory_used:.1f} GB / {memory_total:.1f} GB ({memory_percent:.1f}%)"
                    )

                # Display process memory
                with col3:
                    process_memory = float(metrics_dict.get("process_memory", 0.0))
                    st.markdown("### Process Memory")
                    st.markdown(f"{process_memory:.1f} MB")

                # Display system health
                status = cast(str, metrics_dict.get("health", "OK"))
                color = "green" if status == "OK" else "orange" if status == "WARNING" else "red"
                st.markdown(
                    f"### Health: <span style='color:{color}'>{status}</span>",
                    unsafe_allow_html=True,
                )

                # Display token usage
                st.markdown("### Token Usage")
                token_usage = cast(Dict[str, Any], metrics_dict.get("token_usage", {}))

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Tokens", token_usage.get("total", 0))
                with col2:
                    st.metric("Prompt Tokens", token_usage.get("prompt", 0))
                with col3:
                    st.metric("Completion Tokens", token_usage.get("completion", 0))
                with col4:
                    st.metric("Last Query Tokens", token_usage.get("last_query", 0))

                extra1, extra2 = st.columns(2)
                with extra1:
                    st.metric("Total Input Tokens", int(metrics_dict.get("tokens_in_total", 0)))
                with extra2:
                    st.metric("Total Output Tokens", int(metrics_dict.get("tokens_out_total", 0)))

                # Display metrics history chart
                if (
                    "system_metrics" in st.session_state
                    and len(st.session_state.system_metrics) > 1
                ):
                    st.markdown("### Metrics History")

                    # Create a chart for CPU and memory usage
                    history = cast(list[Dict[str, Any]], st.session_state.system_metrics)
                    chart_data = {
                        "time": list(range(len(history))),
                        "cpu": [float(m.get("cpu_percent", 0.0)) for m in history],
                        "memory": [float(m.get("memory_percent", 0.0)) for m in history],
                    }

                    # Create a DataFrame for the chart
                    df = pd.DataFrame(chart_data)

                    # Display the chart
                    st.line_chart(df.set_index("time")[["cpu", "memory"]])
            else:
                st.info("No metrics data available yet")

        with metrics_tab2:
            # This would render agent performance metrics
            st.info("Agent performance metrics would be rendered here")

    def _render_log_viewer(self) -> None:
        """Render the log viewer interface."""
        st.markdown("<h2 class='subheader'>Log Viewer</h2>", unsafe_allow_html=True)

        # Get logs from session state
        logs = st.session_state.get("logs", [])

        if not logs:
            st.info("No logs available yet")
            return

        # Create filter controls
        st.markdown("### Log Filters")

        col1, col2, col3 = st.columns(3)

        with col1:
            log_levels = ["ALL"] + sorted(set(log["level"] for log in logs))
            selected_level = st.selectbox("Log Level", log_levels)

        with col2:
            logger_names = ["ALL"] + sorted(set(log["logger"] for log in logs))
            selected_logger = st.selectbox("Logger", logger_names)

        with col3:
            filter_text = st.text_input("Filter Text", "")

        # Apply filters
        filtered_logs = logs

        if selected_level != "ALL":
            filtered_logs = [log for log in filtered_logs if log["level"] == selected_level]

        if selected_logger != "ALL":
            filtered_logs = [log for log in filtered_logs if log["logger"] == selected_logger]

        if filter_text:
            import re

            pattern = re.compile(filter_text, re.IGNORECASE)
            filtered_logs = [log for log in filtered_logs if pattern.search(log.get("message", ""))]

        # Display log count
        st.markdown(f"Showing {len(filtered_logs)} of {len(logs)} logs")

        # Create a download button for logs
        if filtered_logs:
            from datetime import datetime

            log_text = "\n".join(
                f"{log['timestamp']} - {log['level']} - {log['logger']} - {log['message']}"
                for log in filtered_logs
            )
            st.download_button(
                label="Download Logs",
                data=log_text,
                file_name=f"autoresearch_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
            )

        # Display logs in a table
        if filtered_logs:
            try:
                import pandas as pd

                log_df = pd.DataFrame(
                    [
                        {
                            "Time": log["timestamp"],
                            "Level": log["level"],
                            "Logger": log["logger"],
                            "Message": log["message"],
                        }
                        for log in filtered_logs
                    ]
                )
                st.dataframe(log_df, use_container_width=True)
            except Exception:
                st.warning("Log table unavailable; install pandas-compatible extras to enable.")
        else:
            st.info("No logs match the current filters")

    def _render_query_history(self) -> None:
        """Render the query history interface."""
        try:
            import pandas as pd
        except Exception:
            st.warning("Pandas is required to display query history.")
            return

        st.markdown("<h2 class='subheader'>Query History</h2>", unsafe_allow_html=True)

        # Get query history from session state
        history = self._state_manager.get_query_history()

        if not history:
            st.info("No query history available yet")
            return

        # Create a DataFrame for the history
        history_data = []

        for i, entry in enumerate(reversed(history)):
            history_data.append(
                {
                    "ID": len(history) - i,
                    "Time": entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "Query": (
                        entry["query"][:50] + "..." if len(entry["query"]) > 50 else entry["query"]
                    ),
                    "Mode": entry["config"]["reasoning_mode"],
                    "Loops": entry["config"]["loops"],
                    "Backend": entry["config"]["llm_backend"],
                }
            )

        history_df = pd.DataFrame(history_data)

        # Display the history table
        st.dataframe(history_df, use_container_width=True)

        # Rerun query functionality would go here
        st.info("Query rerun functionality would be implemented here")

    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable value."""
        return str(__import__("os").environ.get(key, default))

    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get environment variable as boolean."""
        return str(__import__("os").environ.get(key, str(default))).lower() == "true"


# Create a global instance for backwards compatibility
_app_instance: Optional[AutoresearchApp] = None


def get_app() -> AutoresearchApp:
    """Get or create the global app instance."""
    global _app_instance
    if _app_instance is None:
        _app_instance = AutoresearchApp()
    return _app_instance


def main() -> None:
    """Main entry point for the Streamlit application."""
    app = get_app()
    app.run()


if __name__ == "__main__":
    main()
