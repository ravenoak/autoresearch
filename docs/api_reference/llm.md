# LLM API

This page documents the LLM API, which provides language model integration and adapters for the Autoresearch system.

## LLM Adapters

The LLM adapters provide a unified interface for interacting with different language model providers.

::: autoresearch.llm.adapters.LLMAdapter

### OpenAI Adapter

The `OpenAIAdapter` class provides integration with OpenAI's language models.

::: autoresearch.llm.adapters.OpenAIAdapter


### OpenRouter Adapter

The `OpenRouterAdapter` class provides integration with OpenRouter.ai, which offers access to various language models.

::: autoresearch.llm.adapters.OpenRouterAdapter

## LLM Factory

The `LLMFactory` class provides a registry for LLM adapters.

::: autoresearch.llm.registry.LLMFactory

## Token Counting

The token counting functionality provides tools for estimating token usage.

::: autoresearch.llm.token_counting

## LLM Capabilities

The LLM capabilities functionality provides tools for discovering and managing LLM capabilities.

::: autoresearch.llm.capabilities


