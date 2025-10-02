"""Smoke tests for optional extras and their modules.

This suite verifies that each optional dependency extra is installed and that
the corresponding code module can be exercised briefly.  The mapping of extras
to modules is:

* ``[nlp]`` – :mod:`autoresearch.search.context`
* ``[ui]`` – :mod:`autoresearch.streamlit_ui`
* ``[vss]`` – :mod:`autoresearch.extensions`
* ``[git]`` – :mod:`autoresearch.search.core`
* ``[distributed]`` – :mod:`autoresearch.distributed.broker`
* ``[analysis]`` – :mod:`autoresearch.data_analysis`
* ``[llm]`` – :mod:`autoresearch.search.context`
* ``[parsers]`` – :mod:`autoresearch.search.core`
"""

from __future__ import annotations

from typing import Any, cast

import sys
from pathlib import Path

import duckdb
import pytest

from tests.optional_imports import import_or_skip

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.data_analysis import metrics_dataframe
from autoresearch.distributed.broker import (
    AgentResultMessage,
    BrokerMessage,
    MessageQueueProtocol,
    StorageBrokerQueueProtocol,
    get_message_broker,
)
from autoresearch.extensions import VSSExtensionLoader
from autoresearch.search.context import (
    _try_import_sentence_transformers,
    _try_import_spacy,
)
from autoresearch.search.core import _local_file_backend, _local_git_backend
from autoresearch.streamlit_ui import apply_theme_settings


def _build_agent_result_message(
    *, agent: str = "worker", payload: dict[str, Any] | None = None
) -> AgentResultMessage:
    message: AgentResultMessage = {
        "action": "agent_result",
        "agent": agent,
        "result": payload or {"value": 1},
        "pid": 4321,
    }
    return message


@pytest.mark.requires_nlp
def test_spacy_available() -> None:
    """The NLP extra provides spaCy for search context features."""
    available = _try_import_spacy()
    if not available:
        pytest.skip("spaCy not available")
    assert available is True


@pytest.mark.requires_ui
def test_streamlit_ui_helpers() -> None:
    """The UI extra exposes Streamlit helpers."""

    assert callable(apply_theme_settings)


@pytest.mark.requires_vss
def test_vss_extension_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """The VSS extra enables DuckDB vector extension management."""

    monkeypatch.setenv("ENABLE_ONLINE_EXTENSION_INSTALL", "false")
    monkeypatch.setattr(VSSExtensionLoader, "_load_from_package", staticmethod(lambda conn: False))
    monkeypatch.setattr(VSSExtensionLoader, "_load_local_stub", staticmethod(lambda conn: False))
    conn = duckdb.connect(":memory:")
    loaded = VSSExtensionLoader.load_extension(conn)
    assert loaded is True
    assert VSSExtensionLoader.verify_extension(conn, verbose=False) is True


@pytest.mark.requires_git
def test_local_git_backend(tmp_path) -> None:
    """The Git extra powers the local Git search backend."""

    git = import_or_skip("git")
    repo = git.Repo.init(tmp_path)
    path = tmp_path / "sample.txt"
    path.write_text("hello world")
    repo.index.add([str(path)])
    repo.index.commit("init")

    cfg = get_config()
    cfg.search.local_git.repo_path = str(tmp_path)
    cfg.search.local_git.branches = []
    cfg.search.local_file.file_types = ["txt"]
    with temporary_config(cfg):
        results = _local_git_backend("hello", max_results=1)
    assert results and "hello" in results[0]["snippet"].lower()


@pytest.mark.requires_distributed
def test_inmemory_broker_roundtrip() -> None:
    """The distributed extra adds message brokers."""

    broker = get_message_broker("memory")
    message = _build_agent_result_message(payload={"status": "ok"})
    broker.publish(message)
    queue: StorageBrokerQueueProtocol = cast(
        StorageBrokerQueueProtocol, broker.queue
    )
    queue_protocol: MessageQueueProtocol = queue
    queued: BrokerMessage = queue_protocol.get()
    assert cast(AgentResultMessage, queued) == message
    broker.shutdown()


@pytest.mark.requires_analysis
def test_metrics_dataframe_polars() -> None:
    """The analysis extra enables Polars-based metrics summaries."""

    metrics = {"agent_timings": {"agent": [1.0, 2.0, 3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df["avg_time"][0] == pytest.approx(2.0)


@pytest.mark.requires_llm
def test_fastembed_available() -> None:
    """The LLM extra installs fast embedding models."""

    assert _try_import_sentence_transformers() is True


@pytest.mark.requires_parsers
def test_local_file_backend_docx(tmp_path) -> None:
    """The parsers extra allows reading ``.docx`` files."""
    sys.modules.pop("docx", None)
    docx = import_or_skip("docx")
    doc = docx.Document()
    if not hasattr(doc, "add_paragraph"):
        pytest.skip("python-docx not installed")
    path = tmp_path / "sample.docx"
    doc.add_paragraph("hello world")
    doc.save(path)
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["docx"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert isinstance(results, list)


@pytest.mark.requires_parsers
def test_local_file_backend_pdf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The parsers extra allows reading ``.pdf`` files."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%Fake PDF")

    def _stub_pdf_extract(path, *, laparams=None, codec=None, **kwargs):
        return "hello world"

    monkeypatch.setattr("autoresearch.search.parsers.extract_pdf_text", _stub_pdf_extract)
    monkeypatch.setattr("autoresearch.search.core.extract_pdf_text", _stub_pdf_extract)
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["pdf"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results and "hello" in results[0]["snippet"].lower()


@pytest.mark.requires_gpu
def test_bertopic_import() -> None:
    """The GPU extra exposes BERTopic for topic modeling."""
    cfg = get_config()
    cfg.search.context_aware.enabled = True
    with temporary_config(cfg):
        from autoresearch.search.context import _try_import_bertopic

        if not _try_import_bertopic():
            pytest.skip("BERTopic import failed")
