from pytest_bdd import scenario, when, then
from autoresearch.main import app as cli_app


@when('I run `autoresearch gui --port 8502 --no-browser`')
def run_gui_no_browser(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):
    monkeypatch.setattr('subprocess.run', lambda *a, **k: None)
    result = cli_runner.invoke(
        cli_app, ['gui', '--port', '8502', '--no-browser'], catch_exceptions=False
    )
    bdd_context['result'] = result


@when('I run `autoresearch gui --help`')
def run_gui_help(cli_runner, bdd_context, temp_config, isolate_network):
    result = cli_runner.invoke(cli_app, ['gui', '--help'], catch_exceptions=False)
    bdd_context['result'] = result


@then('the CLI should exit successfully')
def cli_success(bdd_context):
    result = bdd_context['result']
    assert result.exit_code == 0
    assert result.stderr == ''


@scenario('../features/gui_cli.feature', 'Launch GUI without opening a browser')
def test_gui_no_browser():
    pass


@scenario('../features/gui_cli.feature', 'Display help for GUI command')
def test_gui_help():
    pass
