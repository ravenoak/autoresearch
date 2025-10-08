import ast
import contextlib
import importlib
import importlib.util
import logging
import multiprocessing
import multiprocessing.pool
import os
import sys
from collections.abc import Iterable, Mapping
from multiprocessing import resource_tracker
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Protocol, cast
from unittest.mock import MagicMock, _patch, patch
from uuid import uuid4

import pytest
from pytest_httpx import httpx_mock  # noqa: F401

from tests.optional_imports import import_or_skip
from tests.typing_helpers import TypedFixture


REPO_ROOT = Path(__file__).resolve().parent.parent
_FUTURE_IMPORT = "from __future__ import annotations"
_DEFAULT_GUARD_DIRECTORIES = (
    REPO_ROOT / "src",
    REPO_ROOT / "tests",
    REPO_ROOT / "scripts",
    REPO_ROOT / "extensions",
)
_SKIP_DIRECTORY_NAMES = {".git", ".ruff_cache", "__pycache__", ".venv", "build", "dist"}


def _should_skip_path(path: Path) -> bool:
    return any(part in _SKIP_DIRECTORY_NAMES for part in path.parts)


def _iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix == ".py" and not _should_skip_path(path):
                yield path
            continue
        for candidate in path.rglob("*.py"):
            if _should_skip_path(candidate):
                continue
            yield candidate


def _find_future_import_index(module: ast.Module) -> int | None:
    for index, node in enumerate(module.body):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            for alias in node.names:
                if alias.name == "annotations":
                    return index
    return None


def find_future_annotations_import_violations(
    paths: Iterable[Path] | None = None,
) -> list[str]:
    """Return messages for modules that import before the future annotations directive."""

    search_roots = (
        [Path(path) for path in paths]
        if paths is not None
        else [candidate for candidate in _DEFAULT_GUARD_DIRECTORIES if candidate.exists()]
    )

    violations: list[str] = []
    for file_path in _iter_python_files(search_roots):
        try:
            contents = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _FUTURE_IMPORT not in contents:
            continue
        try:
            module = ast.parse(contents)
        except SyntaxError:
            continue
        future_index = _find_future_import_index(module)
        if future_index is None:
            continue
        for node in module.body[:future_index]:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    relative = file_path.relative_to(REPO_ROOT)
                except ValueError:
                    relative = file_path
                line = contents.splitlines()[node.lineno - 1].strip()
                violations.append(f"{relative}:{node.lineno} {line}")
    return violations


def pytest_sessionstart(session: pytest.Session) -> None:  # pragma: no cover - exercised in CI
    del session
    violations = find_future_annotations_import_violations()
    if violations:
        formatted = "\n- ".join(violations)
        message = (
            "Modules must place `from __future__ import annotations` before other imports:"
            f"\n- {formatted}"
        )
        raise pytest.UsageError(message)


shared_memory: ModuleType | None
try:
    from multiprocessing import shared_memory
except ImportError:  # pragma: no cover - Python < 3.8
    shared_memory = None

try:
    from typer.testing import CliRunner
except Exception:  # pragma: no cover - typer optional in some environments
    CliRunner = MagicMock()

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - fastapi optional in some environments
    TestClient = MagicMock()

pytest_plugins = [
    "tests.fixtures.config",
    "tests.fixtures.storage",
    "tests.fixtures.redis",
    "tests.fixtures.extras",
    "tests.fixtures.parsers",
    "tests.fixtures.diagnostics",
    "tests.fixtures.performance",
    "pytest_httpx",
]

# Use spawn to avoid fork-related deadlocks and ensure clean state.
multiprocessing.set_start_method("spawn", force=True)


_CREATED_QUEUES: list[Any] = []
_QUEUE_FACTORY: Callable[..., Any] | None = None


class _RedisClient(Protocol):
    """Protocol describing the Redis client methods used in tests."""

    def flushdb(self) -> object: ...

    def close(self) -> object: ...


class _ResourceTrackerLike(Protocol):
    """Minimal protocol for ``multiprocessing.resource_tracker`` internals."""

    _cache: Mapping[str, str | tuple[str, str]]
    _registry: Mapping[str, str | tuple[str, str]]

    def maybe_unlink(self, name: str, rtype: str) -> None: ...


