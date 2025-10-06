# mypy: ignore-errors
import json
import atexit
import importlib.util
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import pytest
import requests
import responses
from responses import matchers

try:
    _spec = importlib.util.find_spec("git")
    GITPYTHON_INSTALLED = bool(_spec and _spec.origin)
except Exception:
    GITPYTHON_INSTALLED = False
from autoresearch.config.models import ConfigModel
from autoresearch.errors import SearchError, TimeoutError
from unittest.mock import MagicMock, patch
import autoresearch.search as search
from autoresearch.search import ExternalLookupResult, Search

SearchPayload = dict[str, Any]
StoragePayload = dict[str, Any]
BackendCallable = Callable[[str, int], list[SearchPayload]]
EmbeddingCallable = Callable[[Sequence[float], int], list[SearchPayload]]


def _cfg() -> ConfigModel:
    cfg: ConfigModel = ConfigModel(loops=1)
    cfg.search.use_semantic_similarity = False
    return cfg


pytestmark = pytest.mark.skipif(
    not GITPYTHON_INSTALLED, reason="GitPython not installed"
)


@pytest.fixture
def sample_search_results() -> list[SearchPayload]:
    """Simple search results for ranking tests."""
    return [
        {"title": "Result 1", "url": "https://site1.com", "snippet": "A"},
        {"title": "Result 2", "url": "https://site2.com", "snippet": "B"},
        {"title": "Result 3", "url": "https://site3.com", "snippet": "C"},
    ]


@pytest.fixture
def storage_vector_doc() -> StoragePayload:
    """Representative storage payload used to hydrate hybrid lookups."""

    return {
        "node_id": "urn:claim:vector-fixture",
        "content": "cached snippet",
        "embedding": [0.25, 0.75],
    }


@responses.activate
def test_external_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    cfg.search.use_semantic_similarity = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"
    params: Mapping[str, str] = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "Python", "FirstURL": "https://python.org"}]},
    )
    results: list[SearchPayload] = Search.external_lookup(query, max_results=1)
    # Check that the results contain the expected title and URL
    assert len(results) == 1
    assert results[0]["title"] == "Python"
    assert results[0]["url"] == "https://python.org"


@responses.activate
def test_external_lookup_special_chars(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    cfg.search.use_semantic_similarity = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "C++ tutorial & basics"
    url = "https://api.duckduckgo.com/"
    params: Mapping[str, str] = {
        "q": query,
        "format": "json",
        "no_redirect": "1",
        "no_html": "1",
    }
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "C++", "FirstURL": "https://cplusplus.com"}]},
    )
    results: list[SearchPayload] = Search.external_lookup(query, max_results=1)
    # Check that the results contain the expected title and URL
    assert len(results) == 1
    assert results[0]["title"] == "C++"
    assert results[0]["url"] == "https://cplusplus.com"


def test_generate_queries() -> None:
    queries: list[str] = Search.generate_queries("some topic")
    assert "some topic" in queries
    assert any(q.startswith("What is") for q in queries)
    assert len(queries) >= 2

    emb: list[float] = Search.generate_queries("abc", return_embeddings=True)
    assert isinstance(emb, list)
    assert all(isinstance(v, float) for v in emb)


