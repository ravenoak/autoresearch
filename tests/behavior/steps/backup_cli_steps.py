from pathlib import Path
from pytest_bdd import scenario, given, when, then, parsers

from autoresearch.main import app as cli_app
from autoresearch.config import ConfigLoader


@given("a temporary work directory", target_fixture="work_dir")
def work_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@when(parsers.parse('I run `autoresearch config backup create --dir {dir}`'))
def run_backup_create(dir, cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "backup", "create", "--dir", dir])
    bdd_context["result"] = result
    bdd_context["backup_dir"] = Path(dir)


@then("the backup directory should contain a backup file")
def check_backup(bdd_context, work_dir):
    backup_dir = work_dir / bdd_context["backup_dir"]
    assert backup_dir.exists() and any(backup_dir.iterdir())
    assert bdd_context["result"].exit_code == 0


@scenario("../features/backup_cli.feature", "Create backup")
def test_backup_create():
    pass