logger = logging.getLogger(__name__)


def _track_multiprocessing_queue(*args, **kwargs):
    if _QUEUE_FACTORY is None:
        raise RuntimeError("multiprocessing.Queue factory is not initialized")
    queue = _QUEUE_FACTORY(*args, **kwargs)
    _CREATED_QUEUES.append(queue)
    return queue


def _get_resource_tracker() -> _ResourceTrackerLike | None:
    """Return the active ``ResourceTracker`` instance when available."""

    tracker = getattr(resource_tracker, "_resource_tracker", None)
    if tracker is None:
        return None
    return cast(_ResourceTrackerLike, tracker)


def _iter_resource_tracker_containers() -> list[Any]:
    """Return resource tracker caches that need clearing."""

    containers: list[Any] = []
    tracker = _get_resource_tracker()
    if tracker is not None:
        for attr in ("_cache", "_registry"):
            containers.append(getattr(tracker, attr, None))
    containers.append(getattr(resource_tracker, "_cache", None))
    return [container for container in containers if container is not None]


def _flush_resource_tracker_cache() -> None:
    for container in _iter_resource_tracker_containers():
        with contextlib.suppress(Exception):
            clear = getattr(container, "clear", None)
            if callable(clear):
                clear()


@pytest.fixture(autouse=True)
def _terminate_active_children() -> TypedFixture[None]:
    """Terminate stray multiprocessing children after each test."""
    yield
    for proc in multiprocessing.active_children():
        proc.terminate()
        proc.join()


@pytest.fixture(autouse=True)
def _clear_resource_tracker_cache() -> TypedFixture[None]:
    """Clear resource tracker caches before and after each test."""
    _flush_resource_tracker_cache()
    yield
    _flush_resource_tracker_cache()


@pytest.fixture(autouse=True)
def _drain_multiprocessing_resources() -> TypedFixture[None]:
    """Unlink all multiprocessing resources registered during a test."""
    yield
    tracker = _get_resource_tracker()
    if tracker is None:
        return
    raw_cache = cast(
        Mapping[str, str | tuple[str, str]], getattr(tracker, "_cache", {})
    )
    cache = dict(raw_cache)
    for name, rtype in cache.items():
        resource_type = rtype[0] if isinstance(rtype, tuple) else rtype
        with contextlib.suppress(Exception):
            resource_tracker.unregister(name, resource_type)
            tracker.maybe_unlink(name, resource_type)


