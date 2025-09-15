# API Authentication

## Overview

API requests include an API key or bearer token. Credentials map to roles
whose permissions gate access to features. The `AuthMiddleware` dispatch
method validates credentials and populates request state before passing
control downstream.

## Algorithms

- Compare presented credentials with `secrets.compare_digest`.
- Resolve roles and verify required permissions.
- Use `AuthMiddleware.dispatch` to emit `401` responses on missing or invalid
  credentials.

## Invariants

- Credential checks use constant-time comparisons.
- Roles grant access only to permitted actions.

## Proof Sketch

`secrets.compare_digest` returns in constant time, eliminating prefix timing
leaks. Set membership enforces role permissions. The simulation
`scripts/api_auth_sim.py` shows `secure_range` approaching zero while
denied roles such as `reader` lack `write` access.

## Simulation Expectations

Running the simulation yields metrics like:
```
{"naive_range": 0.01, "secure_range": 0.0, "admin_write": true,
 "reader_write": false}
```

## Traceability

- Scripts
  - [scripts/api_auth_sim.py][s1]
- Tests
  - [tests/analysis/test_api_auth_sim.py][t1]

[s1]: ../../scripts/api_auth_sim.py
[t1]: ../../tests/analysis/test_api_auth_sim.py
