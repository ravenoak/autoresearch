"""
Configuration loader with validation and hot-reload support.
"""

import os
import time
import tomllib
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Any
import threading
import logging

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchfiles import watch, Change

logger = logging.getLogger(__name__)

class StorageConfig(BaseModel):
    """Storage configuration for DuckDB, RDF, and more."""
    duckdb_path: str = Field(default="autoresearch.duckdb")
    vector_extension: bool = Field(default=True)
    hnsw_m: int = Field(default=16, ge=4)
    hnsw_ef_construction: int = Field(default=200, ge=32)
    hnsw_metric: str = Field(default="l2")
    rdf_backend: str = Field(default="sqlite")
    rdf_path: str = Field(default="rdf_store")

    @field_validator("rdf_backend")
    def validate_rdf_backend(cls, v):
        valid_backends = ["sqlite", "berkeleydb"]
        if v not in valid_backends:
            raise ValueError(f"RDF backend must be one of {valid_backends}")
        return v

class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    enabled: bool = Field(default=True)
    model: Optional[str] = None

class ConfigModel(BaseSettings):
    """Main configuration model with validation."""
    # Core settings
    backend: str = Field(default="lmstudio")  # backward compatibility
    llm_backend: str = Field(default="lmstudio")
    loops: int = Field(default=2, ge=1)
    ram_budget_mb: int = Field(default=1024, ge=0)
    agents: List[str] = Field(default=["Synthesizer", "Contrarian", "FactChecker"])
    primus_start: int = Field(default=0)
    reasoning_mode: str = Field(default="dialectical")
    output_format: Optional[str] = None  # Defaults to None (auto-detect in CLI)

    # Storage settings
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # Agent-specific settings
    agent_config: Dict[str, AgentConfig] = Field(default_factory=dict)

    # Search settings
    search_backends: List[str] = Field(default=["serper"])
    max_results_per_query: int = Field(default=5, ge=1)

    # Dynamic knowledge graph settings
    graph_eviction_policy: str = Field(default="LRU")
    vector_nprobe: int = Field(default=10, ge=1)

    # Model settings
    default_model: str = Field(default="gpt-3.5-turbo")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

    @field_validator("reasoning_mode")
    def validate_reasoning_mode(cls, v):
        valid_modes = ["direct", "dialectical", "chain-of-thought"]
        if v not in valid_modes:
            raise ValueError(f"Reasoning mode must be one of {valid_modes}")
        return v

    @field_validator("graph_eviction_policy")
    def validate_eviction_policy(cls, v):
        valid_policies = ["LRU", "score"]
        if v not in valid_policies:
            raise ValueError(f"Graph eviction policy must be one of {valid_policies}")
        return v

