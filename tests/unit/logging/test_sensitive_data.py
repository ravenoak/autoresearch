"""Comprehensive tests for sensitive data sanitization."""

import json
import pytest
from io import StringIO
from typing import Any

from autoresearch.logging_utils import SensitiveDataFilter, configure_logging, get_logger


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
            ("FAKE_sk-0000000000000000", "[API_KEY]"),  # Test OpenAI-style key
            ("FAKE_sk_test_0000000000", "[API_KEY]"),  # Test Stripe-style key
            ("FAKE_pk_test_0000000000", "[API_KEY]"),  # Test public key pattern
            ("FAKE_Bearer_0000000000", "[BEARER_TOKEN]"),  # Test JWT
            ("FAKE_xoxp_0000000000", "[SLACK_TOKEN]"),  # Test Slack token
            ("FAKE_ghp_0000000000", "[GITHUB_TOKEN]"),  # Test GitHub token
            ("FAKE_gl_0000000000", "[GITLAB_TOKEN]"),  # Test GitLab token
        ]

        for api_key, expected in test_cases:
            result = filter_normal.sanitize_value(api_key)
            assert result == expected, f"Failed to redact {api_key}"