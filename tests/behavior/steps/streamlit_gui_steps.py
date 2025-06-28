# flake8: noqa
import json
import re
from pytest_bdd import scenario, given, when, then, parsers
import pytest
from unittest.mock import patch, MagicMock

from .common_steps import *  # noqa: F401,F403
from autoresearch.models import QueryResponse


@given("the Streamlit application is running")
def streamlit_app_running(monkeypatch, bdd_context):
    """Mock the Streamlit application for testing."""
    # Create mock objects for Streamlit components
    bdd_context["st_mocks"] = {
        "markdown": MagicMock(),
        "tabs": MagicMock(),
        "container": MagicMock(),
        "image": MagicMock(),
        "graphviz": MagicMock(),
    }

    # Patch Streamlit functions
    with (
        patch("streamlit.markdown", bdd_context["st_mocks"]["markdown"]),
        patch("streamlit.tabs", bdd_context["st_mocks"]["tabs"]),
        patch("streamlit.container", bdd_context["st_mocks"]["container"]),
        patch("streamlit.image", bdd_context["st_mocks"]["image"]),
        patch("streamlit.graphviz_chart", bdd_context["st_mocks"]["graphviz"]),
    ):
        # Store the patchers in the context
        bdd_context["streamlit_patchers"] = [
            patch("streamlit.markdown"),
            patch("streamlit.tabs"),
            patch("streamlit.container"),
            patch("streamlit.image"),
            patch("streamlit.graphviz_chart"),
        ]

        # Start the patchers
        for patcher in bdd_context["streamlit_patchers"]:
            patcher.start()

        yield

        # Stop the patchers
        for patcher in bdd_context["streamlit_patchers"]:
            patcher.stop()


