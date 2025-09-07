"""Lightweight stub of the :mod:`git` package used in tests.

The real project depends on GitPython for the optional local Git search
backend.  The test environment does not install the dependency, but unit tests
expect the module to be importable.  This stub provides the minimal ``Repo``
API required by the tests without pulling in the heavyweight dependency.
"""

from __future__ import annotations

from pathlib import Path


class Repo:
    """Minimal stand-in for :class:`git.Repo`.

    Only the features exercised in the tests are implemented. Additional
    methods can be added on demand as the test surface grows.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self.index = self.Index()

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
        return Repo(repo_path)

    class Index:
        """Simplified representation of a Git index."""

        def add(self, files: list[str]) -> None:  # pragma: no cover - no-op
            """Pretend to stage files for commit."""

        def commit(self, message: str) -> None:  # pragma: no cover - no-op
            """Pretend to commit staged changes."""
