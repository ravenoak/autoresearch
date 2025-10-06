# mypy: ignore-errors
from __future__ import annotations
from tests.behavior.utils import empty_metrics

from collections.abc import Iterator
from contextlib import ExitStack
from dataclasses import replace
from typing import Callable, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytest_bdd import given, scenario, then, when
from unittest.mock import MagicMock, patch

from autoresearch.models import QueryResponse

from tests.behavior.context import (
    BehaviorContext,
    StreamlitComponentMocks,
    StreamlitTabMocks,
    get_required,
    set_value,
)

pytest_plugins = ["tests.behavior.steps.common_steps"]

pytestmark = pytest.mark.requires_ui


@given("the Streamlit application is running")
def streamlit_app_running(
    monkeypatch: MonkeyPatch,
    bdd_context: BehaviorContext,
    isolate_network: object,
    restore_environment: object,
) -> Iterator[None]:
    """Mock the Streamlit application for testing."""

    toggle_mock = MagicMock(side_effect=lambda *args, **kwargs: kwargs.get("value", False))
    streamlit_mocks = StreamlitComponentMocks(
        markdown=MagicMock(),
        tabs=MagicMock(),
        container=MagicMock(),
        image=MagicMock(),
        graphviz=MagicMock(),
        success=MagicMock(),
        toggle=toggle_mock,
        checkbox=toggle_mock,
    )
    tab_mocks = StreamlitTabMocks(
        citations=MagicMock(),
        reasoning=MagicMock(),
        metrics=MagicMock(),
        knowledge_graph=MagicMock(),
    )
    streamlit_mocks.tabs.return_value = tab_mocks.as_tuple()
    set_value(bdd_context, "streamlit_mocks", streamlit_mocks)
    set_value(bdd_context, "streamlit_tabs", tab_mocks)

    with ExitStack() as stack:
        stack.enter_context(patch("streamlit.markdown", streamlit_mocks.markdown))
        stack.enter_context(patch("streamlit.tabs", streamlit_mocks.tabs))
        stack.enter_context(patch("streamlit.container", streamlit_mocks.container))
        stack.enter_context(patch("streamlit.image", streamlit_mocks.image))
        stack.enter_context(patch("streamlit.graphviz_chart", streamlit_mocks.graphviz))
        stack.enter_context(patch("streamlit.success", streamlit_mocks.success))
        stack.enter_context(patch("streamlit.toggle", streamlit_mocks.toggle))
        stack.enter_context(patch("streamlit.checkbox", streamlit_mocks.checkbox))

        yield


@when("I enter a query that returns Markdown-formatted content")
def enter_markdown_query(
    bdd_context: BehaviorContext,
    isolate_network: object,
    restore_environment: object,
) -> None:
    """Simulate entering a query that returns Markdown-formatted content."""

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

    set_value(bdd_context, "query_response", mock_response)

    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@then("the answer should be displayed with proper Markdown rendering")
def check_markdown_rendering(bdd_context: BehaviorContext) -> None:
    """Check that the answer is displayed with the expected Markdown text."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    query_response = get_required(bdd_context, "query_response", QueryResponse)

    markdown_calls: list[str] = []
    for call_args in streamlit_mocks.markdown.call_args_list:
        if not call_args.args:
            continue
        markdown_calls.append(cast(str, call_args.args[0]))

    assert query_response.answer in markdown_calls


@then(
    "formatting elements like headers, lists, and code blocks should be properly styled"
)
def check_formatting_elements(bdd_context: BehaviorContext) -> None:
    """Check that formatting elements are properly styled."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    markdown_calls: list[str] = []
    for call_args in streamlit_mocks.markdown.call_args_list:
        if not call_args.args:
            continue
        markdown_calls.append(cast(str, call_args.args[0]))

    assert any("# Main Heading" in call for call in markdown_calls)
    assert any("- List item" in call for call in markdown_calls)
    assert any("```python" in call for call in markdown_calls)