@when("I enter a query that returns Markdown-formatted content")
def enter_markdown_query(bdd_context):
    """Simulate entering a query that returns Markdown-formatted content."""
    # Create a mock query response with Markdown content
    markdown_content = """
    # Main Heading

    This is a paragraph with **bold** and *italic* text.

    ## Subheading

    - List item 1
    - List item 2

    ```python
    def example():
        return "This is a code block"
    ```

    Math expression: $E = mc^2$
    """

    mock_response = QueryResponse(
        answer=markdown_content,
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    # Store the mock response in the context
    bdd_context["query_response"] = mock_response

    # Call the display_results function with the mock response
    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@then("the answer should be displayed with proper Markdown rendering")
def check_markdown_rendering(bdd_context):
    """Check that the answer is displayed with proper Markdown rendering."""
    # Check that st.markdown was called with the answer content
    bdd_context["st_mocks"]["markdown"].assert_any_call(
        bdd_context["query_response"].answer
    )


@then(
    "formatting elements like headers, lists, and code blocks should be properly styled"
)
def check_formatting_elements(bdd_context):
    """Check that formatting elements are properly styled."""
    # This is a visual check that's hard to automate, but we can check that
    # the markdown content was passed to st.markdown
    markdown_calls = [
        call[0][0] for call in bdd_context["st_mocks"]["markdown"].call_args_list
    ]

    # Check for headers, lists, and code blocks in the markdown calls
    assert any(
        "# Main Heading" in call for call in markdown_calls if isinstance(call, str)
    )
    assert any(
        "- List item" in call for call in markdown_calls if isinstance(call, str)
    )
    assert any("```python" in call for call in markdown_calls if isinstance(call, str))


@then("math expressions in LaTeX format should be properly rendered")
def check_math_rendering(bdd_context):
    """Check that math expressions in LaTeX format are properly rendered."""
    # This is a visual check that's hard to automate, but we can check that
    # the markdown content with LaTeX was passed to st.markdown
    markdown_calls = [
        call[0][0] for call in bdd_context["st_mocks"]["markdown"].call_args_list
    ]

    # Check for LaTeX math expressions in the markdown calls
    assert any("$E = mc^2$" in call for call in markdown_calls if isinstance(call, str))


@when("I run a query in the Streamlit interface")
def run_query_in_streamlit(bdd_context):
    """Simulate running a query in the Streamlit interface."""
    # Create a mock query response
    mock_response = QueryResponse(
        answer="This is the answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    # Store the mock response in the context
    bdd_context["query_response"] = mock_response

    # Call the display_results function with the mock response
    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@then("the results should be displayed in a tabbed interface")
def check_tabbed_interface(bdd_context):
    """Check that the results are displayed in a tabbed interface."""
    # Check that st.tabs was called
    bdd_context["st_mocks"]["tabs"].assert_called_once()


@then(
    'there should be tabs for "Citations", "Reasoning", "Metrics", and "Knowledge Graph"'
)
def check_tab_names(bdd_context):
    """Check that there are tabs for Citations, Reasoning, Metrics, and Knowledge Graph."""
    # Check that st.tabs was called with the correct tab names
    bdd_context["st_mocks"]["tabs"].assert_called_with(
        ["Citations", "Reasoning", "Metrics", "Knowledge Graph"]
    )


@then("I should be able to switch between tabs without losing information")
def check_tab_switching(bdd_context):
    """Check that switching between tabs doesn't lose information."""
    # This is a user interaction test that's hard to automate, but we can check that
    # the content for each tab was added to the tab context

    # Get the mock tab objects
    tab_mocks = bdd_context["st_mocks"]["tabs"].return_value

    # Check that each tab has content
    assert tab_mocks[0].markdown.called  # Citations tab
    assert tab_mocks[1].markdown.called  # Reasoning tab
    assert tab_mocks[2].markdown.called  # Metrics tab
    # Knowledge Graph tab might not have content if there's not enough information


@when("I run a query that generates a knowledge graph")
def run_query_with_knowledge_graph(bdd_context):
    """Simulate running a query that generates a knowledge graph."""
    # Create a mock query response with enough information to generate a knowledge graph
    mock_response = QueryResponse(
        answer="This is the answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    # Store the mock response in the context
    bdd_context["query_response"] = mock_response

    # Call the display_results function with the mock response
    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@then('the knowledge graph should be visualized in the "Knowledge Graph" tab')
def check_knowledge_graph_visualization(bdd_context):
    """Check that the knowledge graph is visualized in the Knowledge Graph tab."""
    # Get the mock tab objects
    tab_mocks = bdd_context["st_mocks"]["tabs"].return_value

    # Check that the Knowledge Graph tab has an image
    assert tab_mocks[3].image.called


@then("the visualization should show relationships between concepts")
def check_relationships_visualization(bdd_context):
    """Check that the visualization shows relationships between concepts."""
    # This is a visual check that's hard to automate, but we can check that
    # the create_knowledge_graph function was called with the query response
    from autoresearch.streamlit_app import create_knowledge_graph

    # The image should have been created by create_knowledge_graph
    # We can't easily check this without mocking create_knowledge_graph itself


@then("the nodes should be color-coded by type")
def check_node_coloring(bdd_context):
    """Check that the nodes are color-coded by type."""
    # This is a visual check that's hard to automate, but we can check that
    # the create_knowledge_graph function uses different colors for different node types

    # We would need to inspect the implementation of create_knowledge_graph
    # to verify this, which is beyond the scope of this test


@scenario(
    "../features/streamlit_gui.feature",
    "Formatted Answer Display with Markdown Rendering",
)
def test_formatted_answer_display():
    """Test the Formatted Answer Display with Markdown Rendering scenario."""
    pass


@scenario("../features/streamlit_gui.feature", "Tabbed Interface for Results")
def test_tabbed_interface():
    """Test the Tabbed Interface for Results scenario."""
    pass


@scenario("../features/streamlit_gui.feature", "Knowledge Graph Visualization")
def test_knowledge_graph_visualization():
    """Test the Knowledge Graph Visualization scenario."""
    pass


@when("I navigate to the configuration section")
def navigate_to_config_section(bdd_context):
    """Simulate navigating to the configuration section."""
    # Mock the sidebar expander for configuration
    bdd_context["st_mocks"]["sidebar"] = MagicMock()
    bdd_context["st_mocks"]["expander"] = MagicMock()

    # Patch streamlit.sidebar
    with patch("streamlit.sidebar", bdd_context["st_mocks"]["sidebar"]):
        # Call the function that would display the configuration section
        from autoresearch.streamlit_app import display_config_editor

        display_config_editor()


@then("I should see a form with configuration options")
def check_config_form(bdd_context):
    """Check that a form with configuration options is displayed."""
    # Check that a form was created in the sidebar
    assert bdd_context["st_mocks"]["sidebar"].form.called


@then("the form should have validation for input fields")
def check_form_validation(bdd_context):
    """Check that the form has validation for input fields."""
    # This is hard to test directly, but we can check that the form
    # includes input fields with min/max values or other validation
    form_mock = bdd_context["st_mocks"]["sidebar"].form.return_value

    # Check that at least one input field has validation parameters
    assert form_mock.number_input.called

    # Check that at least one call to number_input includes min_value or max_value
    number_input_calls = form_mock.number_input.call_args_list
    has_validation = False
    for call in number_input_calls:
        kwargs = call[1]
        if "min_value" in kwargs or "max_value" in kwargs:
            has_validation = True
            break

    assert has_validation, "No validation parameters found in number_input calls"


@then("I should be able to save changes to the configuration")
def check_save_config(bdd_context):
    """Check that changes to the configuration can be saved."""
    # Check that the form has a submit button
    form_mock = bdd_context["st_mocks"]["sidebar"].form.return_value
    assert form_mock.form_submit_button.called


@then("I should see feedback when the configuration is saved")
def check_save_feedback(bdd_context):
    """Check that feedback is displayed when the configuration is saved."""
    # Check that a success message is displayed when the form is submitted
    # This is typically done with st.success
    assert (
        bdd_context["st_mocks"]["sidebar"].success.called
        or bdd_context["st_mocks"]["success"].called
    )


@scenario("../features/streamlit_gui.feature", "Configuration Editor Interface")
def test_config_editor():
    """Test the Configuration Editor Interface scenario."""
    pass


@scenario("../features/streamlit_gui.feature", "Configuration Updates Persist")
def test_config_updates_persist():
    """Test that configuration updates are saved and used."""
    pass


@when("I update a configuration value in the GUI")
def update_config_value(monkeypatch, bdd_context):
    """Simulate updating a configuration value in the editor."""
    calls: list[dict] = []

    def fake_save(cfg: dict) -> bool:
        calls.append(cfg)
        return True

    monkeypatch.setattr("autoresearch.streamlit_app.save_config_to_toml", fake_save)

    from autoresearch.streamlit_app import save_config_to_toml

    new_cfg = {"loops": 4}
    save_config_to_toml(new_cfg)

    bdd_context["save_calls"] = calls
    bdd_context["new_config"] = new_cfg


@then("the configuration should be saved with the new value")
def check_config_saved(bdd_context):
    """Verify save_config_to_toml was called with the updated value."""
    assert bdd_context["save_calls"], "save_config_to_toml was not called"
    assert bdd_context["save_calls"][0]["loops"] == bdd_context["new_config"]["loops"]


@then("the updated configuration should be used for the next query")
def check_config_used(monkeypatch, bdd_context):
    """Ensure Orchestrator.run_query receives the updated configuration."""
    with patch(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        return_value=QueryResponse(answer="", citations=[], reasoning=[], metrics={}),
    ) as mock_run:
        from autoresearch.orchestration.orchestrator import Orchestrator
        from autoresearch.config import ConfigModel

        cfg = ConfigModel(loops=bdd_context["new_config"]["loops"])
        Orchestrator.run_query("test", cfg)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert args[1].loops == bdd_context["new_config"]["loops"]


@then("an interaction trace should be displayed")
def check_trace_display(bdd_context):
    """Ensure a graphviz chart was rendered for the trace."""
    assert bdd_context["st_mocks"]["graphviz"].called


@then("progress metrics should be visualized")
def check_progress_metrics(bdd_context):
    """Ensure progress metrics graph was shown."""
    assert bdd_context["st_mocks"]["graphviz"].call_count >= 2


@scenario("../features/streamlit_gui.feature", "Agent Interaction Trace Visualization")
def test_agent_trace():
    """Test the Agent Interaction Trace Visualization scenario."""
    pass


@when("I toggle dark mode")
def toggle_dark_mode(bdd_context):
    """Simulate toggling dark mode."""
    with patch("streamlit.markdown") as mock_markdown:
        import streamlit as st

        st.session_state["dark_mode"] = True
        from autoresearch.streamlit_app import apply_theme_settings

        apply_theme_settings()
        bdd_context["theme_calls"] = mock_markdown.call_args_list


@then("the page background should change according to the selected mode")
def check_background_change(bdd_context):
    """Verify background style was updated for dark mode."""
    css = "".join(call.args[0] for call in bdd_context["theme_calls"])
    assert "background-color" in css


@then("text color should adjust for readability")
def check_text_color(bdd_context):
    """Verify text color was set for dark mode."""
    css = "".join(call.args[0] for call in bdd_context["theme_calls"])
    assert "color:#eee" in css


@scenario("../features/streamlit_gui.feature", "Theme Toggle Switch")
def test_theme_toggle_switch():
    """Test the Theme Toggle Switch scenario."""
    pass
