#!/usr/bin/env python3
"""Test script for LM Studio integration with dynamic model discovery.

This script tests the enhanced LM Studio adapter functionality including:
- Dynamic model discovery from LM Studio API
- Model validation and selection
- Error handling for unavailable LM Studio server
- Fallback behavior when model discovery fails
- Enhanced model selection logic
- Context size awareness and intelligent truncation

Usage:
    python scripts/test_lmstudio_integration.py

Environment Variables:
    LMSTUDIO_ENDPOINT: Override the default LM Studio endpoint
    LMSTUDIO_TIMEOUT: Set timeout for LM Studio requests
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from autoresearch.llm.adapters import LMStudioAdapter
from autoresearch.errors import LLMError
from autoresearch.orchestration.metrics import _select_model_enhanced, _get_lmstudio_discovered_model
from autoresearch.config.models import ConfigModel


def test_lmstudio_adapter():
    """Test LM Studio adapter functionality."""
    print("Testing LM Studio adapter...")

    try:
        # Initialize the adapter
        adapter = LMStudioAdapter()

        # Print adapter information
        print(f"LM Studio endpoint: {adapter.endpoint}")
        print(f"Timeout: {adapter.timeout}s")

        # Test model discovery
        model_info = adapter.get_model_info()
        print(f"Model discovery status: {model_info}")

        if model_info["using_discovered"]:
            print(f"✅ Discovered {len(model_info['discovered_models'])} models:")
            for i, model in enumerate(model_info["discovered_models"], 1):
                print(f"  {i}. {model}")
        else:
            print(f"⚠️ Using fallback models: {model_info['fallback_models']}")
            if model_info["discovery_error"]:
                print(f"Discovery error: {model_info['discovery_error']}")

        # Test available models property
        available = adapter.available_models
        print(f"Available models: {available}")

        # Test model validation
        if available:
            print(f"Testing model validation with '{available[0]}'...")
            validated = adapter.validate_model(available[0])
            print(f"Validated model: {validated}")

            print(f"Testing model validation with None (should use default)...")
            validated_default = adapter.validate_model(None)
            print(f"Validated default model: {validated_default}")

        # Test generation (this will likely fail without LM Studio running)
        print("\nTesting text generation (will likely fail if LM Studio not running)...")
        try:
            response = adapter.generate("Hello, world!", model=available[0] if available else None)
            print(f"✅ Generation successful: {response[:100]}...")
        except LLMError as e:
            print(f"⚠️ Generation failed (expected): {e.context.get('suggestion', str(e))}")
        except Exception as e:
            print(f"⚠️ Generation failed with unexpected error: {e}")

        print("\n✅ LM Studio adapter test completed successfully!")

    except Exception as e:
        print(f"❌ LM Studio adapter test failed: {e}")
        return False

    return True


def test_enhanced_functionality():
    """Test enhanced LM Studio functionality as a researcher would use it."""
    print("\n🧪 Testing enhanced LM Studio functionality...")

    try:
        # 1. Initialize adapter and check model discovery
        print("1. Initializing LM Studio adapter and checking model discovery...")
        adapter = LMStudioAdapter()
        model_info = adapter.get_model_info()

        print(f"   Discovered models: {len(model_info['discovered_models'])}")
        print(f"   Using discovered: {model_info['using_discovered']}")
        print(f"   Fallback models: {model_info['fallback_models']}")

        if model_info['using_discovered']:
            print(f"   ✅ Successfully discovered {len(model_info['discovered_models'])} models")
            for i, model in enumerate(model_info['discovered_models'][:3], 1):
                context_size = adapter.get_context_size(model)
                print(f"     {i}. {model} (context: {context_size} tokens)")
        else:
            print("   ⚠️ Using fallback models due to discovery issues")

        # 2. Test enhanced model selection logic
        print("\n2. Testing enhanced model selection logic...")
        config = ConfigModel(llm_backend="lmstudio")

        # Test model selection for synthesizer agent
        selected_model = _select_model_enhanced(config, "synthesizer")
        print(f"   Selected model for synthesizer: {selected_model}")

        # Test context size awareness
        if selected_model in model_info['discovered_models']:
            context_size = adapter.get_context_size(selected_model)
            print(f"   Context size: {context_size} tokens")

            # Test prompt fitting
            test_prompt = "This is a test prompt to check if it fits within the context window."
            fits, warning = adapter.check_context_fit(test_prompt, selected_model)
            print(f"   Prompt fits: {fits}")
            if warning:
                print(f"   Warning: {warning}")

        # 3. Test intelligent truncation
        print("\n3. Testing intelligent prompt truncation...")
        long_prompt = "This is a very long prompt that should exceed the context limits. " * 100
        original_tokens = adapter.estimate_prompt_tokens(long_prompt)
        print(f"   Original prompt tokens: {original_tokens}")

        if original_tokens > 100:  # Only test if prompt is actually long
            truncated_prompt = adapter.truncate_prompt(long_prompt, selected_model)
            truncated_tokens = adapter.estimate_prompt_tokens(truncated_prompt)
            print(f"   Truncated prompt tokens: {truncated_tokens}")
            print(f"   Reduction: {original_tokens - truncated_tokens} tokens")

            # Verify truncation worked
            fits_after, _ = adapter.check_context_fit(truncated_prompt, selected_model)
            print(f"   Truncated prompt fits: {fits_after}")

        # 4. Test adaptive token budgeting
        print("\n4. Testing adaptive token budgeting...")
        adaptive_budget = adapter.get_adaptive_token_budget(selected_model, 1000)
        print(f"   Adaptive budget: {adaptive_budget} tokens")
        print(f"   Budget efficiency: {adaptive_budget / 1000:.1%} of base budget")

        # 5. Test performance tracking
        print("\n5. Testing performance tracking...")
        adapter.record_token_usage(selected_model, 100, 200, success=True)
        adapter.record_token_usage(selected_model, 150, 250, success=True)

        performance = adapter.get_model_performance_report(selected_model)
        if performance and "metrics" in performance:
            metrics = performance["metrics"]
            print(f"   Success rate: {metrics.get('success_rate', 0):.1%}")
            print(f"   Average tokens: {metrics.get('avg_tokens', 0):.0f}")

        print("✅ Enhanced functionality test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Enhanced functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adapter_factory():
    """Test that the adapter can be retrieved from the factory."""
    print("\nTesting adapter factory...")

    try:
        from autoresearch.llm.adapters import LLMAdapter

        adapter = LLMAdapter.get_adapter("lmstudio")
        print(f"✅ Successfully retrieved LM Studio adapter: {type(adapter).__name__}")

        # Verify it's the enhanced version
        if hasattr(adapter, 'get_model_info'):
            print("✅ Enhanced LM Studio adapter with model discovery")
        else:
            print("⚠️ Basic LM Studio adapter (no model discovery)")

        return True

    except Exception as e:
        print(f"❌ Adapter factory test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting LM Studio integration tests...\n")

    success = True
    success &= test_lmstudio_adapter()
    success &= test_enhanced_functionality()
    success &= test_adapter_factory()

    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
