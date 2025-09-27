"""Streamlit GUI for Autoresearch.

This user interface is experimental and largely untested. Expect rough edges.

This module provides a web-based GUI for Autoresearch using Streamlit.
It allows users to run queries, view results, and configure settings.
"""

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
import json
from typing import Any, Callable, Dict, List, cast
import random
import io
import time
import psutil
from .orchestration import metrics as orch_metrics
import threading
import os
import logging
import re
from datetime import datetime
from PIL import Image

from .config import ConfigLoader, ConfigModel
from .orchestration.orchestrator import Orchestrator
from .models import QueryResponse
from .orchestration import ReasoningMode
from .error_utils import get_error_info, format_error_for_gui
from .cli_utils import print_success
from .config_utils import (
    save_config_to_toml,
    get_config_presets,
    apply_preset,
)
from .output_format import OutputFormatter, build_depth_payload, OutputDepth
from .ui.provenance import (
    audit_status_rollup,
    depth_sequence,
    extract_graphrag_artifacts,
    generate_socratic_prompts,
    section_toggle_defaults,
)
from .streamlit_ui import (
    apply_accessibility_settings,
    apply_theme_settings,
    display_guided_tour,
    display_help_sidebar,
)

# Configure matplotlib to use a non-interactive backend
matplotlib.use("Agg")

