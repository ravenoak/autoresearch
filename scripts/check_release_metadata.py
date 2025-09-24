"""Validate release metadata consistency across project files.

Usage:
    uv run python scripts/check_release_metadata.py

The check verifies that the version and release date recorded in
``pyproject.toml``, ``src/autoresearch/__init__.py``, and the top release entry
in ``CHANGELOG.md`` are aligned. Intended to run via ``task`` targets.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import tomllib


RELEASE_HEADER_PATTERN = re.compile(r"^## \[(?P<version>[^\]]+)\] - (?P<date>.+)$")


class ReleaseMetadataError(RuntimeError):
    """Raised when release metadata is inconsistent."""


@dataclass(frozen=True)
class ReleaseMetadata:
    """Normalized release metadata extracted from project files."""

    version: str
    release_date: str


def parse_args() -> argparse.Namespace:
    """Return CLI arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the repository root (defaults to project root)",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=None,
        help="Path to the changelog file (defaults to CHANGELOG.md)",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=None,
        help="Path to the pyproject file (defaults to pyproject.toml)",
    )
    parser.add_argument(
        "--package-init",
        type=Path,
        default=None,
        help="Path to autoresearch/__init__.py",
    )
    return parser.parse_args()


def load_pyproject(path: Path) -> ReleaseMetadata:
    """Load version and release date from ``pyproject.toml``."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not project or "version" not in project:
        raise ReleaseMetadataError("`project.version` missing from pyproject.toml")
    version = project["version"]

    tool_section = data.get("tool", {})
    autoresearch_section = tool_section.get("autoresearch", {})
    release_date = autoresearch_section.get("release_date")
    if release_date is None:
        raise ReleaseMetadataError(
            "`tool.autoresearch.release_date` missing from pyproject.toml",
        )
    return ReleaseMetadata(version=version, release_date=release_date)


def load_init_metadata(path: Path) -> ReleaseMetadata:
    """Extract fallback metadata literals from ``autoresearch.__init__``."""

    source = path.read_text(encoding="utf-8")
    version_literals = list(_iter_literal_assignments(source, "__version__"))
    if not version_literals:
        raise ReleaseMetadataError("`__version__` literal not found in __init__.py")

    release_literals = list(_iter_literal_assignments(source, "__release_date__"))
    if not release_literals:
        raise ReleaseMetadataError(
            "`__release_date__` literal not found in __init__.py",
        )

    return ReleaseMetadata(version=version_literals[-1], release_date=release_literals[-1])


def _iter_literal_assignments(source: str, symbol: str) -> Iterable[str]:
    """Yield string literals assigned to ``symbol`` within ``source``."""

    pattern = re.compile(
        rf"{re.escape(symbol)}\s*=\s*([\"\'])(?P<value>[^\"\']+)\1",
        re.MULTILINE,
    )
    for match in pattern.finditer(source):
        yield match.group("value")


def load_changelog_metadata(path: Path) -> ReleaseMetadata:
    """Read the first release entry from ``CHANGELOG.md``."""

    for line in path.read_text(encoding="utf-8").splitlines():
        match = RELEASE_HEADER_PATTERN.match(line.strip())
        if not match:
            continue
        version = match.group("version").strip()
        if version.lower() == "unreleased":
            # Skip the placeholder entry at the top of the changelog.
            continue
        release_date = match.group("date").strip()
        if not release_date:
            raise ReleaseMetadataError("Changelog entry missing release date")
        return ReleaseMetadata(version=version, release_date=release_date)
    raise ReleaseMetadataError("No release entries found in CHANGELOG.md")


def validate_alignment(*entries: ReleaseMetadata) -> None:
    """Ensure all provided metadata entries agree on version and date."""

    versions = {entry.version for entry in entries}
    if len(versions) != 1:
        raise ReleaseMetadataError(
            f"Mismatched versions detected: {', '.join(sorted(versions))}",
        )

    release_dates = {entry.release_date for entry in entries}
    if len(release_dates) != 1:
        raise ReleaseMetadataError(
            "Mismatched release dates detected: "
            f"{', '.join(sorted(release_dates))}",
        )

    release_date = next(iter(release_dates))
    if release_date != "Unreleased" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", release_date):
        raise ReleaseMetadataError(
            "Release date must be 'Unreleased' or follow YYYY-MM-DD format",
        )


def main() -> int:
    """Entry point for the CLI."""

    args = parse_args()
    repo_root = args.repo_root
    changelog_path = args.changelog or repo_root / "CHANGELOG.md"
    pyproject_path = args.pyproject or repo_root / "pyproject.toml"
    init_path = args.package_init or repo_root / "src" / "autoresearch" / "__init__.py"

    try:
        pyproject = load_pyproject(pyproject_path)
        package_metadata = load_init_metadata(init_path)
        changelog = load_changelog_metadata(changelog_path)
        validate_alignment(pyproject, package_metadata, changelog)
    except (FileNotFoundError, ReleaseMetadataError) as exc:
        print(f"Release metadata check failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Release metadata aligned: version={version}, date={date}".format(
            version=pyproject.version,
            date=pyproject.release_date,
        ),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
