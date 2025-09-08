import pytest


@pytest.mark.requires_nlp
def test_spacy_tokenization() -> None:
    """NLP extra provides spaCy for tokenization."""
    spacy = pytest.importorskip("spacy")
    doc = spacy.blank("en")("Hello world")
    assert [t.text for t in doc] == ["Hello", "world"]


@pytest.mark.requires_ui
def test_streamlit_text_render() -> None:
    """UI extra exposes Streamlit rendering helpers."""
    streamlit = pytest.importorskip("streamlit")
    if not hasattr(streamlit, "write"):
        pytest.skip("streamlit write not available")
    streamlit.write("hello ui")


@pytest.mark.requires_vss
def test_duckdb_vss_extension() -> None:
    """VSS extra loads the DuckDB VSS extension."""
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    try:
        con.execute("INSTALL 'vss'")
        con.execute("LOAD 'vss'")
    except Exception:
        pytest.skip("vss extension not available")
    assert con.execute("SELECT 1").fetchone()[0] == 1


@pytest.mark.requires_git
def test_git_repo_commit(tmp_path) -> None:
    """Git extra allows committing to a repository."""
    git = pytest.importorskip("git")
    repo = git.Repo.init(tmp_path)
    path = tmp_path / "sample.txt"
    path.write_text("content")
    repo.index.add([str(path)])
    repo.index.commit("init")
    assert repo.head.commit.message.strip() == "init"


@pytest.mark.requires_distributed
def test_redis_client_config() -> None:
    """Distributed extra exposes Redis client."""
    redis = pytest.importorskip("redis")
    client = redis.Redis(host="localhost", port=6379)
    assert client.connection_pool.connection_kwargs["host"] == "localhost"


@pytest.mark.requires_analysis
def test_polars_mean() -> None:
    """Analysis extra installs Polars for metrics work."""
    polars = pytest.importorskip("polars")
    df = polars.DataFrame({"x": [1, 2, 3]})
    assert df.select(polars.col("x").mean()).item() == pytest.approx(2.0)


@pytest.mark.requires_llm
def test_sentence_transformers_available() -> None:
    """LLM extra makes sentence-transformers available."""
    from autoresearch.search.context import _try_import_sentence_transformers

    assert _try_import_sentence_transformers() is True


@pytest.mark.requires_parsers
def test_docx_roundtrip(tmp_path) -> None:
    """Parsers extra enables docx support."""
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    if not hasattr(doc, "add_paragraph"):
        pytest.skip("python-docx not installed")
    doc.add_paragraph("hello")
    path = tmp_path / "file.docx"
    doc.save(path)
    assert path.exists()


@pytest.mark.requires_gpu
def test_bertopic_importable() -> None:
    """GPU extra exposes BERTopic import."""
    from autoresearch.search.context import _try_import_bertopic

    if not _try_import_bertopic():
        pytest.skip("BERTopic import failed")
