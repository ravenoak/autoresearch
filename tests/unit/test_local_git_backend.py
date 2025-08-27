from __future__ import annotations

from contextlib import contextmanager

import git
import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.search.core import _local_git_backend
from autoresearch.storage import StorageManager


@pytest.mark.requires_git
def test_local_git_backend_searches_repo(tmp_path, monkeypatch):
    repo_path = tmp_path / "repo"
    repo = git.Repo.init(repo_path)
    file_path = repo_path / "file.txt"
    file_path.write_text("hello world")
    repo.index.add([str(file_path)])
    repo.index.commit("initial commit")

    cfg = ConfigModel()
    cfg.search.local_git.repo_path = str(repo_path)
    cfg.search.local_git.branches = [repo.active_branch.name]
    cfg.search.local_git.history_depth = 5
    cfg.search.local_file.file_types = ["txt"]
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.shutil.which", lambda name: None)

    @contextmanager
    def dummy_connection():
        class DummyConn:
            def execute(self, *args, **kwargs):
                class Cur:
                    def fetchall(self_inner):
                        return []
                return Cur()
        yield DummyConn()

    monkeypatch.setattr(StorageManager, "connection", staticmethod(dummy_connection))

    results = _local_git_backend("hello", max_results=5)
    assert any("hello" in r["snippet"] for r in results)
