import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pytest_httpx import httpx_mock  # noqa: F401

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
    "pytest_httpx",
]

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
    """Return True if a module can be imported from the real environment."""
    try:
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
    if item.get_closest_marker("requires_nlp") and not NLP_AVAILABLE:
        pytest.skip("nlp extra not installed")


GITPYTHON_INSTALLED = _module_available("git")
POLARS_INSTALLED = _module_available("polars")
UI_AVAILABLE = _module_available("streamlit")
NLP_AVAILABLE = _module_available("sentence_transformers")


def _check_vss() -> bool:
    try:
        conn = duckdb.connect(database=":memory:")
        return VSSExtensionLoader.verify_extension(conn, verbose=False)
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


VSS_AVAILABLE = _check_vss()


@pytest.fixture(autouse=True)
def stub_vss_extension_download(monkeypatch, request, tmp_path):
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
def reset_config_loader_instance():
    """Reset ConfigLoader singleton before each test."""
    ConfigLoader.reset_instance()
    yield
    ConfigLoader.reset_instance()


@pytest.fixture(autouse=True)
def isolate_paths(tmp_path, monkeypatch):
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
def reset_registries():
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
def storage_manager(tmp_path):
    """Initialize storage in a temporary location and clean up."""
    db_file = tmp_path / "kg.duckdb"
    storage.teardown(remove_db=True)
    storage.initialize_storage(str(db_file))
    set_storage_delegate(storage.StorageManager)
    yield storage
    storage.teardown(remove_db=True)
    set_storage_delegate(None)


@pytest.fixture
def config_watcher():
    """Provide a ConfigLoader that is cleaned up after use."""
    loader = ConfigLoader()
    yield loader
    loader.stop_watching()


@pytest.fixture(autouse=True)
def stop_config_watcher(monkeypatch):
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
def reset_rate_limiting():
    """Clear API rate limiter state and request log before each test."""
    reset_limiter_state()
    reset_request_log()
    yield
    reset_limiter_state()
    reset_request_log()


@pytest.fixture(autouse=True)
def reset_orchestration_metrics():
    """Reset global orchestration counters before and after each test."""
    metrics.reset_metrics()
    yield
    metrics.reset_metrics()


@pytest.fixture(autouse=True)
def cleanup_storage():
    """Remove any persistent storage state between tests."""
    StorageManager.teardown(remove_db=True)
    yield
    StorageManager.teardown(remove_db=True)


@pytest.fixture(autouse=True)
def initialize_storage(request, tmp_path, cleanup_storage):
    """Create storage tables for storage-related tests."""
    filename = request.node.path.name
    if filename.startswith("test_storage_") or filename == "test_main_backup_commands.py":
        if not hasattr(StorageManager, "initialize"):
            StorageManager.initialize = staticmethod(storage.initialize_storage)  # type: ignore[attr-defined]
        if not hasattr(duckdb.DuckDBPyConnection, "fetchone"):
            def _fetchone(self):
                rows = self.fetchall()
                return rows[0] if rows else None

            duckdb.DuckDBPyConnection.fetchone = _fetchone  # type: ignore[attr-defined]
        StorageManager.initialize(str(tmp_path / "kg.duckdb"))
    yield


@pytest.fixture(autouse=True)
def restore_sys_modules():
    """Remove non-module entries from ``sys.modules`` between tests."""
    from types import ModuleType

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

            self.patches = []

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
            self.patcher = None

        def __enter__(self):
            self.patcher = patch("autoresearch.config.loader.ConfigLoader.config", self.config)
            self.patcher.start()
            return self.config

        def __exit__(self, exc_type, exc_val, exc_tb):
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
def realistic_claim_batch(claim_factory):
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
    pytest.importorskip("sentence_transformers")
    from autoresearch.search import Search

    path = Path(__file__).resolve().parent / "data" / "eval" / "sample_eval.csv"
    return Search.load_evaluation_data(path)


@pytest.fixture
def dummy_llm_adapter(monkeypatch):
    """Register and provide a dummy LLM adapter for tests."""
    from autoresearch.llm.adapters import DummyAdapter

    LLMFactory.register("dummy", DummyAdapter)
    yield DummyAdapter()
    LLMFactory._registry.pop("dummy", None)


@pytest.fixture
def mock_llm_adapter(monkeypatch):
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
def flexible_llm_adapter(monkeypatch, request):
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
