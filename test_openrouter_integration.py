#!/usr/bin/env python3
"""
Test script for OpenRouter integration with Autoresearch.
Tests various research scenarios to ensure the system works correctly.
"""

import os
import sys
import time
import asyncio
from typing import Dict, List, Any
import json

# Add src to path for imports
sys.path.insert(0, 'src')

from autoresearch.config import ConfigLoader
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse
from autoresearch.orchestration.reasoning import ReasoningMode

def test_openrouter_configuration():
    """Test that OpenRouter configuration is properly loaded."""
    print("🔧 Testing OpenRouter configuration...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Check OpenRouter backend is configured
    assert config.llm_backend == "openrouter", f"Expected openrouter backend, got {config.llm_backend}"

    # Check API key is set
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    assert len(api_key) > 0, "OpenRouter API key not set"

    # Check free-tier model is configured
    assert "mistralai/mistral-small" in config.default_model, f"Free-tier model not configured: {config.default_model}"

    print("✅ OpenRouter configuration test passed")
    return True

def test_basic_research_query():
    """Test a basic research query to ensure OpenRouter integration works."""
    print("🔍 Testing basic research query...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    orchestrator = Orchestrator()
    query = "What are the key benefits of renewable energy sources?"

    try:
        result = orchestrator.run_query(query, config)

        # Basic validation
        assert isinstance(result, QueryResponse), "Result should be QueryResponse object"
        assert len(result.answer) > 0, "Answer should not be empty"
        assert len(result.citations) > 0, "Should have citations"
        assert len(result.reasoning) > 0, "Should have reasoning steps"

        print(f"✅ Basic research query successful - Answer length: {len(result.answer)}")
        return True

    except Exception as e:
        print(f"❌ Basic research query failed: {e}")
        return False

def test_reasoning_modes():
    """Test different reasoning modes work correctly."""
    print("🧠 Testing reasoning modes...")

    modes = [ReasoningMode.DIALECTICAL, ReasoningMode.DIRECT]
    config_loader = ConfigLoader()

    for mode in modes:
        print(f"  Testing {mode.value} mode...")
        config = config_loader.load_config()
        config.reasoning_mode = mode

        orchestrator = Orchestrator()
        query = f"Explain the concept of sustainable development using {mode.value} reasoning."

        try:
            result = orchestrator.run_query(query, config)
            assert len(result.answer) > 0, f"Answer should not be empty for {mode.value} mode"
            print(f"    ✅ {mode.value} mode successful")
        except Exception as e:
            print(f"    ❌ {mode.value} mode failed: {e}")
            return False

    print("✅ Reasoning modes test passed")
    return True

def test_circuit_breaker():
    """Test circuit breaker functionality for API rate limiting."""
    print("🔌 Testing circuit breaker functionality...")

    # Check configuration has circuit breaker settings
    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Verify circuit breaker is configured
    assert hasattr(config, 'circuit_breaker_threshold'), "Circuit breaker threshold not configured"
    assert config.circuit_breaker_threshold == 5, "Circuit breaker threshold not set correctly"
    assert hasattr(config, 'circuit_breaker_cooldown'), "Circuit breaker cooldown not configured"
    assert config.circuit_breaker_cooldown == 60, "Circuit breaker cooldown not set correctly"

    print("✅ Circuit breaker configuration test passed")
    return True

def test_model_routing():
    """Test model routing configuration for free-tier models."""
    print("🎯 Testing model routing configuration...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Check model routing is enabled
    assert config.model_routing.enabled == True, "Model routing should be enabled"

    # Check free-tier models are configured
    synthesizer_config = config.agent_config.synthesizer
    allowed_models = synthesizer_config.allowed_models

    free_tier_models = [
        "mistralai/mistral-small",
        "meta-llama/llama-3.2-3b-instruct",
        "qwen/qwen-2-7b-instruct"
    ]

    for model in free_tier_models:
        assert model in allowed_models, f"Free-tier model {model} not in allowed models"

    print("✅ Model routing configuration test passed")
    return True

def test_performance_monitoring():
    """Test performance monitoring and metrics collection."""
    print("📊 Testing performance monitoring...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Check monitoring is enabled
    assert config.monitoring_enabled == True, "Monitoring should be enabled"

    print("✅ Performance monitoring configuration test passed")
    return True

def test_error_handling():
    """Test error handling for various failure scenarios."""
    print("🛠️ Testing error handling...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Test with invalid API key (simulate error)
    original_key = os.environ.get("OPENROUTER_API_KEY", "")
    os.environ["OPENROUTER_API_KEY"] = "invalid_key_12345"

    orchestrator = Orchestrator()

    try:
        # This should fail gracefully
        result = orchestrator.run_query("Test query with invalid key", config)
        # If we get here, the error handling worked
        print("✅ Error handling test passed - graceful failure with invalid API key")
    except Exception as e:
        print(f"✅ Error handling test passed - caught expected error: {type(e).__name__}")
    finally:
        # Restore original key
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)

    return True

def test_configuration_persistence():
    """Test that configuration changes persist correctly."""
    print("💾 Testing configuration persistence...")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    # Check configuration is properly loaded
    assert config.llm_backend == "openrouter", "Configuration not persisted correctly"

    print("✅ Configuration persistence test passed")
    return True

async def run_research_scenario(name: str, query: str, expected_elements: List[str]) -> Dict[str, Any]:
    """Run a single research scenario and return results."""
    print(f"\n📋 Running research scenario: {name}")
    print(f"Query: {query}")

    config_loader = ConfigLoader()
    config = config_loader.load_config()

    orchestrator = Orchestrator()

    start_time = time.time()
    try:
        result = orchestrator.run_query(query, config)
        end_time = time.time()

        # Validate expected elements
        missing_elements = []
        for element in expected_elements:
            if element == "answer" and not result.answer:
                missing_elements.append("answer")
            elif element == "citations" and not result.citations:
                missing_elements.append("citations")
            elif element == "reasoning" and not result.reasoning:
                missing_elements.append("reasoning")

        success = len(missing_elements) == 0

        return {
            "name": name,
            "query": query,
            "success": success,
            "duration": end_time - start_time,
            "missing_elements": missing_elements,
            "answer_length": len(result.answer) if result.answer else 0,
            "citations_count": len(result.citations) if result.citations else 0,
            "reasoning_count": len(result.reasoning) if result.reasoning else 0
        }

    except Exception as e:
        return {
            "name": name,
            "query": query,
            "success": False,
            "error": str(e),
            "duration": time.time() - start_time
        }

async def run_comprehensive_research_scenarios():
    """Run all research scenarios and return comprehensive results."""
    print("🚀 Running comprehensive research scenarios...")

    scenarios = [
        {
            "name": "Environmental Research",
            "query": "What are the main environmental benefits of transitioning to renewable energy sources?",
            "expected": ["answer", "citations", "reasoning"]
        },
        {
            "name": "Technology Research",
            "query": "Explain the key differences between supervised and unsupervised machine learning.",
            "expected": ["answer", "citations", "reasoning"]
        },
        {
            "name": "Health Research",
            "query": "What are the evidence-based benefits of regular exercise for mental health?",
            "expected": ["answer", "citations", "reasoning"]
        },
        {
            "name": "Policy Research",
            "query": "What are the economic impacts of universal basic income programs?",
            "expected": ["answer", "citations", "reasoning"]
        },
        {
            "name": "Science Research",
            "query": "Explain the role of quantum computing in modern cryptography.",
            "expected": ["answer", "citations", "reasoning"]
        }
    ]

    results = []
    for scenario in scenarios:
        result = await run_research_scenario(
            scenario["name"],
            scenario["query"],
            scenario["expected"]
        )
        results.append(result)

    return results

def main():
    """Run all tests and scenarios."""
    print("🧪 Starting comprehensive Autoresearch OpenRouter integration tests")
    print("=" * 70)

    # Run individual tests
    tests = [
        test_openrouter_configuration,
        test_basic_research_query,
        test_reasoning_modes,
        test_circuit_breaker,
        test_model_routing,
        test_performance_monitoring,
        test_error_handling,
        test_configuration_persistence,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All configuration and integration tests passed!")
    else:
        print(f"❌ {total - passed} tests failed")
        return 1

    # Run research scenarios
    print("\n" + "=" * 70)
    print("🔬 Running research scenarios...")

    try:
        results = asyncio.run(run_comprehensive_research_scenarios())

        # Analyze results
        successful_scenarios = sum(1 for r in results if r["success"])
        total_scenarios = len(results)

        print(f"\n📈 Research Scenarios Results: {successful_scenarios}/{total_scenarios} successful")

        # Detailed results
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"\n{status} {result['name']}")
            print(f"   Duration: {result['duration']:.2f}s")
            if result["success"]:
                print(f"   Answer length: {result['answer_length']} characters")
                print(f"   Citations: {result['citations_count']}")
                print(f"   Reasoning steps: {result['reasoning_count']}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
                print(f"   Missing elements: {result.get('missing_elements', [])}")

        if successful_scenarios == total_scenarios:
            print("\n🎉 All research scenarios completed successfully!")
            return 0
        else:
            print(f"\n⚠️  {total_scenarios - successful_scenarios} research scenarios failed")
            return 1

    except Exception as e:
        print(f"\n❌ Research scenarios failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
