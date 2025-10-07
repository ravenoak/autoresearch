"""Unit tests for archive_task_coverage_minimal helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.archive_task_coverage_minimal import (
    _EXPECTED_LOG_TAIL,
    _copy_coverage_outputs,
    _validate_coverage_xml,
    _validate_log_tail,
)


def test_validate_log_tail_accepts_expected_final_line(tmp_path: Path) -> None:
    log_file = tmp_path / "coverage.log"
    log_file.write_text("noise\n\n  \t\n" + _EXPECTED_LOG_TAIL + "\n", encoding="utf-8")

    _validate_log_tail(log_file)


def test_validate_log_tail_rejects_incorrect_tail(tmp_path: Path) -> None:
    log_file = tmp_path / "coverage.log"
    log_file.write_text("first line\nsecond line\n", encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        _validate_log_tail(log_file)

    assert "Unexpected final log line" in str(excinfo.value)


def _write_coverage_xml(tmp_path: Path, line_rate: str | None) -> Path:
    attributes = [] if line_rate is None else [f' line-rate="{line_rate}"']
    xml = "".join([
        "<?xml version=\"1.0\" ?>\n",
        "<coverage",
        *attributes,
        ">\n",
        "    <packages></packages>\n",
        "</coverage>\n",
    ])
    coverage_file = tmp_path / "coverage.xml"
    coverage_file.write_text(xml, encoding="utf-8")
    return coverage_file


def test_validate_coverage_xml_accepts_threshold(tmp_path: Path) -> None:
    coverage_file = _write_coverage_xml(tmp_path, "0.95")

    _validate_coverage_xml(coverage_file)


def test_validate_coverage_xml_rejects_low_rate(tmp_path: Path) -> None:
    coverage_file = _write_coverage_xml(tmp_path, "0.5")

    with pytest.raises(ValueError) as excinfo:
        _validate_coverage_xml(coverage_file)

    assert "below the 0.900 requirement" in str(excinfo.value)


def test_validate_coverage_xml_requires_line_rate(tmp_path: Path) -> None:
    coverage_file = _write_coverage_xml(tmp_path, None)

    with pytest.raises(ValueError) as excinfo:
        _validate_coverage_xml(coverage_file)

    assert "missing required line-rate" in str(excinfo.value)


def test_copy_coverage_outputs_rejects_invalid_line_rate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "baseline" / "archive").mkdir(parents=True)
    htmlcov_dir = tmp_path / "htmlcov"
    htmlcov_dir.mkdir()
    (htmlcov_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    _write_coverage_xml(tmp_path, "0.5")

    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError) as excinfo:
        _copy_coverage_outputs("20240101T000000Z")

    assert "below the 0.900 requirement" in str(excinfo.value)
