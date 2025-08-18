import json
import responses
from responses import matchers
import pytest
import requests
import subprocess
import importlib.util

try:
    _spec = importlib.util.find_spec("git")
    GITPYTHON_INSTALLED = bool(_spec and _spec.origin)
except Exception:
    GITPYTHON_INSTALLED = False
from autoresearch.config.models import ConfigModel
from autoresearch.errors import SearchError, TimeoutError
from unittest.mock import patch
import autoresearch.search as search
from autoresearch.search import Search

pytestmark = pytest.mark.skipif(
    not GITPYTHON_INSTALLED, reason="GitPython not installed"
)


@pytest.fixture
def sample_search_results():
    """Simple search results for ranking tests."""
    return [
        {"title": "Result 1", "url": "https://site1.com", "snippet": "A"},
        {"title": "Result 2", "url": "https://site2.com", "snippet": "B"},
        {"title": "Result 3", "url": "https://site3.com", "snippet": "C"},
    ]


@responses.activate
def test_external_lookup(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "python"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "Python", "FirstURL": "https://python.org"}]},
    )
    results = Search.external_lookup(query, max_results=1)
    # Check that the results contain the expected title and URL
    assert len(results) == 1
    assert results[0]["title"] == "Python"
    assert results[0]["url"] == "https://python.org"


@responses.activate
def test_external_lookup_special_chars(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    query = "C++ tutorial & basics"
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": "1", "no_html": "1"}
    responses.add(
        responses.GET,
        url,
        match=[matchers.query_param_matcher(params)],
        json={"RelatedTopics": [{"Text": "C++", "FirstURL": "https://cplusplus.com"}]},
    )
    results = Search.external_lookup(query, max_results=1)
    # Check that the results contain the expected title and URL
    assert len(results) == 1
    assert results[0]["title"] == "C++"
    assert results[0]["url"] == "https://cplusplus.com"


def test_generate_queries():
    queries = Search.generate_queries("some topic")
    assert "some topic" in queries
    assert any(q.startswith("What is") for q in queries)
    assert len(queries) >= 2

    emb = Search.generate_queries("abc", return_embeddings=True)
    assert isinstance(emb, list)
    assert all(isinstance(v, float) for v in emb)


@responses.activate
def test_external_lookup_backend_error(monkeypatch):
    """Test that a SearchError is raised when a search backend fails."""
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
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
def test_duckduckgo_timeout_error(monkeypatch):
    """Test that a TimeoutError is raised when DuckDuckGo search times out."""
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["duckduckgo"]
    cfg.search.context_aware.enabled = False
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
def test_duckduckgo_json_decode_error(monkeypatch):
    """Test that a SearchError is raised when DuckDuckGo returns invalid JSON."""
    cfg = ConfigModel(loops=1)
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
def test_serper_backend_error(monkeypatch):
    """Test that a SearchError is raised when Serper search fails."""
    cfg = ConfigModel(loops=1)
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
def test_serper_timeout_error(monkeypatch):
    """Test that a TimeoutError is raised when Serper search times out."""
    cfg = ConfigModel(loops=1)
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


def test_local_file_backend(monkeypatch, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("hello from file")

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results = Search.external_lookup("hello", max_results=5)

    assert any(r["url"] == str(file_path) for r in results)
    assert any("hello" in r["snippet"].lower() for r in results)


@pytest.mark.slow
def test_local_git_backend(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo, check=True)
    readme = repo / "README.md"
    readme.write_text("TODO in code")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add TODO"], cwd=repo, check=True)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_git.repo_path = str(repo)
    cfg.search.local_git.branches = ["master"]
    cfg.search.local_git.history_depth = 10
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results = Search.external_lookup("TODO", max_results=5)

    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()

    assert any(r.get("commit") == commit_hash for r in results)
    assert any(r["url"] == str(readme) for r in results)


def test_external_lookup_vector_search(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = []
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    class DummyModel:
        def encode(self, text):
            return [0.1, 0.2]

    monkeypatch.setattr(
        "autoresearch.search.Search.get_sentence_transformer", lambda: DummyModel()
    )

    def mock_vector_search(embed, k=5):
        return [{"node_id": "n1", "content": "vector snippet"}]

    monkeypatch.setattr(
        "autoresearch.search.StorageManager.vector_search", mock_vector_search
    )

    results = Search.external_lookup("query", max_results=1)

    assert any(r.get("snippet") == "vector snippet" for r in results)


def test_http_session_atexit_hook(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.http_pool_size = 1
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    search.close_http_session()
    calls: list = []
    monkeypatch.setattr(search.atexit, "register", lambda f: calls.append(f))
    session = search.get_http_session()
    assert search.close_http_session in calls

    search.close_http_session()
    calls.clear()
    monkeypatch.setattr(search.atexit, "register", lambda f: calls.append(f))
    search.set_http_session(session)
    assert search.close_http_session in calls


@patch("autoresearch.search.core.get_config")
def test_rank_results_semantic_only(mock_get_config, monkeypatch, sample_search_results):
    cfg = ConfigModel(loops=1)
    cfg.search.semantic_similarity_weight = 1.0
    cfg.search.bm25_weight = 0.0
    cfg.search.source_credibility_weight = 0.0
    mock_get_config.return_value = cfg

    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, r: [0.8, 0.2, 0.1])
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda q, r, query_embedding=None: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [0.5, 0.6, 0.7])

    ranked = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site2.com"


@patch("autoresearch.search.core.get_config")
def test_rank_results_bm25_only(mock_get_config, monkeypatch, sample_search_results):
    cfg = ConfigModel(loops=1)
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
        lambda q, r, query_embedding=None: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [0.5, 0.6, 0.7])

    ranked = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site1.com"


@patch("autoresearch.search.core.get_config")
def test_rank_results_credibility_only(mock_get_config, monkeypatch, sample_search_results):
    cfg = ConfigModel(loops=1)
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
        lambda q, r, query_embedding=None: [0.1, 0.9, 0.2],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda r: [0.5, 0.6, 0.7])

    ranked = Search.rank_results("q", sample_search_results)
    assert ranked[0]["url"] == "https://site3.com"


def test_external_lookup_hybrid_query(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["kw"]
    cfg.search.embedding_backends = ["emb"]
    cfg.search.hybrid_query = True
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    class DummyModel:
        def encode(self, text):
            return [0.1]

    monkeypatch.setattr(Search, "get_sentence_transformer", lambda: DummyModel())

    with Search.temporary_state() as search:
        search.backends["kw"] = lambda q, max_results: [
            {"title": "KW", "url": "kw"}
        ]
        search.embedding_backends["emb"] = lambda e, max_results: [
            {"title": "VEC", "url": "vec"}
        ]

        monkeypatch.setattr(search, "cross_backend_rank", lambda q, b, query_embedding=None: [
            *b.get("kw", []), *b.get("emb", [])
        ])

        results = search.external_lookup("hello", max_results=1)
        urls = {r["url"] for r in results}
        assert "kw" in urls and "vec" in urls
