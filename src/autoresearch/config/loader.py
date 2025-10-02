from __future__ import annotations

from __future__ import annotations

import atexit
import contextvars
import logging
import os
import sys
import threading
import tomllib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    TypedDict,
    TypeVar,
    cast,
)

from dotenv import dotenv_values
from pydantic import BaseModel
from watchfiles import watch

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


JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | Sequence["JSONValue"] | Mapping[str, "JSONValue"]
JSONObject = dict[str, JSONValue]


class ConfigDocument(TypedDict, total=False):
    core: JSONObject
    storage: JSONObject
    api: JSONObject
    distributed: JSONObject
    user_preferences: JSONObject
    analysis: JSONObject
    agent: dict[str, JSONObject]
    profiles: dict[str, JSONObject]


@dataclass
class LoadedConfigFile:
    """Result of loading a configuration document from disk."""

    path: Path | None
    data: ConfigDocument
    modified_time: float | None


MutableJSON = MutableMapping[str, JSONValue]
JSONMapping = Mapping[str, JSONValue]
TMutableJSON = TypeVar("TMutableJSON", bound=MutableJSON)
ConfigInitDict = dict[str, object]


_current_loader: contextvars.ContextVar["ConfigLoader | None"] = contextvars.ContextVar(
    "current_config_loader", default=None
)


def load_config_file(search_paths: Sequence[Path]) -> LoadedConfigFile:
    """Load the first existing TOML document from ``search_paths``."""

    for path in search_paths:
        if path.exists():
            try:
                modified_time = path.stat().st_mtime
                with open(path, "rb") as handle:
                    parsed = tomllib.load(handle)
            except Exception as exc:
                logger.error(f"Error loading config file: {exc}")
                raise ConfigError("Error loading config file", file=str(path), cause=exc) from exc
            if not isinstance(parsed, dict):
                raise ConfigError(
                    "Invalid config file structure",
                    file=str(path),
                    suggestion="Ensure the TOML document contains a root table.",
                )
            logger.info("Loaded configuration from %s", path)
            return LoadedConfigFile(path=path, data=cast(ConfigDocument, parsed), modified_time=modified_time)
    logger.info("No configuration file found; using defaults")
    return LoadedConfigFile(path=None, data=cast(ConfigDocument, {}), modified_time=None)


def _merge_dict(base: TMutableJSON, updates: JSONMapping) -> TMutableJSON:
    """Recursively merge ``updates`` into ``base``."""

    for key, value in updates.items():
        if isinstance(value, Mapping):
            existing = base.get(key)
            nested: MutableJSON
            if isinstance(existing, MutableMapping):
                nested = existing
            else:
                nested = {}
            base[key] = _merge_dict(nested, value)
        else:
            base[key] = value
    return base


def _ensure_object(value: JSONValue) -> JSONObject:
    """Return a JSON object when ``value`` is a mapping; otherwise an empty dict."""

    if isinstance(value, Mapping):
        return dict(value)
    return cast(JSONObject, {})


