# Cache Eviction Strategy

Autoresearch caches intermediate results until a memory budget is reached.
This note outlines the policy used to discard entries when space runs low.

## Eviction policy
- Least Recently Used (LRU): the cache tracks access order and removes the
  stalest entry first.

## Metrics
- Each eviction increments an `EVICTION_COUNTER` metric for observability.
- Accesses update a frequency table that hybrid and adaptive policies use.

## Complexity
- Insert and access: O(1) using an ordered dictionary.
- Evict: O(1) per removed entry.

## Correctness
- LRU maintains items in recency order. When usage exceeds the budget \(B\),
  entries are popped from the head until the total is \(\leq B\).
- LRU is a stack algorithm, so a cache of size \(k\) is always a subset of
  a cache of size \(k+1\), minimizing misses among recency policies [1].

## Proof sketch

LRU exhibits the stack property: for cache size :math:`k`, the set of
cached items is contained in the set for size :math:`k+1`. Mattson et al.
proved that any replacement policy with this property incurs the fewest
misses for all request sequences. Therefore LRU is optimal among
recency-based policies.

## Simulation
Running `uv run scripts/simulate_cache_eviction.py --seed 0` shows bounded
memory:

```
step=0 items=1 total=198
...
final memory 1018/1024
```

The invariant `total \leq B` holds at each step, so the cache never
exceeds its budget `B`.

## References
1. R. Arpaci-Dusseau and A. Arpaci-Dusseau. "Operating Systems: Three
   Easy Pieces – Caching: The LRU Policy." https://pages.cs.wisc.edu/~remzi/OSTEP/
2. J. Mattson, R. Gecsei, D. Slutz, and I. Traiger. "Evaluation Techniques
   for Storage Hierarchies." *IBM Systems Journal*, 1970.
   https://doi.org/10.1147/sj.92.0134

## Assumptions
- Each item reports its memory footprint on insertion.
- All entries are independent and eviction has no side effects.
- The budget is fixed during the simulation.

See [caching](../caching.md) for the storage layer and broader context.
