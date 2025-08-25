"""Tests for SearchContext entity extraction and query expansion."""

import sys
import types

sys.modules.setdefault(
    "pydantic_settings",
    types.SimpleNamespace(BaseSettings=object, CliApp=object, SettingsConfigDict=dict),
)
sys.modules.setdefault("docx", types.SimpleNamespace(Document=object))
sys.modules.setdefault(
    "autoresearch.search.core",
    types.SimpleNamespace(Search=object, get_search=lambda *a, **k: None),
)

from autoresearch.search.context import SearchContext  # noqa: E402

_dummy_cfg = types.SimpleNamespace(
    search=types.SimpleNamespace(
        context_aware=types.SimpleNamespace(enabled=True, expansion_factor=0.5, max_history_items=10)
    )
)


def test_add_to_history_extracts_entities(monkeypatch):
    """Entities from queries and results are tracked for expansion."""
    monkeypatch.setattr(
        "autoresearch.search.context.get_config", lambda: _dummy_cfg
    )
    with SearchContext.temporary_instance() as ctx:
        ctx.add_to_history("alpha beta", [{"title": "Gamma", "snippet": "delta"}])
        assert ctx.entities["alpha"] == 1
        assert ctx.entities["gamma"] == 1


def test_expand_query_uses_entities(monkeypatch):
    """Frequently seen entities are appended to new queries."""
    monkeypatch.setattr(
        "autoresearch.search.context.get_config", lambda: _dummy_cfg
    )
    with SearchContext.temporary_instance() as ctx:
        ctx.entities["theta"] = 3
        expanded = ctx.expand_query("base")
        assert "theta" in expanded
