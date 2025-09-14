# API

## Overview
The API package exposes HTTP endpoints for orchestrator actions.

## Algorithm
Endpoints validate requests, delegate to orchestrator services, and stream
responses to clients.

## Proof sketch
Validation ensures well-formed data; the orchestrator confirms task
completion, so each request yields a finite response.

## Simulation
`tests/unit/test_api.py` simulates calls to key routes and checks status
codes.

## References
- [code](../../src/autoresearch/api/)
- [spec](../specs/api.md)
- [tests](../../tests/unit/test_api.py)

## Related Issues
- [Fix API authentication and metrics tests][issue]

[issue]: ../../issues/fix-api-authentication-and-metrics-tests.md
