# Cache Eviction Strategy

Autoresearch caches intermediate results until a memory budget is reached. This
note outlines the policy used to discard entries when space runs low.

## Eviction policy
- Least Recently Used (LRU): the cache tracks access order and removes the
  stalest entry first.

## Complexity
- Insert and access: O(1) using an ordered dictionary.
- Evict: O(1) per removed entry.

## Correctness
- LRU maintains items in recency order. When usage exceeds the budget \(B\),
  entries are popped from the head until the total is \(\leq B\).
- LRU is a stack algorithm, so a cache of size \(k\) is always a subset of
  a cache of size \(k+1\), minimizing misses among recency policies [1].

## Simulation
Running `uv run scripts/simulate_cache_eviction.py --budget 20 --steps 5`
shows bounded memory:

```
step=0 items=1 total=2
...
final memory 12/20
```

## References
1. R. Arpaci-Dusseau and A. Arpaci-Dusseau. "Operating Systems: Three Easy
   Pieces – Caching: The LRU Policy." https://pages.cs.wisc.edu/~remzi/OSTEP/

## Assumptions
- Each item reports its memory footprint on insertion.
- All entries are independent and eviction has no side effects.
- The budget is fixed during the simulation.

See [caching](../caching.md) for the storage layer and broader context.
