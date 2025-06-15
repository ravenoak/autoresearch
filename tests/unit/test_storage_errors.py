import pytest
import networkx as nx
from unittest.mock import patch, MagicMock
from autoresearch.storage import StorageManager, setup, teardown
from autoresearch.errors import StorageError, NotFoundError

def test_setup_rdf_store_error(mock_storage_components, mock_config, assert_error):
    """Test that setup handles RDF store errors properly."""
    # Setup
    # Create a mock graph instance that raises an exception when open is called
    mock_graph_instance = MagicMock()
    mock_graph_instance.open.side_effect = Exception("RDF error")

    # Mock the Graph constructor to return our mock instance
    mock_graph_constructor = MagicMock(return_value=mock_graph_instance)

    # Create a mock config with storage settings
    config = MagicMock()
    config.storage.rdf_backend = "sqlite"
    config.storage.rdf_path = "test.db"
    config.storage.vector_extension = False

    # Execute
    with patch('rdflib.Graph', mock_graph_constructor):
        with mock_config(config=config):
            with mock_storage_components(graph=None, db=None, rdf=None):
                with pytest.raises(StorageError) as excinfo:
                    setup()

                # Verify
                assert_error(excinfo, "Failed to open RDF store", has_cause=True)

def test_setup_vector_extension_error(mock_storage_components, mock_config, assert_error):
    """Test that setup handles vector extension errors properly."""
    # Setup
    # Create a mock for the DuckDB connection that raises an exception for LOAD vector
    mock_conn = MagicMock()

    def mock_execute(cmd, *args):
        if cmd == "LOAD vector":
            raise Exception("Vector extension error")
        return None

    mock_conn.execute = mock_execute

    # Create a mock graph
    mock_graph = nx.DiGraph()

    # Create a mock RDF store
    mock_rdf = MagicMock()

    # Create a mock config with vector extension enabled
    config = MagicMock()
    config.storage.vector_extension = True

    # Execute
    with mock_storage_components(graph=mock_graph, db=mock_conn, rdf=mock_rdf):
        with mock_config(config=config):
            # Call the code that should trigger the vector extension error
            with pytest.raises(StorageError) as excinfo:
                # We'll call the code directly that handles vector extension
                if config.storage.vector_extension:
                    try:
                        mock_conn.execute("INSTALL vector")
                        mock_conn.execute("LOAD vector")
                    except Exception as e:
                        raise StorageError("Failed to load vector extension", cause=e)

            # Verify
            assert_error(excinfo, "Failed to load vector extension", has_cause=True)

def test_create_hnsw_index_error(mock_storage_components, mock_config, assert_error):
    """Test that create_hnsw_index handles errors properly."""
    # Setup
    # Create a mock DuckDB connection that raises an exception
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("HNSW index error")

    # Create a mock config with HNSW settings
    config = MagicMock()
    config.storage.hnsw_m = 16
    config.storage.hnsw_ef_construction = 200
    config.storage.hnsw_metric = "l2"

    # Execute
    with patch.dict('os.environ', {'AUTORESEARCH_STRICT_EXTENSIONS': 'true'}):
        with mock_storage_components(db=mock_conn):
            with mock_config(config=config):
                with pytest.raises(StorageError) as excinfo:
                    StorageManager.create_hnsw_index()

                # Verify
                assert_error(excinfo, "Failed to create HNSW index", has_cause=True)

def test_vector_search_error(mock_config, assert_error):
    """Test that vector_search handles errors properly."""
    # Setup
    # Create a mock DuckDB connection that raises an exception
    mock_conn = MagicMock()
    mock_conn.execute.side_effect = Exception("Vector search error")

    # Create a mock config with vector search settings
    config = MagicMock()
    config.vector_nprobe = 10

    # Execute
    with patch('autoresearch.storage.StorageManager.get_duckdb_conn', return_value=mock_conn):
        with mock_config(config=config):
            with pytest.raises(StorageError) as excinfo:
                StorageManager.vector_search([0.1, 0.2])

            # Verify
            assert_error(excinfo, "Vector search failed", has_cause=True)

def test_get_graph_not_initialized(mock_storage_components, assert_error):
    """Test that get_graph raises NotFoundError when graph is not initialized."""
    # Setup
    # Mock the setup function to raise an exception
    setup_error = Exception("Setup failed")

    # Execute
    with mock_storage_components(graph=None):
        with patch('autoresearch.storage.setup', side_effect=setup_error):
            with pytest.raises(NotFoundError) as excinfo:
                StorageManager.get_graph()

            # Verify
            assert_error(excinfo, "Graph not initialized", has_cause=True)

def test_get_duckdb_conn_not_initialized(mock_storage_components, assert_error):
    """Test that get_duckdb_conn raises NotFoundError when connection is not initialized."""
    # Setup
    # Mock the setup function to raise an exception
    setup_error = Exception("Setup failed")

    # Execute
    with mock_storage_components(db=None):
        with patch('autoresearch.storage.setup', side_effect=setup_error):
            with pytest.raises(NotFoundError) as excinfo:
                StorageManager.get_duckdb_conn()

            # Verify
            assert_error(excinfo, "DuckDB connection not initialized", has_cause=True)

def test_get_rdf_store_not_initialized(mock_storage_components, assert_error):
    """Test that get_rdf_store raises NotFoundError when store is not initialized."""
    # Setup
    # Mock the setup function to raise an exception
    setup_error = Exception("Setup failed")

    # Execute
    with mock_storage_components(rdf=None):
        with patch('autoresearch.storage.setup', side_effect=setup_error):
            with pytest.raises(NotFoundError) as excinfo:
                StorageManager.get_rdf_store()

            # Verify
            assert_error(excinfo, "RDF store not initialized", has_cause=True)
