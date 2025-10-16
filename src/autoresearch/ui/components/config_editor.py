"""Configuration editor component with validation and presets.

This module provides a comprehensive configuration management interface that handles:
- Configuration presets and templates
- Real-time validation and error handling
- Hot-reload functionality
- Profile management
- Advanced configuration options
"""

from __future__ import annotations

from typing import Any, Dict, cast

from ...config import ConfigLoader, ConfigModel
from ...config_utils import get_config_presets, apply_preset, save_config_to_toml

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


class ConfigEditorComponent:
    """Handles configuration editing with validation and presets."""

    def __init__(self) -> None:
        """Initialize the configuration editor component."""
        self._config_loader = ConfigLoader()

    def render(self) -> None:
        """Render the configuration editor interface."""
        # Load configuration
        config = self._config_loader.load_config()

        # Create a form for editing configuration
        with st.sidebar.form("config_editor"):
            st.markdown("<h3>Edit Configuration</h3>", unsafe_allow_html=True)

            # Configuration presets section
            self._render_presets_section()

            # Core settings section
            self._render_core_settings(config)

            # Storage settings section
            self._render_storage_settings(config)

            # Search settings section
            self._render_search_settings(config)

            # User preferences section
            self._render_user_preferences(config)

            # Hot-reload option
            self._render_hot_reload_option()

            # Submit button
            submitted = st.form_submit_button("Save Configuration")

            if submitted:
                self._handle_config_submission()

    def _render_presets_section(self) -> None:
        """Render the configuration presets section."""
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

        # If a preset is selected and the apply button is clicked, use the preset values
        if apply_preset_button and selected_preset != "Custom":
            preset_config = apply_preset(selected_preset)
            st.session_state.preset_config = preset_config
            st.success(f"Applied preset: {selected_preset}")
        else:
            st.session_state.preset_config = None

    def _render_core_settings(self, config: ConfigModel) -> None:
        """Render core configuration settings."""
        st.markdown("#### Core Settings")

        # Get preset config if available
        preset_config = st.session_state.get("preset_config")

        llm_backend = st.text_input(
            "LLM Backend",
            value=preset_config["llm_backend"] if preset_config else config.llm_backend,
            help="The LLM backend to use for query processing",
        )

        # Get the reasoning mode options
        from ...orchestration import ReasoningMode

        reasoning_mode_options = [mode.value for mode in ReasoningMode]

        # Determine the index for the reasoning mode
        if preset_config and "reasoning_mode" in preset_config:
            reasoning_mode_index = reasoning_mode_options.index(preset_config["reasoning_mode"])
        else:
            reasoning_mode_index = reasoning_mode_options.index(config.reasoning_mode.value)

        reasoning_mode = st.selectbox(
            "Reasoning Mode",
            options=reasoning_mode_options,
            index=reasoning_mode_index,
            help="The reasoning strategy to use for research",
        )

        # Profile selection
        profiles = ["None"] + self._config_loader.available_profiles()
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

        # Store values in session state for form submission
        st.session_state.core_settings = {
            "llm_backend": llm_backend,
            "reasoning_mode": reasoning_mode,
            "selected_profile": selected_profile,
            "loops": loops,
        }

    def _render_storage_settings(self, config: ConfigModel) -> None:
        """Render storage configuration settings."""
        st.markdown("#### Storage Settings")

        preset_config = st.session_state.get("preset_config")

        duckdb_path = st.text_input(
            "DuckDB Path",
            value=(
                preset_config["storage"]["duckdb_path"]
                if preset_config and "storage" in preset_config
                else config.storage.duckdb_path
            ),
            help="Path to the DuckDB database file",
        )

        vector_extension = st.checkbox(
            "Enable Vector Extension",
            value=(
                preset_config["storage"]["vector_extension"]
                if preset_config and "storage" in preset_config
                else config.storage.vector_extension
            ),
            help="Enable the DuckDB vector extension for similarity search",
        )

        # Store values in session state
        st.session_state.storage_settings = {
            "duckdb_path": duckdb_path,
            "vector_extension": vector_extension,
        }

    def _render_search_settings(self, config: ConfigModel) -> None:
        """Render search configuration settings."""
        st.markdown("#### Search Settings")

        preset_config = st.session_state.get("preset_config")

        max_results = st.number_input(
            "Max Results Per Query",
            min_value=1,
            max_value=20,
            value=(
                preset_config["search"]["max_results_per_query"]
                if preset_config and "search" in preset_config
                else config.search.max_results_per_query
            ),
            help="Maximum number of search results to return per query",
        )

        use_semantic_similarity = st.checkbox(
            "Use Semantic Similarity",
            value=(
                preset_config["search"]["use_semantic_similarity"]
                if preset_config and "search" in preset_config
                else config.search.use_semantic_similarity
            ),
            help="Use semantic similarity for search result ranking",
        )

        # Store values in session state
        st.session_state.search_settings = {
            "max_results": max_results,
            "use_semantic_similarity": use_semantic_similarity,
        }

    def _render_user_preferences(self, config: ConfigModel) -> None:
        """Render user preference settings."""
        st.markdown("#### User Preferences")

        preset_config = st.session_state.get("preset_config")

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
            help="How detailed the responses should be",
        )

        perspective = st.selectbox(
            "Perspective",
            options=["neutral", "critical", "optimistic"],
            index=["neutral", "critical", "optimistic"].index(
                pref_config.get("perspective", "neutral")
            ),
            help="The perspective to take in responses",
        )

        format_pref = st.selectbox(
            "Format Preference",
            options=["structured", "narrative", "bullet_points"],
            index=["structured", "narrative", "bullet_points"].index(
                pref_config.get("format_preference", "structured")
            ),
            help="Preferred response format",
        )

        expertise_level = st.selectbox(
            "Expertise Level",
            options=["beginner", "intermediate", "expert"],
            index=["beginner", "intermediate", "expert"].index(
                pref_config.get("expertise_level", "intermediate")
            ),
            help="Your level of expertise in the subject matter",
        )

        focus_areas = st.text_input(
            "Focus Areas (comma-separated)",
            value=", ".join(pref_config.get("focus_areas", [])),
            help="Areas to focus on in responses",
        )

        excluded_areas = st.text_input(
            "Excluded Areas (comma-separated)",
            value=", ".join(pref_config.get("excluded_areas", [])),
            help="Areas to exclude from responses",
        )

        # Store values in session state
        st.session_state.user_preferences = {
            "detail_level": detail_level,
            "perspective": perspective,
            "format_preference": format_pref,
            "expertise_level": expertise_level,
            "focus_areas": focus_areas,
            "excluded_areas": excluded_areas,
        }

    def _render_hot_reload_option(self) -> None:
        """Render the hot-reload configuration option."""
        enable_hot_reload = st.checkbox(
            "Enable Hot-Reload",
            value=True,
            help="Automatically reload the configuration when changes are detected",
        )

        st.session_state.enable_hot_reload = enable_hot_reload

    def _handle_config_submission(self) -> None:
        """Handle form submission and save configuration."""
        try:
            # Get all the form values from session state
            core = st.session_state.get("core_settings", {})
            storage = st.session_state.get("storage_settings", {})
            search = st.session_state.get("search_settings", {})
            user_prefs = st.session_state.get("user_preferences", {})

            # Create a dictionary with the updated configuration
            updated_config = {
                "llm_backend": core.get("llm_backend", ""),
                "reasoning_mode": core.get("reasoning_mode", "dialectical"),
                "loops": core.get("loops", 3),
                "active_profile": (
                    core.get("selected_profile") if core.get("selected_profile") != "None" else None
                ),
                "storage": {
                    "duckdb_path": storage.get("duckdb_path", ""),
                    "vector_extension": storage.get("vector_extension", False),
                },
                "search": {
                    "max_results_per_query": search.get("max_results", 10),
                    "use_semantic_similarity": search.get("use_semantic_similarity", False),
                },
                "user_preferences": {
                    "detail_level": user_prefs.get("detail_level", "balanced"),
                    "perspective": user_prefs.get("perspective", "neutral"),
                    "format_preference": user_prefs.get("format_preference", "structured"),
                    "expertise_level": user_prefs.get("expertise_level", "intermediate"),
                    "focus_areas": [
                        a.strip() for a in user_prefs.get("focus_areas", "").split(",") if a.strip()
                    ],
                    "excluded_areas": [
                        a.strip()
                        for a in user_prefs.get("excluded_areas", "").split(",")
                        if a.strip()
                    ],
                },
            }

            # Save the configuration to the TOML file
            if save_config_to_toml(updated_config):
                st.sidebar.success("Configuration saved successfully!")

                # Reload the configuration
                if core.get("selected_profile") != "None":
                    self._config_loader.set_active_profile(core["selected_profile"])
                else:
                    (
                        self._config_loader.set_active_profile(
                            self._config_loader.available_profiles()[0]
                        )
                        if self._config_loader.available_profiles()
                        else None
                    )

                config = self._config_loader.load_config()
                st.session_state.config = config

                # Start watching for configuration changes if hot-reload is enabled
                if st.session_state.get("enable_hot_reload", False):
                    self._config_loader.watch_changes(self._on_config_change)
            else:
                st.sidebar.error("Failed to save configuration")
        except Exception as e:
            st.sidebar.error(f"Error saving configuration: {str(e)}")

    def _on_config_change(self, config: ConfigModel) -> None:
        """Handle configuration changes from file watching."""
        st.session_state.config = config
        st.session_state.config_changed = True
        st.session_state.config_change_time = __import__("time").time()

    def get_config_help_text(self) -> str:
        """Get comprehensive help text for configuration options."""
        return """
        **Configuration Help:**

        **Core Settings:**
        - **LLM Backend**: The language model service to use (e.g., 'openai', 'anthropic', 'local')
        - **Reasoning Mode**: How agents should approach research problems
        - **Loops**: Number of iterative reasoning cycles (1-10)
        - **Active Profile**: Load a saved configuration profile

        **Storage Settings:**
        - **DuckDB Path**: Location of the research database file
        - **Vector Extension**: Enable similarity search capabilities

        **Search Settings:**
        - **Max Results**: Maximum search results per query (1-20)
        - **Semantic Similarity**: Use AI-powered result ranking

        **User Preferences:**
        - **Detail Level**: Response verbosity (concise/balanced/detailed)
        - **Perspective**: Response tone (neutral/critical/optimistic)
        - **Format**: Response structure preference
        - **Expertise Level**: Adjust complexity for your knowledge level
        - **Focus Areas**: Topics to emphasize in responses
        - **Excluded Areas**: Topics to avoid in responses

        **Hot-Reload**: Automatically apply configuration changes from file

        **Presets**: Quick-start configurations for common use cases
        """

    def validate_config(self, config_dict: Dict[str, Any]) -> tuple[bool, str]:
        """Validate configuration before saving.

        Args:
            config_dict: The configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate LLM backend
            if not config_dict.get("llm_backend", "").strip():
                return False, "LLM backend cannot be empty"

            # Validate loops
            loops = config_dict.get("loops", 3)
            if not isinstance(loops, int) or loops < 1 or loops > 10:
                return False, "Loops must be an integer between 1 and 10"

            # Validate storage path
            duckdb_path = config_dict.get("storage", {}).get("duckdb_path", "")
            if not duckdb_path.strip():
                return False, "DuckDB path cannot be empty"

            # Validate search settings
            max_results = config_dict.get("search", {}).get("max_results_per_query", 10)
            if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                return False, "Max results must be an integer between 1 and 20"

            # Validate user preferences
            detail_level = config_dict.get("user_preferences", {}).get("detail_level", "balanced")
            if detail_level not in ["concise", "balanced", "detailed"]:
                return False, "Detail level must be concise, balanced, or detailed"

            perspective = config_dict.get("user_preferences", {}).get("perspective", "neutral")
            if perspective not in ["neutral", "critical", "optimistic"]:
                return False, "Perspective must be neutral, critical, or optimistic"

            return True, ""

        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"
