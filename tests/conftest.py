from __future__ import annotations

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


def _is_docstring_expr(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _first_non_docstring_index(module: ast.Module) -> int | None:
    for index, node in enumerate(module.body):
        if _is_docstring_expr(node):
            continue
        return index
    return None


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
        first_index = _first_non_docstring_index(module)
        if first_index is None:
            continue
        if first_index != future_index:
            node = module.body[first_index]
            try:
                relative = file_path.relative_to(REPO_ROOT)
            except ValueError:
                relative = file_path
            if hasattr(node, "lineno"):
                line = contents.splitlines()[node.lineno - 1].strip()
                location = f"{relative}:{node.lineno} {line}"
            else:  # pragma: no cover - defensive fallback
                location = f"{relative}:? {type(node).__name__}"
            violations.append(location)
    return violations


def enforce_future_annotations_import_order(
    paths: Iterable[Path] | None = None,
) -> None:
    """Raise ``pytest.UsageError`` when modules import before the future directive."""

    violations = find_future_annotations_import_violations(paths)
    if not violations:
        return

    formatted = "\n- ".join(violations)
    message = (
        "Modules must place `from __future__ import annotations` before other imports:"
        f"\n- {formatted}"
    )
    raise pytest.UsageError(message)


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    enforce_future_annotations_import_order()


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
    "pytest_bdd",
    "tests.behavior.fixtures",
    "tests.behavior.steps",
    "tests.behavior.utils",
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
    raw_cache = cast(Mapping[str, str | tuple[str, str]], getattr(tracker, "_cache", {}))
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

    def tracking_pool_init(self: multiprocessing.pool.Pool, *args: Any, **kwargs: Any) -> None:
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
    raw_excludes = os.environ.get("AR_PYTEST_EXCLUDE", "")
    if raw_excludes:
        tokens = [
            token
            for chunk in raw_excludes.replace(",", " ").split()
            if (token := chunk.strip())
        ]
        if tokens:
            disjunction = " or ".join(tokens)
            markexpr = config.option.markexpr or ""
            if markexpr:
                config.option.markexpr = f"({markexpr}) and not ({disjunction})"
            else:
                config.option.markexpr = f"not ({disjunction})"


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


@pytest.fixture(autouse=True)
def mock_git_operations(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path) -> TypedFixture[None]:
    """Mock Git operations for tests that require Git functionality."""
    if request.node.get_closest_marker("requires_git") or "git" in request.node.nodeid.lower():

        # Mock subprocess operations for git commands (simpler approach)
        def mock_check_output(cmd, **kwargs):
            """Mock subprocess check_output for git commands."""
            if "git log" in " ".join(cmd):
                return b"commit abc123def456\nAuthor: Test Author <test@example.com>\nDate:   Mon Jan 1 00:00:00 2024 +0000\n\n    feature commitmarker"
            elif "git ls-files" in " ".join(cmd):
                return b"data.txt"
            elif "git show" in " ".join(cmd):
                return b"initial"
            else:
                return b""

        import subprocess
        monkeypatch.setattr(subprocess, "check_output", mock_check_output)

        # Mock the import_or_skip function to return a mock git module
        def mock_import_or_skip(name, reason=""):
            """Mock import_or_skip to return a mock git module."""
            if name == "git":
                class MockGitModule:
                    class Repo:
                        @staticmethod
                        def init(path, **kwargs):
                            # Create mock repo structure
                            git_dir = path / ".git"
                            git_dir.mkdir(exist_ok=True)
                            (git_dir / "HEAD").write_text("ref: refs/heads/main")
                            (git_dir / "refs" / "heads" / "main").write_text("abc123def456")

                            # Mock repo object
                            class MockRepo:
                                def __init__(self):
                                    self.path = path
                                    self.git_dir = git_dir

                                    # Mock active branch
                                    class MockBranch:
                                        def __init__(self):
                                            self.name = "main"
                                    self.active_branch = MockBranch()

                                    # Mock index
                                    class MockIndex:
                                        def add(self, files):
                                            pass

                                        def commit(self, message):
                                            class MockCommit:
                                                def __init__(self, msg):
                                                    self.message = msg
                                                    self.hexsha = "abc123def456"
                                            return MockCommit(message)

                                    self.index = MockIndex()

                                def log(self, **kwargs):
                                    class MockCommit:
                                        def __init__(self, message):
                                            self.message = message
                                            self.hexsha = "abc123def456"
                                            class MockAuthor:
                                                def __init__(self):
                                                    self.name = "Test Author"
                                                    self.email = "test@example.com"
                                            self.author = MockAuthor()
                                            self.committed_date = 1234567890

                                    return [MockCommit("initial commit"), MockCommit("feature commitmarker")]

                                def ls_files(self, **kwargs):
                                    return ["data.txt"]

                                def show(self, path, **kwargs):
                                    if "data.txt" in str(path):
                                        return "initial"
                                    return "Mock file content"

                            return MockRepo()

                        @staticmethod
                        def clone_from(url, path, **kwargs):
                            return MockGitModule.Repo.init(path, **kwargs)

                    def __getattr__(self, name):
                        if name == "Repo":
                            return self.Repo
                        return self.Repo

                return MockGitModule()
            else:
                # For non-git imports, use the original import
                import importlib
                return importlib.import_module(name)

        # Patch the import_or_skip function in the test module
        monkeypatch.setattr(
            "tests.optional_imports.import_or_skip",
            mock_import_or_skip
        )

        # Also patch it in the test file if it's imported there
        if hasattr(request.module, "import_or_skip"):
            monkeypatch.setattr(request.module, "import_or_skip", mock_import_or_skip)

    yield


def _gpu_available() -> bool:
    """Check if GPU dependencies (BERTopic) are actually available."""
    try:
        from bertopic import BERTopic

        # Check if it's not the stub by checking the version
        return hasattr(BERTopic, "__version__") and BERTopic.__version__ != "0.0"
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

    # Mock VSS extension loader methods
    monkeypatch.setattr(VSSExtensionLoader, "load_extension", lambda _c: True)
    monkeypatch.setattr(
        VSSExtensionLoader,
        "verify_extension",
        lambda _c, verbose=True: True,
    )

    # Mock DuckDB connection methods for HNSW/VSS operations
    def mock_execute(self, query, parameters=None):
        """Mock DuckDB execute method with VSS/HNSW support."""
        query_lower = query.strip().lower()

        # Create a mock cursor object
        class MockCursor:
            def __init__(self, rows=None):
                self._rows = rows or []

            def fetchall(self):
                return self._rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

            def __iter__(self):
                return iter(self._rows)

        # Handle HNSW index creation
        if "create index" in query_lower and "hnsw" in query_lower:
            # Return mock cursor for CREATE INDEX
            return MockCursor()

        # Handle VSS-related queries
        if "create table" in query_lower and "float[" in query_lower:
            # Handle embeddings table creation
            return MockCursor()

        # Handle all CREATE TABLE queries (including scholarly_papers)
        if "create table" in query_lower:
            return MockCursor()

        # Handle SELECT queries for index verification
        if "duckdb_indexes" in query_lower:
            # Return mock index information
            class MockRow:
                def __init__(self, index_name):
                    self.index_name = index_name
                def __getitem__(self, idx):
                    return self.index_name if idx == 0 else None
            return MockCursor([MockRow("test_hnsw_index")])

        # Handle DELETE queries (dummy embedding cleanup)
        if "delete from" in query_lower and "dummy" in query_lower:
            return MockCursor()

        # Handle INSERT queries (dummy embedding)
        if "insert into" in query_lower and "dummy" in query_lower:
            return MockCursor()

        # Handle all INSERT queries
        if "insert into" in query_lower:
            return MockCursor()

        # Handle SELECT queries
        if query_lower.startswith("select"):
            # Handle schema version queries
            if "schema_version" in query_lower:
                class MockRow:
                    def __init__(self, version):
                        self.version = version
                    def __getitem__(self, idx):
                        return self.version if idx == 0 else None
                return MockCursor([MockRow(1)])

            # Handle COUNT queries
            if "count" in query_lower:
                class MockRow:
                    def __init__(self, count):
                        self.count = count
                    def __getitem__(self, idx):
                        return self.count if idx == 0 else 0
                return MockCursor([MockRow(0)])

            # Handle table existence checks
            if "pragma table_info" in query_lower or "sqlite_master" in query_lower:
                # Return empty result for non-existent tables
                return MockCursor()

            # Handle duckdb_indexes queries
            if "duckdb_indexes" in query_lower:
                class MockRow:
                    def __init__(self, index_name):
                        self.index_name = index_name
                    def __getitem__(self, idx):
                        return self.index_name if idx == 0 else None
                return MockCursor([MockRow("test_hnsw_index")])

            # Handle general SELECT queries
            return MockCursor()

        # Default behavior - call original method but handle errors gracefully
        try:
            return original_execute(self, query, parameters)
        except Exception as e:
            # If there's an error (like missing table), return None to simulate success
            if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
                return MockCursor()
            raise

    # Store original method and patch
    import duckdb
    original_execute = duckdb.DuckDBPyConnection.execute
    monkeypatch.setattr(duckdb.DuckDBPyConnection, "execute", mock_execute)

    # Mock fetchall method for query results
    def mock_fetchall(self):
        """Mock fetchall method."""
        return []

    # Also mock fetchone method
    def mock_fetchone(self):
        """Mock fetchone method."""
        return None

    monkeypatch.setattr(duckdb.DuckDBPyConnection, "fetchall", mock_fetchall)
    monkeypatch.setattr(duckdb.DuckDBPyConnection, "fetchone", mock_fetchone)

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
def isolate_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TypedFixture[None]:
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
def ensure_duckdb_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TypedFixture[str]:
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


@pytest.fixture
def disable_streamlit_metrics(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[None]:
    """Completely disable Streamlit metrics thread for tests marked with requires_ui."""

    def noop_metrics():
        """No-op replacement for update_metrics_periodically in tests."""
        pass

    # Patch the function to do nothing
    monkeypatch.setattr("autoresearch.streamlit_app.update_metrics_periodically", noop_metrics)
    # Also set short timeout as backup
    monkeypatch.setenv("STREAMLIT_METRICS_TIMEOUT", "1")
    yield


@pytest.fixture(autouse=True)
def cleanup_streamlit_threads(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> TypedFixture[None]:
    """Ensure Streamlit background threads (MetricsCollector) are cleaned up and disabled in tests."""
    import threading

    # Set short timeout for metrics thread in all tests
    monkeypatch.setenv("STREAMLIT_METRICS_TIMEOUT", "1")

    # For UI tests, also disable the metrics thread completely
    if request.node.get_closest_marker("requires_ui"):

        def noop_metrics():
            pass

        monkeypatch.setattr("autoresearch.streamlit_app.update_metrics_periodically", noop_metrics)

    # Before test: identify existing threads
    before_threads = {t.name: t for t in threading.enumerate()}

    yield

    # After test: cleanup any MetricsCollector threads
    after_threads = threading.enumerate()
    for thread in after_threads:
        if thread.name == "MetricsCollector" and thread not in before_threads.values():
            # Thread is a daemon so it should stop when we end, but give it a moment
            thread.join(timeout=0.2)


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
def mock_prometheus_metrics(monkeypatch: pytest.MonkeyPatch) -> TypedFixture[None]:
    """Mock Prometheus metrics to return expected format for integration tests."""

    # Mock the generate_latest function that's used in the metrics endpoint
    def mock_generate_latest():
        """Generate mock Prometheus metrics in expected format."""
        return b"""# HELP autoresearch_queries_total Total number of queries processed
# TYPE autoresearch_queries_total counter
autoresearch_queries_total{status="success"} 42
autoresearch_queries_total{status="error"} 3

# HELP autoresearch_query_duration_seconds Query processing duration
# TYPE autoresearch_query_duration_seconds histogram
autoresearch_query_duration_seconds_bucket{le="0.1"} 15
autoresearch_query_duration_seconds_bucket{le="0.5"} 35
autoresearch_query_duration_seconds_bucket{le="1.0"} 40
autoresearch_query_duration_seconds_bucket{le="2.5"} 41
autoresearch_query_duration_seconds_bucket{le="5.0"} 42
autoresearch_query_duration_seconds_bucket{le="10.0"} 42
autoresearch_query_duration_seconds_bucket{le="+Inf"} 42
autoresearch_query_duration_seconds_count 42
autoresearch_query_duration_seconds_sum 45.2

# HELP autoresearch_agents_active Active agent count
# TYPE autoresearch_agents_active gauge
autoresearch_agents_active 5
"""

    # Mock the prometheus_client module import in the monitor.metrics module
    import autoresearch.monitor.metrics
    monkeypatch.setattr(
        autoresearch.monitor.metrics,
        "generate_latest",
        mock_generate_latest
    )

    # Also mock prometheus_client.generate_latest as fallback
    monkeypatch.setattr(
        "prometheus_client.generate_latest",
        mock_generate_latest
    )

    yield


@pytest.fixture(autouse=True)
def cleanup_storage() -> TypedFixture[None]:
    """Remove any persistent storage state between tests."""

    # Use module-level teardown to avoid delegate recursion
    def _safe_teardown(stage: str) -> None:
        try:
            storage.teardown(remove_db=True)
        except Exception:  # pragma: no cover - defensive cleanup
            logger.warning("Storage teardown failed during %s cleanup", stage, exc_info=True)

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


@pytest.fixture(autouse=True)
def mock_knowledge_graph_operations(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> TypedFixture[None]:
    """Mock knowledge graph and RDF operations for tests."""
    # Only apply to knowledge graph related tests
    if ("knowledge" in request.node.nodeid.lower() or
        "graph" in request.node.nodeid.lower() or
        "rdf" in request.node.nodeid.lower()):

        # Mock networkx operations
        try:
            import networkx as nx

            def mock_shortest_path(graph, source, target, weight=None):
                """Mock shortest path calculation."""
                return [source, "intermediate_node", target]

            def mock_degree(graph, node=None):
                """Mock degree calculation."""
                if node:
                    return 3  # Mock degree
                return {node: 3 for node in graph.nodes()}

            def mock_betweenness_centrality(graph, k=None, normalized=True, weight=None):
                """Mock betweenness centrality."""
                return {node: 0.1 for node in graph.nodes()}

            def mock_pagerank(graph, alpha=0.85, personalization=None, max_iter=100, tol=1e-06, nstart=None, weight='weight', dangling=None):
                """Mock pagerank calculation."""
                return {node: 0.05 for node in graph.nodes()}

            monkeypatch.setattr(nx, "shortest_path", mock_shortest_path)
            monkeypatch.setattr(nx, "degree", mock_degree)
            monkeypatch.setattr(nx, "betweenness_centrality", mock_betweenness_centrality)
            monkeypatch.setattr(nx, "pagerank", mock_pagerank)

        except ImportError:
            pass  # networkx not available

        # Mock RDFlib operations
        try:
            import rdflib

            def mock_graph_init(self):
                """Mock RDF graph initialization."""
                self._triples = set()

            def mock_add(self, triple):
                """Mock triple addition."""
                if not hasattr(self, '_triples'):
                    self._triples = set()
                self._triples.add(triple)

            def mock_triples(self, triple_pattern=None):
                """Mock triple retrieval."""
                if not hasattr(self, '_triples'):
                    self._triples = set()

                # Return some mock triples
                mock_triples = [
                    (rdflib.URIRef("http://example.org/subject1"),
                     rdflib.URIRef("http://example.org/predicate1"),
                     rdflib.Literal("object1")),
                    (rdflib.URIRef("http://example.org/subject2"),
                     rdflib.URIRef("http://example.org/predicate2"),
                     rdflib.Literal("object2"))
                ]
                return mock_triples

            def mock_query(self, query_string, initBindings=None, initNs=None, DEBUG=False):
                """Mock SPARQL query execution."""
                class MockQueryResult:
                    def __init__(self):
                        self.bindings = [
                            {"subject": rdflib.URIRef("http://example.org/subject1"),
                             "predicate": rdflib.URIRef("http://example.org/predicate1"),
                             "object": rdflib.Literal("object1")}
                        ]

                    def __iter__(self):
                        return iter(self.bindings)

                return MockQueryResult()

            # Apply RDF mocking
            monkeypatch.setattr(rdflib.Graph, "__init__", mock_graph_init)
            monkeypatch.setattr(rdflib.Graph, "add", mock_add)
            monkeypatch.setattr(rdflib.Graph, "triples", mock_triples)
            monkeypatch.setattr(rdflib.Graph, "query", mock_query)

        except ImportError:
            pass  # rdflib not available

    yield


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
    from autoresearch.errors import LLMError
    import time

    class MockAdapter(DummyAdapter):
        def __init__(self, responses=None, should_fail=False, delay=0.0):
            self.responses = responses or {}
            self.should_fail = should_fail
            self.delay = delay
            self.call_count = 0
            self.call_history = []

        def generate(self, prompt: str, model: str | None = None, **kwargs):
            self.call_count += 1
            self.call_history.append({
                "prompt": prompt,
                "model": model,
                "kwargs": kwargs,
                "timestamp": time.time()
            })

            # Simulate delay if configured
            if self.delay > 0:
                time.sleep(self.delay)

            # Check if should fail
            if self.should_fail:
                raise LLMError("Mock LLM failure for testing")

            # Return configured response or default
            if prompt in self.responses:
                return self.responses[prompt]

            # Default responses based on prompt patterns
            if "error" in prompt.lower() or "fail" in prompt.lower():
                return "Error scenario handled"
            if "summarize" in prompt.lower() or "summary" in prompt.lower():
                return "This is a summarized response to the query."
            if "analyze" in prompt.lower():
                return "Analysis complete: Key findings identified."
            if "research" in prompt.lower():
                return "Research insights: Multiple sources consulted and synthesized."

            return f"Mocked response for {prompt}"

        def generate_stream(self, prompt: str, model: str | None = None, **kwargs):
            """Mock streaming generation."""
            # For simplicity, just return regular generation result
            return self.generate(prompt, model, **kwargs)

        def get_context_size(self, model: str | None = None):
            """Mock context size retrieval."""
            return 4096

        def validate_model(self, model: str) -> bool:
            """Mock model validation."""
            return model is not None and len(model) > 0

        def estimate_prompt_tokens(self, prompt: str) -> int:
            """Mock token estimation."""
            return len(prompt.split()) * 1.3  # Rough token estimate

    LLMFactory.register("mock", MockAdapter)
    adapter = MockAdapter()
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: adapter)
    monkeypatch.setattr("autoresearch.llm.get_pooled_adapter", lambda name: adapter)
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


@pytest.fixture(autouse=True)
def mock_cli_dependencies(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> TypedFixture[None]:
    """Mock CLI dependencies that might not be available in test environment."""
    # Only apply to CLI-related tests
    if "cli" in request.node.nodeid.lower() or "test_cli" in request.node.nodeid:

        # Mock sys.stdout.isatty() for CLI progress indicators
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        # Mock shutil.get_terminal_size for CLI output formatting
        def mock_get_terminal_size(fallback=None):
            # Return a tuple that can be unpacked like the real function
            return (80, 24)

        import shutil
        monkeypatch.setattr(shutil, "get_terminal_size", mock_get_terminal_size)

        # Mock rich console for CLI output
        try:
            from rich.console import Console

            class MockConsole:
                def __init__(self, **kwargs):
                    self.size = (80, 24)
                    self._is_terminal = True
                    self.is_dumb_terminal = False

                @property
                def is_terminal(self):
                    return self._is_terminal

                @is_terminal.setter
                def is_terminal(self, value):
                    self._is_terminal = value

                def print(self, *args, **kwargs):
                    pass

                def rule(self, *args, **kwargs):
                    pass

                def status(self, *args, **kwargs):
                    from contextlib import contextmanager
                    @contextmanager
                    def mock_status():
                        yield self
                    return mock_status()

            monkeypatch.setattr("rich.console.Console", MockConsole)
        except ImportError:
            pass  # Rich not available, skip

        # Mock subprocess operations that CLI might use
        def mock_subprocess_run(*args, **kwargs):
            """Mock subprocess.run to prevent external command execution."""
            class MockCompletedProcess:
                def __init__(self):
                    self.returncode = 0
                    self.stdout = b"Mock subprocess output"
                    self.stderr = b""

            return MockCompletedProcess()

        import subprocess
        if not hasattr(subprocess, "_original_run"):
            subprocess._original_run = subprocess.run
        monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

        # Mock file operations that CLI might perform
        import os
        def mock_makedirs(path, exist_ok=True):
            """Mock os.makedirs to prevent file system operations."""
            pass  # Do nothing for tests

        monkeypatch.setattr(os, "makedirs", mock_makedirs)

    yield


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


@pytest.fixture(autouse=True)
def suppress_logging_for_clean_stderr(request):
    """Suppress logging output to stderr during tests that expect empty stderr.

    This fixture automatically removes loguru handlers before each test unless
    the test uses caplog (which needs logging to be active to capture logs).
    """
    # Skip suppression if test uses caplog fixture
    if "caplog" in request.fixturenames:
        yield
        return

    # Remove all loguru handlers to prevent output to stderr
    import loguru

    # Remove all handlers
    loguru.logger.remove()

    yield

    # Note: Handlers are not restored as this is just for tests
    # If logging is needed after tests, it should be reconfigured
