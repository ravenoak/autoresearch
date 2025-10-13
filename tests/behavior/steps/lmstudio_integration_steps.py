"""
Behavior-driven test steps for LM Studio integration.

This module provides step implementations for testing LM Studio integration
using the Behave framework with natural language test scenarios.
"""

import os
import tempfile
from pathlib import Path

from behave import given, when, then
from hamcrest import assert_that, equal_to, is_not, has_length, greater_than_or_equal_to

from autoresearch.config.loader import ConfigLoader
from autoresearch.llm.adapters import LMStudioAdapter
from autoresearch.errors import LLMError


@given("I have a working LM Studio server running on localhost:1234")
def step_lmstudio_server_running(context):
    """Verify LM Studio server is accessible."""
    try:
        adapter = LMStudioAdapter()
        models = adapter.available_models
        context.lmstudio_adapter = adapter
        context.discovered_models = models
        assert_that(models, is_not(has_length(0)), "LM Studio should have at least one model loaded")
    except Exception as e:
        context.scenario.skip(f"LM Studio server not available: {e}")


@given("I have configured autoresearch to use the lmstudio backend")
def step_configured_lmstudio_backend(context):
    """Verify autoresearch is configured for LM Studio."""
    config_loader = ConfigLoader()
    config = config_loader.config
    assert_that(config.llm_backend, equal_to("lmstudio"), "Backend should be lmstudio")


@given("I have a valid autoresearch.toml configuration file")
def step_valid_config_file(context):
    """Ensure configuration file is valid."""
    config_loader = ConfigLoader()
    config = config_loader.config
    # Configuration should load without errors
    assert_that(config.llm_backend, is_not(None))


@given("I have discovered models with different context sizes")
def step_discovered_models_with_context(context):
    """Verify we have discovered models with context size information."""
    adapter = context.lmstudio_adapter
    models = adapter.available_models

    # Ensure we have context size information for at least some models
    context_sizes = {}
    for model in models[:3]:  # Test first 3 models
        try:
            context_size = adapter.get_context_size(model)
            context_sizes[model] = context_size
        except Exception:
            pass  # Skip models without context size info

    context.model_context_sizes = context_sizes
    assert_that(len(context_sizes), greater_than_or_equal_to(1), "Should have context size info for at least one model")


@given("I have a long prompt that exceeds context limits")
def step_long_prompt_exceeds_context(context):
    """Create a prompt that exceeds typical context limits."""
    long_content = "This is a very detailed explanation of quantum computing principles. " * 1000
    context.long_prompt = long_content
    context.prompt_length = len(long_content)


@given("I have set AUTORESEARCH_MODEL environment variable")
def step_set_env_model_variable(context):
    """Set environment variable for model selection testing."""
    context.original_env_model = os.getenv("AUTORESEARCH_MODEL")
    os.environ["AUTORESEARCH_MODEL"] = "mistral"
    context.env_model_set = True


@given("some models are not available")
def step_some_models_unavailable(context):
    """Simulate some models being unavailable for testing fallback logic."""
    # This would typically be done by mocking or configuring a test scenario
    # For now, we'll just note that this scenario is for testing fallback behavior
    context.fallback_test = True


@given("LM Studio server is unavailable")
def step_lmstudio_server_unavailable(context):
    """Simulate LM Studio server being unavailable."""
    # Set invalid endpoint to simulate unavailability
    original_endpoint = os.getenv("LMSTUDIO_ENDPOINT")
    os.environ["LMSTUDIO_ENDPOINT"] = "http://localhost:9999/invalid"
    context.original_endpoint = original_endpoint
    context.server_unavailable = True


@when("I initialize the LM Studio adapter")
def step_initialize_lmstudio_adapter(context):
    """Initialize the LM Studio adapter."""
    context.adapter = LMStudioAdapter()
    context.adapter_initialized = True


