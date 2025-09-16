# API Authentication Proof

Constant-time comparisons hide timing signals that could reveal secret tokens.
The `secrets.compare_digest` function runs in time dependent only on input
length, preventing attackers from guessing characters by timing responses.

## Role Checks

Authorization verifies that a user's role permits the requested operation. On
each request `AuthMiddleware` reloads configuration, resolves the caller's
role, and stores `role`, `permissions`, and `www_authenticate` on
`request.scope["state"]`. A permissions mapping assigns actions to each role
and fails fast when a role is missing or lacks the required permission.

`enforce_permission` consults that set, returning **401** with the recorded
`WWW-Authenticate` challenge when credentials are missing. It yields **403**
when the role lacks the required action.

Permissions align with the [API spec](../specs/api.md), so query, config,
metrics, docs, health, and capability endpoints stay isolated unless roles
explicitly list the corresponding action.

## Constant-Time Comparison

Traditional equality may exit on the first mismatched character, leaking timing
data. Constant-time comparison evaluates every byte before returning a result,
ensuring uniform execution.

[Python secrets module]:
  https://docs.python.org/3/library/secrets.html#secrets.compare_digest