# Set page configuration
st.set_page_config(
    page_title="Autoresearch",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS
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


def _trigger_rerun() -> None:
    """Trigger a rerun using whichever Streamlit API is available.

    Prefers the stable ``st.rerun`` API and falls back to the experimental variant for
    compatibility with older Streamlit releases.

    Returns:
        None.
    """

    rerun: Callable[[], None]
    if hasattr(st, "rerun"):
        rerun = cast(Callable[[], None], getattr(st, "rerun"))
    else:
        rerun = cast(Callable[[], None], getattr(st, "experimental_rerun"))
    rerun()


def display_config_editor():
    """Display the configuration editor interface in the sidebar."""
    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Create a form for editing configuration
    with st.sidebar.form("config_editor"):
        st.markdown("<h3>Edit Configuration</h3>", unsafe_allow_html=True)

        # Configuration presets
        st.markdown("#### Configuration Presets")
        presets = get_config_presets()
        preset_names = list(presets.keys())
        selected_preset = st.selectbox(
            "Select a preset",
            options=["Custom"] + preset_names,
            index=0,
            help="Select a predefined configuration preset or 'Custom' to configure manually",
        )

        # Apply preset button
        apply_preset_button = st.form_submit_button("Apply Preset")

        # Core settings
        st.markdown("#### Core Settings")

        # If a preset is selected and the apply button is clicked, use the preset values
        preset_config = None
        if apply_preset_button and selected_preset != "Custom":
            preset_config = apply_preset(selected_preset)

        llm_backend = st.text_input(
            "LLM Backend",
            value=preset_config["llm_backend"] if preset_config else config.llm_backend,
        )

        # Get the reasoning mode options
        reasoning_mode_options = [mode.value for mode in ReasoningMode]

        # Determine the index for the reasoning mode
        if preset_config and "reasoning_mode" in preset_config:
            reasoning_mode_index = reasoning_mode_options.index(
                preset_config["reasoning_mode"]
            )
        else:
            reasoning_mode_index = reasoning_mode_options.index(
                config.reasoning_mode.value
            )

        reasoning_mode = st.selectbox(
            "Reasoning Mode",
            options=reasoning_mode_options,
            index=reasoning_mode_index,
        )

        # Profile selection
        profiles = ["None"] + config_loader.available_profiles()
        current_profile = config.active_profile if config.active_profile else "None"
        profile_index = profiles.index(current_profile) if current_profile in profiles else 0
        selected_profile = st.selectbox(
            "Active Profile",
            options=profiles,
            index=profile_index,
            help="Select a saved profile of preferences",
        )

        loops = st.number_input(
            "Loops",
            min_value=1,
            max_value=10,
            value=preset_config["loops"] if preset_config else config.loops,
            help="Number of reasoning loops to perform",
        )

        st.markdown("#### Scout Gate Policy")
        gate_policy_enabled = st.checkbox(
            "Enable Scout Gate Policy",
            value=(
                preset_config.get("gate_policy_enabled", config.gate_policy_enabled)
                if preset_config
                else config.gate_policy_enabled
            ),
            help="Toggle scout-mode heuristics before launching debate loops.",
        )
        gate_retrieval_overlap_threshold = st.number_input(
            "Retrieval Overlap Threshold",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=float(
                preset_config.get(
                    "gate_retrieval_overlap_threshold",
                    config.gate_retrieval_overlap_threshold,
                )
                if preset_config
                else config.gate_retrieval_overlap_threshold
            ),
            format="%.2f",
            help="Overlap scores below this value trigger full debate.",
        )
        gate_nli_conflict_threshold = st.number_input(
            "Conflict Threshold",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=float(
                preset_config.get(
                    "gate_nli_conflict_threshold",
                    config.gate_nli_conflict_threshold,
                )
                if preset_config
                else config.gate_nli_conflict_threshold
            ),
            format="%.2f",
            help="Contradiction probability above this value forces debate.",
        )
        gate_complexity_threshold = st.number_input(
            "Complexity Threshold",
            min_value=0.0,
            max_value=1.0,
            step=0.05,
            value=float(
                preset_config.get(
                    "gate_complexity_threshold",
                    config.gate_complexity_threshold,
                )
                if preset_config
                else config.gate_complexity_threshold
            ),
            format="%.2f",
            help="Complexity scores above this value escalate to debate.",
        )
        overrides_default = ""
        overrides_source: Dict[str, Any] | None = None
        if preset_config and "gate_user_overrides" in preset_config:
            maybe_overrides = preset_config.get("gate_user_overrides")
            if isinstance(maybe_overrides, dict):
                overrides_source = maybe_overrides
        elif isinstance(config.gate_user_overrides, dict) and config.gate_user_overrides:
            overrides_source = config.gate_user_overrides
        if overrides_source:
            overrides_default = json.dumps(overrides_source, indent=2)
        gate_user_overrides_text = st.text_area(
            "Gate Policy Overrides (JSON)",
            value=overrides_default,
            help=(
                "Optional JSON to override heuristic signals or force a "
                "decision. Leave blank to use automatic heuristics."
            ),
        )

        # Storage settings
        st.markdown("#### Storage Settings")
        duckdb_path = st.text_input(
            "DuckDB Path",
            value=preset_config["storage"]["duckdb_path"]
            if preset_config and "storage" in preset_config
            else config.storage.duckdb_path,
            help="Path to the DuckDB database file",
        )

        vector_extension = st.checkbox(
            "Enable Vector Extension",
            value=preset_config["storage"]["vector_extension"]
            if preset_config and "storage" in preset_config
            else config.storage.vector_extension,
            help="Enable the DuckDB vector extension for similarity search",
        )

        # Search settings
        st.markdown("#### Search Settings")
        max_results = st.number_input(
            "Max Results Per Query",
            min_value=1,
            max_value=20,
            value=preset_config["search"]["max_results_per_query"]
            if preset_config and "search" in preset_config
            else config.search.max_results_per_query,
            help="Maximum number of search results to return per query",
        )

        use_semantic_similarity = st.checkbox(
            "Use Semantic Similarity",
            value=preset_config["search"]["use_semantic_similarity"]
            if preset_config and "search" in preset_config
            else config.search.use_semantic_similarity,
            help="Use semantic similarity for search result ranking",
        )

        # User preference settings
        st.markdown("#### User Preferences")

        pref_config = cast(
            Dict[str, Any],
            preset_config.get("user_preferences") if preset_config else config.user_preferences,
        )

        detail_level = st.selectbox(
            "Detail Level",
            options=["concise", "balanced", "detailed"],
            index=["concise", "balanced", "detailed"].index(
                pref_config.get("detail_level", "balanced")
            ),
        )

        perspective = st.selectbox(
            "Perspective",
            options=["neutral", "critical", "optimistic"],
            index=["neutral", "critical", "optimistic"].index(
                pref_config.get("perspective", "neutral")
            ),
        )

        format_pref = st.selectbox(
            "Format Preference",
            options=["structured", "narrative", "bullet_points"],
            index=["structured", "narrative", "bullet_points"].index(
                pref_config.get("format_preference", "structured")
            ),
        )

        expertise_level = st.selectbox(
            "Expertise Level",
            options=["beginner", "intermediate", "expert"],
            index=["beginner", "intermediate", "expert"].index(
                pref_config.get("expertise_level", "intermediate")
            ),
        )

        focus_areas = st.text_input(
            "Focus Areas (comma-separated)",
            value=", ".join(pref_config.get("focus_areas", [])),
        )

        excluded_areas = st.text_input(
            "Excluded Areas (comma-separated)",
            value=", ".join(pref_config.get("excluded_areas", [])),
        )

        # Hot-reload option
        enable_hot_reload = st.checkbox(
            "Enable Hot-Reload",
            value=True,
            help="Automatically reload the configuration when changes are detected",
        )

        # Submit button
        submitted = st.form_submit_button("Save Configuration")

        if submitted:
            try:
                # Create a dictionary with the updated configuration
                overrides_payload: Dict[str, Any] = {}
                overrides_text = gate_user_overrides_text.strip()
                if overrides_text:
                    try:
                        parsed_overrides = json.loads(overrides_text)
                        if isinstance(parsed_overrides, dict):
                            overrides_payload = parsed_overrides
                        else:
                            raise ValueError("Overrides must be a JSON object")
                    except (json.JSONDecodeError, ValueError) as exc:
                        st.sidebar.error(f"Invalid gate override JSON: {exc}")
                        st.stop()
                updated_config = {
                    "llm_backend": llm_backend,
                    "reasoning_mode": reasoning_mode,
                    "loops": loops,
                    "gate_policy_enabled": gate_policy_enabled,
                    "gate_retrieval_overlap_threshold": gate_retrieval_overlap_threshold,
                    "gate_nli_conflict_threshold": gate_nli_conflict_threshold,
                    "gate_complexity_threshold": gate_complexity_threshold,
                    "gate_user_overrides": overrides_payload,
                    "storage": {
                        "duckdb_path": duckdb_path,
                        "vector_extension": vector_extension,
                    },
                    "search": {
                        "max_results_per_query": max_results,
                        "use_semantic_similarity": use_semantic_similarity,
                    },
                    "user_preferences": {
                        "detail_level": detail_level,
                        "perspective": perspective,
                        "format_preference": format_pref,
                        "expertise_level": expertise_level,
                        "focus_areas": [
                            a.strip() for a in focus_areas.split(";") if a.strip()
                        ]
                        if ";" in focus_areas
                        else [
                            a.strip() for a in focus_areas.split(",") if a.strip()
                        ],
                        "excluded_areas": [
                            a.strip() for a in excluded_areas.split(";") if a.strip()
                        ]
                        if ";" in excluded_areas
                        else [
                            a.strip() for a in excluded_areas.split(",") if a.strip()
                        ],
                    },
                    "active_profile": selected_profile if selected_profile != "None" else None,
                }

                # Save the configuration to the TOML file
                if save_config_to_toml(updated_config):
                    st.sidebar.success("Configuration saved successfully!")

                    # Reload the configuration
                    if selected_profile != "None":
                        config_loader.set_active_profile(selected_profile)
                    else:
                        config_loader.set_active_profile(config_loader.available_profiles()[0]) if config_loader.available_profiles() else None
                    config = config_loader.load_config()

                    # Start watching for configuration changes if hot-reload is enabled
                    if enable_hot_reload:
                        config_loader.watch_changes(on_config_change)
                else:
                    st.sidebar.error("Failed to save configuration")
            except Exception as e:
                st.sidebar.error(f"Error saving configuration: {str(e)}")


def on_config_change(config):
    """Handle configuration changes.

    This function is called when the configuration changes, either through
    the configuration editor or by external changes to the configuration file.

    Args:
        config: The new configuration
    """
    # Use Streamlit's session state to store the updated configuration
    if "config" not in st.session_state:
        st.session_state.config = config
    else:
        st.session_state.config = config

    # Add a notification to the session state
    st.session_state.config_changed = True
    st.session_state.config_change_time = time.time()


def track_agent_performance(
    agent_name: str, duration: float, tokens: int, success: bool = True
):
    """Track agent performance metrics.

    Args:
        agent_name: The name of the agent
        duration: The duration of the agent's execution in seconds
        tokens: The number of tokens used by the agent
        success: Whether the agent's execution was successful
    """
    # Initialize agent performance metrics in session state if they don't exist
    if "agent_performance" not in st.session_state:
        st.session_state.agent_performance = {}

    # Initialize metrics for this agent if they don't exist
    if agent_name not in st.session_state.agent_performance:
        st.session_state.agent_performance[agent_name] = {
            "executions": 0,
            "total_duration": 0,
            "total_tokens": 0,
            "successes": 0,
            "failures": 0,
            "history": [],
        }

    # Update metrics
    metrics = st.session_state.agent_performance[agent_name]
    metrics["executions"] += 1
    metrics["total_duration"] += duration
    metrics["total_tokens"] += tokens
    if success:
        metrics["successes"] += 1
    else:
        metrics["failures"] += 1

    # Add to history (keep last 100 executions)
    metrics["history"].append(
        {
            "timestamp": datetime.now(),
            "duration": duration,
            "tokens": tokens,
            "success": success,
        }
    )
    if len(metrics["history"]) > 100:
        metrics["history"].pop(0)

    # Log the performance
    logging.info(
        f"Agent {agent_name} performance: duration={duration:.2f}s, tokens={tokens}, success={success}"
    )


def collect_system_metrics() -> Dict[str, Any]:
    """Collect system metrics (CPU, memory, tokens).

    Returns:
        Dict[str, Any]: A dictionary of system metrics
    """
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # Get memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used = memory.used / (1024 * 1024 * 1024)  # Convert to GB
    memory_total = memory.total / (1024 * 1024 * 1024)  # Convert to GB

    # Get process information
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB

    token_usage = st.session_state.get(
        "token_usage",
        {"total": 0, "prompt": 0, "completion": 0, "last_query": 0},
    )

    # Aggregate total tokens using Prometheus counters
    total_in = int(orch_metrics.TOKENS_IN_COUNTER._value.get())
    total_out = int(orch_metrics.TOKENS_OUT_COUNTER._value.get())

    # Determine overall health status
    health = "OK"
    if cpu_percent > 90 or memory_percent > 90:
        health = "CRITICAL"
    elif cpu_percent > 80 or memory_percent > 80:
        health = "WARNING"

    # Get agent performance metrics
    agent_performance = st.session_state.get("agent_performance", {})

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "memory_used": memory_used,
        "memory_total": memory_total,
        "process_memory": process_memory,
        "token_usage": token_usage,
        "tokens_in_total": total_in,
        "tokens_out_total": total_out,
        "agent_performance": agent_performance,
        "health": health,
    }


