# mypy: ignore-errors
"""BDD steps exercising optional extras."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import parsers, scenarios, then, when

from autoresearch.distributed.broker import BrokerMessage, RedisBroker, STOP_MESSAGE
from tests.optional_imports import import_or_skip

scenarios("../features/optional_extras.feature")


@when(parsers.parse("I check {extra} extra"))
def check_extra(
    extra: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate that a given optional extra functions correctly."""
    if extra == "nlp":
        spacy = import_or_skip("spacy")
        doc = spacy.blank("en")("hello")
        assert doc[0].text == "hello"
    elif extra == "ui":
        streamlit = import_or_skip("streamlit")
        assert callable(streamlit.write)
    elif extra == "vss":
        duckdb = import_or_skip("duckdb")
        from autoresearch.extensions import VSSExtensionLoader

        con = duckdb.connect()
        if not VSSExtensionLoader.load_extension(con):
            pytest.skip("vss extension not available")
        assert VSSExtensionLoader.verify_extension(con)
    elif extra == "git":
        git = import_or_skip("git")
        repo = git.Repo.init(tmp_path)
        file_path = tmp_path / "README.txt"
        file_path.write_text("hello")
        repo.index.add([str(file_path)])
        repo.index.commit("init")
        assert repo.head.commit.message.strip() == "init"
    elif extra == "distributed":
        redis = import_or_skip("redis")
        fakeredis = import_or_skip("fakeredis")
        monkeypatch.setattr(
            redis.Redis, "from_url", lambda *a, **k: fakeredis.FakeRedis()
        )
        broker = RedisBroker()
        broker.publish(STOP_MESSAGE)
        message: BrokerMessage = broker.queue.get()
        assert message["action"] == "stop"
        broker.shutdown()
    elif extra == "analysis":
        pl = import_or_skip("polars")
        df = pl.DataFrame({"x": [1, 2, 3]})
        assert df.select(pl.col("x").mean()).item() == pytest.approx(2.0)
    elif extra == "llm":
        import_or_skip("dspy")
        from autoresearch.llm import get_available_adapters

        adapters = get_available_adapters()
        assert "lmstudio" in adapters
    elif extra == "parsers":
        docx = import_or_skip("docx")
        doc = docx.Document()
        sample = tmp_path / "sample.docx"
        doc.save(sample)
        from autoresearch.config.loader import ConfigLoader
        from autoresearch.search.core import _local_file_backend

        with ConfigLoader.temporary_instance(search_paths=[]) as loader:
            loader.config.search.local_file.path = str(tmp_path)
            loader.config.search.local_file.file_types = ["docx"]
            _local_file_backend("hello", 1)
    elif extra == "gpu":
        import_or_skip("bertopic")
        from autoresearch.search.context import _try_import_bertopic

        if not _try_import_bertopic():
            pytest.skip("BERTopic import failed")
    else:
        pytest.skip(f"unknown extra {extra}")


@then("the extra is functional")
def extra_functional() -> None:
    """Placeholder assertion for the extra check."""
    pass
