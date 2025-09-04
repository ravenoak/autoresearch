# Llm

## Overview

Language Model (LLM) integration module for Autoresearch. See [adapter selection
and token accounting][a1] for switching heuristics and fallback formulas.

## Algorithms

- Implement core behaviors described above.

## Invariants

- Preserve documented state across operations.

## Proof Sketch

Core routines enforce invariants by validating inputs and state.

## Simulation Expectations

Unit tests cover nominal and edge cases for these routines.

## Traceability


- Modules
  - [src/autoresearch/llm/][m1]
- Tests
  - [tests/unit/test_agents_llm.py][t1]
  - [tests/unit/test_llm_adapter.py][t2]
  - [tests/unit/test_llm_capabilities.py][t3]

[a1]: ../algorithms/llm_adapter.md
[m1]: ../../src/autoresearch/llm/
[t1]: ../../tests/unit/test_agents_llm.py
[t2]: ../../tests/unit/test_llm_adapter.py
[t3]: ../../tests/unit/test_llm_capabilities.py
