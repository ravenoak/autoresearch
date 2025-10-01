from scripts.api_auth_sim import _simulate


def test_api_auth_simulation() -> None:
    """compare_digest runs in constant time and roles enforce permissions."""
    metrics = _simulate()
    assert metrics["secure_range"] < metrics["naive_range"]
    assert metrics["admin_write"] is True
    assert metrics["reader_write"] is False
