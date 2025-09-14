# Agents

## Overview
Agents encapsulate specialized behaviours and coordinate via the orchestrator.

## Algorithm
Each agent implements a `step` loop processing tasks from a queue and
reporting results back to the orchestrator.

## Proof sketch
The agent's loop terminates because each step consumes one task and tasks
are finite.

## Simulation
`tests/unit/test_advanced_agents.py` exercises agent registration and task
handling.

## References
- [code](../../src/autoresearch/agents/)
- [spec](../specs/agents.md)
- [tests](../../tests/unit/test_advanced_agents.py)

## Related Issues
- [Test orchestrator with all agent combinations][issue]

[issue]: ../../issues/archive/test-orchestrator-with-all-agent-combinations.md
