"""Ensure algorithm docs exist for newly covered modules."""

from pathlib import Path

DOCS = [
    "docs/algorithms/cli_backup.md",
    "docs/algorithms/cli_utils.md",
    "docs/algorithms/config_utils.md",
    "docs/algorithms/errors.md",
    "docs/algorithms/extensions.md",
    "docs/algorithms/streamlit_app.md",
    "docs/algorithms/synthesis.md",
    "docs/algorithms/test_tools.md",
]


def repo_root() -> Path:
    """Return repository root."""
    return Path(__file__).resolve().parents[2]


def test_algorithm_docs_exist() -> None:
    """All listed algorithm docs must exist."""
    root = repo_root()
    for rel_path in DOCS:
        assert (root / rel_path).is_file(), f"Missing documentation: {rel_path}"