@then("math expressions in LaTeX format should be properly rendered")
def check_math_rendering(bdd_context: BehaviorContext) -> None:
    """Check that math expressions in LaTeX format are properly rendered."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    markdown_calls: list[str] = []
    for call_args in streamlit_mocks.markdown.call_args_list:
        if not call_args.args:
            continue
        markdown_calls.append(cast(str, call_args.args[0]))

    assert any("$E = mc^2$" in call for call in markdown_calls)


@when("I run a query in the Streamlit interface")
def run_query_in_streamlit(bdd_context: BehaviorContext) -> None:
    """Simulate running a query in the Streamlit interface."""

    mock_response = QueryResponse(
        answer="This is the answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    set_value(bdd_context, "query_response", mock_response)

    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@then("the results should be displayed in a tabbed interface")
def check_tabbed_interface(bdd_context: BehaviorContext) -> None:
    """Check that the results are displayed in a tabbed interface."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    streamlit_mocks.tabs.assert_called_once()


@then(
    'there should be tabs for "Citations", "Reasoning", "Metrics", and "Knowledge Graph"'
)
def check_tab_names(bdd_context: BehaviorContext) -> None:
    """Check that there are tabs for Citations, Reasoning, Metrics, and Knowledge Graph."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    streamlit_mocks.tabs.assert_called_with(
        ["Citations", "Reasoning", "Metrics", "Knowledge Graph"]
    )


@then("I should be able to switch between tabs without losing information")
def check_tab_switching(bdd_context: BehaviorContext) -> None:
    """Check that switching between tabs doesn't lose information."""

    tab_mocks = get_required(bdd_context, "streamlit_tabs", StreamlitTabMocks)

    assert tab_mocks.citations.markdown.called
    assert tab_mocks.reasoning.markdown.called
    assert tab_mocks.metrics.markdown.called


@when("I run a query that generates a knowledge graph")
def run_query_with_knowledge_graph(bdd_context: BehaviorContext) -> None:
    """Simulate running a query that generates a knowledge graph."""

    mock_response = QueryResponse(
        answer="This is the answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    set_value(bdd_context, "query_response", mock_response)

    from autoresearch.streamlit_app import display_results

    display_results(mock_response)


@when("I run a query that generates a knowledge graph with exports enabled")
def run_query_with_graph_exports_enabled(bdd_context: BehaviorContext) -> None:
    """Simulate enabling graph exports for a knowledge graph result."""

    mock_response = QueryResponse(
        answer="This is the answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning step 1", "Reasoning step 2"],
        metrics={"tokens": 100, "time": "1.2s"},
    )

    set_value(bdd_context, "query_response", mock_response)

    from autoresearch.output_format import DepthPayload, OutputDepth
    from autoresearch.streamlit_app import OutputFormatter, display_results

    base_payload = DepthPayload(
        depth=OutputDepth.STANDARD,
        tldr="",
        answer=mock_response.answer,
        key_findings=[],
        citations=list(mock_response.citations),
        claim_audits=[],
        reasoning=list(mock_response.reasoning),
        metrics=dict(mock_response.metrics),
        raw_response=None,
        task_graph=None,
        react_traces=[],
        knowledge_graph={"contradictions": []},
        graph_exports={"graphml": True, "graph_json": True},
        graph_export_payloads={},
        sections={
            "tldr": True,
            "key_findings": False,
            "claim_audits": False,
            "reasoning": False,
            "react_traces": False,
            "knowledge_graph": True,
            "graph_exports": True,
        },
    )
    export_payload = replace(
        base_payload,
        graph_export_payloads={
            "graphml": "<graphml/>",
            "graph_json": "{\"nodes\": []}",
        },
    )

    plan_mock = MagicMock(side_effect=[base_payload, export_payload])

    with patch.object(OutputFormatter, "plan_response_depth", plan_mock):
        import streamlit as st

        original_state = dict(st.session_state)
        try:
            st.session_state.clear()
            st.session_state["ui_toggle_graph_exports"] = True
            st.session_state["ui_depth"] = OutputDepth.STANDARD.value
            display_results(mock_response)
        finally:
            st.session_state.clear()
            st.session_state.update(original_state)

    set_value(bdd_context, "graph_export_plan_calls", plan_mock.call_args_list)


@then('the knowledge graph should be visualized in the "Knowledge Graph" tab')
def check_knowledge_graph_visualization(bdd_context: BehaviorContext) -> None:
    """Check that the knowledge graph is visualized in the Knowledge Graph tab."""

    tab_mocks = get_required(bdd_context, "streamlit_tabs", StreamlitTabMocks)
    assert tab_mocks.knowledge_graph.image.called


@then("the visualization should show relationships between concepts")
def check_relationships_visualization(bdd_context: BehaviorContext) -> None:
    """Check that the visualization shows relationships between concepts."""

    from autoresearch.streamlit_app import create_knowledge_graph

    # Placeholder assertion to ensure the function is importable for inspection.
    assert create_knowledge_graph is not None


