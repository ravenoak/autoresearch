from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner, Result
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.main import app as cli_app
from autoresearch.storage_backup import BackupInfo, BackupManager
from tests.behavior.steps import (
    BehaviorContext,
    get_cli_result,
    get_required,
    set_cli_result,
    set_value,
)
from tests.behavior.utils import backup_restore_result

from .common_steps import assert_cli_success


@pytest.fixture
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate CLI invocations to a temporary working directory."""

    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@given("a temporary work directory", target_fixture="work_dir")
def given_work_dir(work_dir: Path) -> Path:
    """Expose the temporary working directory to the scenario."""

    return work_dir


@given(parsers.parse('a dummy backup file "{path}"'))
def dummy_backup_file(work_dir: Path, path: str) -> Path:
    """Create a placeholder backup archive within the working directory."""

    file_path = work_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("dummy")
    return file_path


@when(parsers.parse("I run `autoresearch config backup create --dir {dir}`"))
def run_backup_create(
    dir: str,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Simulate creating a backup via the CLI."""

    monkeypatch.setattr(BackupManager, "list_backups", lambda _d: [])
    monkeypatch.setattr("autoresearch.storage.StorageManager.setup", lambda *a, **k: None)
    monkeypatch.setattr("autoresearch.storage.setup", lambda *a, **k: None)

    def fake_create_backup(
        backup_dir: str,
        db_filename: str = "kg.duckdb",
        rdf_filename: str = "store.rdf",
        compress: bool = True,
        config: Any | None = None,
    ) -> BackupInfo:
        backup_path = Path(backup_dir) / "dummy.tar"
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        backup_path.write_text("data")
        return BackupInfo(
            path=str(backup_path),
            timestamp=datetime.now(),
            compressed=compress,
            size=1,
        )

    monkeypatch.setattr(BackupManager, "create_backup", fake_create_backup)
    result: Result = cli_runner.invoke(cli_app, ["config", "backup", "create", "--dir", dir])
    set_cli_result(bdd_context, result)
    set_value(bdd_context, "backup_dir", Path(dir))


@when(parsers.parse("I run `autoresearch config backup list --dir {dir}`"))
def run_backup_list(
    dir: str,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Invoke the CLI to list available backups."""

    monkeypatch.setattr("autoresearch.storage.StorageManager.setup", lambda *a, **k: None)
    monkeypatch.setattr("autoresearch.storage.setup", lambda *a, **k: None)
    monkeypatch.setattr(
        BackupManager,
        "list_backups",
        lambda _d: [
            BackupInfo(
                path=f"{dir}/dummy.tar",
                timestamp=datetime.now(),
                compressed=True,
                size=10,
            )
        ],
    )
    result: Result = cli_runner.invoke(cli_app, ["config", "backup", "list", "--dir", dir])
    set_cli_result(bdd_context, result)


@when(parsers.parse("I run `autoresearch config backup restore {path} --dir {dir} --force`"))
def run_backup_restore(
    path: str,
    dir: str,
    cli_runner: CliRunner,
    bdd_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: None,
    restore_environment: None,
) -> None:
    """Restore a backup archive using the CLI."""

    monkeypatch.setattr("autoresearch.storage.StorageManager.setup", lambda *a, **k: None)
    monkeypatch.setattr("autoresearch.storage.setup", lambda *a, **k: None)
    monkeypatch.setattr(
        BackupManager,
        "restore_backup",
        lambda _path, *_a, **_k: backup_restore_result(
            db_path="db.duckdb",
            rdf_path="store.rdf",
        ),
    )
    result: Result = cli_runner.invoke(
        cli_app,
        ["config", "backup", "restore", path, "--dir", dir, "--force"],
    )
    set_cli_result(bdd_context, result)


@then("the backup directory should contain a backup file")
def check_backup(bdd_context: BehaviorContext, work_dir: Path) -> None:
    """Assert the backup directory was populated."""

    backup_dir = get_required(bdd_context, "backup_dir", Path)
    filesystem_path = work_dir / backup_dir
    assert filesystem_path.exists() and any(filesystem_path.iterdir())
    result = get_cli_result(bdd_context)
    assert_cli_success(result)


@then("the CLI should exit successfully")
def cli_success(bdd_context: BehaviorContext) -> None:
    """Validate the CLI invocation succeeded."""

    result = get_cli_result(bdd_context)
    assert_cli_success(result)


@scenario("../features/backup_cli.feature", "Create backup")
def test_backup_create() -> None:
    """Scenario for creating a backup."""


@scenario("../features/backup_cli.feature", "List backups")
def test_backup_list() -> None:
    """Scenario for listing available backups."""


@scenario("../features/backup_cli.feature", "Restore backup")
def test_backup_restore_scenario() -> None:
    """Scenario for restoring a backup."""
