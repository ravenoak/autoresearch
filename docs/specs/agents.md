# Agents

## Overview

Dialectical agent infrastructure. See the
[domain model](../domain_model.md) for agent relationships.

## Algorithms

- Implement core behaviors described above.

## Invariants

1. Tasks dequeue in the order they were enqueued.
2. Queue length never exceeds the configured capacity.
3. When capacity is surpassed the oldest tasks are dropped.

## Edge Cases

- Capacity of one forces immediate processing.
- Zero or negative capacity rejects all tasks.

## Complexity

Processing ``n`` tasks uses ``O(n)`` time and ``O(min(n, c))`` space where
``c`` is the capacity.

## Proof Sketch

Simulation [agents_sim.py][s1] enqueues tasks under varying capacities. Metrics
confirm FIFO ordering and bounded growth, validating the invariants and edge
cases above.

## Simulation Expectations

Running ``agents_sim.py`` with ten tasks and capacity five yields
``{"max_queue": 5, "ordered": true}``.

## Traceability


- Modules
  - [src/autoresearch/agents/][m1]
- Scripts
  - [scripts/agents_sim.py][s1]
- Tests
  - [tests/unit/test_advanced_agents.py][t1]
  - [tests/unit/test_agents_llm.py][t2]
  - [tests/unit/test_specialized_agents.py][t3]
  - [tests/analysis/test_agents_sim.py][t4]

[m1]: ../../src/autoresearch/agents/
[t1]: ../../tests/unit/test_advanced_agents.py
[t2]: ../../tests/unit/test_agents_llm.py
[t3]: ../../tests/unit/test_specialized_agents.py
[s1]: ../../scripts/agents_sim.py
[t4]: ../../tests/analysis/test_agents_sim.py
