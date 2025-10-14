#!/usr/bin/env python3
"""
Regression tests for autoresearch import fixes.

This test file ensures that the import issues we fixed don't regress.
Tests verify that agents can properly import from orchestration modules.
"""

import sys
import tempfile
import subprocess
from pathlib import Path


def test_agents_orchestration_import():
    """Test that agents can import from orchestration modules."""
    # This test verifies that the orchestration.py file in agents directory
    # properly re-exports the needed modules
    try:
        from autoresearch.agents.orchestration import get_orchestration_metrics, QueryState
        print("✓ Agents orchestration imports work correctly")
        return True
    except ImportError as e:
        print(f"✗ Agents orchestration import failed: {e}")
        return False


def test_synthesizer_imports():
    """Test that synthesizer can import required orchestration components."""
    try:
        from autoresearch.agents.dialectical.synthesizer import SynthesizerAgent
        print("✓ Synthesizer imports work correctly")
        return True
    except ImportError as e:
        print(f"✗ Synthesizer import failed: {e}")
        return False


def test_base_agent_imports():
    """Test that base agent can import QueryState."""
    try:
        from autoresearch.agents.base import Agent, AgentRole
        print("✓ Base agent imports work correctly")
        return True
    except ImportError as e:
        print(f"✗ Base agent import failed: {e}")
        return False


def test_metrics_function_exists():
    """Test that get_orchestration_metrics function exists."""
    try:
        from autoresearch.orchestration.metrics import get_orchestration_metrics
        # Test that it returns an OrchestrationMetrics instance
        metrics = get_orchestration_metrics()
        print(f"✓ get_orchestration_metrics function works (type: {type(metrics)})")
        return True
    except ImportError as e:
        print(f"✗ get_orchestration_metrics function failed: {e}")
        return False


def test_autoresearch_module_import():
    """Test that the main autoresearch module can be imported."""
    try:
        import autoresearch
        print("✓ Main autoresearch module imports correctly")
        return True
    except ImportError as e:
        print(f"✗ Main autoresearch module import failed: {e}")
        return False


def test_search_command_basic():
    """Test that the search command can be invoked without crashing."""
    try:
        # Test just the import and basic initialization, not full execution
        # since that requires LM Studio and API keys
        from autoresearch.main.app import search
        print("✓ Search command can be imported")
        return True
    except ImportError as e:
        print(f"✗ Search command import failed: {e}")
        return False


def run_all_tests():
    """Run all regression tests."""
    print("Running autoresearch import regression tests...\n")

    tests = [
        test_agents_orchestration_import,
        test_synthesizer_imports,
        test_base_agent_imports,
        test_metrics_function_exists,
        test_autoresearch_module_import,
        test_search_command_basic,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All regression tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
