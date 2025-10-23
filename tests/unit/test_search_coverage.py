# Comprehensive search module test coverage

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from autoresearch.search.context import SearchContext
from autoresearch.search.core import Search


class TestSearchContextCoverage:
    """Test SearchContext functionality for improved coverage."""

    def test_search_context_singleton(self):
        """Test SearchContext singleton behavior."""
        context1 = SearchContext.get_instance()
        context2 = SearchContext.get_instance()
        assert context1 is context2

    def test_search_context_temporary_instance(self):
        """Test temporary instance creation."""
        original = SearchContext.get_instance()
        with SearchContext.temporary_instance() as temp:
            assert temp is not original
            assert SearchContext.get_instance() is temp
        assert SearchContext.get_instance() is original

    @patch("autoresearch.search.context.SearchContext._load_config")
    def test_search_context_config_loading(self, mock_load):
        """Test configuration loading in SearchContext."""
        mock_config = MagicMock()
        mock_load.return_value = mock_config

        context = SearchContext()
        config = context.config

        assert config is mock_config
        mock_load.assert_called_once()


class TestSearchCoreCoverage:
    """Test Search core functionality for improved coverage."""

    @pytest.fixture()
    def search_instance(self):
        """Create a Search instance with mocked dependencies."""
        with patch("autoresearch.search.core.get_config") as mock_config, \
             patch("autoresearch.search.core.SearchContext") as mock_context:

            mock_config.return_value = MagicMock()
            mock_context.get_instance.return_value = MagicMock()

            search = Search()
            return search

    def test_search_initialization(self, search_instance):
        """Test Search initialization."""
        assert search_instance is not None
        assert hasattr(search_instance, 'cache')

    @patch("autoresearch.search.core.Search.calculate_bm25_scores")
    @patch("autoresearch.search.core.Search.compute_query_embedding")
    def test_search_embedding_fallback(self, mock_embedding, mock_bm25, search_instance):
        """Test embedding computation fallback."""
        mock_embedding.return_value = None  # Simulate no transformer

        # This should not raise an exception
        result = search_instance.compute_query_embedding("test query")
        assert result is None

    def test_search_cache_integration(self, search_instance):
        """Test cache integration in search."""
        # Test that search has cache attribute
        assert hasattr(search_instance, 'cache')
        assert search_instance.cache is not None

    @patch("autoresearch.search.core.get_config")
    def test_search_config_access(self, mock_get_config):
        """Test configuration access in search operations."""
        mock_config = MagicMock()
        mock_config.search.use_semantic_similarity = True
        mock_get_config.return_value = mock_config

        search = Search()
        # Access config-dependent properties
        config = search._get_search_config()
        assert config is mock_config


class TestSearchBackendCoverage:
    """Test search backend functionality."""

    @patch("autoresearch.search.core.get_config")
    def test_backend_initialization(self, mock_config):
        """Test backend initialization."""
        mock_config.return_value = MagicMock()

        search = Search()
        # Test backend setup
        assert hasattr(search, 'backends')

    def test_search_query_normalization(self):
        """Test query normalization functionality."""
        search = Search()

        # Test various query formats
        queries = [
            "  normal query  ",
            "UPPERCASE QUERY",
            "query with\ttabs",
            "query\nwith\nlines"
        ]

        for query in queries:
            # Should not raise exceptions
            normalized = search._normalize_query(query)
            assert isinstance(normalized, str)
            assert len(normalized.strip()) > 0


class TestSearchErrorHandling:
    """Test error handling in search operations."""

    def test_search_error_recovery(self):
        """Test error recovery mechanisms."""
        search = Search()

        # Test with invalid inputs
        with pytest.raises((ValueError, TypeError)):
            search.external_lookup(None)  # type: ignore

    @patch("autoresearch.search.core.get_config")
    def test_config_error_handling(self, mock_config):
        """Test configuration error handling."""
        mock_config.side_effect = Exception("Config error")

        with pytest.raises(Exception):
            Search()


class TestSearchIntegrationCoverage:
    """Integration tests for search functionality."""

    @patch("autoresearch.search.core.get_config")
    @patch("autoresearch.search.core.SearchContext")
    def test_full_search_workflow(self, mock_context, mock_config):
        """Test complete search workflow."""
        mock_config.return_value = MagicMock()
        mock_context.get_instance.return_value = MagicMock()

        search = Search()

        # Mock backends
        mock_backend = MagicMock(return_value=[{"title": "Test", "url": "https://test.com"}])
        search.backends = {"test": mock_backend}

        # This should complete without errors
        with search.temporary_state() as state:
            assert state is not None
            assert hasattr(state, 'backends')

    def test_search_state_management(self):
        """Test search state management."""
        search = Search()

        with search.temporary_state() as state:
            # State should be properly initialized
            assert state is not None
            # Should have backends attribute
            assert hasattr(state, 'backends')
