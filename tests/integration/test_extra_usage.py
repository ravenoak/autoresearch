import pytest

pytestmark = pytest.mark.integration


@pytest.mark.requires_nlp
def test_spacy_tokenization() -> None:
    spacy = pytest.importorskip("spacy")
    nlp = spacy.blank("en")
    doc = nlp("hello world")
    assert [t.text for t in doc] == ["hello", "world"]


@pytest.mark.requires_ui
def test_streamlit_markdown() -> None:
    streamlit = pytest.importorskip("streamlit")
    assert callable(streamlit.markdown)


@pytest.mark.requires_vss
def test_duckdb_query() -> None:
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    assert con.execute("SELECT 42").fetchone()[0] == 42


@pytest.mark.requires_git
def test_gitpython_commit(tmp_path) -> None:
    git = pytest.importorskip("git")
    repo = git.Repo.init(tmp_path)
    file_path = tmp_path / "README.md"
    file_path.write_text("hello")
    repo.index.add([str(file_path)])
    repo.index.commit("init")
    assert repo.head.commit.message == "init"


@pytest.mark.requires_distributed
def test_fakeredis_roundtrip() -> None:
    fakeredis = pytest.importorskip("fakeredis")
    r = fakeredis.FakeRedis()
    r.set("k", "v")
    assert r.get("k") == b"v"


@pytest.mark.requires_analysis
def test_polars_groupby() -> None:
    pl = pytest.importorskip("polars")
    df = pl.DataFrame({"x": [1, 2, 3], "y": [1, 1, 2]})
    grouped = df.groupby("y").agg(pl.col("x").sum().alias("x_sum"))
    assert grouped.filter(pl.col("y") == 1)["x_sum"][0] == 3


@pytest.mark.requires_parsers
def test_docx_roundtrip(tmp_path) -> None:
    docx = pytest.importorskip("docx")
    path = tmp_path / "hello.docx"
    doc = docx.Document()
    doc.add_paragraph("hi")
    doc.save(path)
    doc2 = docx.Document(path)
    assert doc2.paragraphs[0].text == "hi"


@pytest.mark.requires_llm
def test_dspy_available() -> None:
    pytest.importorskip("dspy")
    import dspy

    assert hasattr(dspy, "__version__")
