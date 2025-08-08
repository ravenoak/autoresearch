from pytest_bdd import scenario, when, then
from autoresearch.main import app as cli_app


@when('I run `autoresearch visualize-metrics metrics.json metrics.png`')
def run_visualize_metrics(cli_runner, bdd_context, temp_config, isolate_network):
    result = cli_runner.invoke(
        cli_app,
        ['visualize-metrics', 'metrics.json', 'metrics.png'],
        catch_exceptions=False,
    )
    bdd_context['result'] = result


@then('the CLI should report the command is missing')
def cli_reports_missing(bdd_context):
    result = bdd_context['result']
    assert result.exit_code != 0
    assert 'No such command' in result.output


@scenario('../features/visualize_metrics_cli.feature', 'Attempt to visualize metrics before implementation')
def test_visualize_metrics_cli():
    pass
