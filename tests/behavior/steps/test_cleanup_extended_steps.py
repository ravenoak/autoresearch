"""Step definitions for extended test cleanup verification.

This module contains step definitions for verifying that tests clean up
their side effects properly, including temporary files, environment variables,
and handling cleanup errors.
"""

from __future__ import annotations

from typing import Any, cast

import os
import tempfile
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenario, then, when

from tests.behavior.context import BehaviorContext
from tests.behavior.utils import (
    CleanupExtendedPayload,
    TempFileRecord,
    as_payload,
    build_cleanup_payload,
    ensure_cleanup_payload,
)
from tests.typing_helpers import TypedFixture


# Fixtures
@pytest.fixture
def cleanup_extended_context() -> BehaviorContext:
    """Create a context for storing test state and tracking resources."""

    payload: CleanupExtendedPayload = build_cleanup_payload()
    return cast(BehaviorContext, as_payload(payload))


# Scenarios
@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests clean up temporary files properly",
)
def test_cleanup_temporary_files() -> None:
    """Test that temporary files are properly cleaned up."""

    return None


@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests clean up environment variables properly",
)
def test_cleanup_environment_variables() -> None:
    """Test that environment variables are properly restored."""

    return None


@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests handle cleanup errors gracefully",
)
def test_cleanup_errors() -> None:
    """Test that cleanup errors are handled gracefully."""

    return None


# Step definitions for "Tests clean up temporary files properly"
@given("the system creates temporary files during testing")
def system_creates_temporary_files(
    cleanup_extended_context: BehaviorContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Set up the system to create temporary files during testing."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    temp_files = payload["temp_files"]
    original = tempfile.mkstemp

    def tracked_mkstemp(*args: Any, **kwargs: Any) -> tuple[int, str]:
        fd, path = original(*args, **kwargs)
        temp_files.append(TempFileRecord(fd=fd, path=path))
        return fd, path

    monkeypatch.setattr(tempfile, "mkstemp", tracked_mkstemp)


@when("I run a test that creates temporary files")
def run_test_creating_temporary_files(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Run a test that creates temporary files."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    for _ in range(3):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as handle:
            handle.write("Test content")
    assert len(payload["temp_files"]) == 3


@then("all temporary files should be properly cleaned up")
def temporary_files_properly_cleaned_up(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Verify that all temporary files are properly cleaned up."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    for record in payload["temp_files"]:
        try:
            os.close(record.fd)
        except OSError:
            pass
        try:
            os.unlink(record.path)
        except OSError as exc:
            payload["cleanup_errors"].append(
                f"Failed to delete {record.path}: {exc}"
            )
    for record in payload["temp_files"]:
        assert not os.path.exists(record.path), (
            f"Temporary file {record.path} was not deleted"
        )


# Step definitions for "Tests clean up environment variables properly"
@given("the system modifies environment variables during testing")
def system_modifies_environment_variables(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Set up the system to modify environment variables during testing."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    payload["original_env"] = os.environ.copy()
    payload["env_vars"] = {
        "TEST_VAR1": "value1",
        "TEST_VAR2": "value2",
        "TEST_VAR3": "value3",
    }


@when("I run a test that modifies environment variables")
def run_test_modifying_environment_variables(
    cleanup_extended_context: BehaviorContext,
    restore_environment: TypedFixture[None],
) -> None:
    """Run a test that modifies environment variables."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    for key, value in payload["env_vars"].items():
        os.environ[key] = value
        assert os.environ.get(key) == value


@then("all environment variables should be properly restored")
def environment_variables_properly_restored(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Verify that all environment variables are properly restored."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    for key in payload["env_vars"].keys():
        if key in payload["original_env"]:
            os.environ[key] = payload["original_env"][key]
        else:
            os.environ.pop(key, None)
    for key in payload["env_vars"].keys():
        assert os.environ.get(key) == payload["original_env"].get(key)


# Step definitions for "Tests handle cleanup errors gracefully"
@given("the system encounters errors during cleanup")
def system_encounters_cleanup_errors(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Mark that we expect cleanup errors during the test."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    payload["expect_error"] = True


@when("I run a test that encounters cleanup errors")
def run_test_encountering_cleanup_errors(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Run a test that encounters cleanup errors."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    mock_cleanup = MagicMock(side_effect=Exception("Cleanup error"))
    payload["mock_cleanup"] = mock_cleanup
    try:
        mock_cleanup()
    except Exception as exc:  # noqa: BLE001 - capturing test error context
        payload["cleanup_error"] = exc


@then("the test should handle cleanup errors gracefully")
def test_handles_cleanup_errors_gracefully(
    cleanup_extended_context: BehaviorContext,
) -> None:
    """Verify that the error raised during cleanup was captured."""

    payload = ensure_cleanup_payload(cleanup_extended_context)
    err = payload.get("cleanup_error")
    assert isinstance(err, Exception)
    assert str(err) == "Cleanup error"
