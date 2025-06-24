"""Tests for search backend integration.

This module contains tests for the integration between different search
backends and the main search functionality.
"""

import subprocess

import pytest
from autoresearch.search import Search
from autoresearch import cache
from autoresearch.config import ConfigModel


@pytest.fixture(autouse=True)
def cleanup_search():
    """Clean up the search system after each test.

    This fixture ensures that the search system is properly cleaned up
    after each test, preventing test pollution and resource leaks.
    """
    # Setup
    original_backends = Search.backends.copy()
    cache.clear()

    yield

    # Teardown
    Search.backends = original_backends
    cache.clear()


def test_multiple_backends_called_and_merged(monkeypatch):
    """Test that multiple search backends are called and results are merged.

    This test verifies that when multiple search backends are configured,
    all of them are called and their results are merged in the final output.
    """
    # Setup
    calls = []

    def backend1(query, max_results=5):
        calls.append("b1")
        return [{"title": "t1", "url": "u1"}]

    def backend2(query, max_results=5):
        calls.append("b2")
        return [{"title": "t2", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", backend1)
    monkeypatch.setitem(Search.backends, "b2", backend2)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["b1", "b2"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    # Execute
    results = Search.external_lookup("q", max_results=1)

    # Verify
    assert calls == ["b1", "b2"]

    # Check that we have the expected number of results
    assert len(results) == 2

    # Check that the results contain the expected titles and URLs
    # The order might be different due to ranking
    titles = [r["title"] for r in results]
    urls = [r["url"] for r in results]

    assert "t1" in titles
    assert "t2" in titles
    assert "u1" in urls
    assert "u2" in urls


def _init_git_repo(repo_path):
    """Initialize a git repo with a single file."""
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"],
                   cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"],
                   cwd=repo_path, check=True)
    (repo_path / "README.md").write_text("hello from git")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_path, check=True)


def test_local_file_and_git_backends_called(monkeypatch, tmp_path):
    """Invoke local_file and local_git backends when configured."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("hello from file")

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _init_git_repo(repo_path)

    calls = []

    # Wrap existing backends to track invocation order
    original_file_backend = Search.backends["local_file"]
    original_git_backend = Search.backends["local_git"]

    def file_wrapper(query, max_results=5):
        calls.append("file")
        return original_file_backend(query, max_results)

    def git_wrapper(query, max_results=5):
        calls.append("git")
        return original_git_backend(query, max_results)

    monkeypatch.setitem(Search.backends, "local_file", file_wrapper)
    monkeypatch.setitem(Search.backends, "local_git", git_wrapper)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file", "local_git"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    results = Search.external_lookup("hello", max_results=5)

    assert calls == ["file", "git"]
    urls = [r["url"] for r in results]
    assert str(file_path) in urls
    assert str(repo_path / "README.md") in urls


def test_ranking_across_backends(monkeypatch):
    """Results from different backends should be ranked together."""

    def b1(query, max_results=5):
        return [{"title": "python foo", "url": "u1"}]

    def b2(query, max_results=5):
        return [{"title": "other", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", b1)
    monkeypatch.setitem(Search.backends, "b2", b2)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["b1", "b2"]
    cfg.search.context_aware.enabled = False
    cfg.search.semantic_similarity_weight = 0.6
    cfg.search.bm25_weight = 0.4
    cfg.search.source_credibility_weight = 0.0
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        lambda q, docs: [0.3, 0.9],
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda q, docs, query_embedding=None: [0.9, 0.1],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda docs: [1.0, 1.0])

    results = Search.external_lookup("python", max_results=1)

    assert results[0]["url"] == "u1"


def test_embeddings_added_to_results(monkeypatch):
    """Ensure embeddings are added for all backend results."""

    class DummyModel:
        def encode(self, texts):
            if isinstance(texts, str):
                return [0.1, 0.2]
            return [[0.1, 0.2] for _ in texts]

    def b1(query, max_results=5):
        return [{"title": "t", "url": "u"}]

    monkeypatch.setitem(Search.backends, "b1", b1)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["b1"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)
    monkeypatch.setattr(Search, "get_sentence_transformer", lambda: DummyModel())

    results = Search.external_lookup("q", max_results=1)

    assert "embedding" in results[0]
    assert "similarity" in results[0]


def test_git_backend_returns_context(monkeypatch, tmp_path):
    """Git backend should include context lines in snippets."""

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Your Name"], cwd=repo_path, check=True)
    code_file = repo_path / "code.txt"
    code_file.write_text("line1\ncontext\nline3")
    subprocess.run(["git", "add", "code.txt"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "add context"], cwd=repo_path, check=True)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_git"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_git.repo_path = str(repo_path)
    cfg.search.local_git.branches = ["main"]
    cfg.search.local_git.history_depth = 10
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    results = Search.external_lookup("context", max_results=5)

    assert any("\n" in r["snippet"] for r in results)


def test_combined_local_and_web_results(monkeypatch, tmp_path):
    """Local and web backend results should be ranked together."""

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "note.txt"
    file_path.write_text("python from local file")

    def web_backend(query, max_results=5):
        return [{"title": "python article", "url": "https://example.com"}]

    monkeypatch.setitem(Search.backends, "web", web_backend)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file", "web"]
    cfg.search.context_aware.enabled = False
    cfg.search.local_file.path = str(docs_dir)
    cfg.search.local_file.file_types = ["txt"]
    cfg.search.semantic_similarity_weight = 0.6
    cfg.search.bm25_weight = 0.4
    cfg.search.source_credibility_weight = 0.0
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    monkeypatch.setattr(
        Search,
        "calculate_bm25_scores",
        lambda q, docs: [0.9, 0.1],
    )
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda q, docs, query_embedding=None: [0.8, 0.2],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda docs: [1.0, 1.0])

    results = Search.external_lookup("python", max_results=2)

    assert results[0]["url"] == str(file_path)
    urls = {r["url"] for r in results}
    assert {str(file_path), "https://example.com"} <= urls


def test_weight_optimization_improves_ranking(monkeypatch):
    """Tuned weights should improve ranking order."""

    def b1(query, max_results=5):
        return [{"title": "relevant", "url": "u1"}]

    def b2(query, max_results=5):
        return [{"title": "irrelevant", "url": "u2"}]

    monkeypatch.setitem(Search.backends, "b1", b1)
    monkeypatch.setitem(Search.backends, "b2", b2)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["b1", "b2"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, docs: [0.2, 0.9])
    monkeypatch.setattr(
        Search,
        "calculate_semantic_similarity",
        lambda q, docs, query_embedding=None: [0.7, 0.6],
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda docs: [0.4, 0.9])

    cfg.search.semantic_similarity_weight = 0.5
    cfg.search.bm25_weight = 0.3
    cfg.search.source_credibility_weight = 0.2
    results_default = Search.external_lookup("q", max_results=2)
    order_default = [r["url"] for r in results_default]

    import tomllib
    from pathlib import Path

    tuned = tomllib.loads(Path("examples/autoresearch.toml").read_text())["search"]
    cfg.search.semantic_similarity_weight = tuned["semantic_similarity_weight"]
    cfg.search.bm25_weight = tuned["bm25_weight"]
    cfg.search.source_credibility_weight = tuned["source_credibility_weight"]
    results_tuned = Search.external_lookup("q", max_results=2)
    order_tuned = [r["url"] for r in results_tuned]

    assert order_default[0] == "u2"
    assert order_tuned[0] == "u1"
