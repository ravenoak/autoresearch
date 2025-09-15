import pytest

from tests.optional_imports import import_or_skip

pytestmark = pytest.mark.integration


@pytest.mark.requires_nlp
def test_spacy_tokenization() -> None:
    try:
        spacy = import_or_skip("spacy")
    except Exception as exc:  # pragma: no cover - optional import failure
        pytest.skip(f"spaCy import failed: {exc}")
    nlp = spacy.blank("en")
    doc = nlp("hello world")
    assert [t.text for t in doc] == ["hello", "world"]

    from autoresearch.search.context import _try_import_spacy

    assert _try_import_spacy()


@pytest.mark.requires_ui
def test_streamlit_markdown() -> None:
    streamlit = import_or_skip("streamlit")
    assert callable(streamlit.markdown)


@pytest.mark.requires_ui
def test_streamlit_theme_settings() -> None:
    """Ensure theme helper executes with UI extra installed."""
    streamlit = import_or_skip("streamlit")
    from autoresearch.streamlit_ui import apply_theme_settings

    streamlit.session_state["dark_mode"] = True
    apply_theme_settings()


@pytest.mark.requires_vss
def test_duckdb_query() -> None:
    duckdb = import_or_skip("duckdb")
    con = duckdb.connect()
    assert con.execute("SELECT 42").fetchone()[0] == 42

    from autoresearch.extensions import VSSExtensionLoader

    assert VSSExtensionLoader.load_extension(con)
    assert VSSExtensionLoader.verify_extension(con)


@pytest.mark.requires_git
def test_gitpython_commit(tmp_path) -> None:
    git = import_or_skip("git")
    repo = git.Repo.init(tmp_path)
    file_path = tmp_path / "README.txt"
    file_path.write_text("hello")
    repo.index.add([str(file_path)])
    repo.index.commit("init")
    assert repo.head.commit.message == "init"

    from autoresearch.config.loader import ConfigLoader
    from autoresearch.search.core import _local_git_backend

    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader.config.search.local_git.repo_path = str(tmp_path)
        loader.config.search.local_git.branches = [repo.active_branch.name]
        results = _local_git_backend("hello", max_results=1)
        assert results and results[0]["title"] == "README.txt"


@pytest.mark.requires_distributed
def test_fakeredis_roundtrip(monkeypatch) -> None:
    redis = import_or_skip("redis")
    fakeredis = import_or_skip("fakeredis")
    monkeypatch.setattr(redis.Redis, "from_url", lambda *a, **k: fakeredis.FakeRedis())

    from autoresearch.distributed.broker import RedisBroker

    broker = RedisBroker()
    broker.publish({"k": "v"})
    assert broker.queue.get()["k"] == "v"
    broker.shutdown()


@pytest.mark.requires_analysis
def test_polars_groupby() -> None:
    pl = import_or_skip("polars")
    df = pl.DataFrame({"x": [1, 2, 3], "y": [1, 1, 2]})
    grouped = df.group_by("y").agg(pl.col("x").sum().alias("x_sum"))
    assert grouped.filter(pl.col("y") == 1)["x_sum"][0] == 3

    from autoresearch.data_analysis import metrics_dataframe

    metrics = {"agent_timings": {"a": [1, 2, 3]}}
    df_metrics = metrics_dataframe(metrics, polars_enabled=True)
    assert df_metrics["count"][0] == 3


@pytest.mark.requires_parsers
def test_docx_roundtrip(tmp_path) -> None:
    docx = import_or_skip("docx")
    doc = docx.Document()
    sample = tmp_path / "sample.docx"
    doc.save(sample)

    from autoresearch.config.loader import ConfigLoader
    from autoresearch.search.core import _local_file_backend

    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader.config.search.local_file.path = str(tmp_path)
        loader.config.search.local_file.file_types = ["docx"]
        _local_file_backend("hello", max_results=1)


@pytest.mark.requires_llm
def test_dspy_available() -> None:
    import_or_skip("dspy")
    import dspy

    from autoresearch.llm import get_available_adapters

    adapters = get_available_adapters()
    assert "lmstudio" in adapters
    assert hasattr(dspy, "__version__")


@pytest.mark.requires_gpu
def test_bertopic_available() -> None:
    """Verify GPU extra exposes the BERTopic package."""
    import_or_skip("bertopic")
    from autoresearch.search.context import BERTopic, _try_import_bertopic

    if not _try_import_bertopic():
        pytest.skip("BERTopic import failed")
    assert BERTopic is not None