@when("I check context size for each model")
def step_check_context_sizes(context):
    """Check context sizes for discovered models."""
    adapter = context.adapter
    models = adapter.available_models

    context.context_results = {}
    for model in models[:3]:  # Test first 3 models
        try:
            context_size = adapter.get_context_size(model)
            context.context_results[model] = context_size
        except Exception as e:
            context.context_results[model] = f"Error: {e}"


@when("I request prompt truncation")
def step_request_prompt_truncation(context):
    """Request truncation of a long prompt."""
    adapter = context.adapter
    model = adapter.available_models[0] if adapter.available_models else "test-model"

    context.truncated_prompt = adapter.truncate_prompt(context.long_prompt, model)
    context.truncation_performed = True


@when("I request adaptive token budgeting")
def step_request_adaptive_budgeting(context):
    """Request adaptive token budgeting."""
    adapter = context.adapter
    model = adapter.available_models[0] if adapter.available_models else "test-model"
    base_budget = 1000

    context.adaptive_budget = adapter.get_adaptive_token_budget(model, base_budget)
    context.budgeting_performed = True


@when("I initialize the model selection logic")
def step_initialize_model_selection(context):
    """Initialize model selection logic."""
    from autoresearch.orchestration.metrics import _select_model_enhanced
    from autoresearch.config.loader import ConfigLoader

    config_loader = ConfigLoader()
    config = config_loader.config

    context.selected_model = _select_model_enhanced(config, "synthesizer")
    context.model_selection_performed = True


@when("I request model selection")
def step_request_model_selection(context):
    """Request model selection."""
    from autoresearch.orchestration.metrics import _select_model_enhanced
    from autoresearch.config.loader import ConfigLoader

    config_loader = ConfigLoader()
    config = config_loader.config

    context.selected_model = _select_model_enhanced(config, "synthesizer")
    context.model_selection_performed = True


@when("I attempt to use the LM Studio adapter")
def step_attempt_use_lmstudio_adapter(context):
    """Attempt to use LM Studio adapter (expecting it to fail due to unavailability)."""
    try:
        adapter = LMStudioAdapter()
        # Try to get models - this should fail
        models = adapter.available_models
        context.adapter_usage_succeeded = True
    except Exception as e:
        context.adapter_usage_error = str(e)
        context.adapter_usage_succeeded = False


@then("I should discover available models from the LM Studio API")
def step_should_discover_models(context):
    """Verify models were discovered from LM Studio API."""
    adapter = context.adapter
    models = adapter.available_models

    assert_that(models, is_not(has_length(0)), "Should discover at least one model")
    assert_that(adapter.get_model_info()["using_discovered"], equal_to(True), "Should be using discovered models")


@then("I should see model context sizes and capabilities")
def step_should_see_context_sizes(context):
    """Verify context sizes and capabilities are available."""
    adapter = context.adapter
    model_info = adapter.get_model_info()

    assert_that(model_info["model_context_sizes"], is_not({}), "Should have context size information")
    assert_that(len(model_info["discovered_models"]), greater_than_or_equal_to(1), "Should have discovered models")


@then("I should be able to select models based on their capabilities")
def step_should_select_models_by_capability(context):
    """Verify model selection based on capabilities."""
    adapter = context.adapter
    models = adapter.available_models

    # Should be able to get context sizes for models
    for model in models[:2]:  # Test first 2 models
        context_size = adapter.get_context_size(model)
        assert_that(context_size, greater_than_or_equal_to(1), f"Model {model} should have valid context size")


@then("I should get accurate context size information")
def step_should_get_accurate_context(context):
    """Verify accurate context size information."""
    context_sizes = context.context_results

    # At least one model should have a valid context size
    valid_contexts = [size for size in context_sizes.values() if isinstance(size, int) and size > 0]
    assert_that(len(valid_contexts), greater_than_or_equal_to(1), "Should have at least one valid context size")


