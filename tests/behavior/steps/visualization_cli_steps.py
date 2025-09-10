from pathlib import Path
from pytest_bdd import scenario, when, then

from autoresearch.main import app as cli_app


@when('I run `autoresearch visualize "{query}" graph.png`')
def run_visualize_query(
    cli_runner, bdd_context, monkeypatch, temp_config, isolate_network, query
):
    output_path = Path.cwd() / 'graph.png'

    def fake_visualize(q, output, layout='spring'):
        Path(output).touch()

    monkeypatch.setattr('autoresearch.main.app._cli_visualize_query', fake_visualize)
    result = cli_runner.invoke(
        cli_app, ['visualize', query, str(output_path)], catch_exceptions=False
    )
    bdd_context['result'] = result


@when('I run `autoresearch visualize-rdf rdf_graph.png`')
def run_visualize_rdf(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):
    monkeypatch.setattr('autoresearch.main.app._cli_visualize', lambda *a, **k: None)
    result = cli_runner.invoke(cli_app, ['visualize-rdf', 'rdf_graph.png'], catch_exceptions=False)
    bdd_context['result'] = result


@when('I run `autoresearch visualize "What is quantum computing?"')
def run_visualize_missing(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):
    def _raise(*a, **k):
        raise RuntimeError('missing output')
    monkeypatch.setattr('autoresearch.main.app._cli_visualize_query', _raise)
    result = cli_runner.invoke(cli_app, ['visualize', 'What is quantum computing?'], catch_exceptions=False)
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


@then('the file "graph.png" should be created')
def check_graph_created():
    assert Path('graph.png').exists()


@scenario('../features/visualization_cli.feature', 'Generate a query graph PNG')
def test_visualize_query():
    pass


@scenario('../features/visualization_cli.feature', 'Render RDF graph to PNG')
def test_visualize_rdf():
    pass


@scenario('../features/visualization_cli.feature', 'Missing output file for visualization')
def test_visualize_missing():
    pass
