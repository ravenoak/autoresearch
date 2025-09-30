import asyncio

import pytest
from fastapi import HTTPException, Request

from autoresearch.api.deps import require_permission


def test_require_permission_allows() -> None:
    request = Request(scope={"type": "http"})
    request.state.permissions = {"query"}
    dep = require_permission("query").dependency
    assert asyncio.run(dep(request)) is None


def test_require_permission_auth_missing() -> None:
    request = Request(scope={"type": "http"})
    dep = require_permission("query").dependency
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dep(request))
    assert exc.value.status_code == 401


def test_require_permission_forbidden() -> None:
    request = Request(scope={"type": "http"})
    request.state.permissions = {"docs"}
    dep = require_permission("query").dependency
    with pytest.raises(HTTPException) as exc:
        asyncio.run(dep(request))
    assert exc.value.status_code == 403