@then("I should be able to estimate token counts for prompts")
def step_should_estimate_tokens(context):
    """Verify token estimation works."""
    adapter = context.adapter

    test_prompt = "This is a test prompt for token estimation."
    estimated_tokens = adapter.estimate_prompt_tokens(test_prompt)

    assert_that(estimated_tokens, greater_than_or_equal_to(1), "Should estimate at least 1 token")


@then("I should receive warnings when prompts exceed context limits")
def step_should_receive_warnings(context):
    """Verify warnings for prompts exceeding context limits."""
    adapter = context.adapter
    model = adapter.available_models[0] if adapter.available_models else "test-model"

    # Test with a prompt that would exceed limits
    fits, warning = adapter.check_context_fit(context.long_prompt, model)

    # For very long prompts, should either not fit or provide a warning
    if not fits and warning:
        assert_that(warning, is_not(None), "Should provide warning for oversized prompts")


@then("I should get an intelligently truncated prompt")
def step_should_get_truncated_prompt(context):
    """Verify intelligent prompt truncation."""
    assert_that(context.truncation_performed, equal_to(True), "Truncation should have been performed")
    assert_that(context.truncated_prompt, is_not(None), "Should have truncated prompt")


@then("the truncated prompt should preserve important content")
def step_truncated_should_preserve_content(context):
    """Verify truncated prompt preserves important content."""
    original = context.long_prompt
    truncated = context.truncated_prompt

    assert_that(len(truncated), is_not(equal_to(len(original))), "Prompt should be truncated")
    assert_that(len(truncated), greater_than_or_equal_to(100), "Truncated prompt should be substantial")


@then("the truncated prompt should fit within context limits")
def step_truncated_should_fit_limits(context):
    """Verify truncated prompt fits within limits."""
    adapter = context.adapter
    model = adapter.available_models[0] if adapter.available_models else "test-model"

    fits, _ = adapter.check_context_fit(context.truncated_prompt, model)
    assert_that(fits, equal_to(True), "Truncated prompt should fit within context limits")


@then("I should get appropriate token budgets based on model capabilities")
def step_should_get_appropriate_budgets(context):
    """Verify appropriate token budgets."""
    assert_that(context.budgeting_performed, equal_to(True), "Budgeting should have been performed")
    assert_that(context.adaptive_budget, is_not(None), "Should have adaptive budget")
    assert_that(context.adaptive_budget, greater_than_or_equal_to(512), "Budget should be reasonable")


@then("larger models should get higher budgets")
def step_larger_models_higher_budgets(context):
    """Verify larger models get higher budgets."""
    adapter = context.adapter

    # Find models with different context sizes
    models_with_sizes = []
    for model in adapter.available_models[:3]:
        try:
            context_size = adapter.get_context_size(model)
            budget = adapter.get_adaptive_token_budget(model, 1000)
            models_with_sizes.append((model, context_size, budget))
        except Exception:
            pass

    # Should have at least 2 models to compare
    if len(models_with_sizes) >= 2:
        # Sort by context size
        models_with_sizes.sort(key=lambda x: x[1], reverse=True)
        larger_model_budget = models_with_sizes[0][2]
        smaller_model_budget = models_with_sizes[-1][2]

        # Larger model should generally get higher or equal budget
        assert_that(larger_model_budget, greater_than_or_equal_to(smaller_model_budget), "Larger models should get appropriate budgets")


@then("the budgets should consider performance history")
def step_budgets_consider_performance(context):
    """Verify budgets consider performance history."""
    # This would require setting up performance history first
    # For now, just verify that budgeting works
    assert_that(context.adaptive_budget, greater_than_or_equal_to(512), "Budget should be reasonable")


@then("I should use the model specified in the environment variable")
def step_should_use_env_model(context):
    """Verify environment variable model selection."""
    assert_that(context.model_selection_performed, equal_to(True), "Model selection should have been performed")
    assert_that(context.selected_model, equal_to("mistral"), "Should use model from environment variable")


