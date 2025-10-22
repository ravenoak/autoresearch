import pytest

from autoresearch.storage_utils import (
    NamespaceTokens,
    resolve_namespace,
    validate_namespace_routes,
)
from autoresearch.errors import StorageError


def test_resolve_namespace_prefers_project_token():
    tokens = NamespaceTokens(session="sess", workspace="work", project="proj")
    routes = {"session": "workspace", "workspace": "project"}
    assert resolve_namespace(tokens, routes, default_namespace="default") == "proj"


def test_resolve_namespace_falls_back_to_workspace():
    tokens = NamespaceTokens(session="sess", workspace="work", project=None)
    routes = {"session": "workspace", "workspace": "self"}
    assert resolve_namespace(tokens, routes, default_namespace="default") == "work"


def test_validate_namespace_routes_detects_cycle():
    with pytest.raises(StorageError):
        validate_namespace_routes({"session": "workspace", "workspace": "session"})
