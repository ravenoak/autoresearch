from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.optional_imports import import_or_skip


@pytest.mark.requires_nlp
def test_try_import_spacy(monkeypatch):
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
def test_try_import_bertopic(monkeypatch):
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
def test_try_import_sentence_transformers(monkeypatch):
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
def test_apply_theme_settings(monkeypatch):
    """Streamlit UI helper executes with both theme states."""
    st = import_or_skip("streamlit")
    monkeypatch.setattr(st, "markdown", lambda *a, **k: None)
    from autoresearch import streamlit_ui

    st.session_state.clear()
    streamlit_ui.apply_theme_settings()
    st.session_state["dark_mode"] = True
    streamlit_ui.apply_theme_settings()


@pytest.mark.requires_vss
def test_vss_extension_loader(monkeypatch):
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
def test_local_git_backend(monkeypatch):
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
def test_redis_broker_publish(monkeypatch):
    """RedisBroker publishes and retrieves messages using fakeredis."""
    import_or_skip("redis")
    import fakeredis
    import redis
    from autoresearch.distributed.broker import RedisBroker

    fake = fakeredis.FakeRedis()

    class DummyRedis:
        @classmethod
        def from_url(cls, *a, **k):
            return fake

    monkeypatch.setattr(redis, "Redis", DummyRedis)
    broker = RedisBroker()
    broker.publish({"x": 1})
    assert broker.queue.get() == {"x": 1}
    broker.shutdown()


@pytest.mark.requires_analysis
def test_metrics_dataframe(monkeypatch):
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
def test_local_file_backend_docx(tmp_path, monkeypatch):
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
def test_local_file_backend_pdf(tmp_path, monkeypatch):
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
