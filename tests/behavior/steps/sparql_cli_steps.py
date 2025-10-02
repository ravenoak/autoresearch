from tests.behavior.context import BehaviorContext
from pytest_bdd import scenario, when, then
from autoresearch.main import app as cli_app


@when('I run `autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"`')
def run_sparql_query(cli_runner, bdd_context: BehaviorContext, monkeypatch, temp_config, isolate_network):
    monkeypatch.setattr('autoresearch.main.app._cli_sparql', lambda *a, **k: None)
    result = cli_runner.invoke(
        cli_app,
        ['sparql', 'SELECT ?s WHERE { ?s a <http://example.com/B> }'],
        catch_exceptions=False,
    )
    bdd_context['result'] = result


@when('I run `autoresearch sparql "INVALID QUERY"`')
def run_sparql_invalid(cli_runner, bdd_context: BehaviorContext, monkeypatch, temp_config, isolate_network):
    def _raise(*a, **k):
        raise ValueError('invalid')
    monkeypatch.setattr('autoresearch.main.app._cli_sparql', _raise)
    result = cli_runner.invoke(cli_app, ['sparql', 'INVALID QUERY'], catch_exceptions=False)
    bdd_context['result'] = result


@then('the CLI should exit successfully')
def cli_success(bdd_context: BehaviorContext):
    result = bdd_context['result']
    assert result.exit_code == 0
    assert result.stderr == ''


@then('the CLI should exit with an error')
def cli_error(bdd_context: BehaviorContext):
    result = bdd_context['result']
    assert result.exit_code != 0
    assert result.stderr != '' or result.exception is not None


@scenario('../features/sparql_cli.feature', 'Execute a SPARQL query with reasoning')
def test_sparql_success():
    pass


@scenario('../features/sparql_cli.feature', 'Invalid SPARQL query')
def test_sparql_invalid():
    pass
