"""Configuration loader with validation and hot-reload support.

This module provides a configuration system that supports:
1. Loading configuration from TOML files and environment variables
2. Validation of configuration values with helpful error messages
3. Hot-reloading of configuration when files change
4. Observer pattern for notifying components of configuration changes

The configuration system uses Pydantic for validation and watchfiles for
file monitoring. It follows a singleton pattern to ensure consistent
configuration across the application.

Key components:
- ConfigModel: Main configuration schema with validation
- ConfigLoader: Singleton that loads and watches configuration
- StorageConfig: Configuration for storage backends
- AgentConfig: Configuration for individual agents
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Iterator
from contextlib import contextmanager
import threading
import logging
import sys
import atexit

from pydantic import BaseModel, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchfiles import watch, Change

from .orchestration import ReasoningMode
from .errors import ConfigError

class ContextAwareSearchConfig(BaseModel):
    """Configuration for context-aware search functionality."""

    # Context-aware search settings
    enabled: bool = Field(default=True)

    # Query expansion settings
    use_query_expansion: bool = Field(default=True)
    expansion_factor: float = Field(default=0.3, ge=0.0, le=1.0)

    # Entity recognition settings
    use_entity_recognition: bool = Field(default=True)
    entity_weight: float = Field(default=0.5, ge=0.0, le=1.0)

    # Topic modeling settings
    use_topic_modeling: bool = Field(default=True)
    num_topics: int = Field(default=5, ge=1, le=20)
    topic_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    # Search history settings
    use_search_history: bool = Field(default=True)
    history_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    max_history_items: int = Field(default=10, ge=1, le=100)


class SearchConfig(BaseModel):
    """Configuration for search functionality."""

    backends: List[str] = Field(default=["serper"])
    max_results_per_query: int = Field(default=5, ge=1)

    # Enhanced relevance ranking settings
    use_semantic_similarity: bool = Field(default=True)
    use_bm25: bool = Field(default=True)
    semantic_similarity_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    bm25_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    source_credibility_weight: float = Field(default=0.2, ge=0.0, le=1.0)

    # Source credibility settings
    use_source_credibility: bool = Field(default=True)
    domain_authority_factor: float = Field(default=0.6, ge=0.0, le=1.0)
    citation_count_factor: float = Field(default=0.4, ge=0.0, le=1.0)

    # User feedback settings
    use_feedback: bool = Field(default=False)
    feedback_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    # Context-aware search settings
    context_aware: ContextAwareSearchConfig = Field(default_factory=ContextAwareSearchConfig)

    @field_validator("semantic_similarity_weight", "bm25_weight", "source_credibility_weight")
    def validate_weights_sum_to_one(cls, v: float, info) -> float:
        """Validate that the weights sum to 1.0."""
        # Get the current values of all weights
        values = info.data

        # Calculate the sum of all weights
        weights_sum = (
            values.get("semantic_similarity_weight", 0.5) +
            values.get("bm25_weight", 0.3) +
            values.get("source_credibility_weight", 0.2)
        )

        # Allow a small tolerance for floating-point errors
        if abs(weights_sum - 1.0) > 0.001:
            raise ConfigError(
                "Relevance ranking weights must sum to 1.0",
                current_sum=weights_sum,
                weights={
                    "semantic_similarity_weight": values.get("semantic_similarity_weight", 0.5),
                    "bm25_weight": values.get("bm25_weight", 0.3),
                    "source_credibility_weight": values.get("source_credibility_weight", 0.2)
                },
                suggestion="Adjust the weights so they sum to 1.0"
            )

        return v


logger = logging.getLogger(__name__)


class StorageConfig(BaseModel):
    """Storage configuration for DuckDB, RDF, and more."""

    duckdb_path: str = Field(default="autoresearch.duckdb")
    vector_extension: bool = Field(default=True)
    vector_extension_path: Optional[str] = Field(default=None)
    hnsw_m: int = Field(default=16, ge=4)
    hnsw_ef_construction: int = Field(default=200, ge=32)
    hnsw_metric: str = Field(default="l2sq")
    rdf_backend: str = Field(default="sqlite")
    rdf_path: str = Field(default="rdf_store")

    @field_validator("rdf_backend")
    def validate_rdf_backend(cls, v: str) -> str:
        """Validate the RDF backend configuration.

        This validator ensures that the specified RDF backend is supported.
        Currently, only 'sqlite' and 'berkeleydb' backends are supported.

        Args:
            cls: The class (StorageConfig)
            v: The RDF backend value to validate

        Returns:
            str: The validated RDF backend value

        Raises:
            ConfigError: If the specified backend is not in the list of valid backends
        """
        valid_backends = ["sqlite", "berkeleydb"]
        if v not in valid_backends:
            raise ConfigError(f"Invalid RDF backend", 
                             valid_backends=valid_backends, 
                             provided=v)
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
    agents: List[str] = Field(
        default=["Synthesizer", "Contrarian", "FactChecker"]
    )
    primus_start: int = Field(default=0)
    reasoning_mode: ReasoningMode = Field(default=ReasoningMode.DIALECTICAL)
    output_format: Optional[str] = None
    # Defaults to None (auto-detect in CLI)
    tracing_enabled: bool = Field(default=False)

    # Storage settings
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # Agent-specific settings
    agent_config: Dict[str, AgentConfig] = Field(default_factory=dict)

    # Search settings
    search: SearchConfig = Field(default_factory=SearchConfig)

    # Dynamic knowledge graph settings
    graph_eviction_policy: str = Field(default="LRU")
    vector_nprobe: int = Field(default=10, ge=1)

    # Model settings
    default_model: str = Field(default="gpt-3.5-turbo")

    # Profile settings
    active_profile: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @field_validator("reasoning_mode", mode="before")
    def validate_reasoning_mode(cls, v: ReasoningMode | str) -> ReasoningMode:
        """Validate and convert the reasoning mode configuration.

        This validator ensures that the specified reasoning mode is valid and
        converts string values to ReasoningMode enum instances. It accepts either
        a ReasoningMode enum instance or a string that matches a valid enum value.

        Args:
            cls: The class (ConfigModel)
            v: The reasoning mode value to validate (enum or string)

        Returns:
            ReasoningMode: The validated reasoning mode as an enum instance

        Raises:
            ConfigError: If the specified mode is not a valid ReasoningMode value,
                        with a helpful suggestion of valid modes
        """
        if isinstance(v, ReasoningMode):
            return v
        try:
            return ReasoningMode(v)
        except Exception as exc:
            valid_modes = [m.value for m in ReasoningMode]
            raise ConfigError(
                "Invalid reasoning mode",
                valid_modes=valid_modes,
                provided=v,
                suggestion=f"Try using one of the valid modes: {', '.join(valid_modes)}",
                cause=exc
            ) from exc

    @field_validator("graph_eviction_policy")
    def validate_eviction_policy(cls, v: str) -> str:
        """Validate the graph eviction policy configuration.

        This validator ensures that the specified graph eviction policy is supported.
        Currently, only 'LRU' (Least Recently Used) and 'score' policies are supported.

        Args:
            cls: The class (ConfigModel)
            v: The eviction policy value to validate

        Returns:
            str: The validated eviction policy value

        Raises:
            ConfigError: If the specified policy is not in the list of valid policies
        """
        valid_policies = ["LRU", "score"]
        if v not in valid_policies:
            raise ConfigError(
                "Invalid graph eviction policy",
                valid_policies=valid_policies,
                provided=v
            )
        return v


class ConfigLoader:
    """Loads and watches configuration changes."""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance for testing purposes.

        This method is primarily used in tests to ensure a clean state between test cases.
        It stops the config watcher thread if it's running, clears the configuration,
        and sets the singleton instance to None.

        Args:
            cls: The class (ConfigLoader)

        Raises:
            ConfigError: If there's an error stopping the config watcher thread
        """
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.stop_watching()
                except Exception as e:
                    # Raise a ConfigError with the original exception as the cause
                    raise ConfigError(
                        "Error stopping config watcher",
                        cause=e
                    ) from e
                cls._instance._config = None
                cls._instance = None

    def __new__(cls) -> "ConfigLoader":
        """Create or return the singleton instance of ConfigLoader.

        This method implements the singleton pattern to ensure that only one
        instance of ConfigLoader exists throughout the application. It uses
        a thread lock to ensure thread safety.

        Args:
            cls: The class (ConfigLoader)

        Returns:
            ConfigLoader: The singleton instance of ConfigLoader
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigLoader, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the ConfigLoader instance.

        This method initializes the ConfigLoader instance with default values.
        It is designed to be called only once per instance due to the singleton pattern.
        If the instance is already initialized, it returns early.

        The initialization sets up:
        - Configuration storage
        - Thread management for config watching
        - Observer pattern for config change notifications
        - Default search paths for configuration files
        """
        if getattr(self, "_initialized", False):
            return

        self._config: ConfigModel | None = None
        self._watch_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._observers: Set[Callable[[ConfigModel], None]] = set()
        self._config_time: float = 0.0
        self._active_profile: Optional[str] = None
        self._profiles: Dict[str, Dict[str, Any]] = {}

        # Define search paths for configuration files with precedence:
        # 1. Current directory
        # 2. User config directory
        # 3. System-wide config directory
        self._search_paths: List[Path] = [
            Path.cwd() / "autoresearch.toml",  # Current directory
            Path.home() / ".config/autoresearch/autoresearch.toml",  # User config
            Path("/etc/autoresearch/autoresearch.toml"),  # System-wide config
        ]

        # Environment file is only searched in the current directory
        self._env_path: Path = Path.cwd() / ".env"

        # Initialize watch paths with files that exist
        self._watch_paths: List[str] = []
        self._update_watch_paths()

        self._atexit_registered = False
        self._initialized = True

    def _update_watch_paths(self) -> None:
        """Update the list of configuration file paths to watch for changes.

        This method updates the _watch_paths list with the paths of files that exist.
        It checks all search paths for the configuration file and the environment file.
        """
        self._watch_paths = []

        # Add existing config files to watch paths
        for path in self._search_paths:
            if path.exists():
                self._watch_paths.append(str(path))

        # Add environment file if it exists
        if self._env_path.exists():
            self._watch_paths.append(str(self._env_path))

    @property
    def watch_paths(self) -> List[str]:
        """Get the list of configuration file paths to watch for changes.

        This property returns the list of file paths that the ConfigLoader
        is monitoring for changes. This includes any existing configuration files
        from the search paths and the environment file if it exists.

        Returns:
            List[str]: A list of file paths being watched for configuration changes
        """
        return self._watch_paths

    @property
    def config(self) -> ConfigModel:
        """Get the current configuration model.

        This property returns the current configuration model. If the configuration
        has not been loaded yet, it loads it by calling load_config().

        The configuration is cached, so subsequent calls to this property will
        return the same instance unless the configuration is reloaded due to
        file changes or a manual reload.

        Returns:
            ConfigModel: The current configuration model with validated settings
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> ConfigModel:
        """Load and validate configuration from TOML and environment variables.

        This method reads configuration from the first existing 'autoresearch.toml' file
        in the search paths, and combines it with environment variables. It handles 
        the conversion of the raw configuration data into a validated ConfigModel instance.

        The search paths are checked in the following order:
        1. Current directory
        2. User config directory (~/.config/autoresearch)
        3. System-wide config directory (/etc/autoresearch)

        The method performs several steps:
        1. Loads the TOML file if it exists in any of the search paths
        2. Extracts core settings
        3. Maps legacy settings to new names
        4. Processes storage configuration
        5. Extracts agent configuration
        6. Extracts profile configurations
        7. Applies the active profile settings if one is set
        8. Creates a ConfigModel instance with validation

        Returns:
            ConfigModel: A validated configuration model

        Raises:
            ConfigError: If the configuration file cannot be loaded or validation fails
        """
        raw = {}
        config_path = None

        # Update watch paths to ensure we're watching all existing config files
        self._update_watch_paths()

        # Find the first existing config file in the search paths
        for path in self._search_paths:
            if path.exists():
                config_path = path
                break

        if config_path and config_path.exists():
            try:
                self._config_time = config_path.stat().st_mtime
                with open(config_path, "rb") as f:
                    raw = tomllib.load(f)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                # Raise a ConfigError with the original exception as the cause
                raise ConfigError(
                    "Error loading config file",
                    file=str(config_path),
                    cause=e
                ) from e

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
            "vector_extension_path": duckdb_cfg.get("vector_extension_path", None),
            "hnsw_m": duckdb_cfg.get("hnsw_m", 16),
            "hnsw_ef_construction": duckdb_cfg.get(
                "hnsw_ef_construction", 200
            ),
            "hnsw_metric": duckdb_cfg.get("hnsw_metric", "l2"),
            "rdf_backend": rdf_cfg.get("backend", "sqlite"),
            "rdf_path": rdf_cfg.get("path", "rdf_store"),
        }

        # Extract agent configuration
        agent_cfg = raw.get("agent", {})
        enabled_agents = [
            name for name, a in agent_cfg.items() if a.get("enabled", True)
        ]

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

        # Extract profile configurations
        self._profiles = raw.get("profiles", {})

        # Apply active profile settings if one is set
        if self._active_profile and self._active_profile in self._profiles:
            profile_settings = self._profiles[self._active_profile]
            # Merge profile settings with core settings (profile takes precedence)
            for key, value in profile_settings.items():
                core_settings[key] = value
            # Set the active profile in the config
            core_settings["active_profile"] = self._active_profile

        try:
            return ConfigModel(**core_settings)
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            # Raise with more helpful message
            raise ConfigError(
                "Configuration validation error",
                details=str(e),
                cause=e
            ) from e

    def register_observer(
        self, callback: Callable[[ConfigModel], None]
    ) -> None:
        """Register a callback to be notified of configuration changes.

        This method adds a callback function to the set of observers that will be
        notified when the configuration changes. The callback will be called with
        the new configuration model as its argument.

        This implements the Observer pattern, allowing components to react to
        configuration changes without polling.

        Args:
            callback: A callable that takes a ConfigModel as its argument and returns None.
                     This will be called whenever the configuration changes.
        """
        self._observers.add(callback)

    def unregister_observer(
        self, callback: Callable[[ConfigModel], None]
    ) -> None:
        """Unregister a previously registered configuration change observer.

        This method removes a callback function from the set of observers that are
        notified when the configuration changes. If the callback is not in the set
        of observers, this method does nothing (no error is raised).

        Args:
            callback: The callback function to remove from the observers set.
                     This should be the same function object that was previously
                     registered with register_observer.
        """
        self._observers.discard(callback)

    def notify_observers(self, config: ConfigModel) -> None:
        """Notify all registered observers of a configuration change.

        This method calls each registered observer callback with the new configuration
        model as its argument. If any observer raises an exception, the notification
        process is halted and a ConfigError is raised.

        Args:
            config: The new configuration model to pass to the observers

        Raises:
            ConfigError: If any observer callback raises an exception during execution.
                        The original exception is included as the cause.
        """
        for observer in self._observers:
            try:
                observer(config)
            except Exception as e:
                logger.error(f"Error in config observer: {e}")
                # Raise a ConfigError with the original exception as the cause
                raise ConfigError(
                    "Error in config observer",
                    observer=str(observer),
                    cause=e
                ) from e

    def watch_changes(
        self, callback: Optional[Callable[[ConfigModel], None]] = None
    ) -> None:
        """Start watching configuration files for changes.

        This method starts a background thread that monitors the configuration files
        for changes. When a change is detected, the configuration is reloaded and
        all registered observers are notified.

        If a callback is provided, it is registered as an observer before starting
        the watcher. If the watcher is already running, this method does nothing.

        The watcher thread is automatically stopped when the program exits via
        an atexit handler.

        Args:
            callback: Optional callback function to register as an observer.
                     If provided, it will be called whenever the configuration changes.
        """
        if callback:
            self.register_observer(callback)

        if self._watch_thread and self._watch_thread.is_alive():
            logger.info("Config watcher already running")
            return

        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_config_files, daemon=True, name="ConfigWatcher"
        )
        if not self._atexit_registered:
            atexit.register(self.stop_watching)
            self._atexit_registered = True
        self._watch_thread.start()
        logger.info(f"Started config watcher for paths: {self.watch_paths}")

    def stop_watching(self) -> None:
        """Stop the configuration file watcher thread.

        This method signals the configuration watcher thread to stop and waits
        for it to terminate (with a timeout). If the thread is not running,
        this method does nothing.

        The method is automatically called when the program exits via an atexit
        handler registered in watch_changes(). It can also be called manually
        to stop watching for configuration changes.

        Note:
            This method uses a timeout when joining the thread to prevent
            hanging if the thread is blocked. The timeout is set to 1 second.
        """
        if self._watch_thread and self._watch_thread.is_alive():
            self._stop_event.set()
            self._watch_thread.join(timeout=1.0)
            if not getattr(sys.stderr, "closed", False):
                logger.info("Stopped config watcher")

    @contextmanager
    def watching(
        self, callback: Optional[Callable[[ConfigModel], None]] = None
    ) -> Iterator[None]:
        """Context manager to watch configuration files within a scope.

        This method provides a context manager that starts watching configuration
        files when entering the context and automatically stops watching when
        exiting the context, even if an exception occurs.

        This is useful for ensuring that the watcher thread is properly cleaned up
        in scripts or applications that have a defined lifecycle.

        Args:
            callback: Optional callback function to register as an observer.
                     If provided, it will be called whenever the configuration changes.

        Yields:
            None: This context manager doesn't yield a value.

        Example:
            ```python
            with config_loader.watching(on_config_change):
                # Do something while watching for config changes
                # When this block exits, the watcher will be stopped
            ```
        """
        self.watch_changes(callback)
        try:
            yield
        finally:
            self.stop_watching()

    def _watch_config_files(self) -> None:
        """Watch for changes in configuration files (runs in separate thread).

        This private method is the target function for the watcher thread started
        by watch_changes(). It continuously monitors the configuration files for
        changes using the watchfiles library.

        When a change is detected, it:
        1. Reloads the configuration
        2. Updates the internal configuration state
        3. Notifies all registered observers

        The method runs until the stop event is set by stop_watching() or when
        an unhandled exception occurs.

        Raises:
            ConfigError: If there's an error watching the files, reloading the
                        configuration, or notifying observers. The error is logged
                        before being raised.
        """
        # Update watch paths to ensure we're watching all existing config files
        self._update_watch_paths()

        abs_paths = [
            str(Path(p).absolute())
            for p in self.watch_paths
            if Path(p).exists()
        ]

        if not abs_paths:
            logger.warning(
                f"No configuration files found in search paths: {[str(p) for p in self._search_paths]}"
            )
            return

        try:
            # Use watchfiles to monitor changes
            for changes in watch(*abs_paths, stop_event=self._stop_event):
                if self._stop_event.is_set():
                    break

                # Only reload if there are actual changes
                if changes:
                    logger.info(f"{len(changes)} change detected")
                    # Check for any type of change, not just modifications
                    try:
                        new_config = self.load_config()
                        self._config = new_config
                        logger.info("Configuration reloaded successfully")
                        self.notify_observers(new_config)
                    except Exception as e:
                        logger.error(f"Error reloading config: {e}")
                        # Raise a ConfigError with the original exception as the cause
                        raise ConfigError(
                            "Error reloading config",
                            cause=e
                        ) from e

        except Exception as e:
            logger.error(f"Error in config watcher: {e}")
            # Raise a ConfigError with the original exception as the cause
            raise ConfigError(
                "Error in config watcher",
                paths=self.watch_paths,
                cause=e
            ) from e

    def set_active_profile(self, profile_name: str) -> None:
        """Set the active configuration profile.

        This method sets the active configuration profile to the specified name.
        If the profile doesn't exist, a ConfigError is raised with a helpful
        message suggesting valid profiles.

        The configuration is reloaded after setting the profile, and all
        registered observers are notified of the change.

        Args:
            profile_name: The name of the profile to activate.

        Raises:
            ConfigError: If the specified profile doesn't exist in the configuration.
        """
        # Load the configuration if it hasn't been loaded yet
        if not self._profiles:
            self.load_config()

        # Check if the profile exists
        if profile_name not in self._profiles:
            valid_profiles = list(self._profiles.keys())
            raise ConfigError(
                "Invalid profile",
                valid_profiles=valid_profiles,
                provided=profile_name,
                suggestion=f"Valid profiles: {', '.join(valid_profiles)}"
            )

        # Set the active profile
        self._active_profile = profile_name

        # Reload the configuration with the new profile
        self._config = None  # Force reload
        new_config = self.config

        # Notify observers of the change
        self.notify_observers(new_config)

    def on_config_change(self, config: ConfigModel) -> None:
        """Default handler for configuration change events.

        This method is a simple default observer that logs when the configuration
        changes. It can be used as a callback for watch_changes() or as a base
        for more complex handlers.

        Args:
            config: The new configuration model that was loaded after a change
                  was detected.
        """
        logger.info("Configuration changed")


# Convenience function to get the global config
def get_config() -> ConfigModel:
    """Get the current configuration from the global ConfigLoader instance.

    This function provides a convenient way to access the current configuration
    without having to create a ConfigLoader instance explicitly. It returns the
    same configuration that would be obtained by calling ConfigLoader().config.

    Returns:
        ConfigModel: The current configuration model with validated settings

    Example:
        ```python
        from autoresearch.config import get_config

        config = get_config()
        print(f"Using LLM backend: {config.llm_backend}")
        ```
    """
    return ConfigLoader().config
