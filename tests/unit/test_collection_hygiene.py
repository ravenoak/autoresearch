"""Unit tests for collection-time hygiene guards."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import find_future_annotations_import_violations


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


def test_guard_ignores_valid_future_import_order(tmp_path: Path) -> None:
    valid = _write_module(
        tmp_path / "valid.py",
        '"""Docstring."""\nfrom __future__ import annotations\nimport os\n',
    )

    assert find_future_annotations_import_violations([valid]) == []
