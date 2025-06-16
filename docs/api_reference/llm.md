# LLM API

This page documents the LLM API, which provides language model integration and adapters for the Autoresearch system.

## LLM Adapters

The LLM adapters provide a unified interface for interacting with different language model providers.

::: autoresearch.llm.adapters.LLMAdapter

### OpenAI Adapter

The `OpenAIAdapter` class provides integration with OpenAI's language models.

::: autoresearch.llm.adapters.OpenAIAdapter

### Anthropic Adapter

The `AnthropicAdapter` class provides integration with Anthropic's language models.

::: autoresearch.llm.adapters.AnthropicAdapter

### OpenRouter Adapter

The `OpenRouterAdapter` class provides integration with OpenRouter.ai, which offers access to various language models.

::: autoresearch.llm.adapters.OpenRouterAdapter

## LLM Registry

The `LLMRegistry` class provides a registry for LLM adapters.

::: autoresearch.llm.registry.LLMRegistry

## Token Counting

The token counting functionality provides tools for estimating token usage.

::: autoresearch.llm.token_counting

## LLM Capabilities

The LLM capabilities functionality provides tools for discovering and managing LLM capabilities.

::: autoresearch.llm.capabilities