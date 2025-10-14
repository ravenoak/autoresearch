Feature: OpenRouter Integration
    As a developer using Autoresearch
    I want to integrate with OpenRouter for accessing multiple LLM providers
    So that I can use various models for research and analysis through a unified API

    Background:
        Given I have configured autoresearch to use the openrouter backend
        And I have a valid autoresearch.toml configuration file
        And I have set up OpenRouter API credentials

    Scenario: Model Discovery and Free-Tier Models
        When I initialize the OpenRouter adapter
        Then I should discover available models from the OpenRouter API
        And I should see free-tier models available for testing
        And I should be able to identify models by their cost structure

    Scenario: Free-Tier Model Usage
        Given I have discovered free-tier models
        When I select a free-tier model for generation
        Then I should be able to generate text without incurring costs
        And I should receive responses with zero cost per token
        And I should be able to switch between different free models

    Scenario: Context Size Awareness for OpenRouter Models
        Given I have models with different context sizes from OpenRouter
        When I check context size for each model
        Then I should get accurate context size information from OpenRouter API
        And I should be able to estimate token counts for prompts
        And I should receive warnings when prompts exceed context limits

    Scenario: Intelligent Model Selection
        Given I have multiple models with different capabilities
        When I request model selection for a specific task
        Then I should get a model that matches the task requirements
        And I should prefer models based on cost and performance
        And I should fall back to free models when budget is constrained

    Scenario: Rate Limiting and Retry Logic
        Given I am making multiple rapid requests
        When I encounter rate limits from OpenRouter
        Then I should automatically retry with exponential backoff
        And I should respect Retry-After headers when provided
        And I should eventually succeed or provide clear error messages

    Scenario: Enhanced Error Handling
        Given I have configured OpenRouter with various error conditions
        When I encounter different types of API errors
        Then I should receive specific error messages for each error type
        And I should get actionable suggestions for resolving errors
        And I should be able to distinguish between temporary and permanent errors

    Scenario: Model Discovery Caching
        Given I have previously discovered models from OpenRouter
        When I request model information again
        Then I should get cached results for improved performance
        And I should be able to refresh the cache when needed
        And I should be able to clear the cache for fresh discovery

    Scenario: Environment Variable Configuration
        Given I have set OPENROUTER_API_KEY environment variable
        When I initialize the OpenRouter adapter
        Then I should use the API key from the environment
        And I should be able to override endpoint and cache settings
        And I should validate API key authenticity

    Scenario: Streaming Support Foundation
        Given I have OpenRouter models that support streaming
        When I request streaming generation
        Then I should get a streaming-compatible response
        And I should handle streaming interruptions gracefully
        And I should fall back to non-streaming when streaming fails

    Scenario: Cost Tracking and Monitoring
        Given I am using models with different cost structures
        When I generate text with various models
        Then I should track costs per request
        And I should log cost information for monitoring
        And I should be able to estimate total costs for research sessions

    Scenario: Cross-Provider Compatibility
        Given I have models from different providers through OpenRouter
        When I use models from Anthropic, Google, Meta, and others
        Then I should get consistent behavior across all providers
        And I should handle provider-specific features appropriately
        And I should maintain consistent error handling across providers

    Scenario: Configuration Persistence
        Given I have configured OpenRouter settings
        When I restart the autoresearch application
        Then I should retain my OpenRouter configuration
        And I should reconnect to OpenRouter with the same settings
        And I should resume using the same preferred models
