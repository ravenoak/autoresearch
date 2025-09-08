"""Repository indexing and search utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:  # pragma: no cover - real GitPython may be installed
    from git import Repo as GitRepo
except Exception:  # pragma: no cover - fallback to stub
    from . import Repo as GitRepo

__all__ = ["GitSearcher", "SearchResult"]


@dataclass(frozen=True)
class SearchResult:
    """Single search hit."""

    path: Optional[Path]
    line: Optional[int]
    text: str


class GitSearcher:
    """Index and search a Git repository.

    Args:
        repo_path: Location of the repository working tree.
    """

    def __init__(self, repo_path: str | Path) -> None:
        self.repo = GitRepo(repo_path)
        self._index: dict[Path, list[str]] = {}
        self._commit_messages: list[str] = []

    @property
    def index(self) -> dict[Path, list[str]]:
        """Read-only view of the file index."""

        return self._index

    def build_index(self) -> None:
        """Populate the file and commit indexes."""

        root = Path(self.repo.working_tree_dir or ".")
        for file in root.rglob("*"):
            if not file.is_file():
                continue
            rel = file.relative_to(root)
            try:
                lines = file.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            self._index[rel] = lines
        self._commit_messages = [c.message for c in self.repo.iter_commits()]

    def search(self, query: str) -> List[SearchResult]:
        """Return results that contain ``query``.

        The match is case-insensitive and scans both indexed files and commit
        messages.

        Args:
            query: Substring to look for.

        Returns:
            List of :class:`SearchResult` objects ordered by path and line.
        """

        needle = query.lower()
        results: list[SearchResult] = []
        for path, lines in sorted(self._index.items()):
            for lineno, line in enumerate(lines, 1):
                if needle in line.lower():
                    results.append(SearchResult(path, lineno, line))
        for msg in self._commit_messages:
            if needle in msg.lower():
                results.append(SearchResult(None, None, msg))
        return results
