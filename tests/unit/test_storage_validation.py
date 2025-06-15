import pytest
from unittest.mock import patch, MagicMock

from autoresearch.storage import StorageManager
from autoresearch.errors import StorageError


def test_validate_claim_valid():
    """Test that _validate_claim accepts valid claims."""
    # Valid claim with all required fields
    valid_claim = {
        "id": "test-id",
        "type": "fact",
        "content": "test content",
    }

    # Should not raise an exception
    StorageManager._validate_claim(valid_claim)


@pytest.mark.parametrize(
    "claim, error_message",
    [
        ("not a dict", "Invalid claim format"),
        (123, "Invalid claim format"),
        ([], "Invalid claim format"),
        (None, "Invalid claim format"),
    ],
)
def test_validate_claim_invalid_format(claim, error_message):
    """Test that _validate_claim rejects claims with invalid formats.

    Args:
        claim: The claim to validate
        error_message: The expected error message
    """
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_claim(claim)

    assert error_message in str(excinfo.value)
    assert "expected dictionary" in str(excinfo.value)


@pytest.mark.parametrize(
    "missing_field, claim_data",
    [
        ("id", {"type": "fact", "content": "test content"}),
        ("type", {"id": "test-id", "content": "test content"}),
        ("content", {"id": "test-id", "type": "fact"}),
    ],
)
def test_validate_claim_missing_required_field(missing_field, claim_data):
    """Test that _validate_claim rejects claims with missing required fields.

    Args:
        missing_field: The field that is missing
        claim_data: The claim data without the missing field
    """
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_claim(claim_data)

    assert f"Missing required field: '{missing_field}'" in str(excinfo.value)


@pytest.mark.parametrize(
    "field, invalid_value, error_message",
    [
        ("id", 123, "Invalid 'id' field"),
        ("id", None, "Invalid 'id' field"),
        ("type", 123, "Invalid 'type' field"),
        ("type", None, "Invalid 'type' field"),
        ("content", 123, "Invalid 'content' field"),
        ("content", None, "Invalid 'content' field"),
    ],
)
def test_validate_claim_invalid_field_type(field, invalid_value, error_message):
    """Test that _validate_claim rejects claims with invalid field types.

    Args:
        field: The field with an invalid type
        invalid_value: The invalid value
        error_message: The expected error message
    """
    # Setup
    claim_data = {
        "id": "test-id",
        "type": "fact",
        "content": "test content",
    }
    claim_data[field] = invalid_value

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_claim(claim_data)

    assert error_message in str(excinfo.value)
    assert "expected string" in str(excinfo.value)


def test_validate_vector_search_params_valid():
    """Test that _validate_vector_search_params accepts valid parameters."""
    # Valid parameters
    query_embedding = [0.1, 0.2, 0.3]
    k = 5

    # Should not raise an exception
    StorageManager._validate_vector_search_params(query_embedding, k)


@pytest.mark.parametrize(
    "query_embedding, error_message",
    [
        ("not a list", "Invalid query_embedding format"),
        (123, "Invalid query_embedding format"),
        ({}, "Invalid query_embedding format"),
        (None, "Invalid query_embedding format"),
    ],
)
def test_validate_vector_search_params_invalid_format(query_embedding, error_message):
    """Test that _validate_vector_search_params rejects query embeddings with invalid formats.

    Args:
        query_embedding: The query embedding to validate
        error_message: The expected error message
    """
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_vector_search_params(query_embedding, 5)

    assert error_message in str(excinfo.value)
    assert "expected list of floats" in str(excinfo.value)


@pytest.mark.parametrize(
    "query_embedding, error_message",
    [
        ([0.1, "not a number", 0.3], "Invalid query_embedding values"),
        ([0.1, None, 0.3], "Invalid query_embedding values"),
        ([0.1, {}, 0.3], "Invalid query_embedding values"),
    ],
)
def test_validate_vector_search_params_invalid_values(query_embedding, error_message):
    """Test that _validate_vector_search_params rejects query embeddings with non-numeric values.

    Args:
        query_embedding: The query embedding to validate
        error_message: The expected error message
    """
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_vector_search_params(query_embedding, 5)

    assert error_message in str(excinfo.value)
    assert "expected numeric values" in str(excinfo.value)


def test_validate_vector_search_params_empty():
    """Test that _validate_vector_search_params rejects empty query embeddings."""
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_vector_search_params([], 5)

    assert "Empty query_embedding" in str(excinfo.value)


@pytest.mark.parametrize(
    "k, error_message",
    [
        (0, "Invalid k value"),
        (-1, "Invalid k value"),
        ("not an int", "Invalid k value"),
        (None, "Invalid k value"),
        ({}, "Invalid k value"),
    ],
)
def test_validate_vector_search_params_invalid_k(k, error_message):
    """Test that _validate_vector_search_params rejects invalid k values.

    Args:
        k: The k value to validate
        error_message: The expected error message
    """
    # Setup

    # Execute and Verify
    with pytest.raises(StorageError) as excinfo:
        StorageManager._validate_vector_search_params([0.1, 0.2, 0.3], k)

    assert error_message in str(excinfo.value)


def test_format_vector_literal():
    """Test that _format_vector_literal correctly formats vector literals."""
    query_embedding = [0.1, 0.2, 0.3]
    expected = "[0.1, 0.2, 0.3]"

    result = StorageManager._format_vector_literal(query_embedding)
    assert result == expected

    # Test with integers
    query_embedding = [1, 2, 3]
    expected = "[1, 2, 3]"

    result = StorageManager._format_vector_literal(query_embedding)
    assert result == expected
