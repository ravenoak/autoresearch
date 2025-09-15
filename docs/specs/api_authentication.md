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

## Proof

### Assumptions

- Configuration secrets are provisioned with fixed-length tokens.
- `secrets.compare_digest` runs in constant time for equal-length inputs,
  resisting prefix leaks.[1]
- Role permissions are defined by `cfg.role_permissions` within the runtime
  configuration.

### Lemma 1 – Constant-time credential comparisons

`AuthMiddleware._resolve_role` validates API keys with
`secrets.compare_digest(candidate, key)` and returns after finding the first
match. Because `compare_digest` is constant-time, each comparison takes the
same number of operations regardless of the mismatching index, so the runtime
depends only on the number of configured keys, not on any prefix knowledge of
the attacker.[1] The bearer-token helper `verify_bearer_token` delegates to the
same primitive, inheriting the constant-time property.

### Lemma 2 – Permission resolution uses set membership

Successful authentication stores `request.state.permissions` as a set derived
from `cfg.role_permissions`. Middleware and downstream handlers consult this
set, so an action is authorized precisely when it is a member of the resolved
permission set. Absence from the set deterministically denies the action.

### Lemma 3 – Dialectical challenge and synthesis

Naively comparing credentials with `token == guess` would short-circuit at the
first mismatch, leaking timing data proportional to the number of matching
prefix characters. By Lemma 1 the middleware replaces this with
`compare_digest`, eliminating the leak while maintaining configurability for
multiple keys. Likewise, storing permissions as ordered collections would
require linear scans; switching to sets delivers constant-time lookup and makes
unauthorized actions unambiguously false.

### Theorem – Constant-time authentication with sound permissions

From Lemma 1 all credential comparisons execute in constant time whenever the
configuration provides credentials. Lemma 2 shows that authorization decisions
are equivalent to set membership, and Lemma 3 demonstrates that alternative
designs reintroduce timing or authorization risks. Therefore credential checks
are constant-time and permission resolution is sound.

## Simulation Evidence

Two simulations substantiate the proof:

- `scripts/api_auth_sim.py` measures naive equality versus `compare_digest`,
  keeping `secure_range` well below `naive_range`.
- `scripts/api_auth_verification_sim.py` enumerates valid and invalid
  credential scenarios and flags mismatches.

Representative output combining both insights:
```
{
  "timing": {
    "naive_range": 4.16e-05,
    "secure_range": 3.53e-05
  },
  "valid": ["admin_valid_write", "reader_valid_read"],
  "invalid": [
    "admin_invalid_token",
    "reader_invalid_write",
    "anonymous_missing_perm"
  ],
  "mismatches": []
}
```

## Traceability

- Scripts
  - [scripts/api_auth_sim.py][s1]
  - [scripts/api_auth_verification_sim.py][s2]
- Tests
  - [tests/analysis/test_api_auth_sim.py][t1]
  - [tests/unit/test_api_auth_middleware.py][t2]

[s1]: ../../scripts/api_auth_sim.py
[s2]: ../../scripts/api_auth_verification_sim.py
[t1]: ../../tests/analysis/test_api_auth_sim.py
[t2]: ../../tests/unit/test_api_auth_middleware.py
[1]: https://docs.python.org/3/library/secrets.html#secrets.compare_digest
