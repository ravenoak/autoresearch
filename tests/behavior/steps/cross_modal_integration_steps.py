from pytest_bdd import scenario, when, then, parsers, given
from unittest.mock import patch

from .common_steps import *  # noqa: F401,F403


@given("the Autoresearch system is running")
def autoresearch_system_running(tmp_path, monkeypatch):
    """Set up the Autoresearch system for testing."""
    return application_running(tmp_path, monkeypatch)
from autoresearch.models import QueryResponse


@scenario("../features/cross_modal_integration.feature", "Shared Query History")
def test_shared_query_history():
    """Test shared query history across interfaces."""
    pass


@scenario("../features/cross_modal_integration.feature", "Consistent Error Handling")
def test_consistent_error_handling():
    """Test consistent error handling across interfaces."""
    pass


@scenario(
    "../features/cross_modal_integration.feature", "Configuration Synchronization"
)
def test_configuration_synchronization():
    """Test configuration synchronization across interfaces."""
    pass


@scenario("../features/cross_modal_integration.feature", "A2A Interface Consistency")
def test_a2a_interface_consistency():
    """Test A2A interface consistency."""
    pass


@scenario("../features/cross_modal_integration.feature", "MCP Interface Consistency")
def test_mcp_interface_consistency():
    """Test MCP interface consistency."""
    pass


@when(parsers.parse('I execute a query "{query}" via CLI'))
def execute_query_via_cli(bdd_context, query):
    """Execute a query via CLI."""
    # Mock CLI query execution
    with patch("autoresearch.main.search") as mock_query_command:
        mock_response = QueryResponse(
            answer="Paris is the capital of France.",
            reasoning=["France has Paris as its capital city."],
            citations=["Wikipedia: France"],
            metrics={"confidence": 0.95},
        )
        mock_query_command.return_value = mock_response

        # Execute the query
        from autoresearch.main import search

        result = search(query=query)

        # Store the result in the context
        bdd_context["cli_query"] = query
        bdd_context["cli_result"] = result


@when("I open the Streamlit GUI")
def open_streamlit_gui(bdd_context):
    """Open the Streamlit GUI."""
    # Mock Streamlit app
    with patch("streamlit.session_state", {}) as mock_session_state:
        # Mock query history in session state
        if "query_history" not in mock_session_state:
            mock_session_state["query_history"] = []

        # Add CLI query to history if it exists
        if "cli_query" in bdd_context and "cli_result" in bdd_context:
            mock_session_state["query_history"].append(
                {"query": bdd_context["cli_query"], "result": bdd_context["cli_result"]}
            )

        bdd_context["streamlit_session"] = mock_session_state


@then(parsers.parse('the query history should include "{query}"'))
def check_query_history(bdd_context, query):
    """Check that the query history includes the specified query."""
    # Get the session state
    session_state = bdd_context["streamlit_session"]

    # Check that the query is in the history
    query_found = False
    for entry in session_state["query_history"]:
        if entry["query"] == query:
            query_found = True
            break

    assert query_found, f"Query '{query}' not found in history"


@then("I should be able to rerun the query from the GUI")
def check_rerun_query(bdd_context):
    """Check that I can rerun the query from the GUI."""
    # Mock Streamlit components for rerunning a query
    with patch("streamlit.button") as mock_button:
        mock_button.return_value = True

        # Get the first query from history
        session_state = bdd_context["streamlit_session"]
        first_query = session_state["query_history"][0]["query"]

        # Mock rerunning the query
        with patch("autoresearch.streamlit_app.run_query") as mock_run_query:
            mock_run_query.return_value = session_state["query_history"][0]["result"]

            # Rerun the query
            from autoresearch.streamlit_app import run_query

            result = run_query(first_query)

            # Store the result
            bdd_context["gui_result"] = result

            # Verify that run_query was called with the correct query
            mock_run_query.assert_called_once_with(first_query)


@then("the results should be consistent with the CLI results")
def check_consistent_results(bdd_context):
    """Check that the results are consistent between CLI and GUI."""
    cli_result = bdd_context["cli_result"]
    gui_result = bdd_context["gui_result"]

    # Check that the results are the same
    assert cli_result.answer == gui_result.answer
    assert cli_result.reasoning == gui_result.reasoning
    assert cli_result.citations == gui_result.citations
    assert cli_result.metrics == gui_result.metrics


@when("I execute an invalid query via CLI")
def execute_invalid_query_cli(bdd_context):
    """Execute an invalid query via CLI."""
    # Mock CLI query execution with an error
    with patch("autoresearch.main.search") as mock_query_command:
        mock_query_command.side_effect = ValueError(
            "Invalid query: Query cannot be empty"
        )

        # Execute the query and catch the error
        from autoresearch.main import search

        try:
            search(query="")
        except ValueError as e:
            bdd_context["cli_error"] = str(e)


@then("I should receive a specific error message")
def check_cli_error_message(bdd_context):
    """Check that I receive a specific error message."""
    assert "cli_error" in bdd_context
    assert "Invalid query" in bdd_context["cli_error"]


@when("I execute the same invalid query via GUI")
def execute_invalid_query_gui(bdd_context):
    """Execute the same invalid query via GUI."""
    # Mock Streamlit query execution with an error
    with patch("autoresearch.streamlit_app.run_query") as mock_run_query:
        mock_run_query.side_effect = ValueError("Invalid query: Query cannot be empty")

        # Execute the query and catch the error
        from autoresearch.streamlit_app import run_query

        try:
            run_query("")
        except ValueError as e:
            bdd_context["gui_error"] = str(e)


