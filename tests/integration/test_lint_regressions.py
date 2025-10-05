"""Regression tests guarding against lint regressions in critical modules."""

from __future__ import annotations

from pathlib import Path

from flake8.api import legacy as flake8_legacy


SELECT_CODES = ("F401", "F402", "F811", "W291", "W293", "W391")
TARGET_PATHS = (
    Path("src/autoresearch/search/core.py"),
    Path("tests/behavior/fixtures"),
    Path("tests/integration"),
)


def test_no_unused_imports_or_whitespace_regressions() -> None:
    """Ensure core search and integration suites stay free from lint regressions."""

    repo_root = Path(__file__).resolve().parents[2]
    style = flake8_legacy.get_style_guide(select=SELECT_CODES, quiet=1)
    targets = [str(repo_root / path) for path in TARGET_PATHS]

    report = style.check_files(targets)

    assert (
        report.total_errors == 0
    ), f"flake8 reported {report.total_errors} issues for {targets}"
