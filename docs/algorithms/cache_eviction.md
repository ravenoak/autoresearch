# Cache Eviction Strategy

Autoresearch caches intermediate results until a memory budget is reached. This
note outlines the policy used to discard entries when space runs low.

## Eviction policy
- Least Recently Used (LRU): the cache tracks access order and removes the
  stalest entry first.

## Complexity
- Insert and access: O(1) using an ordered dictionary.
- Evict: O(1) per removed entry.

## Assumptions
- Each item reports its memory footprint on insertion.
- All entries are independent and eviction has no side effects.
- The budget is fixed during the simulation.

See [caching](../caching.md) for the storage layer and broader context.