def update_metrics_periodically():
    """Update system metrics periodically in the background."""
    while True:
        # Collect metrics
        metrics = collect_system_metrics()

        # Update session state
        if "system_metrics" not in st.session_state:
            st.session_state.system_metrics = []

        # Add current metrics to history (keep last 60 data points)
        st.session_state.system_metrics.append(metrics)
        if len(st.session_state.system_metrics) > 60:
            st.session_state.system_metrics.pop(0)

        # Update current metrics
        st.session_state.current_metrics = metrics

        # Sleep for 1 second
        time.sleep(1)


def display_agent_performance():
    """Display agent performance visualization."""
    st.markdown("<h2 class='subheader'>Agent Performance</h2>", unsafe_allow_html=True)

    # Get agent performance metrics
    agent_performance = st.session_state.get("agent_performance", {})

    if not agent_performance:
        st.info("No agent performance data available yet")

        # Add some sample data for demonstration
        if st.button("Add Sample Data"):
            # Sample agents
            agents = ["Synthesizer", "Contrarian", "FactChecker"]

            # Add sample data for each agent
            for agent in agents:
                for i in range(5):
                    track_agent_performance(
                        agent_name=agent,
                        duration=random.uniform(0.5, 3.0),
                        tokens=random.randint(100, 1000),
                        success=random.random() > 0.2,
                    )

            st.success("Sample data added")
            _trigger_rerun()

        return

    # Create tabs for different visualizations
    perf_tab1, perf_tab2, perf_tab3 = st.tabs(["Summary", "Comparison", "History"])

    with perf_tab1:
        # Summary view
        st.markdown("### Agent Performance Summary")

        # Create a DataFrame for the summary
        import pandas as pd

        summary_data = []

        for agent_name, metrics in agent_performance.items():
            avg_duration = (
                metrics["total_duration"] / metrics["executions"]
                if metrics["executions"] > 0
                else 0
            )
            avg_tokens = (
                metrics["total_tokens"] / metrics["executions"]
                if metrics["executions"] > 0
                else 0
            )
            success_rate = (
                metrics["successes"] / metrics["executions"] * 100
                if metrics["executions"] > 0
                else 0
            )

            summary_data.append(
                {
                    "Agent": agent_name,
                    "Executions": metrics["executions"],
                    "Avg Duration (s)": round(avg_duration, 2),
                    "Avg Tokens": round(avg_tokens, 0),
                    "Success Rate (%)": round(success_rate, 1),
                }
            )

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

    with perf_tab2:
        # Comparison view
        st.markdown("### Agent Performance Comparison")

        # Create a DataFrame for the comparison
        comparison_data: Dict[str, List[Any]] = {
            "Agent": [],
            "Metric": [],
            "Value": [],
        }

        for agent_name, metrics in agent_performance.items():
            avg_duration = (
                metrics["total_duration"] / metrics["executions"]
                if metrics["executions"] > 0
                else 0
            )
            avg_tokens = (
                metrics["total_tokens"] / metrics["executions"]
                if metrics["executions"] > 0
                else 0
            )
            success_rate = (
                metrics["successes"] / metrics["executions"] * 100
                if metrics["executions"] > 0
                else 0
            )

            comparison_data["Agent"].extend([agent_name, agent_name, agent_name])
            comparison_data["Metric"].extend(
                ["Avg Duration (s)", "Avg Tokens", "Success Rate (%)"]
            )
            comparison_data["Value"].extend([avg_duration, avg_tokens, success_rate])

        comparison_df = pd.DataFrame(comparison_data)

        # Create a bar chart for the comparison
        import altair as alt

        # Normalize the values for better visualization
        pivot_df = comparison_df.pivot(index="Agent", columns="Metric", values="Value")
        normalized_df = pivot_df.copy()
        for col in pivot_df.columns:
            if pivot_df[col].max() > 0:
                normalized_df[col] = pivot_df[col] / pivot_df[col].max()

        normalized_df = normalized_df.reset_index().melt(
            id_vars=["Agent"], var_name="Metric", value_name="Value"
        )

        chart = (
            alt.Chart(normalized_df)
            .mark_bar()
            .encode(
                x=alt.X("Agent:N", title="Agent"),
                y=alt.Y("Value:Q", title="Normalized Value"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=["Agent", "Metric", "Value"],
            )
            .properties(width=600, height=400)
        )

        st.altair_chart(chart, use_container_width=True)

        # Display the actual values
        st.markdown("#### Actual Values")
        st.dataframe(pivot_df, use_container_width=True)

    with perf_tab3:
        # History view
        st.markdown("### Agent Performance History")

        # Select agent
        agent_names = list(agent_performance.keys())
        selected_agent = st.selectbox("Select Agent", agent_names)

        if selected_agent and selected_agent in agent_performance:
            agent_metrics = agent_performance[selected_agent]
            history = agent_metrics["history"]

            if history:
                # Create a DataFrame for the history
                history_data = {
                    "timestamp": [h["timestamp"] for h in history],
                    "duration": [h["duration"] for h in history],
                    "tokens": [h["tokens"] for h in history],
                    "success": [h["success"] for h in history],
                }

                history_df = pd.DataFrame(history_data)

                # Create a line chart for duration and tokens
                st.markdown("#### Duration and Tokens Over Time")

                # Normalize the values for better visualization
                chart_data = history_df.copy()
                chart_data["normalized_duration"] = (
                    chart_data["duration"] / chart_data["duration"].max()
                    if chart_data["duration"].max() > 0
                    else 0
                )
                chart_data["normalized_tokens"] = (
                    chart_data["tokens"] / chart_data["tokens"].max()
                    if chart_data["tokens"].max() > 0
                    else 0
                )

                # Create a line chart
                line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
                    x=alt.X("timestamp:T", title="Time"),
                    y=alt.Y("normalized_duration:Q", title="Normalized Value"),
                    color=alt.value("#1f77b4"),
                    tooltip=["timestamp", "duration"],
                ).properties(width=600, height=300) + alt.Chart(chart_data).mark_line(
                    point=True
                ).encode(
                    x=alt.X("timestamp:T", title="Time"),
                    y=alt.Y("normalized_tokens:Q", title="Normalized Value"),
                    color=alt.value("#ff7f0e"),
                    tooltip=["timestamp", "tokens"],
                )

                st.altair_chart(line_chart, use_container_width=True)

                # Create a legend
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        "<span style='color:#1f77b4'>● Duration</span>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown(
                        "<span style='color:#ff7f0e'>● Tokens</span>",
                        unsafe_allow_html=True,
                    )

                # Create a bar chart for success rate
                st.markdown("#### Success Rate Over Time")

                # Calculate rolling success rate
                window_size = min(10, len(history))
                rolling_success = []

                for i in range(len(history)):
                    start_idx = max(0, i - window_size + 1)
                    window = history[start_idx:i + 1]
                    success_count = sum(1 for h in window if h["success"])
                    success_rate = success_count / len(window) * 100
                    rolling_success.append(success_rate)

                chart_data["rolling_success"] = rolling_success

                # Create a bar chart
                bar_chart = (
                    alt.Chart(chart_data)
                    .mark_bar()
                    .encode(
                        x=alt.X("timestamp:T", title="Time"),
                        y=alt.Y(
                            "rolling_success:Q",
                            title="Success Rate (%)",
                            scale=alt.Scale(domain=[0, 100]),
                        ),
                        color=alt.condition(
                            alt.datum.rolling_success >= 80,
                            alt.value("#2ecc71"),  # Green for high success rate
                            alt.condition(
                                alt.datum.rolling_success >= 50,
                                alt.value("#f39c12"),  # Orange for medium success rate
                                alt.value("#e74c3c"),  # Red for low success rate
                            ),
                        ),
                        tooltip=["timestamp", "rolling_success"],
                    )
                    .properties(width=600, height=300)
                )

                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.info(f"No history data available for {selected_agent}")
        else:
            st.info("Please select an agent")


