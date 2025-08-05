# flake8: noqa
import json
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from pytest_bdd import scenario, given, when, then

from autoresearch.models import QueryResponse
from autoresearch.config.models import ConfigModel


@given("the Streamlit application has a stored query history")
def streamlit_app_with_history(monkeypatch, tmp_path, bdd_context):
    import streamlit as st

    # Isolate session state
    session_state = {}
    monkeypatch.setattr(st, "session_state", session_state, raising=False)

    # Prepare a temporary file to persist history
    history_file = tmp_path / "history.json"

    # Wrap the original store function to also write to disk
    from autoresearch.streamlit_app import store_query_history as orig_store

    def fake_store(query, result, config):
        orig_store(query, result, config)
        serializable = [
            {
                "query": e["query"],
                "result": e["result"].model_dump(),
                "config": e["config"],
            }
            for e in st.session_state["query_history"]
        ]
        history_file.write_text(json.dumps(serializable))

    monkeypatch.setattr(
        "autoresearch.streamlit_app.store_query_history", fake_store
    )

    # Store an initial query in history
    result = QueryResponse(
        answer="The answer",
        citations=[],
        reasoning=[],
        metrics={},
    )
    cfg = ConfigModel()
    fake_store("What is AI?", result, cfg)

    bdd_context.update({
        "history_file": history_file,
        "original_result": result,
    })


@when("I view the query history")
def view_query_history(bdd_context):
    import streamlit as st

    @contextmanager
    def fake_form(*args, **kwargs):
        yield

    with (
        patch("streamlit.markdown"),
        patch("streamlit.dataframe") as mock_df,
        patch("streamlit.info"),
        patch("streamlit.form", fake_form),
    ):
        from autoresearch.streamlit_app import display_query_history

        display_query_history()
        bdd_context["history_df_call"] = mock_df.call_args


@then("the previous query should be visible")
def previous_query_visible(bdd_context):
    (args, _kwargs) = bdd_context["history_df_call"]
    df = args[0]
    assert any(q == "What is AI?" for q in df["Query"])


@when("I rerun the query from history")
def rerun_query_from_history(bdd_context):
    import streamlit as st

    @contextmanager
    def fake_form(*args, **kwargs):
        yield

    with (
        patch("streamlit.markdown"),
        patch("streamlit.dataframe"),
        patch("streamlit.info"),
        patch("streamlit.form", fake_form),
        patch("streamlit.number_input", return_value=1),
        patch("streamlit.checkbox", return_value=False),
        patch("streamlit.text_area", return_value=""),
        patch("streamlit.form_submit_button", return_value=True),
    ):
        from autoresearch.streamlit_app import display_query_history

        display_query_history()

    from autoresearch.orchestration.orchestrator import Orchestrator

    with patch(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        return_value=bdd_context["original_result"],
    ) as mock_run:
        cfg = ConfigModel(**st.session_state.rerun_config)
        result = Orchestrator.run_query(st.session_state.rerun_query, cfg)
        bdd_context["rerun_result"] = result
        mock_run.assert_called_once()


@then("the rerun results should match the stored results")
def rerun_matches_original(bdd_context):
    assert bdd_context["rerun_result"] == bdd_context["original_result"]


@pytest.mark.slow
@scenario("../features/gui_history.feature", "View and rerun a previous query")
def test_gui_history():
    """Scenario for viewing and rerunning queries from history."""
    pass
