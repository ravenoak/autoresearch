from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest

try:
    from tests.optional_imports import import_or_skip
except Exception:  # pragma: no cover - path fallback for --noconftest runs
    import importlib.util
    from pathlib import Path as _Path

    _mod_path = _Path(__file__).resolve().parents[1] / "optional_imports.py"
    spec = importlib.util.spec_from_file_location("tests.optional_imports", str(_mod_path))
    if spec and spec.loader:
        _mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_mod)
        import_or_skip = getattr(_mod, "import_or_skip")
    else:  # If even that fails, raise a clear error
        raise ModuleNotFoundError("Could not import tests.optional_imports via direct path fallback")

from autoresearch.distributed.broker import (
    AgentResultMessage,
    BrokerMessage,
    MessageQueueProtocol,
    RedisBroker,
    StorageBrokerQueueProtocol,
)
from tests.targeted.helpers.distributed import build_agent_result_message


@pytest.mark.requires_nlp
def test_try_import_spacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """SearchContext imports spaCy when NLP extras are available."""
    import_or_skip("spacy")
    from autoresearch.search import context

    monkeypatch.setattr(
        context,
        "get_config",
        lambda: SimpleNamespace(
            search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True))
        ),
    )
    assert context._try_import_spacy()


@pytest.mark.requires_gpu
def test_try_import_bertopic(monkeypatch: pytest.MonkeyPatch) -> None:
    """SearchContext imports BERTopic when GPU extras are available."""
    try:
        import_or_skip("bertopic")
    except Exception as exc:  # pragma: no cover - import-time issues
        pytest.skip(str(exc))
    from autoresearch.search import context

    monkeypatch.setattr(
        context,
        "get_config",
        lambda: SimpleNamespace(
            search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True))
        ),
    )
    if not context._try_import_bertopic():
        pytest.skip("BERTopic import failed")


@pytest.mark.requires_llm
def test_try_import_sentence_transformers(monkeypatch: pytest.MonkeyPatch) -> None:
    """SearchContext imports fastembed when LLM extras are available."""
    import_or_skip("fastembed")
    from autoresearch.search import context

    monkeypatch.setattr(
        context,
        "get_config",
        lambda: SimpleNamespace(
            search=SimpleNamespace(context_aware=SimpleNamespace(enabled=True))
        ),
    )
    assert context._try_import_sentence_transformers()