class ConfigLoader:
    """Loads and watches configuration changes."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigLoader, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self._config = None
        self._watch_thread = None
        self._stop_event = threading.Event()
        self._observers: Set[Callable[[ConfigModel], None]] = set()
        self._config_time = 0
        self._watch_paths = ["autoresearch.toml", ".env"]
        self._initialized = True

    @property
    def watch_paths(self) -> List[str]:
        """Return the list of paths to watch for changes."""
        return self._watch_paths

    @property
    def config(self) -> ConfigModel:
        """Get the current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> ConfigModel:
        """Read TOML and environment, return validated config."""
        raw = {}
        config_path = Path("autoresearch.toml")

        if config_path.exists():
            try:
                self._config_time = config_path.stat().st_mtime
                with open(config_path, "rb") as f:
                    raw = tomllib.load(f)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                # Continue with defaults if file exists but can't be loaded

        # Extract core settings
        core_settings = raw.get("core", {})
        # Map legacy `backend` to `llm_backend` if provided
        if "backend" in core_settings and "llm_backend" not in core_settings:
            core_settings["llm_backend"] = core_settings["backend"]

        # Handle storage settings
        storage_cfg = raw.get("storage", {})
        duckdb_cfg = storage_cfg.get("duckdb", {})
        rdf_cfg = storage_cfg.get("rdf", {})

        storage_settings = {
            "duckdb_path": duckdb_cfg.get("path", "autoresearch.duckdb"),
            "vector_extension": duckdb_cfg.get("vector_extension", True),
            "hnsw_m": duckdb_cfg.get("hnsw_m", 16),
            "hnsw_ef_construction": duckdb_cfg.get("hnsw_ef_construction", 200),
            "hnsw_metric": duckdb_cfg.get("hnsw_metric", "l2"),
            "rdf_backend": rdf_cfg.get("backend", "sqlite"),
            "rdf_path": rdf_cfg.get("path", "rdf_store")
        }

        # Extract agent configuration
        agent_cfg = raw.get("agent", {})
        enabled_agents = [name for name, a in agent_cfg.items() if a.get("enabled", True)]

        # Only override agents list if explicitly defined
        if enabled_agents:
            core_settings["agents"] = enabled_agents

        # Convert agent config to proper format
        agent_config_dict = {}
        for name, cfg in agent_cfg.items():
            agent_config_dict[name] = AgentConfig(**cfg)

        # Add storage config
        core_settings["storage"] = StorageConfig(**storage_settings)

        # Add agent configs
        core_settings["agent_config"] = agent_config_dict

        try:
            return ConfigModel(**core_settings)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            # Raise with more helpful message
            raise ValueError(f"Error in configuration: {e}") from e

    def register_observer(self, callback: Callable[[ConfigModel], None]) -> None:
        """Register a callback to be notified of config changes."""
        self._observers.add(callback)

    def unregister_observer(self, callback: Callable[[ConfigModel], None]) -> None:
        """Unregister a previously registered callback."""
        self._observers.discard(callback)

    def notify_observers(self, config: ConfigModel) -> None:
        """Notify all registered observers of a config change."""
        for observer in self._observers:
            try:
                observer(config)
            except Exception as e:
                logger.error(f"Error in config observer: {e}")

    def watch_changes(self, callback: Optional[Callable[[ConfigModel], None]] = None) -> None:
        """Start watching config files and invoke callback on change."""
        if callback:
            self.register_observer(callback)

        if self._watch_thread and self._watch_thread.is_alive():
            logger.info("Config watcher already running")
            return

        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_config_files,
            daemon=True,
            name="ConfigWatcher"
        )
        self._watch_thread.start()
        logger.info(f"Started config watcher for paths: {self.watch_paths}")

    def stop_watching(self) -> None:
        """Stop the config file watcher thread."""
        if self._watch_thread and self._watch_thread.is_alive():
            self._stop_event.set()
            self._watch_thread.join(timeout=1.0)
            logger.info("Stopped config watcher")

    def _watch_config_files(self) -> None:
        """Watch for changes in config files (runs in separate thread)."""
        abs_paths = [str(Path(p).absolute()) for p in self.watch_paths if Path(p).exists()]

        if not abs_paths:
            logger.warning(f"None of the config paths exist: {self.watch_paths}")
            return

        try:
            # Use watchfiles to monitor changes
            for changes in watch(*abs_paths, stop_event=self._stop_event):
                if self._stop_event.is_set():
                    break

                # Only reload if there are actual changes
                if changes and any(c == Change.modified for c, _ in changes):
                    logger.info("Config files changed, reloading configuration")
                    try:
                        new_config = self.load_config()
                        self._config = new_config
                        self.notify_observers(new_config)
                    except Exception as e:
                        logger.error(f"Error reloading config: {e}")

        except Exception as e:
            logger.error(f"Error in config watcher: {e}")

    def on_config_change(self, config: ConfigModel) -> None:
        """Default handler for config change events."""
        logger.info("Configuration changed")

# Convenience function to get the global config
def get_config() -> ConfigModel:
    """Get the current configuration."""
    return ConfigLoader().config
