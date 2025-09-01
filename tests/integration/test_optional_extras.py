import duckdb
import pytest
from docx import Document

from autoresearch.config.loader import get_config, temporary_config
from autoresearch.data_analysis import metrics_dataframe
from autoresearch.search.context import _try_import_sentence_transformers
from autoresearch.search.core import _local_file_backend


@pytest.mark.requires_nlp
def test_spacy_blank_model() -> None:
    spacy = pytest.importorskip("spacy")
    nlp = spacy.blank("en")
    assert nlp.pipe_names == []


@pytest.mark.requires_ui
def test_streamlit_import() -> None:
    st = pytest.importorskip("streamlit")
    assert hasattr(st, "__version__")


@pytest.mark.requires_vss
def test_duckdb_vss_extension() -> None:
    pytest.importorskip("duckdb_extension_vss")
    con = duckdb.connect()
    try:
        assert con.execute("SELECT 1").fetchone()[0] == 1
    finally:
        con.close()


@pytest.mark.requires_git
def test_git_repo(tmp_path) -> None:
    git = pytest.importorskip("git")
    repo = git.Repo.init(tmp_path)
    assert repo.git_dir


@pytest.mark.requires_distributed
def test_ray_and_redis_import() -> None:
    ray = pytest.importorskip("ray")
    redis = pytest.importorskip("redis")
    try:
        ray.init(num_cpus=1, local_mode=True, ignore_reinit_error=True)
    except Exception:
        pytest.skip("ray init failed")
    try:
        assert ray.is_initialized()
    finally:
        ray.shutdown()
    assert redis.__version__


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
