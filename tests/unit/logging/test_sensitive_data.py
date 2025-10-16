"""Comprehensive tests for sensitive data sanitization."""

import pytest

from autoresearch.logging_utils import SensitiveDataFilter


class TestSensitiveDataFilter:
    """Test suite for SensitiveDataFilter functionality."""

    @pytest.fixture
    def filter_normal(self) -> SensitiveDataFilter:
        """Create a filter with normal sensitivity level."""
        return SensitiveDataFilter("normal")

    @pytest.fixture
    def filter_strict(self) -> SensitiveDataFilter:
        """Create a filter with strict sensitivity level."""
        return SensitiveDataFilter("strict")

    @pytest.fixture
    def filter_permissive(self) -> SensitiveDataFilter:
        """Create a filter with permissive sensitivity level."""
        return SensitiveDataFilter("permissive")

    def test_api_key_detection(self, filter_normal: SensitiveDataFilter) -> None:
        """Test detection and redaction of various API key formats."""
        # Test cases for various API key formats using clearly fake test patterns
        test_cases = [
            ("FAKE_sk-0000000000000000", "FAKE_[API_KEY]"),  # Test OpenAI-style key
            ("FAKE_sk_test_0000000000", "FAKE_[API_KEY]"),  # Test Stripe-style key
            ("FAKE_pk_test_0000000000", "FAKE_[API_KEY]"),  # Test public key pattern
            ("FAKE_Bearer 0000000000", "FAKE_[BEARER_TOKEN]"),  # Test JWT
            ("FAKE_xoxp-123-456-789-abcdef", "FAKE_[SLACK_TOKEN]"),  # Test Slack token
            ("FAKE_ghp_12345678901234567890", "FAKE_[GITHUB_TOKEN]"),  # Test GitHub token
            ("FAKE_gl-1234567890123456", "FAKE_[GITLAB_TOKEN]"),  # Test GitLab token
        ]

        for api_key, expected in test_cases:
            result = filter_normal.sanitize_value(api_key)
            assert result == expected, f"Failed to redact {api_key}"
