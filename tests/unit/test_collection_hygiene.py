"""Unit tests for collection-time hygiene guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import (
    enforce_future_annotations_import_order,
    find_future_annotations_import_violations,
)


def _write_module(path: Path, contents: str) -> Path:
    path.write_text(contents, encoding="utf-8")
    return path


def test_guard_flags_imports_before_future_directive(tmp_path: Path) -> None:
    offending = _write_module(
        tmp_path / "offender.py",
        "import os\nfrom __future__ import annotations\n",
    )

    violations = find_future_annotations_import_violations([offending])

    assert violations
    assert offending.name in violations[0]
    assert "import os" in violations[0]


def test_guard_flags_assignments_before_future_directive(tmp_path: Path) -> None:
    offending = _write_module(
        tmp_path / "assignment_offender.py",
        "VALUE = 1\nfrom __future__ import annotations\n",
    )

    violations = find_future_annotations_import_violations([offending])

    assert violations
    assert "VALUE = 1" in violations[0]


def test_guard_ignores_valid_future_import_order(tmp_path: Path) -> None:
    valid = _write_module(
        tmp_path / "valid.py",
        '"""Docstring."""\nfrom __future__ import annotations\nimport os\n',
    )

    assert find_future_annotations_import_violations([valid]) == []


def test_guard_accepts_repo_conftest() -> None:
    repo_conftest = Path(__file__).resolve().parents[1] / "conftest.py"

    assert repo_conftest.exists()
    assert find_future_annotations_import_violations([repo_conftest]) == []


def test_enforce_guard_raises_usage_error(tmp_path: Path) -> None:
    offending = _write_module(
        tmp_path / "offender.py",
        "import sys\nfrom __future__ import annotations\n",
    )

    with pytest.raises(pytest.UsageError) as excinfo:
        enforce_future_annotations_import_order([offending])

    message = str(excinfo.value)
    assert "offender.py" in message
    assert "import sys" in message