@pytest.fixture(autouse=True)
def _cleanup_multiprocessing_queues(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[None]:
    """Ensure multiprocessing queues are closed and joined."""
    global _QUEUE_FACTORY
    _QUEUE_FACTORY = multiprocessing.Queue
    monkeypatch.setattr(multiprocessing, "Queue", _track_multiprocessing_queue)
    yield
    while _CREATED_QUEUES:
        q = _CREATED_QUEUES.pop()
        with contextlib.suppress(Exception):
            q.close()
        with contextlib.suppress(Exception):
            q.join_thread()
    _QUEUE_FACTORY = None
    _flush_resource_tracker_cache()


@pytest.fixture(autouse=True)
def _cleanup_multiprocessing_pools(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[None]:
    """Ensure multiprocessing pools are closed and joined."""
    created: list[multiprocessing.pool.Pool] = []
    seen_ids: set[int] = set()

    original_pool_init = multiprocessing.pool.Pool.__init__
    original_thread_pool_init = multiprocessing.pool.ThreadPool.__init__

    def _remember(instance: multiprocessing.pool.Pool) -> None:
        ident = id(instance)
        if ident not in seen_ids:
            seen_ids.add(ident)
            created.append(instance)

    def tracking_pool_init(
        self: multiprocessing.pool.Pool, *args: Any, **kwargs: Any
    ) -> None:
        _remember(self)
        original_pool_init(self, *args, **kwargs)

    def tracking_thread_pool_init(
        self: multiprocessing.pool.ThreadPool, *args: Any, **kwargs: Any
    ) -> None:
        _remember(self)
        original_thread_pool_init(self, *args, **kwargs)

    monkeypatch.setattr(
        multiprocessing.pool.Pool,
        "__init__",
        tracking_pool_init,
        raising=False,
    )
    monkeypatch.setattr(
        multiprocessing.pool.ThreadPool,
        "__init__",
        tracking_thread_pool_init,
        raising=False,
    )
    yield
    while created:
        pool = created.pop()
        with contextlib.suppress(Exception):
            pool.close()
        with contextlib.suppress(Exception):
            pool.terminate()
        with contextlib.suppress(Exception):
            pool.join()
    seen_ids.clear()
    _flush_resource_tracker_cache()


if importlib.util.find_spec("autoresearch") is None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    sys.path.insert(0, str(src_path))

# Ensure real dependencies are loaded before test stubs
import networkx  # noqa: F401,E402
import prometheus_client  # noqa: F401,E402
import rdflib  # noqa: F401,E402
import typer  # noqa: E402

import duckdb  # noqa: E402
import tests.stubs  # noqa: F401,E402
from autoresearch import cache, storage  # noqa: E402
from autoresearch.agents.registry import (  # noqa: E402
    AgentFactory,
    AgentRegistry,
)
from autoresearch.api import SLOWAPI_STUB  # noqa: E402
from autoresearch.api import reset_request_log  # noqa: E402
from autoresearch.api import app as api_app  # noqa: E402
from autoresearch.config.loader import ConfigLoader  # noqa: E402
from autoresearch.config.models import ConfigModel  # noqa: E402, F401
from autoresearch.extensions import VSSExtensionLoader  # noqa: E402
from autoresearch.llm.registry import LLMFactory  # noqa: E402
from autoresearch.models import QueryResponse  # noqa: E402, F401
from autoresearch.orchestration import metrics  # noqa: E402
from autoresearch.storage import (  # noqa: E402
    StorageContext,
    StorageManager,
)
from autoresearch.storage import set_delegate as set_storage_delegate  # noqa: E402

_orig_option = typer.Option


def _compat_option(*args, **kwargs):
    kwargs.pop("multiple", None)
    return _orig_option(*args, **kwargs)


typer.Option = _compat_option


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow")
    config.addinivalue_line("markers", "requires_nlp: mark test requiring NLP extras")


def reset_limiter_state() -> None:
    """Reset SlowAPI limiter state when using the real implementation."""
    if not SLOWAPI_STUB:
        limiter = getattr(api_app.state, "limiter", None)
        if limiter is not None:
            try:
                limiter.reset()
            except Exception:
                pass


# Ensure package can be imported without installation


def _module_available(name: str) -> bool:
    """Return True if a module is installed or provided via stubs."""
    try:
        if name in sys.modules:
            return True
        spec = importlib.util.find_spec(name)
    except Exception:
        return False
    return bool(spec and spec.origin)


def pytest_runtest_setup(item):
    if item.get_closest_marker("requires_ui") and not UI_AVAILABLE:
        pytest.skip("ui extra not installed")
    if item.get_closest_marker("requires_vss") and not VSS_AVAILABLE:
        pytest.skip("vss extra not installed")
    if item.get_closest_marker("requires_git") and not GITPYTHON_INSTALLED:
        pytest.skip("git extra not installed")
    if item.get_closest_marker("requires_analysis") and not POLARS_INSTALLED:
        pytest.skip("analysis extra not installed")
    if item.get_closest_marker("requires_llm") and not LLM_AVAILABLE:
        pytest.skip("llm extra not installed")
    if item.get_closest_marker("requires_parsers") and not PARSERS_AVAILABLE:
        pytest.skip("parsers extra not installed")
    if item.get_closest_marker("requires_nlp") and not NLP_AVAILABLE:
        pytest.skip("nlp extra not installed")
    if item.get_closest_marker("requires_gpu") and not GPU_AVAILABLE:
        pytest.skip("gpu extra not installed")
    if item.get_closest_marker("requires_distributed") and not REDIS_AVAILABLE:
        pytest.skip("redis not available")


GITPYTHON_INSTALLED = _module_available("git")
POLARS_INSTALLED = _module_available("polars")
PARSERS_AVAILABLE = _module_available("pdfminer")
LLM_AVAILABLE = _module_available("fastembed")
UI_AVAILABLE = _module_available("streamlit")
NLP_AVAILABLE = _module_available("spacy")


def _gpu_available() -> bool:
    """Check if GPU dependencies (BERTopic) are actually available."""
    try:
        from bertopic import BERTopic
        # Check if it's not the stub by checking the version
        return hasattr(BERTopic, '__version__') and BERTopic.__version__ != "0.0"
    except Exception:
        return False


GPU_AVAILABLE = _gpu_available()

# Provide a lightweight Redis service for distributed tests.
REDIS_URL = "redis://localhost:6379/0"
_fakeredis_server = None
_redis_factory: Callable[[], _RedisClient] | None = None
REDIS_AVAILABLE = False


def _init_redis() -> None:
    """Configure Redis client factory, falling back to fakeredis."""
    global REDIS_AVAILABLE, _redis_factory, _fakeredis_server
    try:
        import redis

        redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1).ping()

        def _make_client() -> _RedisClient:
            return cast(_RedisClient, redis.Redis.from_url(REDIS_URL))

        _redis_factory = _make_client
        REDIS_AVAILABLE = True
    except Exception:
        try:
            import fakeredis

            _fakeredis_server = fakeredis.FakeServer()

            def _make_fake_client() -> _RedisClient:
                return cast(
                    _RedisClient,
                    fakeredis.FakeStrictRedis(server=_fakeredis_server),
                )

            _redis_factory = _make_fake_client
            REDIS_AVAILABLE = True
        except Exception:
            REDIS_AVAILABLE = False


_init_redis()


@pytest.fixture(scope="session")
def redis_service() -> TypedFixture[object]:
    """Yield a Redis client backed by a lightweight service."""
    if not REDIS_AVAILABLE or _redis_factory is None:
        pytest.skip("redis not available")
    factory = _redis_factory
    assert factory is not None
    client = factory()
    try:
        yield client
    finally:
        with contextlib.suppress(Exception):
            client.flushdb()
            client.close()


VSS_AVAILABLE = _module_available("duckdb_extension_vss")


@pytest.fixture(autouse=True)
def stub_vss_extension_download(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
) -> TypedFixture[None]:
    """Prevent network calls when loading the DuckDB VSS extension."""
    if os.getenv("REAL_VSS_TEST") or request.node.get_closest_marker("real_vss"):
        yield
        return

    if "VECTOR_EXTENSION_PATH" not in os.environ:
        env_offline = Path(".env.offline")
        stub_path = None
        if env_offline.exists():
            for line in env_offline.read_text().splitlines():
                if line.startswith("VECTOR_EXTENSION_PATH="):
                    stub_path = Path(line.split("=", 1)[1]).resolve()
                    break
        if stub_path is None:
            stub_path = tmp_path / "vss.duckdb_extension"
            stub_path.write_text("stub")
        monkeypatch.setenv("VECTOR_EXTENSION_PATH", str(stub_path))
    else:
        stub_path = None

    monkeypatch.setattr(VSSExtensionLoader, "load_extension", lambda _c: True)
    monkeypatch.setattr(
        VSSExtensionLoader,
        "verify_extension",
        lambda _c, verbose=True: True,
    )
    yield
    if stub_path:
        monkeypatch.delenv("VECTOR_EXTENSION_PATH", raising=False)


@pytest.fixture(autouse=True)
def reset_config_loader_instance() -> TypedFixture[None]:
    """Reset ConfigLoader singleton before each test."""
    ConfigLoader.reset_instance()
    yield
    ConfigLoader.reset_instance()


@pytest.fixture(autouse=True)
def isolate_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TypedFixture[None]:
    """Use temporary working directory and cache file for each test."""
    monkeypatch.chdir(tmp_path)
    cache_path = tmp_path / "cache.json"
    monkeypatch.setenv("TINYDB_PATH", str(cache_path))
    cache.teardown(remove_file=True)
    cache.setup(str(cache_path))
    yield
    cache.teardown(remove_file=True)
    if cache_path.exists():
        cache_path.unlink()
    monkeypatch.delenv("TINYDB_PATH", raising=False)


@pytest.fixture(autouse=True)
def reset_registries() -> TypedFixture[None]:
    """Restore global registries after each test."""
    agent_reg = AgentRegistry._registry.copy()
    agent_fact = AgentFactory._registry.copy()
    llm_reg = LLMFactory._registry.copy()
    AgentFactory.set_delegate(None)
    set_storage_delegate(None)
    yield
    AgentFactory._instances.clear()
    AgentRegistry._registry = agent_reg
    AgentFactory._registry = agent_fact
    LLMFactory._registry = llm_reg


AgentFactory.set_delegate(None)
set_storage_delegate(None)


@pytest.fixture
def duckdb_path(tmp_path: Path) -> TypedFixture[str]:
    """Create a fresh DuckDB schema and return its path."""
    db_file = tmp_path / "kg.duckdb"
    storage.teardown(remove_db=True)
    initializer = getattr(StorageManager, "initialize_schema", storage.initialize_storage)
    initializer(str(db_file))
    yield str(db_file)
    storage.teardown(remove_db=True)


@pytest.fixture
def ensure_duckdb_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TypedFixture[str]:
    """Ensure StorageManager setup creates required DuckDB tables."""
    db_file = tmp_path / "kg.duckdb"
    StorageManager.teardown(remove_db=True)
    monkeypatch.setattr(
        storage.DuckDBStorageBackend, "_initialize_schema_version", lambda self: None
    )
    monkeypatch.setattr(storage.DuckDBStorageBackend, "_run_migrations", lambda self: None)
    StorageManager.setup(str(db_file))
    yield str(db_file)
    StorageManager.teardown(remove_db=True)


@pytest.fixture
def storage_manager(duckdb_path: str) -> TypedFixture[ModuleType]:
    """Initialize storage using a prepared DuckDB path and clean up."""
    storage.initialize_storage(duckdb_path)
    set_storage_delegate(storage.StorageManager)
    yield storage
    storage.teardown(remove_db=True)
    set_storage_delegate(None)


@pytest.fixture
def config_watcher() -> TypedFixture[ConfigLoader]:
    """Provide a ConfigLoader that is cleaned up after use."""
    loader = ConfigLoader()
    yield loader
    loader.stop_watching()


@pytest.fixture(autouse=True)
def stop_config_watcher(
    monkeypatch: pytest.MonkeyPatch,
) -> TypedFixture[None]:
    """Ensure ConfigLoader watcher threads are cleaned up quickly."""

    def fast_stop(self):
        if self._watch_thread and self._watch_thread.is_alive():
            self._stop_event.set()
            self._watch_thread.join(timeout=0.1)

    monkeypatch.setattr(ConfigLoader, "stop_watching", fast_stop, raising=False)

    ConfigLoader().stop_watching()
    yield
    ConfigLoader().stop_watching()


@pytest.fixture(autouse=True)
def reset_rate_limiting() -> TypedFixture[None]:
    """Clear API rate limiter state and request log before each test."""
    reset_limiter_state()
    reset_request_log()
    yield
    reset_limiter_state()
    reset_request_log()


@pytest.fixture(autouse=True)
def reset_orchestration_metrics() -> TypedFixture[None]:
    """Reset global orchestration counters before and after each test."""
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


@pytest.fixture(autouse=True)
def cleanup_storage() -> TypedFixture[None]:
    """Remove any persistent storage state between tests."""
    # Use module-level teardown to avoid delegate recursion
    def _safe_teardown(stage: str) -> None:
        try:
            storage.teardown(remove_db=True)
        except Exception:  # pragma: no cover - defensive cleanup
            logger.warning(
                "Storage teardown failed during %s cleanup", stage, exc_info=True
            )

    _safe_teardown("setup")
    yield
    _safe_teardown("teardown")


@pytest.fixture(autouse=True)
def initialize_storage(
    request: pytest.FixtureRequest, tmp_path: Path, cleanup_storage: None
) -> TypedFixture[None]:
    """Create storage tables for storage-related tests."""
    filename = request.node.path.name
    if filename.startswith("test_storage_") or filename == "test_main_backup_commands.py":
        if not hasattr(duckdb.DuckDBPyConnection, "fetchone"):

            def _fetchone(self: Any):
                rows = self.fetchall()
                return rows[0] if rows else None

            setattr(cast(Any, duckdb.DuckDBPyConnection), "fetchone", _fetchone)
        storage.initialize_storage(str(tmp_path / "kg.duckdb"))
    yield


@pytest.fixture(autouse=True)
def restore_sys_modules() -> TypedFixture[None]:
    """Remove non-module entries from ``sys.modules`` between tests."""
    orig_modules = {k: v for k, v in sys.modules.items() if isinstance(v, ModuleType)}
    for name, module in list(sys.modules.items()):
        if not isinstance(module, ModuleType):
            sys.modules.pop(name, None)
    yield
    for name, module in list(sys.modules.items()):
        if not isinstance(module, ModuleType) or name not in orig_modules:
            sys.modules.pop(name, None)
    for name, module in orig_modules.items():
        sys.modules.setdefault(name, module)


@pytest.fixture
def bdd_context():
    """Mutable mapping for sharing data between BDD steps."""
    return {}


@pytest.fixture
def mock_storage_components():
    """Mock the storage components in ``StorageManager.context``.

    This fixture provides a function that creates a context manager for patching
    the storage components with mock objects.

    Usage:
        def test_something(mock_storage_components):
            # Create mocks if needed
            mock_graph = MagicMock()

            # Use the context manager
            with mock_storage_components(graph=mock_graph):
                # Test code that uses the storage components

    Args:
        graph: Optional mock graph to use (default: None)
        db_backend: Optional mock database backend to use (default: None)
        rdf: Optional mock RDF store to use (default: None)

    Returns:
        A function that creates a context manager for patching storage components
    """

    class StorageComponentsMocker:
        def __init__(self, **kwargs):
            # Store the components to patch
            self.graph = kwargs.get("graph", None)
            self.db_backend = kwargs.get("db_backend", None)
            # For backward compatibility, also accept 'db' parameter
            if "db" in kwargs and "db_backend" not in kwargs:
                self.db_backend = kwargs.get("db", None)
            self.rdf = kwargs.get("rdf", None)

            # Keep track of which components were explicitly passed
            self.has_graph = "graph" in kwargs
            self.has_db_backend = "db_backend" in kwargs or "db" in kwargs
            self.has_rdf = "rdf" in kwargs

            self.patches: list[_patch] = []

        def __enter__(self):
            # Add patches for all components that were explicitly passed
            # This allows patching a component to None
            import autoresearch.storage as storage

            if self.has_graph:
                self.patches.append(
                    patch.object(storage.StorageManager.context, "graph", self.graph)
                )
            if self.has_db_backend:
                self.patches.append(
                    patch.object(storage.StorageManager.context, "db_backend", self.db_backend)
                )
            if self.has_rdf:
                self.patches.append(
                    patch.object(storage.StorageManager.context, "rdf_store", self.rdf)
                )

            # Start all patches
            for p in self.patches:
                p.start()

            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # Stop all patches in reverse order
            for p in reversed(self.patches):
                p.stop()

    def create_mocker(**kwargs):
        return StorageComponentsMocker(**kwargs)

    return create_mocker


@pytest.fixture
def storage_context_factory(tmp_path):
    """Return a factory for creating isolated ``StorageContext`` instances."""

    from contextlib import contextmanager
    from uuid import uuid4

    @contextmanager
    def _make():
        ctx = StorageContext()
        db_file = tmp_path / f"{uuid4()}.duckdb"
        storage.initialize_storage(str(db_file), context=ctx)
        try:
            yield ctx
        finally:
            StorageManager.teardown(remove_db=True, context=ctx)

    return _make


@pytest.fixture
def mock_config():
    """Mock the ConfigLoader.config object.

    This fixture provides a function that creates a context manager for patching
    the ConfigLoader.config property with a mock object.

    Usage:
        def test_something(mock_config):
            # Create a mock config if needed
            config = MagicMock()
            config.some_property = "some value"

            # Use the context manager
            with mock_config(config=config):
                # Test code that uses ConfigLoader.config

    Args:
        config: Optional mock config to use (default: MagicMock())

    Returns:
        A function that creates a context manager for patching ConfigLoader.config
    """

    class ConfigMocker:
        def __init__(self, **kwargs):
            self.config = kwargs.get("config", MagicMock())
            self.patcher: _patch | None = None

        def __enter__(self):
            self.patcher = patch("autoresearch.config.loader.ConfigLoader.config", self.config)
            self.patcher.start()
            return self.config

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.patcher is not None:
                self.patcher.stop()

    def create_mocker(**kwargs):
        return ConfigMocker(**kwargs)

    return create_mocker


@pytest.fixture
def assert_error():
    """Fixture for asserting error messages and causes.

    This fixture provides a function for asserting that an exception has the
    expected error message and cause.

    Usage:
        def test_something(assert_error):
            with pytest.raises(SomeError) as excinfo:
                # Code that raises an error
            assert_error(excinfo, "Expected error message", has_cause=True)

    Returns:
        A function for asserting error messages and causes
    """

    def _assert_error(excinfo, expected_message, has_cause=False):
        """Assert that an exception has the expected error message and cause.

        Args:
            excinfo: The pytest.raises context
            expected_message: The expected error message (substring)
            has_cause: Whether the exception should have a cause
        """
        assert expected_message in str(excinfo.value)
        if has_cause:
            assert excinfo.value.__cause__ is not None
        else:
            assert excinfo.value.__cause__ is None

    return _assert_error


@pytest.fixture
def claim_factory():
    """Factory for creating simple claim dictionaries."""

    class ClaimFactory:
        def create_claim(self, claim_id=None, embedding=None):
            if claim_id is None:
                claim_id = f"claim-{uuid4()}"
            if embedding is None:
                embedding = [0.1] * 384
            return {
                "id": claim_id,
                "type": "fact",
                "content": "test claim",
                "confidence": 0.9,
                "attributes": {"verified": True},
                "relations": [
                    {
                        "src": claim_id,
                        "dst": "source-1",
                        "rel": "cites",
                        "weight": 1.0,
                    }
                ],
                "embedding": embedding,
            }

    return ClaimFactory()


@pytest.fixture
def realistic_claims(claim_factory):
    """Provide a batch of sample claims with varied content."""

    claims = [
        claim_factory.create_claim(claim_id="claim-1", embedding=[0.1] * 384),
        claim_factory.create_claim(claim_id="claim-2", embedding=[0.2] * 384),
        claim_factory.create_claim(claim_id="claim-3", embedding=[0.3] * 384),
    ]
    for idx, claim in enumerate(claims, start=1):
        claim["content"] = f"Realistic claim number {idx}"
    return claims


@pytest.fixture
def realistic_claim_batch(
    claim_factory,
) -> TypedFixture[list[dict[str, object]]]:
    """Yield a diverse batch of realistic claim dictionaries."""

    claims = [
        claim_factory.create_claim(claim_id="claim-a", embedding=[0.1] * 384),
        claim_factory.create_claim(claim_id="claim-b", embedding=[0.2] * 384),
        claim_factory.create_claim(claim_id="claim-c", embedding=[0.3] * 384),
    ]
    claims[0]["relations"] = [{"src": "claim-a", "dst": "source-1", "rel": "cites", "weight": 1.0}]
    claims[1]["relations"] = [
        {"src": "claim-b", "dst": "claim-a", "rel": "supports", "weight": 0.8}
    ]
    claims[2]["relations"] = [
        {"src": "claim-c", "dst": "claim-a", "rel": "contradicts", "weight": 0.5},
        {"src": "claim-c", "dst": "source-2", "rel": "cites", "weight": 1.0},
    ]
    yield claims


@pytest.fixture
def sample_eval_data():
    """Load the sample evaluation CSV for search weight tests."""
    import_or_skip("fastembed")
    from autoresearch.search import Search

    path = Path(__file__).resolve().parent / "data" / "eval" / "sample_eval.csv"
    return Search.load_evaluation_data(path)


@pytest.fixture
def dummy_llm_adapter() -> TypedFixture[object]:
    """Register and provide a dummy LLM adapter for tests."""
    from autoresearch.llm.adapters import DummyAdapter

    LLMFactory.register("dummy", DummyAdapter)
    yield DummyAdapter()
    LLMFactory._registry.pop("dummy", None)


@pytest.fixture
def mock_llm_adapter(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[object]:
    """Provide a configurable mock LLM adapter for tests."""

    from autoresearch.llm.adapters import DummyAdapter

    class MockAdapter(DummyAdapter):
        def __init__(self, responses=None):
            self.responses = responses or {}

        def generate(self, prompt: str, model: str | None = None, **kwargs):
            if prompt in self.responses:
                return self.responses[prompt]
            return f"Mocked response for {prompt}"

    LLMFactory.register("mock", MockAdapter)
    adapter = MockAdapter()
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: adapter)
    yield adapter
    LLMFactory._registry.pop("mock", None)


@pytest.fixture
def flexible_llm_adapter(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> TypedFixture[object]:
    """Register a configurable LLM adapter returning custom prompt responses."""

    from autoresearch.llm.adapters import DummyAdapter

    class FlexibleAdapter(DummyAdapter):
        def __init__(self, responses: dict[str, str] | None = None) -> None:
            self.responses: dict[str, str] = responses or {}

        def set_responses(self, mapping: dict[str, str]) -> None:
            self.responses.update(mapping)

        def generate(self, prompt: str, model: str | None = None, **kwargs):
            if prompt in self.responses:
                return self.responses[prompt]
            return super().generate(prompt, model=model, **kwargs)

    responses = getattr(request, "param", None)
    LLMFactory.register("flexible", FlexibleAdapter)
    adapter = FlexibleAdapter(responses)
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: adapter)
    monkeypatch.setattr("autoresearch.llm.get_pooled_adapter", lambda name: adapter)
    yield adapter
    LLMFactory._registry.pop("flexible", None)


@pytest.fixture
def cli_runner() -> CliRunner:
    """Return a Typer CLI runner configured for the tests."""
    return CliRunner()


@pytest.fixture
def api_client():
    """Return a FastAPI test client."""
    return TestClient(api_app)


@pytest.fixture
def api_client_factory() -> Callable[[dict[str, str] | None], TestClient]:
    """Return a factory for creating TestClient instances with optional headers."""

    def _make(headers: dict[str, str] | None = None) -> TestClient:
        client = TestClient(api_app)
        if headers:
            client.headers.update(headers)
        return client

    return _make


@pytest.fixture
def mock_run_query():
    """Return a simple Orchestrator.run_query stub for tests."""

    def _mock_run_query(
        self,
        query,
        config,
        callbacks=None,
        *,
        agent_factory=None,
        storage_manager=None,
        visualize=False,
    ):
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={"m": 1})

    return _mock_run_query


