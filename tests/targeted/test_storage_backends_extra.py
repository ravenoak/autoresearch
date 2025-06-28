from unittest.mock import MagicMock, patch
from autoresearch.storage_backends import DuckDBStorageBackend


def test_has_vss_property():
    backend = DuckDBStorageBackend()
    with patch.object(backend, '_conn', MagicMock()):
        with patch('autoresearch.extensions.VSSExtensionLoader.load_extension', return_value=True):
            backend._has_vss = True
            assert backend.has_vss() is True
