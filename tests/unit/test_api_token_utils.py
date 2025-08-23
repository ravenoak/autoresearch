from autoresearch.api.utils import generate_bearer_token, verify_bearer_token


def test_generate_bearer_token_unique():
    t1 = generate_bearer_token()
    t2 = generate_bearer_token()
    assert t1 != t2


def test_verify_bearer_token():
    token = generate_bearer_token()
    assert verify_bearer_token(token, token)
    assert not verify_bearer_token(token, token + "x")
