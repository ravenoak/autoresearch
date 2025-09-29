"""Lightweight stub of the :mod:`git` package used in tests.

The real project depends on GitPython for the optional local Git search
backend. The test environment does not install the dependency, but unit tests
expect the module to be importable. This stub provides the minimal ``Repo`` API
required by the tests without pulling in the heavyweight dependency.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace, TracebackType
from typing import Iterable, Iterator
from uuid import uuid4

__all__ = ["Repo", "GitSearcher", "SearchResult"]


class Repo:
    """Minimal stand-in for :class:`git.Repo`.

    Only the features exercised in the tests are implemented. Additional
    methods can be added on demand as the test surface grows.
    """

    _registry: dict[Path, "Repo"] = {}

    class Commit:
        """Simplified commit object."""

        def __init__(self, message: str, parents: list["Repo.Commit"] | None = None) -> None:
            self.message = message
            self.parents = parents or []
            self.hexsha = uuid4().hex
            self.author = SimpleNamespace(name="stub")
            self.committed_datetime = datetime.now()

        def diff(
            self,
            parent: "Repo.Commit" | None = None,
            create_patch: bool | None = None,
        ) -> list[SimpleNamespace]:
            """Return an empty diff list."""

            return []

    class Head:
        """Represents the current ``HEAD`` reference."""

        def __init__(self, commit: "Repo.Commit") -> None:
            self.commit = commit

    class Branch:
        """Simple branch representation exposing only ``name``."""

        def __init__(self, name: str) -> None:
            self.name = name

    class Index:
        """Simplified representation of a Git index."""

        def __init__(self, repo: "Repo") -> None:
            self.repo = repo

        def add(self, files: list[str]) -> None:  # pragma: no cover - no-op
            """Pretend to stage files for commit."""

        def commit(self, message: str) -> "Repo.Commit":  # pragma: no cover - minimal behavior
            """Create a commit and update ``HEAD``.

            Args:
                message: Commit message.

            Returns:
                The newly created :class:`Repo.Commit`.
            """

            parents = [self.repo._commits[-1]] if self.repo._commits else []
            commit = Repo.Commit(message, parents)
            self.repo._commits.append(commit)
            self.repo._head = Repo.Head(commit)
            return commit

    def __new__(cls, path: str | Path | None = None) -> "Repo":
        if path is not None:
            repo_path = Path(path)
            if repo_path in cls._registry:
                return cls._registry[repo_path]
            inst = super().__new__(cls)
            cls._registry[repo_path] = inst
            return inst
        return super().__new__(cls)

    def __init__(self, path: str | Path | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.path = Path(path) if path is not None else None
        self.git_dir: Path | None = self.path / ".git" if self.path else None
        self.working_tree_dir: str | None = str(self.path) if self.path else None
        self._commits: list[Repo.Commit] = []
        self._head: Repo.Head | None = None
        self.index = self.Index(self)
        self.active_branch = self.Branch("main")
        self.heads = [self.active_branch]

    @staticmethod
    def init(path: str | Path) -> "Repo":
        """Create a new repository instance.

        Args:
            path: Location of the repository.

        Returns:
            Newly initialised :class:`Repo` object.
        """

        repo_path = Path(path)
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / ".git").mkdir(exist_ok=True)
        return Repo(repo_path)

    @property
    def head(self) -> "Repo.Head":
        """Return the current ``HEAD`` reference.

        Raises:
            AttributeError: If no commits have been created yet.
        """

        if self._head is None:
            raise AttributeError("Repository has no HEAD")
        return self._head

    def close(self) -> None:  # pragma: no cover - placeholder
        """Close the repository."""

    def __enter__(self) -> "Repo":
        """Return ``self`` to support context manager usage."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Invoke :meth:`close` when leaving a ``with`` block."""

        self.close()

    def iter_commits(
        self,
        branches: Iterable[str] | None = None,
        max_count: int | None = None,
    ) -> Iterator["Repo.Commit"]:
        """Yield commits from newest to oldest.

        Args:
            branches: Ignored in the stub.
            max_count: Maximum number of commits to yield.

        Yields:
            Repo.Commit: Commit objects in reverse chronological order.
        """

        commits = list(reversed(self._commits))
        if max_count is not None:
            commits = commits[:max_count]
        for commit in commits:
            yield commit


from .search import GitSearcher, SearchResult  # noqa: E402
