# Configuration API

This page documents the Configuration API, which provides configuration management for the Autoresearch system.

## Config Loader

The `ConfigLoader` class is responsible for loading and watching configuration changes.
Use the :py:meth:`~autoresearch.config.ConfigLoader.temporary_instance` context
manager when you need a separate configuration loader for a short period.

```python
from autoresearch.config import ConfigLoader

with ConfigLoader.temporary_instance() as loader:
    loader.load("custom.yaml")
    # operate with the temporary configuration here
```

::: autoresearch.config.ConfigLoader

## Config Model

The `ConfigModel` class defines the structure of the configuration.

::: autoresearch.config.ConfigModel


## Storage Config

The `StorageConfig` class defines the storage configuration options.

::: autoresearch.config.StorageConfig

## Agent Config

The `AgentConfig` class defines the agent configuration options.

::: autoresearch.config.AgentConfig

## Search Config

The `SearchConfig` class defines the search configuration options.

::: autoresearch.config.SearchConfig

## Context-Aware Search Config

The `ContextAwareSearchConfig` class defines the context-aware search configuration options.

::: autoresearch.config.ContextAwareSearchConfig




