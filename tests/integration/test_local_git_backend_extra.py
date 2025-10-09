# mypy: ignore-errors
from __future__ import annotations

from contextlib import contextmanager

import pytest

from tests.optional_imports import import_or_skip

from autoresearch.search.core import _local_git_backend
from autoresearch.storage import StorageManager


@contextmanager
def _dummy_connection():
    class DummyConn:
        def execute(self, *args, **kwargs):
            class Cur:
                def fetchall(self_inner):
                    return []

            return Cur()

    yield DummyConn()


@pytest.mark.requires_git
def test_local_git_backend_finds_file_content(tmp_path, monkeypatch, config_factory):
    git = import_or_skip("git", reason="git extra not installed")
    repo_path = tmp_path / "repo"
    repo = git.Repo.init(repo_path)
    file_path = repo_path / "data.txt"
    file_path.write_text("searchable text")
    repo.index.add([str(file_path)])
    repo.index.commit("add data")

    cfg = config_factory(
        {
            "search": {
                "local_git": {
                    "repo_path": str(repo_path),
                    "branches": [repo.active_branch.name],
                    "history_depth": 5,
                },
                "local_file": {"file_types": ["txt"]},
            }
        }
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Repo", git.Repo)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_dummy_connection))

    results = _local_git_backend("searchable", max_results=5)
    assert any("searchable text" in r["snippet"] for r in results)


@pytest.mark.requires_git
def test_local_git_backend_finds_commit_message(tmp_path, monkeypatch, config_factory):
    git = import_or_skip("git", reason="git extra not installed")
    repo_path = tmp_path / "repo"
    repo = git.Repo.init(repo_path)
    file_path = repo_path / "data.txt"
    file_path.write_text("initial")
    repo.index.add([str(file_path)])
    repo.index.commit("initial commit")
    file_path.write_text("updated")
    repo.index.add([str(file_path)])
    repo.index.commit("feature commitmarker")

    cfg = config_factory(
        {
            "search": {
                "local_git": {
                    "repo_path": str(repo_path),
                    "branches": [repo.active_branch.name],
                    "history_depth": 5,
                },
                "local_file": {"file_types": ["txt"]},
            }
        }
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Repo", git.Repo)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_dummy_connection))

    results = _local_git_backend("commitmarker", max_results=5)
    assert any(
        r["title"] == "commit message" and "commitmarker" in r["snippet"] for r in results
    )