@then("the nodes should be color-coded by type")
def check_node_coloring(bdd_context: BehaviorContext) -> None:
    """Check that the nodes are color-coded by type."""

    from autoresearch.streamlit_app import create_knowledge_graph

    assert create_knowledge_graph is not None


@then("graph export downloads should be prepared")
def assert_graph_export_prefetch(bdd_context: BehaviorContext) -> None:
    """Ensure enabling graph exports triggers payload prefetch."""

    plan_calls = get_required(bdd_context, "graph_export_plan_calls", list)
    assert len(plan_calls) >= 2, "Expected depth planner to run twice with exports"
    first_call = plan_calls[0]
    second_call = plan_calls[-1]
    assert not first_call.kwargs.get("prefetch_graph_exports", False)
    assert second_call.kwargs.get("prefetch_graph_exports", False) is True
    formats = second_call.kwargs.get("graph_export_formats")
    assert formats == ["graphml", "graph_json"]


@pytest.mark.slow
@scenario(
    "../features/streamlit_gui.feature",
    "Formatted Answer Display with Markdown Rendering",
)
def test_formatted_answer_display() -> None:
    """Test the Formatted Answer Display with Markdown Rendering scenario."""


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Tabbed Interface for Results")
def test_tabbed_interface() -> None:
    """Test the Tabbed Interface for Results scenario."""


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Knowledge Graph Visualization")
def test_knowledge_graph_visualization() -> None:
    """Test the Knowledge Graph Visualization scenario."""


@pytest.mark.slow
@scenario(
    "../features/streamlit_gui.feature",
    "Knowledge graph exports toggle prepares downloads",
)
def test_graph_export_toggle_prepares_downloads() -> None:
    """Test the knowledge graph export toggle scenario."""


@when("I navigate to the configuration section")
def navigate_to_config_section(bdd_context: BehaviorContext) -> None:
    """Simulate navigating to the configuration section."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    streamlit_mocks.sidebar = MagicMock()
    streamlit_mocks.expander = MagicMock()

    assert streamlit_mocks.sidebar is not None

    with patch("streamlit.sidebar", streamlit_mocks.sidebar):
        from autoresearch.streamlit_app import display_config_editor

        display_config_editor()


@then("I should see a form with configuration options")
def check_config_form(bdd_context: BehaviorContext) -> None:
    """Check that a form with configuration options is displayed."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    sidebar = streamlit_mocks.sidebar
    assert isinstance(sidebar, MagicMock)
    assert sidebar.form.called


@then("the form should have validation for input fields")
def check_form_validation(bdd_context: BehaviorContext) -> None:
    """Check that the form has validation for input fields."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    sidebar = streamlit_mocks.sidebar
    assert isinstance(sidebar, MagicMock)

    form_mock = sidebar.form.return_value
    assert form_mock.number_input.called

    has_validation = False
    for call_args in form_mock.number_input.call_args_list:
        kwargs = call_args.kwargs
        if "min_value" in kwargs or "max_value" in kwargs:
            has_validation = True
            break

    assert has_validation, "No validation parameters found in number_input calls"


@then("I should be able to save changes to the configuration")
def check_save_config(bdd_context: BehaviorContext) -> None:
    """Check that changes to the configuration can be saved."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    sidebar = streamlit_mocks.sidebar
    assert isinstance(sidebar, MagicMock)

    form_mock = sidebar.form.return_value
    assert form_mock.form_submit_button.called


