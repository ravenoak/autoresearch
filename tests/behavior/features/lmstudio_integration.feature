Feature: LM Studio Integration
    As a developer using Autoresearch
    I want to integrate with LM Studio for local LLM inference
    So that I can use local models for research and analysis

    Background:
        Given I have a working LM Studio server running on localhost:1234
        And I have configured autoresearch to use the lmstudio backend
        And I have a valid autoresearch.toml configuration file

    Scenario: Model Discovery
        When I initialize the LM Studio adapter
        Then I should discover available models from the LM Studio API
        And I should see model context sizes and capabilities
        And I should be able to select models based on their capabilities

    Scenario: Context Size Awareness
        Given I have discovered models with different context sizes
        When I check context size for each model
        Then I should get accurate context size information
        And I should be able to estimate token counts for prompts
        And I should receive warnings when prompts exceed context limits

    Scenario: Intelligent Prompt Truncation
        Given I have a long prompt that exceeds context limits
        When I request prompt truncation
        Then I should get an intelligently truncated prompt
        And the truncated prompt should preserve important content
        And the truncated prompt should fit within context limits

    Scenario: Adaptive Token Budgeting
        Given I have models with different capabilities
        When I request adaptive token budgeting
        Then I should get appropriate token budgets based on model capabilities
        And larger models should get higher budgets
        And the budgets should consider performance history

    Scenario: Environment Variable Model Selection
        Given I have set AUTORESEARCH_MODEL environment variable
        When I initialize the model selection logic
        Then I should use the model specified in the environment variable
        And agent-specific overrides should take precedence

    Scenario: Fallback Model Selection
        Given some models are not available
        When I request model selection
        Then I should get a fallback model from available models
        And the fallback should prefer models with larger context windows

    Scenario: Error Handling and Recovery
        Given LM Studio server is unavailable
        When I attempt to use the LM Studio adapter
        Then I should get appropriate error messages
        And I should be able to fall back to alternative models
        And the system should remain functional