@responses.activate
def test_external_lookup_backend_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a SearchError is raised when a search backend fails."""
    cfg = _cfg()
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    cfg.search.use_semantic_similarity = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock a failed HTTP request
    responses.add(
        responses.GET,
        url,
        status=500,  # Server error
        json={"error": "Internal Server Error"},
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_duckduckgo_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a TimeoutError is raised when DuckDuckGo search times out."""
    cfg = _cfg()
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    cfg.search.use_semantic_similarity = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock a timeout
    responses.add(
        responses.GET, url, body=requests.exceptions.Timeout("Connection timed out")
    )

    # The external_lookup method should raise a TimeoutError
    with pytest.raises(TimeoutError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "timed out" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, requests.exceptions.Timeout)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_duckduckgo_json_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a SearchError is raised when DuckDuckGo returns invalid JSON."""
    cfg = _cfg()
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"

    # Mock an invalid JSON response
    responses.add(
        responses.GET, url, body="Invalid JSON", content_type="application/json"
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, json.JSONDecodeError)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "duckduckgo"


@responses.activate
def test_serper_backend_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a SearchError is raised when Serper search fails."""
    cfg = _cfg()
    cfg.search.backends = ["serper"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    query = "python"
    url = "https://google.serper.dev/search"

    # Mock a failed HTTP request
    responses.add(
        responses.POST,
        url,
        status=403,  # Forbidden (e.g., invalid API key)
        json={"error": "Invalid API key"},
    )

    # The external_lookup method should raise a SearchError
    with pytest.raises(SearchError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "search failed" in str(excinfo.value)
    assert excinfo.value.__cause__ is not None
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "serper"


@responses.activate
def test_serper_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a TimeoutError is raised when Serper search times out."""
    cfg = _cfg()
    cfg.search.backends = ["serper"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    query = "python"
    url = "https://google.serper.dev/search"

    # Mock a timeout
    responses.add(
        responses.POST, url, body=requests.exceptions.Timeout("Connection timed out")
    )

    # The external_lookup method should raise a TimeoutError
    with pytest.raises(TimeoutError) as excinfo:
        Search.external_lookup(query, max_results=1)

    # Verify the error message and cause
    assert "timed out" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, requests.exceptions.Timeout)
    assert "backend" in excinfo.value.context
    assert excinfo.value.context["backend"] == "serper"


def test_local_file_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("hello from file")

    cfg = _cfg()
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results: list[SearchPayload] = Search.external_lookup("hello", max_results=5)

    assert any(r["url"] == str(file_path) for r in results)
    assert any("hello" in r["snippet"].lower() for r in results)


@pytest.mark.slow
def test_local_git_backend(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo, check=True)
    readme = repo / "README.md"
    readme.write_text("TODO in code")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add TODO"], cwd=repo, check=True)

    cfg = _cfg()
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_git.repo_path = str(repo)
    cfg.search.local_git.branches = ["master"]
    cfg.search.local_git.history_depth = 10
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results: list[SearchPayload] = Search.external_lookup("TODO", max_results=5)

    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()

    assert any(r.get("commit") == commit_hash for r in results)
    assert any(r["url"] == str(readme) for r in results)


def test_external_lookup_vector_search(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    cfg.search.backends = []
    cfg.search.context_aware.enabled = False
    cfg.search.embedding_backends = ["duckdb"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    class DummyModel:
        def encode(self, text: str) -> list[float]:
            return [0.1, 0.2]

    monkeypatch.setattr(
        "autoresearch.search.Search.get_sentence_transformer",
        lambda *args, **kwargs: DummyModel(),
    )

    def mock_vector_search(embed: Sequence[float], k: int = 5) -> list[SearchPayload]:
        return [{"node_id": "n1", "content": "vector snippet"}]

    vector_backend: EmbeddingCallable = mock_vector_search

    monkeypatch.setattr(
        "autoresearch.search.StorageManager.vector_search", vector_backend
    )

    results: list[SearchPayload] = Search.external_lookup("query", max_results=1)

    assert any(r.get("snippet") == "vector snippet" for r in results)
    assert all(r.get("backend") == "storage" for r in results)
    assert any("vector" in (r.get("storage_sources") or []) for r in results)


def test_external_lookup_returns_handles(
    monkeypatch: pytest.MonkeyPatch, storage_vector_doc: StoragePayload
) -> None:
    cfg = _cfg()
    cfg.search.backends = []
    cfg.search.embedding_backends = []
    cfg.search.hybrid_query = True
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    with Search.temporary_state() as search_instance:
        search_state: Search = search_instance
        search_state.cache.clear()

        def vector_backend_func(
            embedding: Sequence[float], k: int = 5
        ) -> list[SearchPayload]:
            return [dict(storage_vector_doc)]

        vector_backend: EmbeddingCallable = vector_backend_func

        monkeypatch.setattr(
            "autoresearch.search.StorageManager.vector_search",
            vector_backend,
        )

        bundle: ExternalLookupResult = search_state.external_lookup(
            {"text": "vector query", "embedding": storage_vector_doc["embedding"]},
            max_results=1,
            return_handles=True,
        )

        assert isinstance(bundle, ExternalLookupResult)
        assert bundle.query == "vector query"
        assert bundle.cache is search_state.cache
        assert bundle.storage is search.StorageManager
        assert list(bundle) == bundle.results
        assert bundle[0]["backend"] == "storage"
        storage_docs: Iterable[Mapping[str, Any]] = bundle.by_backend.get("storage") or []
        assert storage_docs
        assert storage_docs[0]["snippet"] == "cached snippet"
        assert "vector" in (storage_docs[0].get("storage_sources") or [])


def test_http_session_atexit_hook(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    cfg.search.http_pool_size = 1
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    search.close_http_session()
    calls: list[Callable[[], None]] = []
    monkeypatch.setattr(atexit, "register", lambda f: calls.append(f))
    session: requests.Session = search.get_http_session()
    assert search.close_http_session in calls

    search.close_http_session()
    calls.clear()
    monkeypatch.setattr(atexit, "register", lambda f: calls.append(f))
    search.set_http_session(session)
    assert search.close_http_session in calls


@patch("autoresearch.search.core.get_config")
def test_rank_results_semantic_only(
    mock_get_config: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sample_search_results: list[SearchPayload],
) -> None:
    cfg = _cfg()
    cfg.search.semantic_similarity_weight = 1.0
    cfg.search.bm25_weight = 0.0
    cfg.search.source_credibility_weight = 0.0
    cfg.search.use_semantic_similarity = True
    mock_get_config.return_value = cfg

    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.8, 0.2, 0.1])
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda *args, **kwargs: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda *args, **kwargs: [0.5, 0.6, 0.7],
    )

    ranked: list[SearchPayload] = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site2.com"


@patch("autoresearch.search.core.get_config")
def test_rank_results_bm25_only(
    mock_get_config: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sample_search_results: list[SearchPayload],
) -> None:
    cfg = _cfg()
    cfg.search.semantic_similarity_weight = 0.0
    cfg.search.bm25_weight = 1.0
    cfg.search.source_credibility_weight = 0.0
    mock_get_config.return_value = cfg

    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.8, 0.2, 0.1])
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda *args, **kwargs: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda *args, **kwargs: [0.5, 0.6, 0.7],
    )

    ranked: list[SearchPayload] = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site1.com"


@patch("autoresearch.search.core.get_config")
def test_rank_results_credibility_only(
    mock_get_config: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    sample_search_results: list[SearchPayload],
) -> None:
    cfg = _cfg()
    cfg.search.semantic_similarity_weight = 0.0
    cfg.search.bm25_weight = 0.0
    cfg.search.source_credibility_weight = 1.0
    mock_get_config.return_value = cfg

    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.8, 0.2, 0.1])
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda *args, **kwargs: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(
        Search,
        "assess_source_credibility",
        lambda *args, **kwargs: [0.5, 0.6, 0.7],
    )

    ranked: list[SearchPayload] = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site3.com"


def test_external_lookup_hybrid_query(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = _cfg()
    cfg.search.backends = ["kw"]
    cfg.search.embedding_backends = ["emb"]
    cfg.search.hybrid_query = True
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    class DummyModel:
        def encode(self, text: str) -> list[float]:
            return [0.1]

    monkeypatch.setattr(Search, "get_sentence_transformer", lambda *args, **kwargs: DummyModel())

    with Search.temporary_state() as search_state:
        search_instance: Search = search_state

        def keyword_backend_func(query: str, max_results: int) -> list[SearchPayload]:
            return [{"title": "KW", "url": "kw"}]

        keyword_backend: BackendCallable = keyword_backend_func

        def embedding_backend_func(
            embedding: Sequence[float], max_results: int
        ) -> list[SearchPayload]:
            return [{"title": "VEC", "url": "vec"}]

        embedding_backend: EmbeddingCallable = embedding_backend_func

        search_instance.backends["kw"] = keyword_backend
        search_instance.embedding_backends["emb"] = embedding_backend

        def cross_backend_rank(
            query: str,
            backend_results: Mapping[str, list[SearchPayload]],
            *,
            query_embedding: Sequence[float] | None = None,
        ) -> list[SearchPayload]:
            _ = query
            _ = query_embedding
            return [
                *backend_results.get("kw", []),
                *backend_results.get("emb", []),
            ]

        monkeypatch.setattr(search_instance, "cross_backend_rank", cross_backend_rank)

        results: list[SearchPayload] = search_instance.external_lookup("hello", max_results=2)
        urls: set[str] = {r["url"] for r in results}
        assert "kw" in urls and "vec" in urls
