"""Centralized session state management for the Streamlit UI.

This module provides a clean interface for managing all UI state, including:
- Configuration state and hot-reload handling
- Query execution state and results
- Metrics and performance data
- User preferences and settings
- Query history management
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Optional, cast

import streamlit as st

from ...config import ConfigLoader, ConfigModel
from ...models import QueryResponse


class SessionStateManager:
    """Centralized manager for all Streamlit session state."""

    def __init__(self) -> None:
        """Initialize the session state manager."""
        self._config_loader = ConfigLoader()

    def initialize(self) -> None:
        """Initialize all session state variables."""
        self._initialize_config()
        self._initialize_query_state()
        self._initialize_metrics_state()
        self._initialize_ui_preferences()

    def _initialize_config(self) -> None:
        """Initialize configuration state."""
        if "config" not in st.session_state:
            st.session_state.config = self._config_loader.load_config()
            # Start watching for configuration changes
            self._config_loader.watch_changes(self._on_config_change)

    def _initialize_query_state(self) -> None:
        """Initialize query execution state."""
        if "current_query" not in st.session_state:
            st.session_state.current_query = ""

        if "current_result" not in st.session_state:
            st.session_state.current_result = None

        if "query_history" not in st.session_state:
            st.session_state.query_history = []

        if "rerun_triggered" not in st.session_state:
            st.session_state.rerun_triggered = False

        if "run_button" not in st.session_state:
            st.session_state.run_button = False

    def _initialize_metrics_state(self) -> None:
        """Initialize metrics and performance state."""
        if "token_usage" not in st.session_state:
            st.session_state.token_usage = {
                "total": 0,
                "prompt": 0,
                "completion": 0,
                "last_query": 0,
            }

        if "agent_performance" not in st.session_state:
            st.session_state.agent_performance = {}

        if "system_metrics" not in st.session_state:
            st.session_state.system_metrics = []

        if "current_metrics" not in st.session_state:
            st.session_state.current_metrics = {}

    def _initialize_ui_preferences(self) -> None:
        """Initialize UI preferences and settings."""
        if "ui_depth" not in st.session_state:
            st.session_state.ui_depth = "standard"

        if "high_contrast" not in st.session_state:
            st.session_state.high_contrast = False

        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = False

        if "show_tour" not in st.session_state:
            st.session_state.show_tour = True

        if "first_visit" not in st.session_state:
            st.session_state.first_visit = True

    def _on_config_change(self, config: ConfigModel) -> None:
        """Handle configuration changes from file watching.

        Args:
            config: The new configuration
        """
        st.session_state.config = config
        st.session_state.config_changed = True
        st.session_state.config_change_time = time.time()

    def set_current_query(self, query: str) -> None:
        """Set the current query text.

        Args:
            query: The query string
        """
        st.session_state.current_query = query

    def get_current_query(self) -> str:
        """Get the current query text.

        Returns:
            The current query string
        """
        return cast(str, st.session_state.get("current_query", ""))

    def set_current_result(self, result: QueryResponse) -> None:
        """Set the current query result.

        Args:
            result: The query response
        """
        st.session_state.current_result = result
        if hasattr(result, "state_id") and result.state_id:
            st.session_state.current_state_id = result.state_id

    def get_current_result(self) -> Optional[QueryResponse]:
        """Get the current query result.

        Returns:
            The current query result or None if not set
        """
        return cast(Optional[QueryResponse], st.session_state.get("current_result"))

    def add_to_history(self, query: str, result: QueryResponse, config: ConfigModel) -> None:
        """Add a query to the history.

        Args:
            query: The query string
            result: The query response
            config: The configuration used
        """
        if "query_history" not in st.session_state:
            st.session_state.query_history = []

        history_entry = {
            "timestamp": datetime.now(),
            "query": query,
            "result": result,
            "config": {
                "reasoning_mode": config.reasoning_mode.value,
                "loops": config.loops,
                "llm_backend": config.llm_backend,
            },
        }

        st.session_state.query_history.append(history_entry)

        # Keep only the last 50 queries to avoid memory issues
        if len(st.session_state.query_history) > 50:
            st.session_state.query_history = st.session_state.query_history[-50:]

    def get_query_history(self) -> list[Dict[str, Any]]:
        """Get the query history.

        Returns:
            List of query history entries
        """
        return cast(list[Dict[str, Any]], st.session_state.get("query_history", []))

    def update_token_usage(self, tokens: Dict[str, Any]) -> None:
        """Update token usage metrics.

        Args:
            tokens: Token usage data
        """
        if "token_usage" not in st.session_state:
            st.session_state.token_usage = {
                "total": 0,
                "prompt": 0,
                "completion": 0,
                "last_query": 0,
            }

        usage = st.session_state.token_usage

        if isinstance(tokens, dict):
            usage["prompt"] += tokens.get("prompt", 0)
            usage["completion"] += tokens.get("completion", 0)
            usage["last_query"] = tokens.get("total", 0)
            usage["total"] += tokens.get("total", 0)
        else:
            # Handle case where tokens is just a number
            usage["last_query"] = tokens
            usage["total"] += tokens

    def get_token_usage(self) -> Dict[str, Any]:
        """Get current token usage metrics.

        Returns:
            Dictionary of token usage metrics
        """
        return cast(Dict[str, Any], st.session_state.get("token_usage", {}))

    def set_ui_preference(self, key: str, value: Any) -> None:
        """Set a UI preference value.

        Args:
            key: The preference key
            value: The preference value
        """
        st.session_state[key] = value

    def get_ui_preference(self, key: str, default: Any = None) -> Any:
        """Get a UI preference value.

        Args:
            key: The preference key
            default: Default value if key not found

        Returns:
            The preference value or default
        """
        return st.session_state.get(key, default)

    def trigger_rerun(self, query: str = "", config: Optional[Dict[str, Any]] = None) -> None:
        """Trigger a rerun with specific query and config.

        Args:
            query: The query to rerun
            config: The configuration to use
        """
        if query:
            st.session_state.rerun_query = query
        if config:
            st.session_state.rerun_config = config
        st.session_state.rerun_triggered = True

    def is_rerun_triggered(self) -> bool:
        """Check if a rerun has been triggered.

        Returns:
            True if rerun is triggered, False otherwise
        """
        return cast(bool, st.session_state.get("rerun_triggered", False))

    def clear_rerun_trigger(self) -> None:
        """Clear the rerun trigger state."""
        st.session_state.rerun_triggered = False

    def get_config(self) -> ConfigModel:
        """Get the current configuration.

        Returns:
            The current configuration
        """
        return cast(ConfigModel, st.session_state.get("config"))

    def reload_config(self) -> None:
        """Reload configuration from file."""
        st.session_state.config = self._config_loader.load_config()

    def export_state(self) -> Dict[str, Any]:
        """Export current session state for debugging.

        Returns:
            Dictionary of current session state (sanitized)
        """
        # Create a safe copy of session state for export
        safe_state: Dict[str, Any] = {}

        for key, value in st.session_state.items():
            if key.startswith("_"):
                continue  # Skip internal keys

            # Sanitize sensitive data
            if "token" in key.lower() or "key" in key.lower() or "secret" in key.lower():
                safe_state[key] = "***"
            elif isinstance(value, dict) and any(k in value for k in ["token", "key", "secret"]):
                safe_value = value.copy()
                for sensitive_key in ["token", "key", "secret"]:
                    if sensitive_key in safe_value:
                        safe_value[sensitive_key] = "***"
                safe_state[key] = safe_value
            else:
                safe_state[key] = value

        return safe_state
