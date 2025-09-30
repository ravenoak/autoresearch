import requests

from autoresearch.search import http as http_mod


def test_http_session_lifecycle() -> None:
    http_mod.close_http_session()
    session = http_mod.get_http_session()
    assert isinstance(session, requests.Session)
    http_mod.set_http_session(session)
    assert http_mod.get_http_session() is session
    http_mod.close_http_session()
    http_mod.close_http_session()
    assert http_mod._http_session is None