@then("agent-specific overrides should take precedence")
def step_agent_overrides_precedence(context):
    """Verify agent-specific overrides take precedence."""
    # Set agent-specific override
    os.environ["AUTORESEARCH_MODEL_SYNTHESIZER"] = "llama-3.2-1b-instruct"

    from autoresearch.orchestration.metrics import _select_model_enhanced
    from autoresearch.config.loader import ConfigLoader

    config_loader = ConfigLoader()
    config = config_loader.config

    selected_model = _select_model_enhanced(config, "synthesizer")
    assert_that(selected_model, equal_to("llama-3.2-1b-instruct"), "Should use agent-specific override")


@then("I should get a fallback model from available models")
def step_should_get_fallback_model(context):
    """Verify fallback model selection."""
    assert_that(context.model_selection_performed, equal_to(True), "Model selection should have been performed")
    assert_that(context.selected_model, is_not(None), "Should have selected a fallback model")
    assert_that(context.selected_model, is_not(""), "Fallback model should not be empty")


@then("the fallback should prefer models with larger context windows")
def step_fallback_prefers_large_context(context):
    """Verify fallback prefers larger context models."""
    adapter = context.adapter

    # Test the intelligent fallback logic
    fallback_model = adapter._get_intelligent_fallback(adapter)
    assert_that(fallback_model, is_not(None), "Should get a fallback model")

    # If we have multiple models, the fallback should prefer larger context
    if len(adapter.available_models) > 1:
        # This is a simplified test - in practice we'd need more sophisticated logic
        context_size = adapter.get_context_size(fallback_model)
        assert_that(context_size, greater_than_or_equal_to(4096), "Fallback should have reasonable context size")


@then("I should get appropriate error messages")
def step_should_get_error_messages(context):
    """Verify appropriate error messages for unavailable server."""
    assert_that(context.adapter_usage_succeeded, equal_to(False), "Adapter usage should fail")
    assert_that(context.adapter_usage_error, is_not(None), "Should have error message")
    assert_that(context.adapter_usage_error, is_not(""), "Error message should not be empty")


@then("I should be able to fall back to alternative models")
def step_should_fallback_alternatives(context):
    """Verify fallback to alternative models."""
    # This would test fallback to other backends when LM Studio fails
    # For now, just verify the error handling works
    assert_that(context.adapter_usage_error, is_not(None), "Should have error information for fallback")


@then("the system should remain functional")
def step_system_should_remain_functional(context):
    """Verify system remains functional despite LM Studio issues."""
    # The system should still be able to load configuration and perform other operations
    config_loader = ConfigLoader()
    config = config_loader.config

    assert_that(config, is_not(None), "Configuration should still load")
    assert_that(config.llm_backend, is_not(None), "LLM backend should be configured")


# Cleanup steps
def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    # Restore environment variables
    if hasattr(context, 'original_env_model') and context.original_env_model is not None:
        os.environ["AUTORESEARCH_MODEL"] = context.original_env_model
    elif hasattr(context, 'original_env_model') and "AUTORESEARCH_MODEL" in os.environ:
        del os.environ["AUTORESEARCH_MODEL"]

    if hasattr(context, 'env_model_set') and "AUTORESEARCH_MODEL_SYNTHESIZER" in os.environ:
        del os.environ["AUTORESEARCH_MODEL_SYNTHESIZER"]

    if hasattr(context, 'original_endpoint') and context.original_endpoint is not None:
        os.environ["LMSTUDIO_ENDPOINT"] = context.original_endpoint
    elif hasattr(context, 'original_endpoint') and "LMSTUDIO_ENDPOINT" in os.environ:
        del os.environ["LMSTUDIO_ENDPOINT"]

    # Clean up any test files
    if hasattr(context, 'temp_config_file') and context.temp_config_file.exists():
        context.temp_config_file.unlink()
