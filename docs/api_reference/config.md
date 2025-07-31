# Configuration API

This page documents the Configuration API, which provides configuration management for the Autoresearch system.

## Config Loader

The `ConfigLoader` class is responsible for loading and watching configuration changes.
Use the :py:meth:`~autoresearch.config.loader.ConfigLoader.temporary_instance` context
manager when you need a separate configuration loader for a short period.

```python
from autoresearch.config.loader import ConfigLoader

with ConfigLoader.temporary_instance() as loader:
    loader.load("custom.yaml")
    # operate with the temporary configuration here
```

::: autoresearch.config.loader.ConfigLoader

## Config Model

The `ConfigModel` class defines the structure of the configuration.

::: autoresearch.config.models.ConfigModel


## Storage Config

The `StorageConfig` class defines the storage configuration options.

::: autoresearch.config.models.StorageConfig

## Agent Config

The `AgentConfig` class defines the agent configuration options.

::: autoresearch.config.models.AgentConfig

## Search Config

The `SearchConfig` class defines the search configuration options.

::: autoresearch.config.models.SearchConfig

## Context-Aware Search Config

The `ContextAwareSearchConfig` class defines the context-aware search configuration options.

::: autoresearch.config.models.ContextAwareSearchConfig




