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

    def local_file(query, max_results=5):
        calls.append("file")
        results = []
        for f in docs_dir.rglob("*.txt"):
            if query in f.read_text():
                results.append({"title": f.name, "url": str(f)})
        return results[:max_results]

    def local_git(query, max_results=5):
        calls.append("git")
        readme = repo_path / "README.md"
        if query in readme.read_text():
            return [{"title": readme.name, "url": str(readme)}]
        return []

    monkeypatch.setitem(Search.backends, "local_file", local_file)
    monkeypatch.setitem(Search.backends, "local_git", local_git)

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["local_file", "local_git"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.get_config", lambda: cfg)

    results = Search.external_lookup("hello", max_results=5)

    assert calls == ["file", "git"]
    urls = [r["url"] for r in results]
    assert str(file_path) in urls
    assert str(repo_path / "README.md") in urls
