from pytest_bdd import scenario, when, then
from autoresearch.main import app as cli_app
from autoresearch.orchestration.orchestrator import Orchestrator


@when('I run `autoresearch search "What is artificial intelligence?" --reasoning-mode direct`')
def run_search_direct(cli_runner, bdd_context, monkeypatch, dummy_query_response, temp_config, isolate_network):
    monkeypatch.setattr(Orchestrator, 'run_query', lambda *a, **k: dummy_query_response)
    result = cli_runner.invoke(
        cli_app,
        ['search', 'What is artificial intelligence?', '--reasoning-mode', 'direct'],
        catch_exceptions=False,
    )
    bdd_context['result'] = result


@when('I run `autoresearch search`')
def run_search_missing(cli_runner, bdd_context, temp_config, isolate_network):
    result = cli_runner.invoke(cli_app, ['search'], catch_exceptions=False)
    bdd_context['result'] = result


@then('the CLI should exit successfully')
def cli_success(bdd_context):
    result = bdd_context['result']
    assert result.exit_code == 0
    assert result.stderr == ''


@then('the CLI should exit with an error')
def cli_error(bdd_context):
    result = bdd_context['result']
    assert result.exit_code != 0
    assert result.stderr != '' or result.exception is not None


@scenario('../features/search_cli.feature', 'Run a basic search query')
def test_search_direct():
    pass


@scenario('../features/search_cli.feature', 'Missing query argument')
def test_search_missing():
    pass
