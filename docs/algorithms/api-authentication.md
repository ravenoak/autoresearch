# API Authentication Proof

Constant-time comparisons hide timing signals that could reveal secret tokens.
The `secrets.compare_digest` function runs in time dependent only on input
length, preventing attackers from guessing characters by timing responses.

## Role Checks

Authorization verifies that a user's role permits the requested operation. A
permissions mapping assigns actions to each role and fails fast when a role is
missing or lacks the required permission.

## Constant-Time Comparison

Traditional equality may exit on the first mismatched character, leaking timing
data. Constant-time comparison evaluates every byte before returning a result,
ensuring uniform execution.

[Python secrets module]:
  https://docs.python.org/3/library/secrets.html#secrets.compare_digest
