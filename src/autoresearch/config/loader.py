from __future__ import annotations

import atexit
import contextvars
import logging
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Sequence
import sys
import tomllib

from watchfiles import watch
from dotenv import dotenv_values
import os

from ..errors import ConfigError
from .models import (
    AgentConfig,
    AnalysisConfig,
    APIConfig,
    ConfigModel,
    DistributedConfig,
    StorageConfig,
)

logger = logging.getLogger(__name__)


def _merge_dict(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _merge_dict(base.get(key, {}), value)
        else:
            base[key] = value
    return base


class ConfigLoader:
    """Loads and watches configuration changes."""

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance for testing purposes."""
        with cls._lock:
            if cls._instance is not None:
                try:
                    cls._instance.stop_watching()
                except Exception as e:
                    raise ConfigError("Error stopping config watcher", cause=e) from e
                cls._instance._config = None
                cls._instance = None

    @classmethod
    def new_for_tests(cls) -> "ConfigLoader":
        """Return a fresh loader instance for isolated tests."""
        cls.reset_instance()
        return cls()

    @classmethod
    @contextmanager
    def temporary_instance(cls) -> Iterator["ConfigLoader"]:
        """Provide a temporary loader instance for tests."""
        instance = cls.new_for_tests()
        try:
            yield instance
        finally:
            cls.reset_instance()

    def __enter__(self) -> "ConfigLoader":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.close()

    def __init__(
        self,
        search_paths: Optional[Sequence[str | Path]] = None,
        env_path: str | Path | None = None,
    ) -> None:
        self.search_paths: List[Path] = [
            Path(p) for p in (search_paths or ["autoresearch.toml", "config/autoresearch.toml"])
        ]
        self.env_path: Path = Path(env_path) if env_path else Path(".env")
        # Maintain watch_paths for backward compatibility and tests
        self.watch_paths: List[str] = [str(p) for p in self.search_paths]
        self._config: ConfigModel | None = None
        self._watch_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._observers: Set[Callable[[ConfigModel], None]] = set()
        self._active_profile: str | None = None
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._config_time = 0.0
        self._atexit_registered = False

    def _update_watch_paths(self) -> None:
        """Update ``watch_paths`` to match current ``search_paths``."""
        self.watch_paths = [str(p) for p in self.search_paths]

    @property
    def config(self) -> ConfigModel:
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> ConfigModel:
        raw_env: Dict[str, str] = {}
        if self.env_path.exists():
            raw_env.update({k: v for k, v in dotenv_values(self.env_path).items() if v is not None})
        for key, value in os.environ.items():
            if key.startswith("AUTORESEARCH_") or "__" in key:
                raw_env.setdefault(key, value)

        env_settings: Dict[str, Any] = {}
        for key, value in raw_env.items():
            key_lower = key.lower()
            if key_lower.startswith("autoresearch_"):
                key_lower = key_lower[len("autoresearch_"):]
            parts = key_lower.split("__")
            d = env_settings
            for part in parts[:-1]:
                d = d.setdefault(part, {})
            d[parts[-1]] = value
        storage_env = env_settings.pop("storage", {})

        raw: Dict[str, Any] = {}
        config_path: Path | None = None
        for path in self.search_paths:
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
                raise ConfigError(
                    "Error loading config file", file=str(config_path), cause=e
                ) from e
        else:
            logger.info("No configuration file found; using defaults")

        core_settings = raw.get("core", {})
        _merge_dict(core_settings, env_settings)
        if "backend" in core_settings and "llm_backend" not in core_settings:
            core_settings["llm_backend"] = core_settings["backend"]

        storage_cfg = raw.get("storage", {})
        duckdb_cfg = storage_cfg.get("duckdb", {})
        rdf_cfg = storage_cfg.get("rdf", {})

        storage_settings = {
            "duckdb_path": duckdb_cfg.get("path", "autoresearch.duckdb"),
            "vector_extension": duckdb_cfg.get("vector_extension", True),
            "vector_extension_path": duckdb_cfg.get("vector_extension_path", None),
            "hnsw_m": duckdb_cfg.get("hnsw_m", 16),
            "hnsw_ef_construction": duckdb_cfg.get("hnsw_ef_construction", 200),
            "hnsw_metric": duckdb_cfg.get("hnsw_metric", "l2"),
            "hnsw_ef_search": duckdb_cfg.get("hnsw_ef_search", duckdb_cfg.get("vector_nprobe", 10)),
            "hnsw_auto_tune": duckdb_cfg.get("hnsw_auto_tune", True),
            "vector_nprobe": duckdb_cfg.get("vector_nprobe", 10),
            "vector_search_batch_size": duckdb_cfg.get("vector_search_batch_size"),
            "vector_search_timeout_ms": duckdb_cfg.get("vector_search_timeout_ms"),
            "rdf_backend": rdf_cfg.get("backend", "sqlite"),
            "rdf_path": rdf_cfg.get("path", "rdf_store"),
            "use_kuzu": storage_cfg.get("use_kuzu", False),
            "kuzu_path": storage_cfg.get("kuzu_path", "kuzu.db"),
        }
        _merge_dict(storage_settings, storage_env)

        api_cfg = raw.get("api", {})
        distributed_cfg = raw.get("distributed", {})
        user_pref_cfg = raw.get("user_preferences", {})
        analysis_cfg = raw.get("analysis", {})

        if "enabled" in distributed_cfg and "distributed" not in core_settings:
            core_settings["distributed"] = bool(distributed_cfg.get("enabled", False))

        agent_cfg = raw.get("agent", {})
        enabled_agents = [
            name for name, a in agent_cfg.items() if a.get("enabled", True)
        ]
        if enabled_agents:
            core_settings["agents"] = enabled_agents

        agent_config_dict: Dict[str, AgentConfig] = {}
        for name, cfg in agent_cfg.items():
            try:
                agent_config_dict[name] = AgentConfig(**cfg)
            except Exception as e:
                logger.warning(
                    "Invalid agent configuration for %s: %s", name, e
                )

        def _safe_model(model_cls: Any, settings: Dict[str, Any], section: str):
            try:
                return model_cls(**settings)
            except Exception as e:
                logger.warning("Invalid %s configuration: %s", section, e)
                return model_cls()

        core_settings["storage"] = _safe_model(StorageConfig, storage_settings, "storage")
        core_settings["api"] = _safe_model(APIConfig, api_cfg, "api")
        core_settings["distributed_config"] = _safe_model(
            DistributedConfig, distributed_cfg, "distributed"
        )
        core_settings["user_preferences"] = user_pref_cfg
        core_settings["analysis"] = _safe_model(AnalysisConfig, analysis_cfg, "analysis")
        core_settings["agent_config"] = agent_config_dict

        self._profiles = raw.get("profiles", {})

        if self._active_profile and self._active_profile in self._profiles:
            profile_settings = self._profiles[self._active_profile]
            for key, value in profile_settings.items():
                core_settings[key] = value
            core_settings["active_profile"] = self._active_profile

        try:
            return ConfigModel.from_dict(core_settings)
        except Exception as e:  # pragma: no cover - unexpected
            logger.error(f"Configuration validation error: {e}")
            return ConfigModel()

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration files and return status and errors."""
        try:
            self.load_config()
            return True, []
        except ConfigError as e:
            return False, [str(e)]
        except Exception as e:  # pragma: no cover - unexpected
            return False, [str(e)]

    def register_observer(self, callback: Callable[[ConfigModel], None]) -> None:
        self._observers.add(callback)

    def unregister_observer(self, callback: Callable[[ConfigModel], None]) -> None:
        self._observers.discard(callback)

    def notify_observers(self, config: ConfigModel) -> None:
        for observer in self._observers:
            try:
                observer(config)
            except Exception as e:
                logger.error(f"Error in config observer: {e}")
                raise ConfigError(
                    "Error in config observer", observer=str(observer), cause=e
                ) from e

    def watch_changes(
        self, callback: Optional[Callable[[ConfigModel], None]] = None
    ) -> None:
        if callback:
            self.register_observer(callback)
        if self._watch_thread and self._watch_thread.is_alive():
            logger.info("Config watcher already running")
            return

        watch_targets = [Path(p) for p in self.watch_paths if Path(p).exists()]
        if self.env_path.exists():
            watch_targets.append(self.env_path)
        if not watch_targets:
            logger.info("No configuration files found to watch; skipping watcher")
            return

        watch_dirs = {p.resolve().parent for p in watch_targets}
        target_files = {p.resolve() for p in watch_targets}

        self._stop_event.clear()
        self._watch_thread = threading.Thread(
            target=self._watch_config_files,
            args=(watch_dirs, target_files),
            daemon=True,
            name="ConfigWatcher",
        )
        if not self._atexit_registered:
            atexit.register(self.stop_watching)
            self._atexit_registered = True
        self._watch_thread.start()
        logger.info(
            f"Started config watcher for paths: {[str(p) for p in target_files]}"
        )

    def stop_watching(self) -> None:
        if self._watch_thread and self._watch_thread.is_alive():
            self._stop_event.set()
            self._watch_thread.join(timeout=1.0)
            if not getattr(sys.stderr, "closed", False):
                logger.info("Stopped config watcher")

    def close(self) -> None:
        try:
            self.stop_watching()
        finally:
            self._config = None

    @contextmanager
    def watching(
        self, callback: Optional[Callable[[ConfigModel], None]] = None
    ) -> Iterator[None]:
        self.watch_changes(callback)
        try:
            yield
        finally:
            self.stop_watching()

    def _watch_config_files(
        self,
        directories: Set[Path] | None = None,
        target_files: Set[Path] | None = None,
    ) -> None:
        if directories is None or target_files is None:
            watch_targets = [Path(p) for p in self.watch_paths if Path(p).exists()]
            if self.env_path.exists():
                watch_targets.append(self.env_path)
            directories = {p.resolve().parent for p in watch_targets}
            target_files = {p.resolve() for p in watch_targets}
        try:
            for changes in watch(*(str(d) for d in directories), stop_event=self._stop_event):
                for change in changes:
                    file_path = Path(change[1]).resolve()
                    if file_path in target_files:
                        if not file_path.exists():
                            continue
                        try:
                            new_config = self.load_config()
                            self._config = new_config
                            self.notify_observers(new_config)
                        except Exception as e:
                            logger.error(f"Error reloading config: {e}")
                            raise ConfigError("Error reloading config", cause=e) from e
        except Exception as e:
            logger.error(f"Error in config watcher: {e}")
            raise ConfigError(
                "Error in config watcher", paths=[str(p) for p in directories], cause=e
            ) from e

    def set_active_profile(self, profile_name: str) -> None:
        if not self._profiles:
            self.load_config()
        if profile_name not in self._profiles:
            valid_profiles = list(self._profiles.keys())
            raise ConfigError(
                "Invalid profile",
                valid_profiles=valid_profiles,
                provided=profile_name,
                suggestion=f"Valid profiles: {', '.join(valid_profiles)}",
            )
        self._active_profile = profile_name
        self._config = None
        new_config = self.config
        self.notify_observers(new_config)

    def available_profiles(self) -> List[str]:
        if not self._profiles:
            self.load_config()
        return list(self._profiles.keys())

    def on_config_change(self, config: ConfigModel) -> None:  # pragma: no cover
        logger.info("Configuration changed")


_current_config: contextvars.ContextVar[ConfigModel | None] = contextvars.ContextVar(
    "current_config", default=None
)


@contextmanager
def temporary_config(config: ConfigModel) -> Iterator[ConfigModel]:
    token = _current_config.set(config)
    try:
        yield config
    finally:
        _current_config.reset(token)


def get_config() -> ConfigModel:
    cfg = _current_config.get()
    if cfg is not None:
        return cfg
    return ConfigLoader().config
