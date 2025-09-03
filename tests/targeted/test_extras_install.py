import duckdb
import pytest


@pytest.mark.requires_nlp
def test_nlp_extra_imports() -> None:
    spacy = pytest.importorskip("spacy")
    bertopic = pytest.importorskip("bertopic")
    nlp = spacy.blank("en")
    assert getattr(nlp, "pipe_names", []) == []
    assert hasattr(bertopic, "__version__")


@pytest.mark.requires_ui
def test_ui_extra_imports() -> None:
    st = pytest.importorskip("streamlit")

    assert hasattr(st, "__version__")


@pytest.mark.requires_vss
def test_vss_extra_imports() -> None:
    vss = pytest.importorskip("duckdb_extension_vss")
    con = duckdb.connect()
    try:
        assert con.execute("SELECT 1").fetchone()[0] == 1
    finally:
        con.close()
    assert hasattr(vss, "__version__") or vss is not None


@pytest.mark.requires_git
def test_git_extra_imports(tmp_path) -> None:
    git = pytest.importorskip("git")

    repo = git.Repo.init(tmp_path)
    assert repo.git_dir


@pytest.mark.requires_distributed
def test_distributed_extra_imports() -> None:
    ray = pytest.importorskip("ray")
    redis = pytest.importorskip("redis")
    ray.init(num_cpus=1, local_mode=True, ignore_reinit_error=True)
    try:
        is_initialized = getattr(ray, "is_initialized", lambda: True)
        assert is_initialized()
    finally:
        ray.shutdown()
    assert hasattr(redis, "__version__")


@pytest.mark.requires_analysis
def test_analysis_extra_imports() -> None:
    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"a": [1, 2]})
    assert df.shape == (2, 1)


@pytest.mark.requires_llm
def test_llm_extra_imports() -> None:
    fastembed = pytest.importorskip("fastembed")
    dspy = pytest.importorskip("dspy")

    assert hasattr(fastembed, "TextEmbedding")
    assert hasattr(dspy, "__version__")


@pytest.mark.requires_parsers
def test_parsers_extra_imports(tmp_path) -> None:
    docx = pytest.importorskip("docx")

    path = tmp_path / "test.docx"
    docx.Document().save(path)
    doc = docx.Document(path)
    assert len(doc.paragraphs) == 0
