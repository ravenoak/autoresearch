"""Streamlit GUI for Autoresearch.

This module provides a web-based GUI for Autoresearch using Streamlit.
It allows users to run queries, view results, and configure settings.
"""

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from typing import Dict, Any
import random
import io
import time
import tomllib
import psutil
from .orchestration import metrics as orch_metrics
import threading
import os
import logging
import re
from datetime import datetime
from PIL import Image

from .config import ConfigLoader
from .orchestration.orchestrator import Orchestrator
from .models import QueryResponse
from .orchestration import ReasoningMode
from .error_utils import get_error_info, format_error_for_gui

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
    @media (max-width: 800px) {
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
    @media (max-width: 600px) {
        .responsive-container, .metrics-container {
            flex-direction: column;
        }
        .main-header {
            font-size: 2rem;
        }
        .subheader {
            font-size: 1.2rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)


def apply_accessibility_settings() -> None:
    """Apply accessibility-related CSS such as focus outlines and high contrast."""
    # Always provide visible focus indicators for keyboard navigation
    st.markdown(
        """
        <style>
        *:focus {
            outline: 2px solid #ffbf00 !important;
            outline-offset: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("high_contrast"):
        # Inject a high contrast theme when enabled
        st.markdown(
            """
            <style>
            body, .stApp {background-color:#000 !important; color:#fff !important;}
            .stButton>button {background-color:#fff !important; color:#000 !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def apply_theme_settings() -> None:
    """Apply light or dark theme based on session state."""
    if st.session_state.get("dark_mode"):
        st.markdown(
            """
            <style>
            body, .stApp {background-color:#222 !important; color:#eee !important;}
            .stButton>button {background-color:#444 !important; color:#fff !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            body, .stApp {background-color:#fff !important; color:#000 !important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def display_guided_tour() -> None:
    """Show a short help overlay explaining the interface."""
    if "show_tour" not in st.session_state:
        st.session_state.show_tour = True
    if st.session_state.show_tour:
        with st.modal("Welcome to Autoresearch", key="guided_tour"):
            st.markdown(
                """
                <div role="dialog" aria-label="Onboarding Tour">
                1. **Enter a query** in the text area on the main tab.<br/>
                2. **Adjust settings** like reasoning mode and loops.<br/>
                3. Click **Run Query** to start the agents.
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Got it", key="tour_done"):
                st.session_state.show_tour = False


def save_config_to_toml(config_dict):
    """Save the configuration to the TOML file.

    Args:
        config_dict: A dictionary containing the configuration to save

    Returns:
        bool: True if the configuration was saved successfully, False otherwise
    """
    import tomli_w
    from pathlib import Path

    # Get the path to the configuration file
    config_path = Path.cwd() / "autoresearch.toml"

    try:
        # Read the existing configuration file if it exists
        if config_path.exists():
            with open(config_path, "rb") as f:
                existing_config = tomllib.load(f)
        else:
            existing_config = {}

        # Update the core section with the new configuration
        if "core" not in existing_config:
            existing_config["core"] = {}

        # Update core settings
        for key, value in config_dict.items():
            if key not in ["storage", "search"]:
                existing_config["core"][key] = value

        # Handle active profile separately so preferences persist
        if "active_profile" in config_dict:
            existing_config["core"]["active_profile"] = config_dict["active_profile"]

        # Update storage settings
        if "storage" in config_dict:
            if "storage" not in existing_config:
                existing_config["storage"] = {}
            if "duckdb" not in existing_config["storage"]:
                existing_config["storage"]["duckdb"] = {}

            for key, value in config_dict["storage"].items():
                existing_config["storage"]["duckdb"][key] = value

        # Update search settings
        if "search" in config_dict:
            if "search" not in existing_config:
                existing_config["search"] = {}

            for key, value in config_dict["search"].items():
                existing_config["search"][key] = value

        # Update user preferences
        if "user_preferences" in config_dict:
            if "user_preferences" not in existing_config:
                existing_config["user_preferences"] = {}
            for key, value in config_dict["user_preferences"].items():
                existing_config["user_preferences"][key] = value

        # Write the updated configuration to the file
        with open(config_path, "wb") as f:
            tomli_w.dump(existing_config, f)

        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False


def get_config_presets():
    """Get a dictionary of configuration presets for common use cases.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary of preset configurations
    """
    return {
        "Default": {
            "llm_backend": "lmstudio",
            "reasoning_mode": ReasoningMode.DIALECTICAL.value,
            "loops": 2,
            "storage": {
                "duckdb_path": "autoresearch.duckdb",
                "vector_extension": True,
            },
            "search": {
                "max_results_per_query": 5,
                "use_semantic_similarity": True,
            },
            "user_preferences": {
                "detail_level": "balanced",
                "perspective": "neutral",
                "format_preference": "structured",
                "expertise_level": "intermediate",
                "focus_areas": [],
                "excluded_areas": [],
            },
        },
        "Fast Mode": {
            "llm_backend": "lmstudio",
            "reasoning_mode": ReasoningMode.DIRECT.value,
            "loops": 1,
            "storage": {
                "duckdb_path": "autoresearch.duckdb",
                "vector_extension": True,
            },
            "search": {
                "max_results_per_query": 3,
                "use_semantic_similarity": False,
            },
            "user_preferences": {
                "detail_level": "concise",
                "perspective": "neutral",
                "format_preference": "bullet_points",
                "expertise_level": "intermediate",
                "focus_areas": [],
                "excluded_areas": [],
            },
        },
        "Thorough Mode": {
            "llm_backend": "lmstudio",
            "reasoning_mode": ReasoningMode.DIALECTICAL.value,
            "loops": 3,
            "storage": {
                "duckdb_path": "autoresearch.duckdb",
                "vector_extension": True,
            },
            "search": {
                "max_results_per_query": 8,
                "use_semantic_similarity": True,
            },
            "user_preferences": {
                "detail_level": "detailed",
                "perspective": "critical",
                "format_preference": "structured",
                "expertise_level": "expert",
                "focus_areas": [],
                "excluded_areas": [],
            },
        },
        "Chain of Thought": {
            "llm_backend": "lmstudio",
            "reasoning_mode": ReasoningMode.CHAIN_OF_THOUGHT.value,
            "loops": 3,
            "storage": {
                "duckdb_path": "autoresearch.duckdb",
                "vector_extension": True,
            },
            "search": {
                "max_results_per_query": 5,
                "use_semantic_similarity": True,
            },
            "user_preferences": {
                "detail_level": "detailed",
                "perspective": "optimistic",
                "format_preference": "narrative",
                "expertise_level": "intermediate",
                "focus_areas": [],
                "excluded_areas": [],
            },
        },
        "OpenAI Mode": {
            "llm_backend": "openai",
            "reasoning_mode": ReasoningMode.DIALECTICAL.value,
            "loops": 2,
            "storage": {
                "duckdb_path": "autoresearch.duckdb",
                "vector_extension": True,
            },
            "search": {
                "max_results_per_query": 5,
                "use_semantic_similarity": True,
            },
            "user_preferences": {
                "detail_level": "balanced",
                "perspective": "neutral",
                "format_preference": "structured",
                "expertise_level": "intermediate",
                "focus_areas": [],
                "excluded_areas": [],
            },
        },
    }


def apply_preset(preset_name):
    """Apply a configuration preset.

    Args:
        preset_name: The name of the preset to apply

    Returns:
        Dict[str, Any]: The preset configuration
    """
    presets = get_config_presets()
    if preset_name in presets:
        return presets[preset_name]
    return None


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

        pref_config = (
            preset_config.get("user_preferences") if preset_config else config.user_preferences
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
                updated_config = {
                    "llm_backend": llm_backend,
                    "reasoning_mode": reasoning_mode,
                    "loops": loops,
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
            st.experimental_rerun()

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
        comparison_data = {"Agent": [], "Metric": [], "Value": []}

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
    with st.container():
        st.markdown("<div role='region' aria-label='Query input area'>", unsafe_allow_html=True)
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
            st.session_state.run_button = st.button(
                "Run Query",
                type="primary",
                help="Activate to run your query",
                key="run_query_button",
            )
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


def store_query_history(query: str, result: QueryResponse, config: Dict[str, Any]):
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
            st.experimental_rerun()

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
                result = Orchestrator.run_query(
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
                result = Orchestrator.run_query(rerun_query, st.session_state.config)

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
    G = nx.DiGraph()

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


def format_result_as_markdown(result: QueryResponse) -> str:
    """Format the query result as Markdown.

    Args:
        result: The query response to format

    Returns:
        str: The formatted Markdown string
    """
    markdown = []

    # Add answer
    markdown.append("# Answer")
    markdown.append("")
    markdown.append(result.answer)
    markdown.append("")

    # Add citations
    markdown.append("## Citations")
    markdown.append("")
    if result.citations:
        for i, citation in enumerate(result.citations):
            markdown.append(f"{i + 1}. {citation}")
            markdown.append("")
    else:
        markdown.append("No citations provided")
        markdown.append("")

    # Add reasoning
    markdown.append("## Reasoning")
    markdown.append("")
    if result.reasoning:
        for i, step in enumerate(result.reasoning):
            markdown.append(f"{i + 1}. {step}")
            markdown.append("")
    else:
        markdown.append("No reasoning steps provided")
        markdown.append("")

    # Add metrics
    markdown.append("## Metrics")
    markdown.append("")
    if result.metrics:
        for key, value in result.metrics.items():
            markdown.append(f"**{key}:** {value}")
        markdown.append("")
    else:
        markdown.append("No metrics provided")
        markdown.append("")

    return "\n".join(markdown)


def format_result_as_json(result: QueryResponse) -> str:
    """Format the query result as JSON.

    Args:
        result: The query response to format

    Returns:
        str: The formatted JSON string
    """
    import json

    # Convert the result to a dictionary
    result_dict = {
        "answer": result.answer,
        "citations": result.citations,
        "reasoning": result.reasoning,
        "metrics": result.metrics,
    }

    # Convert to JSON with pretty formatting
    return json.dumps(result_dict, indent=2)


def visualize_rdf(output_path: str = "rdf_graph.png") -> None:
    """Generate a PNG visualization of the current RDF graph."""
    from .storage import StorageManager

    StorageManager.setup()
    StorageManager.visualize_rdf(output_path)
    print(f"Graph written to {output_path}")


def display_results(result: QueryResponse):
    """Display the query results in a formatted way.

    Args:
        result: The query response to display
    """
    # Store the result in session state
    st.session_state.current_result = result

    # Display answer
    st.markdown("<h2 class='subheader'>Answer</h2>", unsafe_allow_html=True)

    # Enhanced Markdown rendering with support for LaTeX
    # Use unsafe_allow_html=True to allow HTML formatting in the Markdown
    st.markdown(result.answer, unsafe_allow_html=True)

    # Add support for LaTeX math expressions
    # This is handled automatically by Streamlit's Markdown renderer

    # Add export buttons
    col1, col2 = st.columns(2)
    with col1:
        # Export as Markdown
        markdown_result = format_result_as_markdown(result)
        st.download_button(
            label="Export as Markdown",
            data=markdown_result,
            file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )

    with col2:
        # Export as JSON
        json_result = format_result_as_json(result)
        st.download_button(
            label="Export as JSON",
            data=json_result,
            file_name=f"autoresearch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )

    # Create tabs for citations, reasoning, metrics, knowledge graph and trace
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Citations", "Reasoning", "Metrics", "Knowledge Graph", "Trace"]
    )

    # Citations tab
    with tab1:
        st.markdown("<h3>Citations</h3>", unsafe_allow_html=True)
        if result.citations:
            for i, citation in enumerate(result.citations):
                with st.container():
                    st.markdown(
                        f"<div class='citation'>{citation}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No citations provided")

    # Reasoning tab
    with tab2:
        st.markdown("<h3>Reasoning</h3>", unsafe_allow_html=True)
        if result.reasoning:
            for i, step in enumerate(result.reasoning):
                st.markdown(
                    f"<div class='reasoning-step'>{i + 1}. {step}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No reasoning steps provided")

    # Metrics tab
    with tab3:
        st.markdown("<h3>Metrics</h3>", unsafe_allow_html=True)
        if result.metrics:
            with st.container():
                st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
                for key, value in result.metrics.items():
                    st.markdown(f"**{key}:** {value}")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No metrics provided")

    # Knowledge Graph tab
    with tab4:
        st.markdown("<h3>Knowledge Graph</h3>", unsafe_allow_html=True)
        if result.reasoning and result.citations:
            # Create and display the knowledge graph
            graph_image = create_knowledge_graph(result)
            st.image(graph_image, use_column_width=True, caption="Knowledge graph")
        else:
            st.info("Not enough information to create a knowledge graph")

    # Trace tab
    with tab5:
        st.markdown("<h3>Agent Trace</h3>", unsafe_allow_html=True)
        if result.reasoning:
            trace_graph = create_interaction_trace(result.reasoning)
            st.graphviz_chart(trace_graph)
        metrics = st.session_state.get("agent_performance", {})
        if metrics:
            st.markdown("### Progress Metrics")
            progress_graph = create_progress_graph(metrics)
            st.graphviz_chart(progress_graph)


if __name__ == "__main__":
    main()
