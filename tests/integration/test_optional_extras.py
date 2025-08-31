import pytest
from docx import Document

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.data_analysis import metrics_dataframe
from autoresearch.search.context import _try_import_sentence_transformers
from autoresearch.search.core import _local_file_backend


@pytest.mark.requires_analysis
def test_metrics_dataframe_polars() -> None:
    metrics = {"agent_timings": {"agent": [1.0, 2.0, 3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df["avg_time"][0] == 2.0


@pytest.mark.requires_llm
def test_sentence_transformers_import() -> None:
    assert _try_import_sentence_transformers() is True


@pytest.mark.requires_parsers
def test_local_file_backend_docx(tmp_path) -> None:
    path = tmp_path / "sample.docx"
    doc = Document()
    doc.add_paragraph("hello world")
    doc.save(path)
    cfg = get_config()
    cfg.search.local_file.path = str(tmp_path)
    cfg.search.local_file.file_types = ["docx"]
    with temporary_config(cfg):
        results = _local_file_backend("hello", max_results=1)
    assert results and "hello" in results[0]["snippet"].lower()
