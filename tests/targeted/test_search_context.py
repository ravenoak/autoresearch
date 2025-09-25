"""Tests for SearchContext entity extraction and query expansion."""

import types

from tests.helpers.modules import ensure_stub_module

ensure_stub_module(
    "pydantic_settings",
    {
        "BaseSettings": object,
        "CliApp": object,
        "SettingsConfigDict": dict,
    },
)
ensure_stub_module("docx", {"Document": object})
ensure_stub_module(
    "autoresearch.search.core",
    {"Search": object, "get_search": lambda *a, **k: None},
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
