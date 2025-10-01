"""Tests for Git repository indexing and search."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:  # pragma: no cover - used only for static analysis
    from git.search import SearchResult  # type: ignore[import-untyped]


@pytest.fixture()
def git_components(monkeypatch: pytest.MonkeyPatch) -> tuple[type[Any], type[Any], type[Any]]:
    """Return Git search classes, installing stubs when extras are absent."""

    try:
        git_module = importlib.import_module("git")
    except ModuleNotFoundError:
        repo_root = Path(__file__).resolve().parents[2]
        stub_path = repo_root / "src" / "git" / "__init__.py"
        spec = importlib.util.spec_from_file_location("git", stub_path)
        if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
            pytest.skip("git module unavailable")
        git_module = importlib.util.module_from_spec(spec)
        sys.modules["git"] = git_module
        spec.loader.exec_module(git_module)

    git_module_typed: ModuleType = git_module
    try:
        search_module = importlib.import_module("git.search")
    except ModuleNotFoundError:
        search_module = None

    git_searcher = getattr(git_module_typed, "GitSearcher", None)
    search_result = getattr(git_module_typed, "SearchResult", None)
    repo_cls = getattr(git_module_typed, "Repo", None)

    if search_module is not None:
        if git_searcher is None and hasattr(search_module, "GitSearcher"):
            git_searcher = getattr(search_module, "GitSearcher")
            monkeypatch.setattr(git_module_typed, "GitSearcher", git_searcher, raising=False)
        if search_result is None and hasattr(search_module, "SearchResult"):
            search_result = getattr(search_module, "SearchResult")
            monkeypatch.setattr(git_module_typed, "SearchResult", search_result, raising=False)

    if git_searcher is None or repo_cls is None or search_result is None:
        pytest.skip("Git search components unavailable")

    return git_searcher, repo_cls, search_result


@pytest.mark.requires_git
def test_build_index_tracks_files(
    tmp_path: Path, git_components: tuple[type[Any], type[Any], type[Any]]
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
    tmp_path: Path, git_components: tuple[type[Any], type[Any], type[Any]]
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
