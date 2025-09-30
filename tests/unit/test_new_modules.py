import logging
import types

from autoresearch import output_format, streamlit_app
from autoresearch.storage_backup import BackupManager
import pytest


class DummySession(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class DummySt(types.SimpleNamespace):
    def __init__(self):
        super().__init__(session_state=DummySession(), markdown=lambda *a, **k: None)


def test_output_formatter_initializes_once(monkeypatch: pytest.MonkeyPatch) -> None:
    called = []
    monkeypatch.setattr(output_format.TemplateRegistry, "load_from_config", lambda: called.append(True))
    resp = output_format.QueryResponse(answer="a", citations=[], reasoning=[], metrics={})
    output_format.OutputFormatter.format(resp, "json")
    assert called


def test_streamlit_log_handler_appends_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    st = DummySt()
    monkeypatch.setattr(streamlit_app, "st", st)
    handler = streamlit_app.StreamlitLogHandler()
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "msg", None, None)
    handler.emit(record)
    assert st.session_state["logs"][0]["message"] == "msg"


def test_backup_manager_singleton() -> None:
    first = BackupManager.get_scheduler()
    second = BackupManager.get_scheduler()

    assert first is second
