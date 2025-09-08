"""Tests for Git repository indexing and search."""

from pathlib import Path

import pytest

from git import GitSearcher, Repo


@pytest.mark.requires_git
def test_build_index_tracks_files(tmp_path: Path) -> None:
    """File contents are indexed by relative path."""
    repo = Repo.init(tmp_path)
    file_path = tmp_path / "file.txt"
    file_path.write_text("alpha\n")
    repo.index.add(["file.txt"])
    repo.index.commit("add file")
    searcher = GitSearcher(tmp_path)
    searcher.build_index()
    assert Path("file.txt") in searcher.index


@pytest.mark.requires_git
def test_search_finds_file_and_commit(tmp_path: Path) -> None:
    """Search returns matches from files and commit messages."""
    repo = Repo.init(tmp_path)
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello world\nsecond line\n")
    repo.index.add(["note.txt"])
    repo.index.commit("greeting commit")
    searcher = GitSearcher(tmp_path)
    searcher.build_index()
    results = searcher.search("hello")
    assert any(r.path == Path("note.txt") and r.line == 1 for r in results)
    commit_hits = searcher.search("greeting")
    assert any(r.path is None and "greeting commit" in r.text for r in commit_hits)
