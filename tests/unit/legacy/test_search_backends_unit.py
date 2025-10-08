# mypy: ignore-errors
from typing import Any, Callable

import pytest

from autoresearch.search import Search
from autoresearch.search.core import _local_git_backend, hybridmethod
from autoresearch.config.models import ConfigModel
from autoresearch.errors import SearchError


def _make_hybrid_stub(
    calls: list[dict[str, Any]],
    *,
    responder: Callable[[Any, tuple[Any, ...], dict[str, Any]], Any] | None = None,
    default: Any = None,
):
    """Create a hybridmethod stub that tracks invocations.

    The returned stub accepts both class and instance invocations, mirroring the
    behaviour of :func:`hybridmethod` in production code. Calls are recorded with
    the binding context and provided positional and keyword arguments. A custom
    ``responder`` can tailor the return value; otherwise ``default`` is used.
    """

    def _stub(subject, *args, **kwargs):
        is_class = isinstance(subject, type) and issubclass(subject, Search)
        binding = "class" if is_class else "instance"
        calls.append(
            {
                "binding": binding,
                "subject": subject,
                "args": args,
                "kwargs": kwargs,
            }
        )
        if responder is not None:
            return responder(subject, args, kwargs)
        return default

    return hybridmethod(_stub)


def test_register_backend_and_lookup(monkeypatch):
    with Search.temporary_state() as search:
        @search.register_backend("dummy")
        def dummy_backend(query: str, max_results: int = 5):
            return [{"title": "t", "url": "u"}]

        cfg = ConfigModel(loops=1)
        cfg.search.backends = ["dummy"]
        cfg.search.context_aware.enabled = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        monkeypatch.setattr(Search, "get_sentence_transformer", lambda self: None)
        embedding_calls: list[dict[str, Any]] = []
        add_calls: list[dict[str, Any]] = []
        monkeypatch.setattr(
            Search,
            "embedding_lookup",
            _make_hybrid_stub(embedding_calls, default={}),
        )
        monkeypatch.setattr(
            Search,
            "add_embeddings",
            _make_hybrid_stub(add_calls),
        )
        monkeypatch.setattr(
            search, "cross_backend_rank", lambda q, b, query_embedding=None: b["dummy"]
        )

        results = search.external_lookup("x", max_results=1)
        assert results == [{"title": "t", "url": "u", "backend": "dummy", "canonical_url": "u"}]


def test_external_lookup_unknown_backend(monkeypatch):
    with Search.temporary_state() as search:
        cfg = ConfigModel(loops=1)
        cfg.search.backends = ["unknown"]
        cfg.search.context_aware.enabled = False
        monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
        with pytest.raises(SearchError):
            search.external_lookup("q", max_results=1)


def test_local_git_backend_ast_search(tmp_path, monkeypatch):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    py_file = repo_dir / "module.py"
    py_file.write_text("def my_special_function():\n    return 42\n")

    class DummyCommit:
        hexsha = "dummy"

    class DummyRepo:
        def __init__(self, path):
            self.head = type("head", (), {"commit": DummyCommit()})

        def iter_commits(self, branches=None, max_count=None):
            return []

    monkeypatch.setattr("autoresearch.search.core.Repo", DummyRepo)
    monkeypatch.setattr("autoresearch.search.core.GITPYTHON_AVAILABLE", True)

    cfg = ConfigModel(loops=1)
    cfg.search.local_git.repo_path = str(repo_dir)
    cfg.search.local_file.file_types = ["py"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    results = _local_git_backend("myspecialfunction", max_results=5)
    assert any("my_special_function" in r["snippet"] for r in results)


def test_local_git_backend_missing_repo(monkeypatch):
    """Return empty list when repo_path is not configured."""

    cfg = ConfigModel(loops=1)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    assert _local_git_backend("query") == []


def test_local_git_backend_nonexistent_repo(monkeypatch, tmp_path):
    """Return empty list when repo_path does not exist."""

    cfg = ConfigModel(loops=1)
    cfg.search.local_git.repo_path = str(tmp_path / "missing")
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    assert _local_git_backend("query") == []


def test_local_git_backend_requires_gitpython(monkeypatch, tmp_path):
    """Raise SearchError when gitpython is unavailable."""

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    cfg = ConfigModel(loops=1)
    cfg.search.local_git.repo_path = str(repo_dir)
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Repo", None)

    with pytest.raises(SearchError):
        _local_git_backend("query")


def test_rank_results_merges_scores(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.bm25_weight = 0.7
    cfg.search.semantic_similarity_weight = 0.2
    cfg.search.source_credibility_weight = 0.1
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    docs = [{"title": "a", "snippet": ""}, {"title": "b", "snippet": ""}]

    monkeypatch.setattr(
        Search, "calculate_bm25_scores", staticmethod(lambda q, d: [1.0, 0.0])
    )
    monkeypatch.setattr(
        Search, "calculate_semantic_similarity", lambda self, q, d, e: [0.0, 1.0]
    )
    monkeypatch.setattr(
        Search, "assess_source_credibility", lambda self, d: [0.0, 0.0]
    )

    ranked = Search.rank_results("q", docs)
    assert ranked[0]["title"] == "a"
    assert ranked[0]["merged_score"] == pytest.approx(0.75)