class ConfigLoader:
    """Loads and watches configuration changes."""

    _instance: "ConfigLoader | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: object, **kwargs: object) -> "ConfigLoader":
        loader = _current_loader.get()
        if loader is not None:
            return loader
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the loader instance for testing purposes."""
        with cls._lock:
            loaders: list[ConfigLoader] = []
            ctx_loader = _current_loader.get()
            if ctx_loader is not None:
                loaders.append(ctx_loader)
            if cls._instance is not None and cls._instance is not ctx_loader:
                loaders.append(cls._instance)
            for loader in loaders:
                try:
                    loader.stop_watching()
                except Exception as e:  # pragma: no cover - unexpected
                    raise ConfigError("Error stopping config watcher", cause=e) from e
            if ctx_loader is not None:
                _current_loader.set(None)
            if cls._instance is not None:
                cls._instance._config = None
                cls._instance = None

    @classmethod
    def new_for_tests(
        cls,
        search_paths: Sequence[str | Path] | None = None,
        env_path: str | Path | None = None,
    ) -> "ConfigLoader":
        """Return a fresh loader instance for isolated tests."""
        cls.reset_instance()
        loader = super().__new__(cls)
        ConfigLoader.__init__(loader, search_paths=search_paths, env_path=env_path)
        _current_loader.set(loader)
        return loader

    @classmethod
    @contextmanager
    def temporary_instance(
        cls,
        search_paths: Sequence[str | Path] | None = None,
        env_path: str | Path | None = None,
    ) -> Iterator["ConfigLoader"]:
        """Provide a temporary loader instance for tests."""
        instance = cls.new_for_tests(search_paths=search_paths, env_path=env_path)
        try:
            yield instance
        finally:
            cls.reset_instance()

    def __enter__(self) -> "ConfigLoader":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def __init__(
        self,
        search_paths: Sequence[str | Path] | None = None,
        env_path: str | Path | None = None,
    ) -> None:
        if getattr(self, "_initialized", False):  # pragma: no cover - defensive
            return
        self.search_paths: List[Path] = [
            Path(p) for p in (search_paths or ["autoresearch.toml", "config/autoresearch.toml"])
        ]
        self.env_path: Path = Path(env_path) if env_path else Path(".env")
        self.watch_paths: List[str] = [str(p) for p in self.search_paths]
        self._config: ConfigModel | None = None
        self._watch_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._observers: Set[Callable[[ConfigModel], None]] = set()
        self._active_profile: str | None = None
        self._profiles: Dict[str, Dict[str, object]] = {}
        self._config_time = 0.0
        self._atexit_registered = False
        self._initialized = True

    def _update_watch_paths(self) -> None:
        """Update ``watch_paths`` to match current ``search_paths``."""
        self.watch_paths = [str(p) for p in self.search_paths]

    @property
    def config(self) -> ConfigModel:
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self) -> ConfigModel:
        raw_env: dict[str, str] = {}
        if self.env_path.exists():
            raw_env.update({k: v for k, v in dotenv_values(self.env_path).items() if v is not None})

        for key, value in os.environ.items():
            if key.startswith("AUTORESEARCH_"):
                raw_env.setdefault(key, value)
            elif "__" in key and not (key.startswith("__") or key.endswith("__")):
                raw_env.setdefault(key, value)

        env_settings: JSONObject = {}
        for key, value in raw_env.items():
            key_lower = key.lower()
            if key_lower.startswith("autoresearch_"):
                key_lower = key_lower.removeprefix("autoresearch_")
            parts = key_lower.split("__")
            target: JSONObject = env_settings
            for part in parts[:-1]:
                nested = target.get(part)
                if not isinstance(nested, dict):
                    nested = {}
                    target[part] = nested
                target = cast(JSONObject, nested)
            target[parts[-1]] = value

        storage_env_raw = env_settings.pop("storage", {})
        if isinstance(storage_env_raw, Mapping):
            storage_env: MutableJSON = dict(storage_env_raw)
        else:
            storage_env = {}

        loaded = load_config_file(self.search_paths)
        self._config_time = loaded.modified_time or 0.0
        raw = loaded.data

        core_section = raw.get("core", {})
        if isinstance(core_section, Mapping):
            core_raw: MutableJSON = dict(core_section)
        else:
            core_raw = {}
        _merge_dict(core_raw, env_settings)
        core_settings = cast(ConfigInitDict, dict(core_raw))
        if "backend" in core_settings and "llm_backend" not in core_settings:
            core_settings["llm_backend"] = core_settings["backend"]

        storage_section = raw.get("storage", {})
        storage_cfg = _ensure_object(storage_section)
        duckdb_cfg = _ensure_object(storage_cfg.get("duckdb", {}))
        rdf_cfg = _ensure_object(storage_cfg.get("rdf", {}))

        storage_settings: MutableJSON = {
            "duckdb_path": duckdb_cfg.get("path", "autoresearch.duckdb"),
            "vector_extension": duckdb_cfg.get("vector_extension", True),
            "vector_extension_path": duckdb_cfg.get("vector_extension_path"),
            "hnsw_m": duckdb_cfg.get("hnsw_m", 16),
            "hnsw_ef_construction": duckdb_cfg.get("hnsw_ef_construction", 200),
            "hnsw_metric": duckdb_cfg.get("hnsw_metric", "l2"),
            "hnsw_ef_search": duckdb_cfg.get("hnsw_ef_search", duckdb_cfg.get("vector_nprobe", 10)),
            "hnsw_auto_tune": duckdb_cfg.get("hnsw_auto_tune", True),
            "vector_nprobe": duckdb_cfg.get("vector_nprobe", 10),
            "vector_search_batch_size": duckdb_cfg.get("vector_search_batch_size"),
            "vector_search_timeout_ms": duckdb_cfg.get("vector_search_timeout_ms"),
            "rdf_backend": rdf_cfg.get("backend", "oxigraph"),
            "rdf_path": rdf_cfg.get("path", "rdf_store"),
            "ontology_reasoner": storage_cfg.get("ontology_reasoner", "owlrl"),
            "ontology_reasoner_timeout": storage_cfg.get("ontology_reasoner_timeout"),
            "ontology_reasoner_max_triples": storage_cfg.get("ontology_reasoner_max_triples"),
            "max_connections": storage_cfg.get("max_connections", 1),
            "use_kuzu": storage_cfg.get("use_kuzu", False),
            "kuzu_path": storage_cfg.get("kuzu_path", "kuzu.db"),
            "deterministic_node_budget": storage_cfg.get("deterministic_node_budget"),
        }
        minimum_resident_nodes = storage_cfg.get("minimum_deterministic_resident_nodes")
        if minimum_resident_nodes is not None:
            storage_settings[
                "minimum_deterministic_resident_nodes"
            ] = minimum_resident_nodes
        _merge_dict(storage_settings, storage_env)

        api_section = raw.get("api", {})
        api_settings: ConfigInitDict = dict(api_section) if isinstance(api_section, Mapping) else {}
        distributed_section = raw.get("distributed", {})
        distributed_settings: ConfigInitDict = (
            dict(distributed_section) if isinstance(distributed_section, Mapping) else {}
        )
        user_preferences_section = raw.get("user_preferences", {})
        user_pref_cfg: ConfigInitDict = (
            dict(user_preferences_section) if isinstance(user_preferences_section, Mapping) else {}
        )
        analysis_section = raw.get("analysis", {})
        analysis_settings: ConfigInitDict = (
            dict(analysis_section) if isinstance(analysis_section, Mapping) else {}
        )

        if "enabled" in distributed_settings and "distributed" not in core_settings:
            core_settings["distributed"] = bool(distributed_settings.get("enabled", False))

        agent_section = raw.get("agent", {})
        enabled_agents: list[str] = []
        agent_config_dict: Dict[str, AgentConfig] = {}
        if isinstance(agent_section, Mapping):
            typed_agent_section = cast(Mapping[str, JSONValue], agent_section)
            for name, raw_value in typed_agent_section.items():
                cfg_mapping: ConfigInitDict
                if isinstance(raw_value, Mapping):
                    cfg_mapping = cast(
                        ConfigInitDict, {k: cast(object, v) for k, v in raw_value.items()}
                    )
                else:
                    cfg_mapping = {}
                if cfg_mapping.get("enabled", True):
                    enabled_agents.append(name)
                try:
                    agent_config_dict[name] = AgentConfig(**cfg_mapping)
                except Exception as exc:
                    logger.warning("Invalid agent configuration for %s: %s", name, exc)
        if enabled_agents:
            core_settings["agents"] = enabled_agents

        def _safe_model(
            model_cls: type[BaseModel], settings: Mapping[str, object], section: str
        ) -> BaseModel:
            try:
                return model_cls(**settings)
            except Exception as exc:
                logger.warning("Invalid %s configuration: %s", section, exc)
                valid_settings: Dict[str, object] = {}
                for field, value in settings.items():
                    if field in model_cls.model_fields:
                        try:
                            model_cls(**{field: value})
                        except Exception:
                            continue
                        valid_settings[field] = value
                return model_cls(**valid_settings)

        core_settings["storage"] = _safe_model(StorageConfig, dict(storage_settings), "storage")
        core_settings["api"] = _safe_model(APIConfig, api_settings, "api")
        core_settings["distributed_config"] = _safe_model(
            DistributedConfig, distributed_settings, "distributed"
        )
        core_settings["user_preferences"] = user_pref_cfg
        core_settings["analysis"] = _safe_model(AnalysisConfig, analysis_settings, "analysis")
        core_settings["agent_config"] = agent_config_dict

        profiles_section = raw.get("profiles", {})
        self._profiles = {}
        if isinstance(profiles_section, Mapping):
            typed_profiles = cast(Mapping[str, JSONValue], profiles_section)
            for name, raw_value in typed_profiles.items():
                if isinstance(raw_value, Mapping):
                    self._profiles[name] = {k: cast(object, v) for k, v in raw_value.items()}
                else:
                    self._profiles[name] = {}

        active_candidate = self._active_profile or core_settings.get("active_profile")
        if isinstance(active_candidate, str):
            if active_candidate not in self._profiles:
                valid_profiles = list(self._profiles.keys())
                raise ConfigError(
                    "Invalid profile",
                    valid_profiles=valid_profiles,
                    provided=active_candidate,
                    suggestion=f"Valid profiles: {', '.join(valid_profiles)}",
                )
            core_settings.update(self._profiles[active_candidate])
            core_settings["active_profile"] = active_candidate
            self._active_profile = active_candidate

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

    def watch_changes(self, callback: Optional[Callable[[ConfigModel], None]] = None) -> None:
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
        logger.info(f"Started config watcher for paths: {[str(p) for p in target_files]}")

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
    def watching(self, callback: Optional[Callable[[ConfigModel], None]] = None) -> Iterator[None]:
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
                            logger.error("Config file missing: %s", file_path)
                            continue
                        try:
                            new_config = self.load_config()
                        except Exception as e:  # pragma: no cover - defensive
                            logger.error("Error reloading config: %s", e)
                            raise ConfigError("Error in config watcher", cause=e) from e
                        self._config = new_config
                        self.notify_observers(new_config)
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
