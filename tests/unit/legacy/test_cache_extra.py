from autoresearch import cache


def test_get_db_after_teardown(tmp_path):
    orig = cache._db_path
    cache.teardown(remove_file=False)
    cache._db_path = tmp_path / "c.json"
    db1 = cache.get_db()
    cache.teardown(remove_file=False)
    db2 = cache.get_db()
    assert db1 is not db2
    cache.teardown(remove_file=True)
    cache._db_path = orig
