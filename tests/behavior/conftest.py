import pytest


@pytest.fixture(autouse=True)
def bdd_storage_manager(storage_manager):
    """Use the global temporary storage fixture for behavior tests."""
    yield storage_manager