def display_metrics_dashboard():
    """Display the system metrics dashboard."""
    # Create tabs for different metrics
    metrics_tab1, metrics_tab2 = st.tabs(["System Metrics", "Agent Performance"])

    with metrics_tab1:
        st.markdown("<h2 class='subheader'>System Metrics</h2>", unsafe_allow_html=True)

        # Create columns for metrics
        col1, col2, col3 = st.columns(3)

        # Get current metrics
        metrics = st.session_state.get("current_metrics", collect_system_metrics())

        # Display CPU usage
        with col1:
            st.markdown("### CPU Usage")
            st.progress(metrics["cpu_percent"] / 100)
            st.markdown(f"{metrics['cpu_percent']:.1f}%")

        # Display memory usage
        with col2:
            st.markdown("### Memory Usage")
            st.progress(metrics["memory_percent"] / 100)
            st.markdown(
                f"{metrics['memory_used']:.1f} GB / {metrics['memory_total']:.1f} GB ({metrics['memory_percent']:.1f}%)"
            )

        # Display process memory
        with col3:
            st.markdown("### Process Memory")
            st.markdown(f"{metrics['process_memory']:.1f} MB")

        # Display system health
        status = metrics.get("health", "OK")
        color = "green" if status == "OK" else "orange" if status == "WARNING" else "red"
        st.markdown(f"### Health: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)

        # Display token usage
        st.markdown("### Token Usage")
        token_usage = metrics["token_usage"]

        # Create columns for token metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Tokens", token_usage["total"])

        with col2:
            st.metric("Prompt Tokens", token_usage["prompt"])

        with col3:
            st.metric("Completion Tokens", token_usage["completion"])

        with col4:
            st.metric("Last Query Tokens", token_usage["last_query"])

        extra1, extra2 = st.columns(2)
        with extra1:
            st.metric("Total Input Tokens", metrics["tokens_in_total"])
        with extra2:
            st.metric("Total Output Tokens", metrics["tokens_out_total"])

        # Display metrics history chart
        if (
            "system_metrics" in st.session_state
            and len(st.session_state.system_metrics) > 1
        ):
            st.markdown("### Metrics History")

            # Create a chart for CPU and memory usage
            chart_data = {
                "time": list(range(len(st.session_state.system_metrics))),
                "cpu": [m["cpu_percent"] for m in st.session_state.system_metrics],
                "memory": [
                    m["memory_percent"] for m in st.session_state.system_metrics
                ],
            }

            # Create a DataFrame for the chart
            import pandas as pd

            df = pd.DataFrame(chart_data)

            # Display the chart
            st.line_chart(df.set_index("time")[["cpu", "memory"]])

    with metrics_tab2:
        display_agent_performance()


class StreamlitLogHandler(logging.Handler):
    """Custom log handler that stores logs in Streamlit's session state."""

    def __init__(self, level=logging.INFO):
        """Initialize the handler with the specified log level."""
        super().__init__(level)
        self.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    def emit(self, record):
        """Store the log record in Streamlit's session state."""
        try:
            # Format the log message
            log_entry = self.format(record)

            # Initialize logs list in session state if it doesn't exist
            if "logs" not in st.session_state:
                st.session_state.logs = []

            # Add the log entry to the session state
            log_dict = {
                "timestamp": datetime.fromtimestamp(record.created),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "formatted": log_entry,
            }
            st.session_state.logs.append(log_dict)

            # Keep only the last 1000 log entries to avoid memory issues
            if len(st.session_state.logs) > 1000:
                st.session_state.logs = st.session_state.logs[-1000:]

        except Exception:
            self.handleError(record)


def setup_logging():
    """Set up the logging system with the custom handler."""
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


def display_log_viewer():
    """Display the log viewer with filtering capabilities."""
    st.markdown("<h2 class='subheader'>Log Viewer</h2>", unsafe_allow_html=True)

    # Get logs from session state
    logs = st.session_state.get("logs", [])

    if not logs:
        st.info("No logs available yet")
        return

    # Create filter controls
    st.markdown("### Log Filters")

    # Create columns for filter controls
    col1, col2, col3 = st.columns(3)

    with col1:
        # Filter by log level
        log_levels = ["ALL"] + sorted(set(log["level"] for log in logs))
        selected_level = st.selectbox("Log Level", log_levels)

    with col2:
        # Filter by logger name
        logger_names = ["ALL"] + sorted(set(log["logger"] for log in logs))
        selected_logger = st.selectbox("Logger", logger_names)

    with col3:
        # Filter by text
        filter_text = st.text_input("Filter Text", "")

    # Apply filters
    filtered_logs = logs

    if selected_level != "ALL":
        filtered_logs = [log for log in filtered_logs if log["level"] == selected_level]

    if selected_logger != "ALL":
        filtered_logs = [
            log for log in filtered_logs if log["logger"] == selected_logger
        ]

    if filter_text:
        pattern = re.compile(filter_text, re.IGNORECASE)
        filtered_logs = [
            log for log in filtered_logs if pattern.search(log["formatted"])
        ]

    # Display log count
    st.markdown(f"Showing {len(filtered_logs)} of {len(logs)} logs")

    # Create a download button for logs
    if filtered_logs:
        log_text = "\n".join(log["formatted"] for log in filtered_logs)
        st.download_button(
            label="Download Logs",
            data=log_text,
            file_name=f"autoresearch_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )

    # Display logs in a table
    if filtered_logs:
        # Create a DataFrame for the logs
        import pandas as pd

        log_df = pd.DataFrame(
            [
                {
                    "Time": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "Level": log["level"],
                    "Logger": log["logger"],
                    "Message": log["message"],
                }
                for log in filtered_logs
            ]
        )

        # Display the DataFrame
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No logs match the current filters")


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    # Initialize configuration
    if "config" not in st.session_state:
        config_loader = ConfigLoader()
        st.session_state.config = config_loader.load_config()

        # Start watching for configuration changes
        config_loader.watch_changes(on_config_change)

    # Initialize token usage metrics
    if "token_usage" not in st.session_state:
        st.session_state.token_usage = {
            "total": 0,
            "prompt": 0,
            "completion": 0,
            "last_query": 0,
        }

    # Initialize query history
    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    # Initialize rerun state
    if "rerun_triggered" not in st.session_state:
        st.session_state.rerun_triggered = False

    # Initialize current query
    if "current_query" not in st.session_state:
        st.session_state.current_query = ""

    # Initialize current result
    if "current_result" not in st.session_state:
        st.session_state.current_result = None


def display_query_input() -> None:
    """Render the query input controls."""
    st.markdown("<h2 class='subheader'>Query Input</h2>", unsafe_allow_html=True)
    st.markdown(
        (
            "<p id='keyboard-nav' class='sr-only'>"
            "Use Tab to navigate fields and press Enter on 'Run Query' to submit."
            "</p>"
        ),
        unsafe_allow_html=True,
    )
    with st.form("query_form"):
        st.markdown(
            "<div role='region' aria-label='Query input area' tabindex='0'>",
            unsafe_allow_html=True,
        )
        col_query, col_actions = st.columns([3, 1])
        with col_query:
            st.session_state.current_query = st.text_area(
                "Enter your query:",
                height=100,
                placeholder="What would you like to research?",
                key="query_input",
                help="After typing, press Tab to reach the Run button",
            )
        with col_actions:
            st.session_state.reasoning_mode = st.selectbox(
                "Reasoning Mode:",
                options=[mode.value for mode in ReasoningMode],
                index=[mode.value for mode in ReasoningMode].index(
                    st.session_state.config.reasoning_mode.value
                ),
                key="reasoning_mode",
            )
            st.session_state.loops = st.slider(
                "Loops:",
                min_value=1,
                max_value=5,
                value=st.session_state.config.loops,
                key="loops_slider",
            )
            submitted = st.form_submit_button(
                "Run Query",
                type="primary",
                help="Activate to run your query",
                use_container_width=True,
            )
            st.session_state.run_button = submitted
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Run the Streamlit app."""
    # Initialize session state
    initialize_session_state()

    # Start background threads if not already running
    if not any(thread.name == "MetricsCollector" for thread in threading.enumerate()):
        # Start background thread for metrics collection
        metrics_thread = threading.Thread(
            target=update_metrics_periodically, daemon=True, name="MetricsCollector"
        )
        metrics_thread.start()

        # Set up logging
        setup_logging()

        # Log application start
        logging.info("Streamlit application started")

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

    # Sidebar for configuration
    with st.sidebar:
        st.markdown("<h2 class='subheader'>Configuration</h2>", unsafe_allow_html=True)

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

        # Display current configuration
        st.markdown("### Current Settings")
        st.markdown(f"**LLM Backend:** {st.session_state.config.llm_backend}")
        st.markdown(
            f"**Reasoning Mode:** {st.session_state.config.reasoning_mode.value}"
        )
        st.markdown(f"**Loops:** {st.session_state.config.loops}")
        st.markdown(
            f"**Active Profile:** {st.session_state.config.active_profile or 'None'}"
        )
        if hasattr(st.session_state.config, "user_preferences"):
            prefs = st.session_state.config.user_preferences
            st.markdown("### Preferences")
            st.markdown(f"**Detail:** {prefs.get('detail_level', 'balanced')}")
            st.markdown(f"**Perspective:** {prefs.get('perspective', 'neutral')}")

        # Add a button to reload configuration
        if st.button("Reload Configuration"):
            config_loader = ConfigLoader()
            st.session_state.config = config_loader.load_config()
            st.success("Configuration reloaded")

        # Show notification if configuration has changed
        if st.session_state.get("config_changed", False):
            st.success("Configuration updated")
            # Reset the notification flag
            st.session_state.config_changed = False

        # Add an expander for the configuration editor
        with st.expander("Edit Configuration"):
            display_config_editor()

        # Tutorial/help sidebar
        display_help_sidebar()

    # Apply theme and accessibility styles based on sidebar settings
    apply_theme_settings()
    apply_accessibility_settings()

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
        display_query_input()

    with metrics_tab:
        # Display metrics dashboard
        display_metrics_dashboard()

    with logs_tab:
        # Display log viewer
        display_log_viewer()

    with history_tab:
        # Display query history
        display_query_history()


def store_query_history(query: str, result: QueryResponse, config: ConfigModel) -> None:
    """Store query history in the session state.

    Args:
        query: The query string
        result: The query response
        config: The configuration used for the query
    """
    # Initialize query history in session state if it doesn't exist
    if "query_history" not in st.session_state:
        st.session_state.query_history = []

    # Create a history entry
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

    # Add to history
    st.session_state.query_history.append(history_entry)

    # Keep only the last 50 queries to avoid memory issues
    if len(st.session_state.query_history) > 50:
        st.session_state.query_history = st.session_state.query_history[-50:]

    # Log the query
    logging.info(f"Query stored in history: {query[:50]}...")


def display_query_history():
    """Display query history and allow rerunning previous queries."""
    st.markdown("<h2 class='subheader'>Query History</h2>", unsafe_allow_html=True)

    # Get query history from session state
    history = st.session_state.get("query_history", [])

    if not history:
        st.info("No query history available yet")
        return

    # Create a DataFrame for the history
    import pandas as pd

    history_data = []

    for i, entry in enumerate(reversed(history)):
        history_data.append(
            {
                "ID": len(history) - i,
                "Time": entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "Query": entry["query"][:50] + "..."
                if len(entry["query"]) > 50
                else entry["query"],
                "Mode": entry["config"]["reasoning_mode"],
                "Loops": entry["config"]["loops"],
                "Backend": entry["config"]["llm_backend"],
            }
        )

    history_df = pd.DataFrame(history_data)

    # Display the history table
    st.dataframe(history_df, use_container_width=True)

    # Create a form to select and rerun a query
    with st.form("rerun_query_form"):
        st.markdown("### Rerun a Previous Query")

        # Select a query to rerun
        query_id = st.number_input(
            "Select Query ID to Rerun",
            min_value=1,
            max_value=len(history),
            value=1,
            step=1,
        )

        # Option to modify the query
        modify_query = st.checkbox("Modify Query")

        # If modify query is checked, show a text area to edit the query
        if modify_query:
            selected_entry = history[len(history) - query_id]
            modified_query = st.text_area(
                "Edit Query", value=selected_entry["query"], height=100
            )

        # Submit button
        rerun_button = st.form_submit_button("Rerun Query")

        if rerun_button:
            # Get the selected query
            selected_entry = history[len(history) - query_id]

            # Set the query and configuration
            if modify_query:
                st.session_state.rerun_query = modified_query
            else:
                st.session_state.rerun_query = selected_entry["query"]

            st.session_state.rerun_config = selected_entry["config"]
            st.session_state.rerun_triggered = True

            # Rerun the app to process the query
            _trigger_rerun()

    # Process query when button is clicked
    if st.session_state.run_button and st.session_state.current_query:
        # Update config with selected options
        st.session_state.config.reasoning_mode = ReasoningMode(
            st.session_state.reasoning_mode
        )
        st.session_state.config.loops = st.session_state.loops

        # Show spinner while processing
        with st.spinner("Processing query..."):
            try:
                # Run the query
                result = Orchestrator().run_query(
                    st.session_state.current_query,
                    st.session_state.config,
                )

                if hasattr(result, "metrics") and result.metrics:
                    track_agent_performance(
                        agent_name="Query",
                        duration=result.metrics.get("time", 0),
                        tokens=result.metrics.get("tokens", 0),
                    )

                # Update token usage metrics
                if (
                    hasattr(result, "metrics")
                    and result.metrics
                    and "tokens" in result.metrics
                ):
                    tokens = result.metrics["tokens"]
                    if "token_usage" not in st.session_state:
                        st.session_state.token_usage = {
                            "total": 0,
                            "prompt": 0,
                            "completion": 0,
                            "last_query": 0,
                        }

                    # Update token usage metrics
                    if isinstance(tokens, dict):
                        # If tokens is a dictionary with detailed metrics
                        st.session_state.token_usage["prompt"] += tokens.get(
                            "prompt", 0
                        )
                        st.session_state.token_usage["completion"] += tokens.get(
                            "completion", 0
                        )
                        st.session_state.token_usage["last_query"] = tokens.get(
                            "total", 0
                        )
                        st.session_state.token_usage["total"] += tokens.get("total", 0)
                    else:
                        # If tokens is just a number
                        st.session_state.token_usage["last_query"] = tokens
                        st.session_state.token_usage["total"] += tokens

                # Store query in history
                store_query_history(
                    st.session_state.current_query,
                    result,
                    st.session_state.config,
                )

                # Display results
                display_results(result)
            except Exception as e:
                # Get error information with suggestions and code examples
                error_info = get_error_info(e)
                formatted_error = format_error_for_gui(error_info)

                # Display error with suggestions and code examples
                st.error(formatted_error)

                # Log the error
                logging.error(f"Error processing query: {str(e)}", exc_info=e)
    elif st.session_state.run_button and not st.session_state.current_query:
        st.warning("Please enter a query")

    # Process rerun query if triggered
    if st.session_state.get("rerun_triggered", False):
        # Get the query and configuration
        rerun_query = st.session_state.get("rerun_query", "")
        rerun_config = st.session_state.get("rerun_config", {})

        # Reset the trigger
        st.session_state.rerun_triggered = False

        # Update the configuration
        st.session_state.config.reasoning_mode = ReasoningMode(
            rerun_config["reasoning_mode"]
        )
        st.session_state.config.loops = rerun_config["loops"]

        # Show spinner while processing
        with st.spinner(f"Rerunning query: {rerun_query[:50]}..."):
            try:
                # Run the query
                result = Orchestrator().run_query(rerun_query, st.session_state.config)

                # Update token usage metrics
                if (
                    hasattr(result, "metrics")
                    and result.metrics
                    and "tokens" in result.metrics
                ):
                    tokens = result.metrics["tokens"]
                    if "token_usage" not in st.session_state:
                        st.session_state.token_usage = {
                            "total": 0,
                            "prompt": 0,
                            "completion": 0,
                            "last_query": 0,
                        }

                    # Update token usage metrics
                    if isinstance(tokens, dict):
                        # If tokens is a dictionary with detailed metrics
                        st.session_state.token_usage["prompt"] += tokens.get(
                            "prompt", 0
                        )
                        st.session_state.token_usage["completion"] += tokens.get(
                            "completion", 0
                        )
                        st.session_state.token_usage["last_query"] = tokens.get(
                            "total", 0
                        )
                        st.session_state.token_usage["total"] += tokens.get("total", 0)
                    else:
                        # If tokens is just a number
                        st.session_state.token_usage["last_query"] = tokens
                        st.session_state.token_usage["total"] += tokens

                if hasattr(result, "metrics") and result.metrics:
                    track_agent_performance(
                        agent_name="Query",
                        duration=result.metrics.get("time", 0),
                        tokens=result.metrics.get("tokens", 0),
                    )

                # Store query in history
                store_query_history(rerun_query, result, st.session_state.config)

                # Display results
                display_results(result)

                # Show success message
                st.success(f"Successfully reran query: {rerun_query[:50]}...")
            except Exception as e:
                # Get error information with suggestions and code examples
                error_info = get_error_info(e)
                formatted_error = format_error_for_gui(error_info)

                # Display error with suggestions and code examples
                st.error(formatted_error)

                # Log the error
                logging.error(f"Error rerunning query: {str(e)}", exc_info=e)


def create_knowledge_graph(result: QueryResponse) -> Image.Image:
    """Create a knowledge graph visualization from the query response.

    Args:
        result: The query response to visualize

    Returns:
        A PIL Image containing the knowledge graph visualization
    """
    # Create a directed graph
    G: nx.DiGraph[Any] = nx.DiGraph()

    # Add the main query node
    main_query = "Query"
    G.add_node(main_query, type="query")

    # Add the answer node
    answer = "Answer"
    G.add_node(answer, type="answer")
    G.add_edge(main_query, answer)

    # Add citation nodes
    for i, citation in enumerate(result.citations):
        citation_id = f"Citation {i + 1}"
        G.add_node(citation_id, type="citation")
        G.add_edge(answer, citation_id)

    # Add reasoning nodes
    for i, step in enumerate(result.reasoning):
        reasoning_id = f"Reasoning {i + 1}"
        G.add_node(reasoning_id, type="reasoning")
        if i == 0:
            G.add_edge(main_query, reasoning_id)
        else:
            G.add_edge(f"Reasoning {i}", reasoning_id)

        if i == len(result.reasoning) - 1:
            G.add_edge(reasoning_id, answer)

    # Create a figure and axis
    plt.figure(figsize=(10, 8))

    # Define node colors based on type
    node_colors = {
        "query": "#3498db",  # Blue
        "answer": "#2ecc71",  # Green
        "citation": "#e74c3c",  # Red
        "reasoning": "#f39c12",  # Orange
    }

    # Get node positions using spring layout
    pos = nx.spring_layout(G, seed=42)

    # Draw nodes with different colors based on type
    for node_type in node_colors:
        nodes = [
            node for node, data in G.nodes(data=True) if data.get("type") == node_type
        ]
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist=nodes,
            node_color=node_colors[node_type],
            node_size=1000,
            alpha=0.8,
        )

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, width=1.5, alpha=0.7, arrows=True, arrowstyle="->", arrowsize=15
    )

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Remove axis
    plt.axis("off")

    # Add a title
    plt.title("Knowledge Graph", fontsize=16)

    # Save the figure to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()

    # Create a PIL Image from the buffer
    buf.seek(0)
    img = Image.open(buf)

    return img


def create_interaction_trace(reasoning_steps: list[str]) -> str:
    """Create a GraphViz description of the agent interaction trace."""
    lines = ["digraph Trace {", "rankdir=LR;"]
    prev = "Start"
    lines.append('Start [shape=circle,label="Start"];')
    for idx, step in enumerate(reasoning_steps, start=1):
        node = f"step{idx}"
        label = re.sub(r"[\n\"]", "", step)[:20]
        lines.append(f'{node} [label="{label}"];')
        lines.append(f'{prev} -> {node};')
        prev = node
    lines.append("}")
    return "\n".join(lines)


def create_progress_graph(agent_perf: Dict[str, Any]) -> str:
    """Create a GraphViz chart for agent progress metrics."""
    lines = ["digraph Progress {", "rankdir=LR;"]
    agents = list(agent_perf.keys())
    for name in agents:
        metrics = agent_perf[name]
        label = f"{name}\n{metrics.get('executions', 0)} runs"
        lines.append(f'"{name}" [label="{label}"];')
    for i in range(len(agents) - 1):
        lines.append(f'"{agents[i]}" -> "{agents[i+1]}";')
    lines.append("}")
    return "\n".join(lines)


def format_result_as_markdown(result: QueryResponse, depth: OutputDepth) -> str:
    """Format the query result as Markdown using the shared formatter."""

    return OutputFormatter.render(result, "markdown", depth=depth)


def format_result_as_json(result: QueryResponse, depth: OutputDepth) -> str:
    """Format the query result as JSON."""

    return OutputFormatter.render(result, "json", depth=depth)


def visualize_rdf(output_path: str = "rdf_graph.png") -> None:
    """Generate a PNG visualization of the current RDF graph."""
    from .storage import StorageManager

    StorageManager.setup()
    StorageManager.visualize_rdf(output_path)
    print_success(f"Graph written to {output_path}")


def display_results(result: QueryResponse) -> None:
    """Display the query results in a formatted way."""

    st.session_state.current_result = result

    depth_options = depth_sequence()
    depth_values = [depth.value for depth in depth_options]
    stored_depth = st.session_state.get("ui_depth", OutputDepth.STANDARD.value)
    try:
        default_index = depth_values.index(stored_depth)
    except ValueError:
        default_index = depth_values.index(OutputDepth.STANDARD.value)

    selected_value = st.radio(
        "Detail depth",
        depth_values,
        index=default_index,
        format_func=lambda val: OutputDepth(val).label,
        horizontal=True,
        help="Choose how much detail to display, from TL;DR to full trace.",
    )
    selected_depth = OutputDepth(selected_value)
    st.session_state.ui_depth = selected_depth.value

    payload = build_depth_payload(result, selected_depth)
    st.session_state["current_payload"] = payload

    toggle_defaults = section_toggle_defaults(payload)
    depth_state_key = "last_selected_depth"
    if st.session_state.get(depth_state_key) != selected_depth.value:
        for name, config in toggle_defaults.items():
            st.session_state[f"ui_toggle_{name}"] = (
                config["value"] if config["available"] else False
            )
        st.session_state[depth_state_key] = selected_depth.value

    toggle_widget = getattr(st, "toggle", st.checkbox)
    toggle_definitions: List[tuple[str, str, str]] = [
        ("tldr", "Show TL;DR", "Display the auto-generated summary."),
        (
            "key_findings",
            "Show key findings",
            "Highlight the main evidence-backed points.",
        ),
        (
            "claim_audits",
            "Show claim table",
            "Inspect verification outcomes for each claim.",
        ),
        (
            "full_trace",
            "Show full trace",
            "Reveal reasoning steps and ReAct traces.",
        ),
    ]
    toggle_states: Dict[str, bool] = {}
    st.markdown("#### Depth controls")
    toggle_columns = st.columns(len(toggle_definitions))
    for column, (name, label, help_text) in zip(toggle_columns, toggle_definitions):
        config = toggle_defaults[name]
        state_key = f"ui_toggle_{name}"
        if state_key not in st.session_state:
            st.session_state[state_key] = (
                config["value"] if config["available"] else False
            )
        if not config["available"]:
            st.session_state[state_key] = False
        with column:
            toggle_widget(
                label,
                value=st.session_state[state_key],
                help=help_text,
                disabled=not config["available"],
                key=state_key,
            )
        toggle_states[name] = (
            st.session_state[state_key] if config["available"] else False
        )

    st.markdown(
        "<div role='region' aria-label='Query results' aria-live='polite'>",
        unsafe_allow_html=True,
    )
    st.markdown("<h2 class='subheader'>TL;DR</h2>", unsafe_allow_html=True)
    if toggle_states.get("tldr", True) and payload.tldr:
        st.write(payload.tldr)
    elif toggle_states.get("tldr", True):
        st.info("No summary available.")
    elif not toggle_defaults["tldr"]["available"] and (note := payload.notes.get("tldr")):
        st.info(note)
    else:
        st.caption("Enable 'Show TL;DR' to surface the summary.")

    st.markdown("<h2 class='subheader'>Answer</h2>", unsafe_allow_html=True)
    st.markdown(payload.answer, unsafe_allow_html=True)

    st.markdown("<h3>Key Findings</h3>", unsafe_allow_html=True)
    if toggle_states.get("key_findings"):
        if payload.key_findings:
            for finding in payload.key_findings:
                st.markdown(f"- {finding}")
        else:
            st.info("No key findings available.")
        if note := payload.notes.get("key_findings"):
            st.caption(note)
    elif not toggle_defaults["key_findings"]["available"] and (
        note := payload.notes.get("key_findings")
    ):
        st.info(note)
    else:
        st.caption("Enable 'Show key findings' to review highlights.")

    prompts = generate_socratic_prompts(payload)
    if prompts:
        with st.expander("Socratic prompts", expanded=False):
            for prompt in prompts:
                st.markdown(f"- {prompt}")

    with st.expander("Provenance & verification", expanded=False):
        rollup = audit_status_rollup(payload.claim_audits)
        if rollup:
            st.markdown("**Claim status overview**")
            for status, count in rollup.items():
                st.markdown(
                    f"- {status.replace('_', ' ').title()}: {count}",
                    unsafe_allow_html=False,
                )
        elif payload.notes.get("claim_audits"):
            st.info(payload.notes["claim_audits"])
        else:
            st.info("Increase depth to capture claim verification data.")

        artifacts = extract_graphrag_artifacts(result.metrics)
        if artifacts:
            st.markdown("**GraphRAG artifacts**")
            st.json(artifacts)
        elif payload.notes.get("metrics"):
            st.caption(payload.notes["metrics"])
        else:
            st.caption("GraphRAG metrics appear once runs collect graph evidence.")

    col1, col2 = st.columns(2)
    with col1:
        markdown_result = format_result_as_markdown(result, selected_depth)
        st.download_button(
            label="Export as Markdown",
            data=markdown_result,
            file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )

    with col2:
        json_result = format_result_as_json(result, selected_depth)
        st.download_button(
            label="Export as JSON",
            data=json_result,
            file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Citations", "Reasoning", "Provenance", "Metrics", "Knowledge Graph", "Trace"]
    )

    with tab1:
        st.markdown("<h3>Citations</h3>", unsafe_allow_html=True)
        if payload.citations:
            for citation in payload.citations:
                st.markdown(
                    f"<div class='citation' role='listitem'>{citation}</div>",
                    unsafe_allow_html=True,
                )
        elif note := payload.notes.get("citations"):
            st.info(note)
        else:
            st.info("No citations provided")

    with tab2:
        st.markdown("<h3>Reasoning</h3>", unsafe_allow_html=True)
        if toggle_states.get("full_trace"):
            if payload.reasoning:
                for idx, step in enumerate(payload.reasoning, 1):
                    st.markdown(
                        f"<div class='reasoning-step' role='listitem'>{idx}. {step}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No reasoning steps provided")
            if note := payload.notes.get("reasoning"):
                st.caption(note)
        elif not toggle_defaults["full_trace"]["available"]:
            message = payload.notes.get("reasoning") or "Increase depth to unlock trace details."
            st.info(message)
        else:
            st.info("Enable 'Show full trace' to inspect agent reasoning.")

    with tab3:
        st.markdown("<h3>Claim Audits</h3>", unsafe_allow_html=True)
        if toggle_states.get("claim_audits"):
            if payload.claim_audits:
                badge_styles = {
                    "supported": "#0f5132",
                    "unsupported": "#842029",
                    "needs_review": "#664d03",
                }
                st.markdown(
                    """
                    <style>
                    .claim-audit-table {width:100%; border-collapse: collapse;}
                    .claim-audit-table th, .claim-audit-table td {
                        border: 1px solid rgba(151, 151, 151, 0.4);
                        padding: 0.5rem;
                    }
                    .claim-audit-badge {
                        border-radius: 0.5rem;
                        padding: 0.25rem 0.6rem;
                        color: #fff;
                        font-size: 0.85rem;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                rows: list[str] = []
                for audit in payload.claim_audits:
                    status_raw = str(audit.get("status", "unknown")).lower()
                    color = badge_styles.get(status_raw, "#6c757d")
                    badge = (
                        f"<span class='claim-audit-badge' style='background-color:{color}'>"
                        f"{status_raw.replace('_', ' ').title()}</span>"
                    )
                    entailment = audit.get("entailment_score")
                    entailment_display = "—" if entailment is None else f"{entailment:.2f}"
                    sources = audit.get("sources") or []
                    primary = sources[0] if sources else {}
                    label = (
                        primary.get("title")
                        or primary.get("url")
                        or primary.get("snippet")
                        or ""
                    )
                    if label and len(label) > 80:
                        label = label[:77] + "..."
                    rows.append(
                        "<tr>"
                        f"<td>{audit.get('claim_id', '')}</td>"
                        f"<td>{badge}</td>"
                        f"<td>{entailment_display}</td>"
                        f"<td>{label}</td>"
                        "</tr>"
                    )
                table_html = (
                    "<table class='claim-audit-table'>"
                    "<thead><tr><th>Claim ID</th><th>Status</th><th>Entailment</th><th>Top Source</th></tr></thead>"
                    f"<tbody>{''.join(rows)}</tbody></table>"
                )
                st.markdown(table_html, unsafe_allow_html=True)
            elif note := payload.notes.get("claim_audits"):
                st.info(note)
            else:
                st.info("No claim audits recorded")
            if note := payload.notes.get("claim_audits"):
                st.caption(note)
            st.caption("See the provenance panel above for GraphRAG artifacts.")
        elif not toggle_defaults["claim_audits"]["available"]:
            message = (
                payload.notes.get("claim_audits")
                or "Increase depth to capture claim verification data."
            )
            st.info(message)
        else:
            st.info("Enable 'Show claim table' to inspect verification details.")

    with tab4:
        st.markdown("<h3>Metrics</h3>", unsafe_allow_html=True)
        if payload.metrics:
            with st.container():
                st.markdown(
                    "<div class='metrics-container' role='region' aria-label='Metrics'>",
                    unsafe_allow_html=True,
                )
                for key, value in payload.metrics.items():
                    st.markdown(f"**{key}:** {value}")
                st.markdown("</div>", unsafe_allow_html=True)
            if note := payload.notes.get("metrics"):
                st.caption(note)
        elif note := payload.notes.get("metrics"):
            st.info(note)
        else:
            st.info("No metrics provided")

    with tab5:
        st.markdown("<h3>Knowledge Graph</h3>", unsafe_allow_html=True)
        summary = payload.knowledge_graph or {}
        summary_displayed = False
        if summary:
            summary_displayed = True
            counts_lines: list[str] = []
            if (entities := summary.get("entity_count")) is not None:
                counts_lines.append(f"- **Entities:** {entities}")
            if (relations := summary.get("relation_count")) is not None:
                counts_lines.append(f"- **Relations:** {relations}")
            if (score := summary.get("contradiction_score")) is not None:
                counts_lines.append(f"- **Contradiction score:** {score:.2f}")
            if counts_lines:
                st.markdown("### Summary")
                st.markdown("\n".join(counts_lines))

            contradictions = summary.get("contradictions") or []
            if contradictions:
                st.markdown("### Contradictions")
                for item in contradictions:
                    if isinstance(item, dict):
                        subject = item.get("subject") or item.get("text")
                        predicate = item.get("predicate")
                        objects = item.get("objects") or []
                        if subject and predicate and isinstance(objects, list):
                            joined = ", ".join(str(obj) for obj in objects if str(obj).strip())
                            st.markdown(f"- {subject} — {predicate} → {joined or '—'}")
                        else:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(f"- {item}")
                if note := payload.notes.get("knowledge_graph_contradictions"):
                    st.caption(note)

            paths = summary.get("multi_hop_paths") or []
            if paths:
                st.markdown("### Multi-hop paths")
                for path in paths:
                    if isinstance(path, list):
                        labels = [str(node) for node in path if str(node).strip()]
                        st.markdown(f"- {' → '.join(labels) if labels else '—'}")
                    else:
                        st.markdown(f"- {path}")
                if note := payload.notes.get("knowledge_graph_paths"):
                    st.caption(note)
        elif note := payload.notes.get("knowledge_graph"):
            st.info(note)
        else:
            st.info("Knowledge graph not generated yet.")

        if payload.citations and payload.reasoning:
            graph_image = create_knowledge_graph(result)
            import base64

            buffered = io.BytesIO()
            graph_image.save(buffered, format="PNG")
            encoded = base64.b64encode(buffered.getvalue()).decode()
            st.markdown(
                f"<img src='data:image/png;base64,{encoded}' alt='Knowledge graph visualization' style='width:100%;' />",
                unsafe_allow_html=True,
            )
        elif not summary_displayed:
            if payload.notes.get("citations") or payload.notes.get("reasoning"):
                st.caption("Increase depth to view the knowledge graph visualization.")
            else:
                st.caption("Not enough information to render the knowledge graph visualization.")

        if payload.graph_exports:
            st.markdown("### Graph exports")
            commands: list[str] = []
            if payload.graph_exports.get("graphml"):
                commands.append("`--output graphml`")
            if payload.graph_exports.get("graph_json"):
                commands.append("`--output graph-json`")
            if commands:
                st.info("CLI shortcuts: " + " or ".join(dict.fromkeys(commands)))
            from .storage import StorageManager

            if payload.graph_exports.get("graphml"):
                graphml_data = StorageManager.export_knowledge_graph_graphml()
                if graphml_data:
                    st.download_button(
                        label="Download GraphML",
                        data=graphml_data,
                        file_name=f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.graphml",
                        mime="application/graphml+xml",
                    )
            if payload.graph_exports.get("graph_json"):
                graph_json_data = StorageManager.export_knowledge_graph_json()
                if graph_json_data:
                    st.download_button(
                        label="Download Graph JSON",
                        data=graph_json_data,
                        file_name=f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    )
        elif note := payload.notes.get("graph_exports"):
            st.caption(note)

    with tab6:
        st.markdown("<h3>Agent Trace</h3>", unsafe_allow_html=True)
        if toggle_states.get("full_trace"):
            if payload.reasoning:
                trace_graph = create_interaction_trace(payload.reasoning)
                st.graphviz_chart(trace_graph)
            elif payload.notes.get("reasoning"):
                st.info(payload.notes["reasoning"])
            else:
                st.info("No reasoning steps available")

            if payload.react_traces:
                st.markdown("### ReAct events")
                st.json(payload.react_traces)
            elif note := payload.notes.get("react_traces"):
                st.info(note)
            elif not payload.react_traces:
                st.caption("No ReAct events captured for this run.")

            metrics = st.session_state.get("agent_performance", {})
            if metrics:
                st.markdown("### Progress Metrics")
                progress_graph = create_progress_graph(metrics)
                st.graphviz_chart(progress_graph)
        elif not toggle_defaults["full_trace"]["available"]:
            message = (
                payload.notes.get("react_traces")
                or payload.notes.get("reasoning")
                or "Increase depth to unlock detailed traces."
            )
            st.info(message)
        else:
            st.info("Enable 'Show full trace' to inspect the agent trace.")

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
