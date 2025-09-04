import duckdb
import pytest


@pytest.mark.requires_nlp
def test_nlp_extra_imports() -> None:
    """Ensure NLP extras are installed and runnable."""

    spacy = pytest.importorskip("spacy")
    bertopic = pytest.importorskip("bertopic")
    nlp = spacy.blank("en")
    doc = nlp("hello")
    assert len(doc) == 1
    assert hasattr(bertopic, "__version__")


@pytest.mark.requires_ui
def test_ui_extra_imports() -> None:
    """Verify Streamlit loads for UI extra."""

    st = pytest.importorskip("streamlit")

    assert hasattr(st, "__version__")


@pytest.mark.requires_vss
def test_vss_extra_imports() -> None:
    """Smoke test DuckDB VSS extension."""

    vss = pytest.importorskip("duckdb_extension_vss")
    con = duckdb.connect()
    try:
        con.install_extension("vss")
        con.load_extension("vss")
        assert con.execute("SELECT 1").fetchone()[0] == 1
    finally:
        con.close()
    assert hasattr(vss, "__version__") or vss is not None


@pytest.mark.requires_git
def test_git_extra_imports(tmp_path) -> None:
    """Ensure Git extra can create a repository and commit."""

    git = pytest.importorskip("git")

    repo = git.Repo.init(tmp_path)
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    repo.index.add([file_path])
    repo.index.commit("init")
    assert repo.head.commit.message == "init"


@pytest.mark.requires_distributed
def test_distributed_extra_imports() -> None:
    """Run a simple Ray task to confirm distributed extras."""

    ray = pytest.importorskip("ray")
    redis = pytest.importorskip("redis")
    ray.init(num_cpus=1, local_mode=True, ignore_reinit_error=True)
    try:
        @ray.remote
        def f() -> int:
            return 1

        assert ray.get(f.remote()) == 1
    finally:
        ray.shutdown()
    assert hasattr(redis, "__version__")


@pytest.mark.requires_analysis
def test_analysis_extra_imports() -> None:
    """Check basic Polars operations."""

    pl = pytest.importorskip("polars")

    df = pl.DataFrame({"a": [1, 2]})
    result = df.select((pl.col("a") * 2).alias("b"))
    assert result.to_dict(False) == {"b": [2, 4]}


@pytest.mark.requires_llm
def test_llm_extra_imports() -> None:
    """Ensure LLM extras are present."""

    fastembed = pytest.importorskip("fastembed")
    dspy = pytest.importorskip("dspy")

    assert hasattr(fastembed, "TextEmbedding")
    assert hasattr(dspy, "__version__")


@pytest.mark.requires_parsers
def test_parsers_extra_imports(tmp_path) -> None:
    """Smoke test python-docx document handling."""

    docx = pytest.importorskip("docx")

    path = tmp_path / "test.docx"
    doc = docx.Document()
    doc.add_paragraph("hi")
    doc.save(path)
    loaded = docx.Document(path)
    assert loaded.paragraphs[0].text == "hi"