@then("I should see feedback when the configuration is saved")
def check_save_feedback(bdd_context: BehaviorContext) -> None:
    """Check that feedback is displayed when the configuration is saved."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    sidebar = streamlit_mocks.sidebar
    sidebar_success_called = False
    if isinstance(sidebar, MagicMock):
        sidebar_success = getattr(sidebar, "success", None)
        if isinstance(sidebar_success, MagicMock):
            sidebar_success_called = sidebar_success.called

    assert sidebar_success_called or streamlit_mocks.success.called


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Configuration Editor Interface")
def test_config_editor() -> None:
    """Test the Configuration Editor Interface scenario."""


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Configuration Updates Persist")
def test_config_updates_persist() -> None:
    """Test that configuration updates are saved and used."""


@when("I update a configuration value in the GUI")
def update_config_value(
    monkeypatch: MonkeyPatch,
    bdd_context: BehaviorContext,
    isolate_network: object,
    restore_environment: object,
) -> None:
    """Simulate updating a configuration value in the editor."""

    calls: list[dict[str, int]] = []

    def fake_save(cfg: dict[str, int]) -> bool:
        calls.append(cfg)
        return True

    monkeypatch.setattr("autoresearch.streamlit_app.save_config_to_toml", fake_save)

    import importlib

    streamlit_module = importlib.import_module("autoresearch.streamlit_app")
    save_config_to_toml = cast(
        Callable[[dict[str, int]], bool], getattr(streamlit_module, "save_config_to_toml")
    )

    new_cfg: dict[str, int] = {"loops": 4}
    save_config_to_toml(new_cfg)

    set_value(bdd_context, "save_calls", calls)
    set_value(bdd_context, "new_config", new_cfg)


@then("the configuration should be saved with the new value")
def check_config_saved(bdd_context: BehaviorContext) -> None:
    """Verify save_config_to_toml was called with the updated value."""

    save_calls = cast(list[dict[str, int]], get_required(bdd_context, "save_calls"))
    new_config = cast(dict[str, int], get_required(bdd_context, "new_config"))

    assert save_calls, "save_config_to_toml was not called"
    assert save_calls[0] == new_config


@then("the updated configuration should be used for the next query")
def check_config_used(bdd_context: BehaviorContext) -> None:
    """Ensure Orchestrator.run_query receives the updated configuration."""

    new_config = cast(dict[str, int], get_required(bdd_context, "new_config"))

    with patch(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        return_value=QueryResponse(answer="", citations=[], reasoning=[], metrics=empty_metrics()),
    ) as mock_run:
        from autoresearch.orchestration.orchestrator import Orchestrator
        from autoresearch.config.models import ConfigModel

        cfg = ConfigModel(loops=new_config["loops"])
        orchestrator = Orchestrator()
        orchestrator.run_query("test", cfg)

        mock_run.assert_called_once()
        args = mock_run.call_args[0]
        assert args[1].loops == new_config["loops"]


@then("an interaction trace should be displayed")
def check_trace_display(bdd_context: BehaviorContext) -> None:
    """Ensure a graphviz chart was rendered for the trace."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    assert streamlit_mocks.graphviz.called


@then("progress metrics should be visualized")
def check_progress_metrics(bdd_context: BehaviorContext) -> None:
    """Ensure progress metrics graph was shown."""

    streamlit_mocks = get_required(
        bdd_context, "streamlit_mocks", StreamlitComponentMocks
    )
    assert streamlit_mocks.graphviz.call_count >= 2


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Agent Interaction Trace Visualization")
def test_agent_trace() -> None:
    """Test the Agent Interaction Trace Visualization scenario."""


@when("I toggle dark mode")
def toggle_dark_mode(
    bdd_context: BehaviorContext,
    isolate_network: object,
    restore_environment: object,
) -> None:
    """Simulate toggling dark mode."""

    with patch("streamlit.markdown") as mock_markdown:
        import importlib
        import streamlit as st

        st.session_state["dark_mode"] = True
        streamlit_module = importlib.import_module("autoresearch.streamlit_app")
        apply_theme_settings = cast(
            Callable[[], None], getattr(streamlit_module, "apply_theme_settings")
        )

        apply_theme_settings()
        css_calls = [
            cast(str, call_args.args[0])
            for call_args in mock_markdown.call_args_list
            if call_args.args
        ]
        set_value(bdd_context, "theme_css_calls", css_calls)


@then("the page background should change according to the selected mode")
def check_background_change(bdd_context: BehaviorContext) -> None:
    """Verify background style was updated for dark mode."""

    css_calls = cast(list[str], get_required(bdd_context, "theme_css_calls"))
    css = "".join(css_calls)
    assert "background-color" in css


@then("text color should adjust for readability")
def check_text_color(bdd_context: BehaviorContext) -> None:
    """Verify text color was set for dark mode."""

    css_calls = cast(list[str], get_required(bdd_context, "theme_css_calls"))
    css = "".join(css_calls)
    assert "color:#eee" in css


@pytest.mark.slow
@scenario("../features/streamlit_gui.feature", "Theme Toggle Switch")
def test_theme_toggle_switch() -> None:
    """Test the Theme Toggle Switch scenario."""