@pytest.mark.requires_ui
def test_apply_theme_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streamlit UI helper executes with both theme states."""
    import_or_skip("streamlit")
    from autoresearch import streamlit_ui

    fake_st = SimpleNamespace(markdown=MagicMock(), session_state={})
    monkeypatch.setattr(streamlit_ui, "st", fake_st)

    streamlit_ui.apply_theme_settings()
    fake_st.session_state["dark_mode"] = True
    streamlit_ui.apply_theme_settings()

    assert fake_st.markdown.call_count == 2
    light_markup = fake_st.markdown.call_args_list[0].args[0]
    dark_markup = fake_st.markdown.call_args_list[1].args[0]
    assert "background-color:#fff" in light_markup
    assert "background-color:#1c1c1c" in dark_markup


@pytest.mark.requires_ui
def test_apply_accessibility_settings_high_contrast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """High-contrast mode injects the expected CSS overrides."""
    import_or_skip("streamlit")
    from autoresearch import streamlit_ui

    calls: list[str] = []
    fake_st = SimpleNamespace(
        markdown=lambda markup, **_: calls.append(markup),
        session_state={},
    )
    monkeypatch.setattr(streamlit_ui, "st", fake_st)

    streamlit_ui.apply_accessibility_settings()
    fake_st.session_state["high_contrast"] = True
    streamlit_ui.apply_accessibility_settings()

    assert any("outline: 2px solid #ffbf00" in html for html in calls)
    assert any("background-color:#000" in html for html in calls)


@pytest.mark.requires_vss
def test_vss_extension_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """VSSExtensionLoader loads extension using a dummy connection."""
    import_or_skip("duckdb_extension_vss")
    from autoresearch.extensions import VSSExtensionLoader

    class DummyConn:
        def execute(self, _):  # pragma: no cover - trivial
            class Result:
                def fetchall(self_inner):
                    return [("vss",)]

            return Result()

    monkeypatch.setattr(
        "autoresearch.extensions.ConfigLoader",
        lambda: SimpleNamespace(
            config=SimpleNamespace(storage=SimpleNamespace(vector_extension_path=None))
        ),
    )
    assert VSSExtensionLoader.load_extension(DummyConn())


@pytest.mark.requires_git
def test_local_git_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Local Git backend searches this repository."""
    import_or_skip("git")
    from autoresearch.search.core import _local_git_backend

    repo_path = Path(__file__).resolve().parents[2]
    cfg = SimpleNamespace(
        search=SimpleNamespace(
            local_git=SimpleNamespace(
                repo_path=str(repo_path), branches=["HEAD"], history_depth=1
            ),
            local_file=SimpleNamespace(file_types=["py"]),
        )
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    results = _local_git_backend("def", max_results=1)
    assert results


@pytest.mark.requires_distributed
def test_redis_broker_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    """RedisBroker publishes and retrieves messages using fakeredis."""
    import_or_skip("redis")
    import fakeredis
    import redis

    fake = fakeredis.FakeRedis()

    class DummyRedis:
        @classmethod
        def from_url(
            cls, *args: object, **kwargs: object
        ) -> fakeredis.FakeRedis:  # pragma: no cover - stub
            del args, kwargs
            return fake

    monkeypatch.setattr(redis, "Redis", DummyRedis)
    broker = RedisBroker()
    expected: AgentResultMessage = build_agent_result_message(result={"value": 1})
    broker.publish(expected)
    queue: StorageBrokerQueueProtocol = broker.queue
    queue_protocol: MessageQueueProtocol = queue
    message: BrokerMessage = queue_protocol.get()
    assert cast(AgentResultMessage, message) == expected
    broker.shutdown()


@pytest.mark.requires_analysis
def test_metrics_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    """metrics_dataframe builds a Polars DataFrame."""
    import_or_skip("polars")
    from autoresearch.data_analysis import metrics_dataframe

    monkeypatch.setattr(
        "autoresearch.data_analysis.ConfigLoader",
        lambda: SimpleNamespace(
            config=SimpleNamespace(analysis=SimpleNamespace(polars_enabled=True))
        ),
    )
    df = metrics_dataframe({"agent_timings": {"a": [1.0, 2.0]}})
    assert list(df.columns) == ["agent", "avg_time", "count"]


@pytest.mark.requires_parsers
def test_local_file_backend_docx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local file backend extracts text from DOCX files."""
    docx = import_or_skip("docx")
    from autoresearch.search.core import _local_file_backend

    doc_path = tmp_path / "sample.docx"
    doc = docx.Document()
    doc.add_paragraph("hello world")
    doc.save(doc_path)
    cfg = SimpleNamespace(
        search=SimpleNamespace(
            local_file=SimpleNamespace(path=str(tmp_path), file_types=["docx"])
        )
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    results = _local_file_backend("hello", max_results=1)
    assert results and results[0]["title"] == "sample.docx"


@pytest.mark.requires_parsers
def test_local_file_backend_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local file backend extracts text from PDF files."""
    import_or_skip("pdfminer.high_level")
    from autoresearch.search.core import _local_file_backend

    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%Fake PDF")
    monkeypatch.setattr(
        "autoresearch.search.core.extract_pdf_text", lambda _: "hello pdf"
    )
    cfg = SimpleNamespace(
        search=SimpleNamespace(
            local_file=SimpleNamespace(path=str(tmp_path), file_types=["pdf"])
        )
    )
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    results = _local_file_backend("hello", max_results=1)
    assert results and results[0]["title"] == "sample.pdf"
