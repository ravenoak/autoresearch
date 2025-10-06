# mypy: ignore-errors
import pytest

from autoresearch.config.models import ConfigModel
from autoresearch.llm import pool as llm_pool


@pytest.mark.requires_llm
def test_get_session_reuses_existing_instance(monkeypatch) -> None:
    cfg = ConfigModel()
    monkeypatch.setattr("autoresearch.llm.pool.get_config", lambda: cfg)
    llm_pool.close_session()
    session1 = llm_pool.get_session()
    session2 = llm_pool.get_session()
    assert session1 is session2
    llm_pool.close_session()
