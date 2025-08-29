"""Configuration helper utilities for the Streamlit app.

See ``docs/algorithms/config_utils.md`` for validation, hot reload, and schema
guarantees.
"""

from __future__ import annotations

import tomllib
from typing import Any, Dict

import streamlit as st

from .config.loader import ConfigLoader
from .errors import ConfigError
from .orchestration import ReasoningMode


def save_config_to_toml(config_dict: Dict[str, Any]) -> bool:
    """Save the configuration to ``autoresearch.toml``.

    Parameters
    ----------
    config_dict:
        Dictionary containing configuration values.

    Returns
    -------
    bool
        ``True`` on success.
    """
    from pathlib import Path

    import tomli_w

    config_path = Path.cwd() / "autoresearch.toml"

    try:
        if config_path.exists():
            with open(config_path, "rb") as f:
                existing_config = tomllib.load(f)
        else:
            existing_config = {}

        if "core" not in existing_config:
            existing_config["core"] = {}

        for key, value in config_dict.items():
            if key not in ["storage", "search"]:
                existing_config["core"][key] = value

        if "active_profile" in config_dict:
            existing_config["core"]["active_profile"] = config_dict["active_profile"]

        if "storage" in config_dict:
            if "storage" not in existing_config:
                existing_config["storage"] = {}
            if "duckdb" not in existing_config["storage"]:
                existing_config["storage"]["duckdb"] = {}
            for key, value in config_dict["storage"].items():
                existing_config["storage"]["duckdb"][key] = value

        if "search" in config_dict:
            if "search" not in existing_config:
                existing_config["search"] = {}
            for key, value in config_dict["search"].items():
                existing_config["search"][key] = value

        if "user_preferences" in config_dict:
            if "user_preferences" not in existing_config:
                existing_config["user_preferences"] = {}
            for key, value in config_dict["user_preferences"].items():
                existing_config["user_preferences"][key] = value

        with open(config_path, "wb") as f:
            tomli_w.dump(existing_config, f)
        return True
    except Exception as e:  # pragma: no cover - Streamlit displays the error
        st.error(f"Error saving configuration: {e}")
        return False


def validate_config(
    config_loader: ConfigLoader | None = None,
) -> tuple[bool, list[str]]:
    """Validate configuration files.

    Parameters
    ----------
    config_loader:
        Optional pre-configured :class:`~autoresearch.config.loader.ConfigLoader`.

    Returns
    -------
    tuple[bool, list[str]]
        ``(True, [])`` if configuration is valid, otherwise ``(False, errors)``.
    """
    loader = config_loader or ConfigLoader()
    try:
        loader.load_config()
        return True, []
    except ConfigError as e:
        return False, [str(e)]
    except Exception as e:  # pragma: no cover - defensive
        return False, [str(e)]


def get_config_presets() -> Dict[str, Dict[str, Any]]:
    """Return configuration presets for common use cases."""
    return {
        "Default": {
            "llm_backend": "lmstudio",
            "reasoning_mode": ReasoningMode.DIALECTICAL.value,
            "loops": 2,
            "storage": {"duckdb_path": "autoresearch.duckdb", "vector_extension": True},
            "search": {"max_results_per_query": 5, "use_semantic_similarity": True},
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
            "storage": {"duckdb_path": "autoresearch.duckdb", "vector_extension": True},
            "search": {"max_results_per_query": 3, "use_semantic_similarity": False},
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
            "storage": {"duckdb_path": "autoresearch.duckdb", "vector_extension": True},
            "search": {"max_results_per_query": 8, "use_semantic_similarity": True},
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
            "storage": {"duckdb_path": "autoresearch.duckdb", "vector_extension": True},
            "search": {"max_results_per_query": 5, "use_semantic_similarity": True},
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
            "storage": {"duckdb_path": "autoresearch.duckdb", "vector_extension": True},
            "search": {"max_results_per_query": 5, "use_semantic_similarity": True},
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


def apply_preset(preset_name: str) -> Dict[str, Any] | None:
    """Return the selected preset configuration."""
    presets = get_config_presets()
    if preset_name in presets:
        return presets[preset_name]
    return None
