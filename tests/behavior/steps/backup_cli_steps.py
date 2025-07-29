from pathlib import Path
from datetime import datetime
from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.main import app as cli_app
from autoresearch.config import ConfigLoader
from autoresearch.storage_backup import BackupManager, BackupInfo


@given("a temporary work directory", target_fixture="work_dir")
def work_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@given(parsers.parse('a dummy backup file "{path}"'))
def dummy_backup_file(work_dir, path):
    file_path = work_dir / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("dummy")
    return file_path


@when(parsers.parse('I run `autoresearch config backup create --dir {dir}`'))
def run_backup_create(dir, cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "backup", "create", "--dir", dir])
    bdd_context["result"] = result
    bdd_context["backup_dir"] = Path(dir)


@when(parsers.parse('I run `autoresearch config backup list --dir {dir}`'))
def run_backup_list(dir, cli_runner, bdd_context, monkeypatch):
    monkeypatch.setattr(
        BackupManager,
        "list_backups",
        lambda d: [
            BackupInfo(
                path=f"{dir}/dummy.tar",
                timestamp=datetime.now(),
                compressed=True,
                size=10,
            )
        ],
    )
    result = cli_runner.invoke(cli_app, ["config", "backup", "list", "--dir", dir])
    bdd_context["result"] = result


@when(parsers.parse('I run `autoresearch config backup restore {path} --dir {dir} --force`'))
def run_backup_restore(path, dir, cli_runner, bdd_context, monkeypatch):
    monkeypatch.setattr(
        BackupManager,
        "restore_backup",
        lambda backup_path, target_dir=None, db_filename="db.duckdb", rdf_filename="store.rdf": {
            "db_path": "db.duckdb",
            "rdf_path": "store.rdf",
        },
    )
    result = cli_runner.invoke(
        cli_app,
        ["config", "backup", "restore", path, "--dir", dir, "--force"],
    )
    bdd_context["result"] = result


@then("the backup directory should contain a backup file")
def check_backup(bdd_context, work_dir):
    backup_dir = work_dir / bdd_context["backup_dir"]
    assert backup_dir.exists() and any(backup_dir.iterdir())
    assert bdd_context["result"].exit_code == 0


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    assert bdd_context["result"].exit_code == 0


@scenario("../features/backup_cli.feature", "Create backup")
def test_backup_create():
    pass


@scenario("../features/backup_cli.feature", "List backups")
def test_backup_list():
    pass


@scenario("../features/backup_cli.feature", "Restore backup")
def test_backup_restore_scenario():
    pass
