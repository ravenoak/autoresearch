"""Tests for Git repository indexing and search."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import pytest

from autoresearch.config.models import ConfigModel, RepositoryManifestEntry
from autoresearch.search.core import _local_git_backend
from autoresearch.storage import StorageManager
from tests.targeted.helpers.git import (
    GitComponentTypes,
    GitComponentsUnavailable,
    load_git_components,
)
from tests.typing_helpers import TypedFixture

if TYPE_CHECKING:  # pragma: no cover - used only for static analysis
    from git.search import SearchResult


@contextmanager
def _dummy_connection():
    class DummyConn:
        def execute(self, *args, **kwargs):
            class Cursor:
                def fetchall(self_inner):
                    return []

            return Cursor()

    yield DummyConn()


@pytest.fixture()
def git_components() -> TypedFixture[GitComponentTypes]:
    """Return Git search classes, installing stubs when extras are absent."""

    try:
        return load_git_components()
    except GitComponentsUnavailable as exc:
        pytest.skip(str(exc))


@pytest.mark.requires_git
def test_build_index_tracks_files(tmp_path: Path, git_components: GitComponentTypes) -> None:
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
def test_search_finds_file_and_commit(tmp_path: Path, git_components: GitComponentTypes) -> None:
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
        isinstance(result, SearchResultCls) and result.path == Path("note.txt") and result.line == 1
        for result in results
    )
    commit_hits: Iterable["SearchResult"] = searcher.search("greeting")
    assert any(
        isinstance(result, SearchResultCls)
        and result.path is None
        and "greeting commit" in result.text
        for result in commit_hits
    )


def test_manifest_entry_derives_slug_and_branches() -> None:
    """Repository manifest entries normalise derived fields."""

    entry = RepositoryManifestEntry(
        path="/tmp/example-repo",
        branches=["main", " feature ", "main"],
        namespace="Team.Namespace",
    )
    assert entry.slug == "example-repo"
    assert entry.branches == ["main", "feature"]
    assert entry.namespace == "Team.Namespace"


@pytest.mark.requires_git
def test_local_git_backend_manifest_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_components: GitComponentTypes,
) -> None:
    """Manifest-driven searches return provenance for each repository."""

    _, Repo, _ = git_components
    query = "shared-manifest-term"
    manifest_entries: list[dict[str, str]] = []
    for slug, namespace in (("alpha", "workspace.alpha"), ("beta", "workspace.beta")):
        repo_path = tmp_path / slug
        repo = Repo.init(repo_path)
        file_path = repo_path / "README.md"
        file_path.write_text(f"{slug} {query}\n", encoding="utf-8")
        repo.index.add(["README.md"])
        repo.index.commit(f"{slug} commit {query}")
        manifest_entries.append(
            {
                "slug": slug,
                "path": str(repo_path),
                "branches": [repo.active_branch.name],
                "namespace": namespace,
            }
        )

    cfg = ConfigModel.model_validate(
        {
            "search": {
                "backends": ["local_git"],
                "local_git": {"manifest": manifest_entries, "history_depth": 5},
                "local_file": {"file_types": ["md", "txt"]},
            }
        }
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Repo", Repo)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_dummy_connection))

    results = _local_git_backend(query, max_results=6)
    repositories = {result.get("repository") for result in results}
    assert {"alpha", "beta"}.issubset(repositories)
    for result in results:
        provenance = result.get("provenance", {})
        assert provenance.get("repository") == result.get("repository")
        assert result.get("commit", "").startswith(f"{result['repository']}@")

    commit_results = _local_git_backend("commit", max_results=4)
    assert any(r.get("commit_hash") for r in commit_results)


@pytest.mark.requires_git
def test_local_git_backend_workspace_filters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    git_components: GitComponentTypes,
) -> None:
    """Workspace hints restrict local git search to matching resources."""

    _, Repo, _ = git_components
    repo_path = tmp_path / "alpha"
    repo = Repo.init(repo_path)
    include_file = repo_path / "include.md"
    include_file.write_text("workspace scoped term", encoding="utf-8")
    exclude_file = repo_path / "skip.txt"
    exclude_file.write_text("workspace scoped term", encoding="utf-8")
    repo.index.add(["include.md", "skip.txt"])
    repo.index.commit("add files")

    cfg = ConfigModel.model_validate(
        {
            "search": {
                "backends": ["local_git"],
                "local_git": {
                    "manifest": [
                        {
                            "slug": "alpha",
                            "path": str(repo_path),
                            "branches": [repo.active_branch.name],
                            "namespace": "audit.alpha",
                        }
                    ],
                    "history_depth": 5,
                },
                "local_file": {"file_types": ["md", "txt"]},
            }
        }
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    monkeypatch.setattr("autoresearch.search.core.Repo", Repo)
    monkeypatch.setattr(StorageManager, "connection", staticmethod(_dummy_connection))

    workspace_hints = {
        "workspace_id": "workspace-alpha",
        "manifest_id": "manifest-1",
        "manifest_version": 1,
        "resources": {
            "wsres-alpha": {
                "resource_id": "wsres-alpha",
                "kind": "repo",
                "reference": "alpha@HEAD",
                "citation_required": True,
            }
        },
        "search": {
            "repositories": {
                "alpha": {
                    "slug": "alpha",
                    "resource_ids": ("wsres-alpha",),
                    "resource_specs": (
                        {
                            "resource_id": "wsres-alpha",
                            "file_globs": ("**/*.md",),
                            "path_prefixes": (),
                            "file_types": ("md",),
                            "namespaces": ("audit.alpha",),
                        },
                    ),
                    "namespace": "audit.alpha",
                }
            }
        },
        "storage": {"namespaces": ("audit.alpha",)},
    }

    results = _local_git_backend(
        "workspace scoped term",
        max_results=5,
        workspace_hints=workspace_hints,
        workspace_filters={"resource_ids": ["wsres-alpha"]},
    )
    assert results
    urls = {result.get("url") for result in results}
    assert str(include_file) in urls
    assert str(exclude_file) not in urls
    assert all(result.get("workspace_resource_id") == "wsres-alpha" for result in results)
