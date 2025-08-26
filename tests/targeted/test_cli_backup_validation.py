import io
from pathlib import Path

import pytest
import typer
from rich.console import Console

from autoresearch.cli_backup import _validate_dir, _validate_file


def test_validate_dir_accepts_new_directory(tmp_path):
    console = Console(file=io.StringIO())
    path = _validate_dir(str(tmp_path / "new"), console)
    assert Path(path).name == "new"


def test_validate_dir_rejects_file(tmp_path):
    file_path = tmp_path / "f"
    file_path.write_text("x")
    console = Console(file=io.StringIO())
    with pytest.raises(typer.Exit):
        _validate_dir(str(file_path), console)


def test_validate_file_checks_existence(tmp_path):
    file_path = tmp_path / "backup.bak"
    file_path.write_text("data")
    console = Console(file=io.StringIO())
    assert _validate_file(str(file_path), console) == str(file_path)


def test_validate_file_rejects_missing(tmp_path):
    file_path = tmp_path / "missing"
    console = Console(file=io.StringIO())
    with pytest.raises(typer.Exit):
        _validate_file(str(file_path), console)
