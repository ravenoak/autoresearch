from pytest_bdd import scenario, given, when, then

from autoresearch.main import app as cli_app
from autoresearch.config import ConfigLoader


def pytest_configure(config):  # pragma: no cover - silence unused warning
    pass


@given("a temporary work directory", target_fixture="work_dir")
def work_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ConfigLoader.reset_instance()
    return tmp_path


@when("I run `autoresearch config init --force` in a temporary directory")
def run_config_init(work_dir, cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "init", "--force"])
    bdd_context["result"] = result


@when("I run `autoresearch config validate`")
def run_config_validate(cli_runner, bdd_context):
    result = cli_runner.invoke(cli_app, ["config", "validate"])
    bdd_context["result"] = result


@then('the files "autoresearch.toml" and ".env" should be created')
def check_config_files(work_dir):
    assert (work_dir / "autoresearch.toml").exists()
    assert (work_dir / ".env").exists()


@then("the CLI should exit successfully")
def cli_success(bdd_context):
    assert bdd_context["result"].exit_code == 0


@scenario("../features/config_cli.feature", "Initialize configuration files")
def test_config_init():
    pass


@scenario("../features/config_cli.feature", "Validate configuration files")
def test_config_validate():
    pass
