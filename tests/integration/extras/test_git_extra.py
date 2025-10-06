# mypy: ignore-errors
"""Tests for the Git optional extra."""

from __future__ import annotations

import pytest

from tests.optional_imports import import_or_skip

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.search.core import _local_git_backend


@pytest.mark.requires_git
def test_local_git_backend(tmp_path) -> None:
    """The Git extra powers the local Git search backend."""
    git = import_or_skip("git")
    repo = git.Repo.init(tmp_path)
    path = tmp_path / "sample.txt"
    path.write_text("hello world")
    repo.index.add([str(path)])
    repo.index.commit("init")

    cfg = get_config()
    cfg.search.local_git.repo_path = str(tmp_path)
    cfg.search.local_git.branches = []
    cfg.search.local_file.file_types = ["txt"]
    with temporary_config(cfg):
        results = _local_git_backend("hello", max_results=1)
    assert results and "hello" in results[0]["snippet"].lower()
