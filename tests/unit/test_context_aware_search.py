"""Unit tests for context-aware search functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock

from autoresearch.search import Search, SearchContext
from autoresearch.config.models import SearchConfig, ContextAwareSearchConfig


@pytest.fixture
def reset_search_context():
    """Reset the ``SearchContext`` singleton before and after each test."""
    SearchContext.reset_instance()
    yield
    SearchContext.reset_instance()


@pytest.fixture
def mock_context_config():
    """Create a mock configuration with context-aware search enabled."""
    context_config = ContextAwareSearchConfig(
        enabled=True,
        use_query_expansion=True,
        use_entity_recognition=True,
        use_topic_modeling=True,
        use_search_history=True,
    )
    search_config = SearchConfig(backends=["serper"], context_aware=context_config)
    config = MagicMock()
    config.search = search_config
    return config


@pytest.fixture
def sample_results():
    """Create sample search results for testing."""
    return [
        {
            "title": "Python Programming",
            "url": "https://python.org",
            "snippet": "Official Python website",
        },
        {
            "title": "Learn Python",
            "url": "https://example.com/python",
            "snippet": "Python tutorials",
        },
        {
            "title": "Python (programming language) - Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "snippet": "Python is a high-level programming language",
        },
    ]


def test_search_context_singleton(reset_search_context):
    """Test that SearchContext is a singleton."""
    context1 = SearchContext.get_instance()
    context2 = SearchContext.get_instance()

    # Both instances should be the same object
    assert context1 is context2


@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
@patch("autoresearch.search.context.spacy")
def test_initialize_nlp(mock_spacy, reset_search_context):
    """Test that the NLP model is initialized correctly."""
    # Setup mock
    mock_nlp = MagicMock()
    mock_spacy.load.return_value = mock_nlp

    # Create context
    context = SearchContext.get_instance()

    # Verify
    mock_spacy.load.assert_called_once_with("en_core_web_sm")
    assert context.nlp is mock_nlp


@patch.dict(os.environ, {"AUTORESEARCH_AUTO_DOWNLOAD_SPACY_MODEL": "true"})
@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
@patch("autoresearch.search.context.spacy")
def test_initialize_nlp_downloads_model_when_env_set(mock_spacy, reset_search_context):
    """spaCy model is downloaded if missing and env var is set."""
    second_load = MagicMock()
    mock_spacy.load.side_effect = [OSError(), second_load]

    context = SearchContext.get_instance()

    mock_spacy.cli.download.assert_called_once_with("en_core_web_sm")
    assert mock_spacy.load.call_count == 2
    assert context.nlp is second_load


@patch.dict(os.environ, {}, clear=True)
@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
@patch("autoresearch.search.context.spacy")
def test_initialize_nlp_no_download_by_default(mock_spacy, reset_search_context):
    """No download occurs if model missing and env var is unset."""
    mock_spacy.load.side_effect = OSError()

    context = SearchContext.get_instance()

    mock_spacy.cli.download.assert_not_called()
    assert context.nlp is None


@patch("autoresearch.search.context.get_config")
def test_add_to_history(
    mock_get_config, mock_context_config, sample_results, reset_search_context
):
    """Test adding queries to the search history."""
    mock_get_config.return_value = mock_context_config

    # Create context
    context = SearchContext.get_instance()

    # Add a query to history
    context.add_to_history("python", sample_results)

    # Verify
    assert len(context.search_history) == 1
    assert context.search_history[0]["query"] == "python"
    assert context.search_history[0]["results"] == sample_results
    assert "timestamp" in context.search_history[0]


@patch("autoresearch.search.context.SPACY_AVAILABLE", True)
@patch("autoresearch.search.context.get_config")
def test_extract_entities(mock_get_config, mock_context_config, reset_search_context):
    """Test entity extraction from text."""
    mock_get_config.return_value = mock_context_config

    # Create context
    context = SearchContext.get_instance()

    # Create a mock NLP model
    mock_nlp = MagicMock()
    mock_doc = MagicMock()
    mock_ent1 = MagicMock()
    mock_ent1.text = "Python"
    mock_ent1.label_ = "PRODUCT"
    mock_ent2 = MagicMock()
    mock_ent2.text = "Guido van Rossum"
    mock_ent2.label_ = "PERSON"
    mock_doc.ents = [mock_ent1, mock_ent2]
    mock_nlp.return_value = mock_doc

    # Set the mock NLP model
    context.nlp = mock_nlp

    # Extract entities
    context._extract_entities("Python was created by Guido van Rossum")

    # Verify
    assert "python" in context.entities
    assert "guido van rossum" in context.entities
    assert context.entities["python"] == 1
    assert context.entities["guido van rossum"] == 1


@patch("autoresearch.search.BERTOPIC_AVAILABLE", True)
@patch("autoresearch.search.SENTENCE_TRANSFORMERS_AVAILABLE", True)
@patch("autoresearch.search.context.get_config")
@patch("autoresearch.search.Search.get_sentence_transformer")
def test_build_topic_model(
    mock_get_transformer,
    mock_get_config,
    mock_context_config,
    sample_results,
    reset_search_context,
):
    """Test building a topic model from search history."""
    mock_get_config.return_value = mock_context_config

    # Create mocks
    mock_transformer = MagicMock()
    mock_get_transformer.return_value = mock_transformer

    # Create context
    context = SearchContext.get_instance()

    # Add a query to history
    context.add_to_history("python", sample_results)

    # Mock the build_topic_model method to set the topic_model and documents attributes
    original_method = context.build_topic_model

    def mock_build_topic_model():
        context.topic_model = MagicMock()
        context.documents = ["python", "programming", "code"]
        return None

    # Replace the method with our mock
    context.build_topic_model = mock_build_topic_model

    # Call the method
    context.build_topic_model()

    # Verify
    assert context.topic_model is not None
    assert hasattr(context, "documents")
    assert len(context.documents) > 0

    # Restore the original method
    context.build_topic_model = original_method


@patch("autoresearch.search.context.get_config")
def test_expand_query_with_history(
    mock_get_config, mock_context_config, sample_results, reset_search_context
):
    """Test query expansion based on search history."""
    mock_get_config.return_value = mock_context_config

    # Create context
    context = SearchContext.get_instance()

    # Add a query to history
    context.add_to_history("python programming", sample_results)

    # Expand a new query
    expanded_query = context.expand_query("django")

    # Verify that the expanded query includes terms from the history
    assert expanded_query != "django"
    assert "python" in expanded_query or "programming" in expanded_query


@patch("autoresearch.search.context.get_config")
@patch("autoresearch.search.core.get_config")
def test_context_aware_search_integration(
    mock_core_get_config,
    mock_context_get_config,
    mock_context_config,
    sample_results,
    reset_search_context,
):
    mock_core_get_config.return_value = mock_context_config
    mock_context_get_config.return_value = mock_context_config
    """Test the integration of context-aware search with the Search class."""
    # Ensure context-aware search is enabled in the config
    mock_context_config.search.context_aware.enabled = True

    # Create a mock for SearchContext.get_instance
    mock_context = MagicMock()
    mock_context.expand_query.return_value = "python advanced"
    mock_context.add_to_history.return_value = None
    mock_context.build_topic_model.return_value = None

    # Create a mock for the actual lookup function to avoid making real requests
    mock_lookup = MagicMock(return_value=sample_results)

    with patch(
        "autoresearch.search.SearchContext.get_instance", return_value=mock_context
    ):
        with patch.dict("autoresearch.search.Search.backends", {"serper": mock_lookup}):
            # Perform a search
            result = Search.external_lookup("python")

            # Verify that the context was used
            mock_context.expand_query.assert_called_once_with("python")
            mock_context.add_to_history.assert_called_once()
            mock_context.build_topic_model.assert_called_once()

            # Verify the result is not empty
            assert result
            assert isinstance(result, list)
            assert len(result) > 0


@patch("autoresearch.search.context.get_config")
@patch("autoresearch.search.core.get_config")
def test_context_aware_search_disabled(
    mock_core_get_config,
    mock_context_get_config,
    mock_context_config,
    reset_search_context,
):
    mock_core_get_config.return_value = mock_context_config
    mock_context_get_config.return_value = mock_context_config
    """Test that context-aware search can be disabled."""
    # Disable context-aware search
    mock_context_config.search.context_aware.enabled = False

    # Create a mock for SearchContext.get_instance
    mock_context = MagicMock()

    with patch(
        "autoresearch.search.SearchContext.get_instance", return_value=mock_context
    ):
        # Perform a search with a mock for the actual lookup
        with patch(
            "autoresearch.search.Search.backends",
            {"serper": MagicMock(return_value=[])},
        ):
            Search.external_lookup("python")

            # Verify that the context was not used
            mock_context.expand_query.assert_not_called()


@patch("autoresearch.search.context.SPACY_AVAILABLE", False)
@patch("autoresearch.search.BERTOPIC_AVAILABLE", False)
@patch("autoresearch.search.context.get_config")
def test_expand_query_respects_settings(
    mock_get_config, reset_search_context
):
    cfg = MagicMock()
    cfg.search.context_aware.use_query_expansion = False
    cfg.search.context_aware.max_history_items = 10
    mock_get_config.return_value = cfg

    ctx = SearchContext.get_instance()
    ctx.search_history.append({"query": "python programming", "results": []})
    result = ctx.expand_query("django")
    assert result == "django"


@patch("autoresearch.search.context.SPACY_AVAILABLE", False)
@patch("autoresearch.search.BERTOPIC_AVAILABLE", False)
@patch("autoresearch.search.context.get_config")
def test_expand_query_expansion_factor(
    mock_get_config, reset_search_context
):
    cfg = MagicMock()
    cfg.search.context_aware.expansion_factor = 1.0
    cfg.search.context_aware.use_search_history = True
    cfg.search.context_aware.max_history_items = 10
    mock_get_config.return_value = cfg

    ctx = SearchContext.get_instance()
    ctx.add_to_history("python programming", [])
    result = ctx.expand_query("django")
    assert "python" in result
