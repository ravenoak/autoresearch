from pytest_bdd import scenario, when, then
from autoresearch.main import app as cli_app


@when('I run `autoresearch test_mcp --host 127.0.0.1 --port 8080`')
def run_test_mcp(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):

    class DummyClient:
        def __init__(self, host='127.0.0.1', port=8080):
            pass

        def run_test_suite(self):
            return {'connection_test': {'status': 'success'}}
    monkeypatch.setattr('autoresearch.main.app.MCPTestClient', DummyClient)
    monkeypatch.setattr('autoresearch.main.app.format_test_results', lambda r, f: 'ok')
    result = cli_runner.invoke(
        cli_app,
        ['test_mcp', '--host', '127.0.0.1', '--port', '8080'],
        catch_exceptions=False,
    )
    bdd_context['result'] = result


@when('I run `autoresearch test_mcp --port 9`')
def run_test_mcp_fail(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):

    class FailingClient:
        def __init__(self, host='127.0.0.1', port=9):
            raise RuntimeError('connection failed')
    monkeypatch.setattr('autoresearch.main.app.MCPTestClient', FailingClient)
    result = cli_runner.invoke(cli_app, ['test_mcp', '--port', '9'], catch_exceptions=False)
    bdd_context['result'] = result


@when('I run `autoresearch test_a2a --host 127.0.0.1 --port 8765`')
def run_test_a2a(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):

    class DummyClient:
        def __init__(self, host='127.0.0.1', port=8765):
            pass

        def run_test_suite(self):
            return {'connection_test': {'status': 'success'}}
    monkeypatch.setattr('autoresearch.main.app.A2ATestClient', DummyClient)
    monkeypatch.setattr('autoresearch.main.app.format_test_results', lambda r, f: 'ok')
    result = cli_runner.invoke(
        cli_app,
        ['test_a2a', '--host', '127.0.0.1', '--port', '8765'],
        catch_exceptions=False,
    )
    bdd_context['result'] = result


@when('I run `autoresearch test_a2a --port 9`')
def run_test_a2a_fail(cli_runner, bdd_context, monkeypatch, temp_config, isolate_network):

    class FailingClient:
        def __init__(self, host='127.0.0.1', port=9):
            raise RuntimeError('connection failed')
    monkeypatch.setattr('autoresearch.main.app.A2ATestClient', FailingClient)
    result = cli_runner.invoke(cli_app, ['test_a2a', '--port', '9'], catch_exceptions=False)
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


@scenario('../features/interface_test_cli.feature', 'Run MCP interface tests')
def test_mcp_success():
    pass


@scenario('../features/interface_test_cli.feature', 'Fail to connect to MCP server')
def test_mcp_failure():
    pass


@scenario('../features/interface_test_cli.feature', 'Run A2A interface tests')
def test_a2a_success():
    pass


@scenario('../features/interface_test_cli.feature', 'Fail to connect to A2A server')
def test_a2a_failure():
    pass
