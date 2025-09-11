import pytest

from autoresearch.config.loader import ConfigLoader


@pytest.mark.requires_nlp
def test_spacy_tokenization_and_import() -> None:
    spacy = pytest.importorskip("spacy")
    from autoresearch.search.context import _try_import_spacy

    doc = spacy.blank("en")("hello world")
    assert [t.text for t in doc] == ["hello", "world"]
    assert _try_import_spacy() is True


@pytest.mark.requires_ui
def test_streamlit_theme_apply() -> None:
    streamlit = pytest.importorskip("streamlit")
    from autoresearch.streamlit_ui import apply_theme_settings

    streamlit.session_state["dark_mode"] = True
    apply_theme_settings()


@pytest.mark.requires_vss
def test_vss_extension_verify() -> None:
    duckdb = pytest.importorskip("duckdb")
    from autoresearch.extensions import VSSExtensionLoader

    con = duckdb.connect()
    assert isinstance(VSSExtensionLoader.verify_extension(con, verbose=False), bool)


@pytest.mark.requires_git
def test_local_git_search(tmp_path) -> None:
    git = pytest.importorskip("git")
    from autoresearch.search.core import _local_git_backend

    repo = git.Repo.init(tmp_path)
    path = tmp_path / "file.txt"
    path.write_text("hello")
    repo.index.add([str(path)])
    repo.index.commit("init")

    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader.config.search.local_git.repo_path = str(tmp_path)
        loader.config.search.local_git.branches = [repo.active_branch.name]
        results = _local_git_backend("hello", max_results=1)
    assert results and results[0]["title"] == "file.txt"


@pytest.mark.requires_distributed
def test_redis_broker_roundtrip(monkeypatch) -> None:
    redis = pytest.importorskip("redis")
    fakeredis = pytest.importorskip("fakeredis")
    from autoresearch.distributed.broker import RedisBroker

    monkeypatch.setattr(redis.Redis, "from_url", lambda *a, **k: fakeredis.FakeRedis())
    broker = RedisBroker()
    broker.publish({"k": "v"})
    assert broker.queue.get()["k"] == "v"
    broker.shutdown()


@pytest.mark.requires_analysis
def test_metrics_dataframe_polars() -> None:
    pl = pytest.importorskip("polars")
    from autoresearch.data_analysis import metrics_dataframe

    sample = pl.DataFrame({"x": [1, 2, 3]})
    assert sample.height == 3
    metrics = {"agent_timings": {"a": [1, 2, 3]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df["count"][0] == 3


@pytest.mark.requires_llm
def test_available_adapters() -> None:
    pytest.importorskip("dspy")
    from autoresearch.llm import get_available_adapters

    adapters = get_available_adapters()
    assert "lmstudio" in adapters


@pytest.mark.requires_parsers
def test_docx_backend(tmp_path) -> None:
    docx = pytest.importorskip("docx")
    from autoresearch.search.core import _local_file_backend

    sample = tmp_path / "sample.docx"
    docx.Document().save(sample)
    with ConfigLoader.temporary_instance(search_paths=[]) as loader:
        loader.config.search.local_file.path = str(tmp_path)
        loader.config.search.local_file.file_types = ["docx"]
        _local_file_backend("hello", max_results=1)


@pytest.mark.requires_gpu
def test_bertopic_import_available() -> None:
    pytest.importorskip("bertopic")
    from autoresearch.search.context import _try_import_bertopic

    assert _try_import_bertopic() is True
