# Orchestration Concurrency

The orchestration layer coordinates agents and queries while guarding
against race conditions.

- Each query builds a fresh `QueryState`. The state now uses an
  internal re-entrant lock to serialize updates across threads. Agent
  results, messages and errors are merged within the lock to avoid
  corruption when cycles run concurrently.
- The orchestrator may execute agents in parallel or process multiple
  queries at once. Separate `QueryState` instances ensure one query's
  data cannot leak into another.
- Thread pools and `asyncio` tasks power parallelism. Work units are
  kept small and hold locks briefly, preserving responsiveness.

This strategy provides predictable results even when agent execution or
query submission is highly concurrent.
