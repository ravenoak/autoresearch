import sys
import os
import types
# Provide a lightweight stub for the optional ``ray`` dependency so that
# ``autoresearch`` can be imported without the actual package installed.
if "ray" not in sys.modules:
    def _remote(func):
        return types.SimpleNamespace(remote=lambda *a, **k: func(*a, **k))

    ray_stub = types.SimpleNamespace(
        init=lambda *a, **k: None,
        shutdown=lambda *a, **k: None,
        remote=_remote,
        get=lambda x: x,
    )
    sys.modules["ray"] = ray_stub

# Provide a minimal stub for GitPython used by the Search module
if "git" not in sys.modules:
    git_stub = types.SimpleNamespace(Repo=object)
    sys.modules["git"] = git_stub

# Stub heavy optional dependencies used by the search module
if "pdfminer.high_level" not in sys.modules:
    pm_stub = types.ModuleType("pdfminer.high_level")
    pm_stub.extract_text = lambda *a, **k: ""
    sys.modules["pdfminer.high_level"] = pm_stub
if "docx" not in sys.modules:
    docx_stub = types.ModuleType("docx")
    docx_stub.Document = object
    sys.modules["docx"] = docx_stub

if "streamlit" not in sys.modules:
    st_stub = types.ModuleType("streamlit")
    st_stub.markdown = lambda *a, **k: None
    class SessionState(dict):
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__

    st_stub.session_state = SessionState()
    st_stub.set_page_config = lambda *a, **k: None
    st_stub.text_area = lambda *a, **k: ""
    st_stub.selectbox = lambda *a, **k: None
    st_stub.slider = lambda *a, **k: 0
    st_stub.button = lambda *a, **k: False
    st_stub.columns = lambda *a, **k: (types.SimpleNamespace(), types.SimpleNamespace())
    st_stub.container = lambda: types.SimpleNamespace(__enter__=lambda s: None, __exit__=lambda s,e,t,b: None)
    st_stub.modal = lambda *a, **k: types.SimpleNamespace(__enter__=lambda s: None, __exit__=lambda s,e,t,b: None)
    sys.modules["streamlit"] = st_stub

if "matplotlib" not in sys.modules:
    mpl = types.ModuleType("matplotlib")
    mpl.use = lambda *a, **k: None
    sys.modules["matplotlib"] = mpl
if "matplotlib.pyplot" not in sys.modules:
    mpl_py = types.ModuleType("matplotlib.pyplot")
    mpl_py.plot = lambda *a, **k: None
    mpl_py.figure = lambda *a, **k: None
    mpl_py.gca = lambda *a, **k: types.SimpleNamespace()
    mpl_py.savefig = lambda *a, **k: None
    sys.modules["matplotlib.pyplot"] = mpl_py

if "PIL" not in sys.modules:
    pil_mod = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")
    image_mod.Image = object
    pil_mod.Image = image_mod
    sys.modules["PIL"] = pil_mod
    sys.modules["PIL.Image"] = image_mod

from uuid import uuid4
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util
from typer.testing import CliRunner
from fastapi.testclient import TestClient
from typing import Callable
from autoresearch.api import app as api_app

# Older Typer versions used in tests may not support the ``multiple`` parameter.
import typer
_orig_option = typer.Option

def _compat_option(*args, **kwargs):
    kwargs.pop("multiple", None)
    return _orig_option(*args, **kwargs)

typer.Option = _compat_option

# Ensure package can be imported without installation
if importlib.util.find_spec("autoresearch") is None:
    src_path = Path(__file__).resolve().parents[1] / "src"
    sys.path.insert(0, str(src_path))  # noqa: E402

import pytest  # noqa: E402

# Provide a lightweight fallback for sentence_transformers to avoid heavy
# imports during test startup.
dummy_st_module = types.ModuleType("sentence_transformers")


class DummySentenceTransformer:
    def __init__(self, *_, **__):
        pass

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[0.0] * 384 for _ in texts]


dummy_st_module.SentenceTransformer = DummySentenceTransformer
sys.modules.setdefault("sentence_transformers", dummy_st_module)

# Mock heavy optional dependencies to avoid model downloads during tests.
sys.modules.setdefault("bertopic", MagicMock())
sys.modules.setdefault("transformers", MagicMock())

from autoresearch import cache, storage  # noqa: E402
from autoresearch.config import ConfigLoader  # noqa: E402
from autoresearch.agents.registry import (  # noqa: E402
    AgentFactory,
    AgentRegistry,
)
from autoresearch.llm.registry import LLMFactory  # noqa: E402
from autoresearch.storage import (  # noqa: E402
    set_delegate as set_storage_delegate,
)
from autoresearch.extensions import VSSExtensionLoader  # noqa: E402


@pytest.fixture(autouse=True)
def stub_vss_extension_download(monkeypatch, request):
    """Prevent network calls when loading the DuckDB VSS extension."""
    if os.getenv("REAL_VSS_TEST") or request.node.get_closest_marker("real_vss"):
        yield
        return

    monkeypatch.setattr(VSSExtensionLoader, "load_extension", lambda _c: False)
    monkeypatch.setattr(
        VSSExtensionLoader,
        "verify_extension",
        lambda _c, verbose=True: False,
    )
    yield


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


@pytest.fixture
def storage_manager(tmp_path):
    """Initialise storage in a temporary location and clean up."""
    db_file = tmp_path / "kg.duckdb"
    storage.teardown(remove_db=True)
    storage.setup(str(db_file))
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


@pytest.fixture
def bdd_context():
    """Mutable mapping for sharing data between BDD steps."""
    return {}


@pytest.fixture
def mock_storage_components():
    """Mock the storage components (_graph, _db_backend, _rdf_store).

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
            if self.has_graph:
                self.patches.append(patch("autoresearch.storage._graph", self.graph))
            if self.has_db_backend:
                self.patches.append(
                    patch("autoresearch.storage._db_backend", self.db_backend)
                )
            if self.has_rdf:
                self.patches.append(patch("autoresearch.storage._rdf_store", self.rdf))

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
            self.patcher = patch("autoresearch.config.ConfigLoader.config", self.config)
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