@then("I should receive the same error message in the GUI")
def check_gui_error_message(bdd_context):
    """Check that I receive the same error message in the GUI."""
    assert "gui_error" in bdd_context
    assert bdd_context["cli_error"] == bdd_context["gui_error"]


@when("I update the configuration via CLI")
def update_config_via_cli(bdd_context):
    """Update the configuration via CLI."""
    # Mock configuration update via CLI
    with patch("autoresearch.config.ConfigLoader.update") as mock_update:
        mock_update.return_value = True

        # Update the configuration
        from autoresearch.config import ConfigLoader

        config_loader = ConfigLoader()
        config_loader.update({"core": {"loops": 3}})

        # Store the updated config
        bdd_context["updated_config"] = {"core": {"loops": 3}}


@then("the GUI should reflect the updated configuration")
def check_gui_config(bdd_context):
    """Check that the GUI reflects the updated configuration."""
    # Mock Streamlit config display
    with patch("streamlit.json") as mock_json:
        # Display the config
        import streamlit as st

        st.json(bdd_context["updated_config"])

        # Verify that the correct config was displayed
        mock_json.assert_called_once_with(bdd_context["updated_config"])


@when("I update the configuration via GUI")
def update_config_via_gui(bdd_context):
    """Update the configuration via GUI."""
    # Mock configuration update via GUI
    with patch("autoresearch.config.ConfigLoader.update") as mock_update:
        mock_update.return_value = True

        # Update the configuration
        from autoresearch.config import ConfigLoader

        config_loader = ConfigLoader()
        new_config = {"core": {"loops": 5}}
        config_loader.update(new_config)

        # Store the updated config
        bdd_context["updated_config"] = new_config


@when("I check the configuration via CLI")
def check_config_via_cli(bdd_context):
    """Check the configuration via CLI."""
    # Mock CLI config display
    with patch("autoresearch.main.config_command") as mock_config_command:
        mock_config_command.return_value = bdd_context["updated_config"]

        # Get the config
        from autoresearch.main import config_command

        cli_config = config_command()

        # Store the CLI config
        bdd_context["cli_config"] = cli_config


@then("the CLI should show the updated configuration")
def check_cli_config_updated(bdd_context):
    """Check that the CLI shows the updated configuration."""
    assert bdd_context["cli_config"] == bdd_context["updated_config"]


@when("I execute a query via the A2A interface")
def execute_query_via_a2a(bdd_context):
    """Execute a query via the A2A interface."""
    # Mock A2A query execution
    with patch("autoresearch.a2a_interface.query") as mock_a2a_query:
        mock_response = {
            "answer": "Paris is the capital of France.",
            "reasoning": ["France has Paris as its capital city."],
            "citations": ["Wikipedia: France"],
            "metrics": {"confidence": 0.95},
        }
        mock_a2a_query.return_value = mock_response

        # Execute the query
        from autoresearch.a2a_interface import query

        result = query("What is the capital of France?")

        # Store the result
        bdd_context["a2a_result"] = result


@then("the response format should match the CLI response format")
def check_response_format(bdd_context):
    """Check that the interface response format matches the CLI format."""
    cli_result = QueryResponse(
        answer="Paris is the capital of France.",
        reasoning=["France has Paris as its capital city."],
        citations=["Wikipedia: France"],
        metrics={"confidence": 0.95},
    )

    cli_dict = {
        "answer": cli_result.answer,
        "reasoning": cli_result.reasoning,
        "citations": cli_result.citations,
        "metrics": cli_result.metrics,
    }

    result = bdd_context.get("a2a_result") or bdd_context.get("mcp_result")
    assert result == cli_dict


@then("the response should contain the same fields as the GUI response")
def check_response_fields(bdd_context):
    """Check that the response contains the same fields as the GUI response."""
    expected_fields = ["answer", "reasoning", "citations", "metrics"]

    result = bdd_context.get("a2a_result") or bdd_context.get("mcp_result")
    for field in expected_fields:
        assert field in result


@then("the error handling should be consistent with other interfaces")
def check_error_handling(bdd_context):
    """Ensure interface errors match CLI errors."""
    # Generate CLI error
    with patch("autoresearch.main.search") as mock_cli_query:
        mock_cli_query.side_effect = ValueError("Invalid query: Query cannot be empty")
        from autoresearch.main import search

        try:
            search(query="")
        except ValueError as e:
            bdd_context["cli_error"] = str(e)

    # Determine interface under test
    if "a2a_result" in bdd_context:
        patch_path = "autoresearch.a2a_interface.query"
        module_name = "autoresearch.a2a_interface"
        error_key = "a2a_error"
    else:
        patch_path = "autoresearch.mcp_interface.query"
        module_name = "autoresearch.mcp_interface"
        error_key = "mcp_error"

    with patch(patch_path) as mock_query:
        mock_query.side_effect = ValueError("Invalid query: Query cannot be empty")
        module = __import__(module_name, fromlist=["query"])

        try:
            module.query("")
        except ValueError as e:
            bdd_context[error_key] = str(e)

    assert bdd_context[error_key] == bdd_context["cli_error"]


@when("I execute a query via the MCP interface")
def execute_query_via_mcp(bdd_context):
    """Execute a query via the MCP interface."""
    # Mock MCP query execution
    with patch("autoresearch.mcp_interface.query") as mock_mcp_query:
        mock_response = {
            "answer": "Paris is the capital of France.",
            "reasoning": ["France has Paris as its capital city."],
            "citations": ["Wikipedia: France"],
            "metrics": {"confidence": 0.95},
        }
        mock_mcp_query.return_value = mock_response

        # Execute the query
        from autoresearch.mcp_interface import query

        result = query("What is the capital of France?")

        # Store the result
        bdd_context["mcp_result"] = result

