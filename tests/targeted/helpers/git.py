"""Utilities for loading Git search components in targeted tests."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, TypeAlias, cast

if TYPE_CHECKING:  # pragma: no cover - import for static analysis only
    from git import GitSearcher as _GitSearcher
    from git import Repo as _Repo
    from git.search import SearchResult as _SearchResult
else:  # pragma: no cover - provide runtime placeholders for type aliasing
    _GitSearcher = _Repo = _SearchResult = object

GitComponentTypes: TypeAlias = tuple[
    type[_GitSearcher],
    type[_Repo],
    type[_SearchResult],
]


class GitComponentsUnavailable(RuntimeError):
    """Raised when Git search components cannot be located."""


def _load_stubbed_git() -> ModuleType:
    """Load the in-repo Git stub when GitPython is unavailable."""

    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "src" / "git" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "git",
        module_path,
        submodule_search_locations=[str(module_path.parent)],
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise GitComponentsUnavailable("git module unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("git", module)
    spec.loader.exec_module(module)
    return module


def _import_git_module() -> ModuleType:
    """Return the git module, loading the stub when necessary."""

    try:
        return importlib.import_module("git")
    except ModuleNotFoundError:
        return _load_stubbed_git()


def load_git_components() -> GitComponentTypes:
    """Return the Git search classes without mutating module attributes."""

    git_module = _import_git_module()
    repo_cls = getattr(git_module, "Repo", None)
    git_searcher = getattr(git_module, "GitSearcher", None)
    search_result = getattr(git_module, "SearchResult", None)

    try:
        search_module = importlib.import_module("git.search")
    except ModuleNotFoundError:
        search_module = None

    if git_searcher is None and search_module is not None:
        git_searcher = getattr(search_module, "GitSearcher", None)
    if search_result is None and search_module is not None:
        search_result = getattr(search_module, "SearchResult", None)

    if repo_cls is None or git_searcher is None or search_result is None:
        raise GitComponentsUnavailable("Git search components unavailable")

    return (
        cast(type[_GitSearcher], git_searcher),
        cast(type[_Repo], repo_cls),
        cast(type[_SearchResult], search_result),
    )


__all__ = ["GitComponentsUnavailable", "GitComponentTypes", "load_git_components"]
