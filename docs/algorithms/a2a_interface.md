# A2A Interface

The A2A interface connects the orchestrator to the Autonomous Agent (A2A)
network. It accepts JSON messages from the SDK and forwards queries to the
orchestrator.

## Protocol flow

- Client sends a message with `query` or `command` fields to the server.
- The interface validates the payload and dispatches it to orchestration.
- The server returns an `answer`, citations, and related metadata.

## Security assumptions

- Only trusted clients can reach the interface port.
- The SDK enforces message schemas and sanitizes untrusted input.
- Error traces are filtered so no secrets are leaked.

## Concurrency model

Dispatch uses a single `Lock` to serialize updates to the shared state. The
proof sketch in [../specs/a2a-interface.md](../specs/a2a-interface.md) shows
why the invariants hold. The
[a2a_concurrency_sim.py](../../scripts/a2a_concurrency_sim.py) simulation
exercises this model with threads and reports consistent counts.

## References

- [`a2a_interface.py`](../../src/autoresearch/a2a_interface.py)
- [`a2a_concurrency_sim.py`](../../scripts/a2a_concurrency_sim.py)
- [`test_a2a_mcp_handshake.py`](../../tests/unit/test_a2a_mcp_handshake.py)

## Simulation

Automated tests confirm A2A interface behavior.

- [Spec](../specs/a2a-interface.md)
- [Tests](../../tests/integration/test_a2a_interface.py)
