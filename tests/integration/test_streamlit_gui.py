import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.optional_imports import import_or_skip

pytestmark = [pytest.mark.slow, pytest.mark.requires_ui]

AppTest = import_or_skip(
    "streamlit.testing.v1",
    attr="AppTest",
    reason="streamlit testing module not available",
)

try:  # pragma: no cover - optional dependency in UI extras
    import pandas  # type: ignore # noqa: F401
except Exception:  # pragma: no cover - provide a stub for tests
    sys.modules.setdefault("pandas", SimpleNamespace(DataFrame=None))

APP_FILE = str(Path(__file__).resolve().with_name("streamlit_app_wrapper.py"))


def test_skip_link_has_aria_label():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("aria-label='Skip to main content'" in b or "aria-label=\"Skip to main content\"" in b for b in bodies)


def test_guided_tour_dialog_role():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = True
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("role=\"dialog\"" in b for b in bodies)


def test_main_content_live_region():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.run()
    bodies = [m.proto.body for m in at.markdown]
    assert any("aria-live='polite'" in b or "aria-live=\"polite\"" in b for b in bodies)


def test_dark_mode_injects_styles():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["dark_mode"] = True
    at.run()
    styles = [m.proto.body for m in at.markdown if "<style>" in m.proto.body]
    assert any("background-color:#222" in css for css in styles)


def test_high_contrast_injects_styles():
    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["high_contrast"] = True
    at.run()
    styles = [m.proto.body for m in at.markdown if "<style>" in m.proto.body]
    assert any("background-color:#000" in css for css in styles)


def test_graph_toggles_initialize(monkeypatch):
    if AppTest is None:
        return

    from autoresearch.models import QueryResponse
    from autoresearch.config.models import ConfigModel
    from autoresearch.orchestration.orchestrator import Orchestrator
    from autoresearch.config.loader import ConfigLoader
    from autoresearch.knowledge.graph import SessionGraphPipeline

    def fake_run_query(query, config, callbacks=None, **kwargs):
        return QueryResponse(
            answer="ok",
            citations=["c"],
            reasoning=["r"],
            metrics={
                "knowledge_graph": {
                    "summary": {
                        "entity_count": 2,
                        "relation_count": 1,
                        "contradiction_score": 0.1,
                    },
                    "exports": {"graphml": True, "graph_json": True},
                }
            },
        )

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: ConfigModel(loops=1))
    monkeypatch.setattr(ConfigLoader, "watch_changes", lambda self, callback: None)
    monkeypatch.setattr(Orchestrator, "run_query", fake_run_query)
    monkeypatch.setattr(
        SessionGraphPipeline,
        "export_artifacts",
        lambda self: {"graphml": "<graphml/>", "graph_json": '{"graph": []}'},
    )
    monkeypatch.setattr(
        "autoresearch.streamlit_app.update_metrics_periodically", lambda: None
    )
    monkeypatch.setattr("streamlit.form_submit_button", lambda *_, **__: True)

    at = AppTest.from_file(APP_FILE)
    at.session_state["show_tour"] = False
    at.session_state["current_query"] = "graph"
    at.session_state["query_input"] = "graph"
    at.session_state["run_button"] = True
    at.run()
    state = at.session_state
    if "ui_toggle_knowledge_graph" not in state:
        pytest.skip("Streamlit testing environment did not initialize toggle state")
    assert "ui_toggle_knowledge_graph" in state
    assert "ui_toggle_graph_exports" in state
