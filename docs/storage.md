# Storage

The storage system is responsible for persisting claims and supporting vector search. It uses a hybrid approach with multiple backends:

1. **NetworkX Graph** - For storing the knowledge graph structure
2. **DuckDB** - For efficient vector storage and similarity search
3. **RDFLib** - For semantic storage and querying

## Architecture

The storage component consists of several key classes:

- **StorageManager** - Main class for interacting with the storage system
- **Global Storage State** - Maintains the state of the storage system
- **StorageConfig** - Configuration for the storage system
- **StorageError** - Error hierarchy for storage-related errors

The diagram below shows the relationships between these classes and their interactions with external libraries:

![Storage Component](diagrams/storage.png)

## Storage Flow

1. The `setup()` method initializes the storage backends
2. The `persist_claim()` method validates and stores claims in all backends
3. The `vector_search()` method finds similar claims using vector similarity
4. The `teardown()` method closes connections and cleans up resources

## Eviction Policies

The storage system supports automatic eviction of claims when the memory usage exceeds the configured budget:

1. **LRU (Least Recently Used)** - Evicts the least recently accessed claims
2. **Low Score** - Evicts claims with the lowest relevance scores

The eviction process is triggered automatically by the `_enforce_ram_budget()` method when the memory usage exceeds the configured budget.

## Adding Custom Storage Backends

To add a custom storage backend:

1. Extend the `StorageManager` class with methods for your backend
2. Add initialization in `setup()`
3. Add cleanup in `teardown()`
4. Add persistence in `persist_claim()`
5. Update the configuration schema in `ConfigModel`
