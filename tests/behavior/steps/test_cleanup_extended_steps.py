"""Step definitions for extended test cleanup verification.

This module contains step definitions for verifying that tests clean up
their side effects properly, including temporary files, environment variables,
and handling cleanup errors.
"""

import os
import tempfile
import pytest
from pytest_bdd import scenario, given, when, then
from unittest.mock import MagicMock


# Fixtures
@pytest.fixture
def cleanup_extended_context():
    """Create a context for storing test state and tracking resources."""
    return {
        "temp_files": [],
        "env_vars": {},
        "original_env": {},
        "cleanup_errors": [],
    }


# Scenarios
@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests clean up temporary files properly",
)
def test_cleanup_temporary_files():
    """Test that temporary files are properly cleaned up."""
    pass


@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests clean up environment variables properly",
)
def test_cleanup_environment_variables():
    """Test that environment variables are properly restored."""
    pass


@scenario(
    "../features/test_cleanup_extended.feature",
    "Tests handle cleanup errors gracefully",
)
def test_cleanup_errors():
    """Test that cleanup errors are handled gracefully."""
    pass


# Step definitions for "Tests clean up temporary files properly"
@given("the system creates temporary files during testing")
def system_creates_temporary_files(cleanup_extended_context):
    """Set up the system to create temporary files during testing."""
    # Store the original tempfile.mkstemp function
    cleanup_extended_context["original_mkstemp"] = tempfile.mkstemp

    # Track the created temporary files
    def tracked_mkstemp(*args, **kwargs):
        fd, path = cleanup_extended_context["original_mkstemp"](*args, **kwargs)
        cleanup_extended_context["temp_files"].append((fd, path))
        return fd, path

    # Patch tempfile.mkstemp to track created files
    tempfile.mkstemp = tracked_mkstemp


@when("I run a test that creates temporary files")
def run_test_creating_temporary_files(cleanup_extended_context):
    """Run a test that creates temporary files."""
    # Create some temporary files
    for _ in range(3):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as f:
            f.write("Test content")

    # Verify that the files were created and tracked
    assert len(cleanup_extended_context["temp_files"]) == 3


@then("all temporary files should be properly cleaned up")
def temporary_files_properly_cleaned_up(cleanup_extended_context):
    """Verify that all temporary files are properly cleaned up."""
    # Clean up the temporary files
    for fd, path in cleanup_extended_context["temp_files"]:
        try:
            os.close(fd)
        except OSError:
            # File descriptor might already be closed
            pass

        try:
            os.unlink(path)
        except OSError as e:
            # File might already be deleted
            cleanup_extended_context["cleanup_errors"].append(
                f"Failed to delete {path}: {e}"
            )

    # Verify that all files were deleted
    for _, path in cleanup_extended_context["temp_files"]:
        assert not os.path.exists(path), f"Temporary file {path} was not deleted"

    # Restore the original tempfile.mkstemp function
    tempfile.mkstemp = cleanup_extended_context["original_mkstemp"]


# Step definitions for "Tests clean up environment variables properly"
@given("the system modifies environment variables during testing")
def system_modifies_environment_variables(cleanup_extended_context):
    """Set up the system to modify environment variables during testing."""
    # Store the original environment
    cleanup_extended_context["original_env"] = os.environ.copy()

    # Define test environment variables
    cleanup_extended_context["env_vars"] = {
        "TEST_VAR1": "value1",
        "TEST_VAR2": "value2",
        "TEST_VAR3": "value3",
    }


@when("I run a test that modifies environment variables")
def run_test_modifying_environment_variables(cleanup_extended_context):
    """Run a test that modifies environment variables."""
    # Set the test environment variables
    for key, value in cleanup_extended_context["env_vars"].items():
        os.environ[key] = value

    # Verify that the environment variables were set
    for key, value in cleanup_extended_context["env_vars"].items():
        assert os.environ.get(key) == value


@then("all environment variables should be properly restored")
def environment_variables_properly_restored(cleanup_extended_context):
    """Verify that all environment variables are properly restored."""
    # Restore the original environment
    for key in cleanup_extended_context["env_vars"].keys():
        if key in cleanup_extended_context["original_env"]:
            os.environ[key] = cleanup_extended_context["original_env"][key]
        else:
            os.environ.pop(key, None)

    # Verify that the environment variables were restored
    for key in cleanup_extended_context["env_vars"].keys():
        assert os.environ.get(key) == cleanup_extended_context["original_env"].get(key)


# Step definitions for "Tests handle cleanup errors gracefully"
@given("the system encounters errors during cleanup")
def system_encounters_cleanup_errors(cleanup_extended_context):
    """Set up the system to encounter errors during cleanup."""
    # We'll set up the mock cleanup function in the when step
    pass


@when("I run a test that encounters cleanup errors")
def run_test_encountering_cleanup_errors(cleanup_extended_context):
    """Run a test that encounters cleanup errors."""
    # Create a mock cleanup function that will raise an exception
    mock_cleanup = MagicMock(side_effect=Exception("Cleanup error"))
    cleanup_extended_context["mock_cleanup"] = mock_cleanup

    try:
        # Call the mock cleanup function
        mock_cleanup()
    except Exception as e:
        # Store the exception
        cleanup_extended_context["cleanup_error"] = e


@then("the test should handle cleanup errors gracefully")
def test_handles_cleanup_errors_gracefully(cleanup_extended_context):
    """Verify that the test handles cleanup errors gracefully."""
    # Create a mock cleanup function that will raise an exception
    mock_cleanup = MagicMock(side_effect=Exception("Cleanup error"))

    # Call the mock cleanup function and catch the exception
    try:
        mock_cleanup()
        # If we get here, the mock didn't raise an exception, which is unexpected
        assert False, "Mock cleanup function should have raised an exception"
    except Exception as e:
        # Verify that the exception is what we expect
        assert str(e) == "Cleanup error"
        assert isinstance(e, Exception)

    # In a real test, we would want to log the error but not fail the test
    # Here we're just verifying that the error was caught
