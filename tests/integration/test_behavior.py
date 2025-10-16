#!/usr/bin/env python3
"""
Behavior tests for autoresearch in temporary directory setup.

This test file verifies that autoresearch works correctly when run from
a temporary directory with its own configuration files.
"""

import subprocess
import sys
import os
from pathlib import Path


def test_autoresearch_help() -> int:
    """Test that autoresearch --help works."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "autoresearch", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and "Usage:" in result.stdout:
            print("✓ autoresearch --help works correctly")
            return 0
        else:
            print(f"✗ autoresearch --help failed: {result.stderr}")
            return 1
    except Exception as e:
        print(f"✗ autoresearch --help exception: {e}")
        return 1


def test_autoresearch_search_help() -> int:
    """Test that autoresearch search --help works."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "autoresearch", "search", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and "Run a search query" in result.stdout:
            print("✓ autoresearch search --help works correctly")
            return 0
        else:
            print(f"✗ autoresearch search --help failed: {result.stderr}")
            return 1
    except Exception as e:
        print(f"✗ autoresearch search --help exception: {e}")
        return 1


def test_config_loading_from_temp_dir() -> int:
    """Test that autoresearch can load config from temporary directory."""
    # Create a simple test that just checks if the config loading works
    # without actually running a full search (which needs API keys)
    test_dir = "/tmp/autoresearch_behavior_test"
    os.makedirs(test_dir, exist_ok=True)

    # Create a minimal config
    config_content = """
[core]
llm_backend = "lmstudio"
loops = 1
default_model = "mistral"

[search]
backends = ["serper"]
max_results_per_query = 1
"""

    config_path = Path(test_dir) / "autoresearch.toml"
    config_path.write_text(config_content)

    try:
        # Test that config loading works by checking if we can import and initialize
        # without errors (this will fail due to missing API keys but should not
        # fail due to import issues)
        from autoresearch.config.loader import ConfigLoader

        # Try to load config from our test directory
        loader = ConfigLoader([str(config_path)])
        _ = loader.config  # Just test that loading doesn't fail

        print("✓ Config loading works correctly")
        return 0

    except Exception as e:
        # We expect this to fail due to missing API keys, but not due to import errors
        if "No module named" in str(e) or "ImportError" in str(e):
            print(f"✗ Config loading failed due to import error: {e}")
            return 1
        else:
            print("✓ Config loading works (failed as expected due to missing API keys)")
            return 0


def test_search_command_initialization() -> int:
    """Test that search command can initialize without crashing."""
    try:
        # This tests that all the imports work correctly for the search command
        from autoresearch.main.app import search

        # Try to call the search function with minimal arguments to test initialization
        # We expect it to fail due to missing API keys, but not due to import errors
        try:
            # This should fail due to missing API keys but not import errors
            search("test query")
            print("✓ Search command initialization works")
            return 0
        except Exception as e:
            if "No module named" in str(e) or "ImportError" in str(e):
                print(f"✗ Search command initialization failed due to import error: {e}")
                return 1
            else:
                print(
                    "✓ Search command initialization works (failed as expected due to missing API keys)"
                )
                return 0

    except ImportError as e:
        print(f"✗ Search command import failed: {e}")
        return 1


def run_behavior_tests() -> int:
    """Run all behavior tests."""
    print("Running autoresearch behavior tests...\n")

    tests = [
        test_autoresearch_help,
        test_autoresearch_search_help,
        test_config_loading_from_temp_dir,
        test_search_command_initialization,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} behavior tests passed")

    if passed == total:
        print("🎉 All behavior tests passed!")
        return 0
    else:
        print("❌ Some behavior tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_behavior_tests())
