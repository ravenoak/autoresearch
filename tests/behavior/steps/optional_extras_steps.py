"""BDD steps exercising optional extras."""

from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, then, when

scenarios("../features/optional_extras.feature")


@when(parsers.parse("I check {extra} extra"))
def check_extra(extra: str, tmp_path, monkeypatch) -> None:
    """Validate that a given optional extra functions correctly."""
    if extra == "nlp":
        spacy = pytest.importorskip("spacy")
        doc = spacy.blank("en")("hello")
        assert doc[0].text == "hello"
    elif extra == "ui":
        streamlit = pytest.importorskip("streamlit")
        assert callable(streamlit.write)
    elif extra == "vss":
        duckdb = pytest.importorskip("duckdb")
        from autoresearch.extensions import VSSExtensionLoader

        con = duckdb.connect()
        if not VSSExtensionLoader.load_extension(con):
            pytest.skip("vss extension not available")
        assert VSSExtensionLoader.verify_extension(con)
    elif extra == "git":
        git = pytest.importorskip("git")
        repo = git.Repo.init(tmp_path)
        file_path = tmp_path / "README.txt"
        file_path.write_text("hello")
        repo.index.add([str(file_path)])
        repo.index.commit("init")
        assert repo.head.commit.message.strip() == "init"
    elif extra == "distributed":
        redis = pytest.importorskip("redis")
        fakeredis = pytest.importorskip("fakeredis")
        monkeypatch.setattr(
            redis.Redis, "from_url", lambda *a, **k: fakeredis.FakeRedis()
        )
        from autoresearch.distributed.broker import RedisBroker

        broker = RedisBroker()
        broker.publish({"k": "v"})
        assert broker.queue.get()["k"] == "v"
        broker.shutdown()
    elif extra == "analysis":
        pl = pytest.importorskip("polars")
        df = pl.DataFrame({"x": [1, 2, 3]})
        assert df.select(pl.col("x").mean()).item() == pytest.approx(2.0)
    elif extra == "llm":
        pytest.importorskip("dspy")
        from autoresearch.llm import get_available_adapters

        adapters = get_available_adapters()
        assert "lmstudio" in adapters
    elif extra == "parsers":
        docx = pytest.importorskip("docx")
        doc = docx.Document()
        sample = tmp_path / "sample.docx"
        doc.save(sample)
        from autoresearch.config.loader import ConfigLoader
        from autoresearch.search.core import _local_file_backend

        with ConfigLoader.temporary_instance(search_paths=[]) as loader:
            loader.config.search.local_file.path = str(tmp_path)
            loader.config.search.local_file.file_types = ["docx"]
            _local_file_backend("hello", max_results=1)
    elif extra == "gpu":
        pytest.importorskip("bertopic")
        from autoresearch.search.context import _try_import_bertopic

        if not _try_import_bertopic():
            pytest.skip("BERTopic import failed")
    else:
        pytest.skip(f"unknown extra {extra}")


@then("the extra is functional")
def extra_functional() -> None:
    """Placeholder assertion for the extra check."""
    pass
