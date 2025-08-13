import pytest

from autoresearch.search import Search
from autoresearch.search.core import _local_git_backend
from autoresearch.config.models import ConfigModel
from autoresearch.errors import SearchError


def test_register_backend_and_lookup(monkeypatch):
    Search.backends = {}
    original_defaults = dict(Search._default_backends)

    @Search.register_backend("dummy")
    def dummy_backend(query: str, max_results: int = 5):
        return [{"title": "t", "url": "u"}]

    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["dummy"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr(Search, "get_sentence_transformer", lambda: None)
    monkeypatch.setattr(
        Search, "cross_backend_rank", lambda q, b, query_embedding=None: b["dummy"]
    )

    results = Search.external_lookup("x", max_results=1)
    assert results == [{"title": "t", "url": "u", "backend": "dummy"}]

    Search.reset()
    Search._default_backends = original_defaults


def test_external_lookup_unknown_backend(monkeypatch):
    Search.backends = {}
    cfg = ConfigModel(loops=1)
    cfg.search.backends = ["unknown"]
    cfg.search.context_aware.enabled = False
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    with pytest.raises(SearchError):
        Search.external_lookup("q", max_results=1)


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


def test_rank_results_merges_scores(monkeypatch):
    cfg = ConfigModel(loops=1)
    cfg.search.bm25_weight = 0.7
    cfg.search.semantic_similarity_weight = 0.2
    cfg.search.source_credibility_weight = 0.1
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)

    docs = [{"title": "a", "snippet": ""}, {"title": "b", "snippet": ""}]

    monkeypatch.setattr(Search, "calculate_bm25_scores", lambda q, d: [1.0, 0.0])
    monkeypatch.setattr(
        Search, "calculate_semantic_similarity", lambda q, d, e: [0.0, 1.0]
    )
    monkeypatch.setattr(Search, "assess_source_credibility", lambda d: [0.0, 0.0])

    ranked = Search.rank_results("q", docs)
    assert ranked[0]["title"] == "a"
    assert ranked[0]["merged_score"] == pytest.approx(0.7)
