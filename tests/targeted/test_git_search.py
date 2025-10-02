"""Tests for Git repository indexing and search."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.targeted.helpers.git import (
    GitComponentTypes,
    GitComponentsUnavailable,
    load_git_components,
)

if TYPE_CHECKING:  # pragma: no cover - used only for static analysis
    from git.search import SearchResult


@pytest.fixture()
def git_components() -> GitComponentTypes:
    """Return Git search classes, installing stubs when extras are absent."""

    try:
        return load_git_components()
    except GitComponentsUnavailable as exc:
        pytest.skip(str(exc))


@pytest.mark.requires_git
def test_build_index_tracks_files(
    tmp_path: Path, git_components: GitComponentTypes
) -> None:
    """File contents are indexed by relative path."""

    GitSearcher, Repo, _ = git_components
    repo = Repo.init(tmp_path)
    file_path = tmp_path / "file.txt"
    file_path.write_text("alpha\n", encoding="utf-8")
    repo.index.add(["file.txt"])
    repo.index.commit("add file")
    searcher = GitSearcher(tmp_path)
    searcher.build_index()
    assert Path("file.txt") in searcher.index


@pytest.mark.requires_git
def test_search_finds_file_and_commit(
    tmp_path: Path, git_components: GitComponentTypes
) -> None:
    """Search returns matches from files and commit messages."""

    GitSearcher, Repo, SearchResultCls = git_components
    repo = Repo.init(tmp_path)
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello world\nsecond line\n", encoding="utf-8")
    repo.index.add(["note.txt"])
    repo.index.commit("greeting commit")
    searcher = GitSearcher(tmp_path)
    searcher.build_index()
    results: Iterable["SearchResult"] = searcher.search("hello")
    assert any(
        isinstance(result, SearchResultCls)
        and result.path == Path("note.txt")
        and result.line == 1
        for result in results
    )
    commit_hits: Iterable["SearchResult"] = searcher.search("greeting")
    assert any(
        isinstance(result, SearchResultCls)
        and result.path is None
        and "greeting commit" in result.text
        for result in commit_hits
    )
