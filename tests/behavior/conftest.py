import pytest

from autoresearch import storage


@pytest.fixture(autouse=True)
def storage_manager(tmp_path):
    """Provide isolated storage for behavior tests."""
    db_file = tmp_path / "kg.duckdb"
    storage.teardown(remove_db=True)
    storage.setup(str(db_file))
    yield
    storage.teardown(remove_db=True)