SAMPLE_TOML = """
[core]
backend = "lmstudio"
loops = 1
ram_budget_mb = 512

[search]
backends = []

[search.context_aware]
enabled = false
"""

SAMPLE_ENV = """OPENAI_API_KEY=your-openai-api-key
SERPER_API_KEY=your-serper-api-key
"""


@pytest.fixture()
def example_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write a sample ``.env`` and populate required variables."""
    env_path = tmp_path / ".env"
    env_path.write_text(SAMPLE_ENV)
    monkeypatch.setenv("SERPER_API_KEY", "your-serper-api-key")
    monkeypatch.setenv("OPENAI_API_KEY", "your-openai-api-key")
    return env_path


@pytest.fixture()
def example_autoresearch_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, example_env_file: Path
) -> Path:
    """Provide a realistic ``autoresearch.toml`` for tests."""
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / "autoresearch.toml"
    cfg_path.write_text(SAMPLE_TOML)
    return cfg_path


@pytest.fixture()
def temp_config(example_autoresearch_toml: Path) -> Path:
    """Compatibility alias for legacy tests expecting ``temp_config``."""
    return example_autoresearch_toml


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Clear shared memory segments and tracker state after the test session."""

    del session, exitstatus  # Unused but part of the hook signature.
    if shared_memory is not None:
        cleanup = getattr(shared_memory, "_cleanup", None)
        if callable(cleanup):
            with contextlib.suppress(Exception):
                cleanup()
    _flush_resource_tracker_cache()
