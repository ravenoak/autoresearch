from autoresearch.api.middleware import AuthMiddleware
from autoresearch.config.models import APIConfig, ConfigModel


def test_resolve_role_valid_key():
    cfg = ConfigModel(api=APIConfig(api_keys={"good": "user"}))
    middleware = AuthMiddleware(lambda *_: None)
    role, err = middleware._resolve_role("good", cfg.api)
    assert role == "user"
    assert err is None


def test_resolve_role_invalid_key():
    cfg = ConfigModel(api=APIConfig(api_keys={"good": "user"}))
    middleware = AuthMiddleware(lambda *_: None)
    role, err = middleware._resolve_role("bad", cfg.api)
    assert role == "anonymous"
    assert err is not None
    assert err.status_code == 401
