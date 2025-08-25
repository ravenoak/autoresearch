# Storage Eviction

Autoresearch manages bounded in-memory data with configurable eviction
policies. We model two strategies:

- **LRU**: removes the least recently accessed item.
- **FIFO**: evicts items in insertion order.

Both policies operate in constant time per update and require memory
linear in cache size.

## Verification

Simulation tests
[tests/analysis/test_storage_eviction.py](../../tests/analysis/test_storage_eviction.py)
exercise typical access patterns and confirm the expected eviction order.
