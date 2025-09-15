# API Auth Error Paths

Enumerates failure responses for API credential verification.

## Missing Credential

- When authentication is configured but no usable credentials are supplied,
  the middleware returns **401 Unauthorized** and sets `WWW-Authenticate` to the
  required scheme (`API-Key` or `Bearer`).

## Invalid Credential

- API keys and bearer tokens that fail constant-time comparison return
  **401 Unauthorized** with a message such as `Invalid API key` or
  `Invalid token`.

## Insufficient Permissions

- Authenticated clients lacking a required permission trigger
  `enforce_permission`, which raises **403 Forbidden** with
  `detail="Insufficient permissions"`. Examples include roles that can run
  queries but lack the `docs` permission for `/docs` or the `metrics`
  permission for `/metrics`.

## Rate Limit Exceeded

- Excess requests trigger a **429 Too Many Requests** response via rate limiting
  middleware.

## Probabilistic Modeling

Credential checks can be described by probabilities for missing, invalid,
forbidden, and rate-limited requests. Let `p_m`, `p_i`, `p_f`, and `p_r` denote
those values.

- **401 Unauthorized (missing)**: `p_m`
- **401 Unauthorized (invalid)**: `p_i`
- **403 Forbidden:** `p_f`
- **429 Too Many Requests:** `p_r`

Expected response rates follow from the chosen distribution. The simulation
script illustrates outcome frequencies:

```
uv run scripts/simulate_api_auth_errors.py --requests 1000 \
    --missing 0.2 --invalid 0.3 --forbidden 0.1 --rate-limit 0.1 --seed 0
```

## References

- [src/autoresearch/api/](../../src/autoresearch/api/)
- [tests/unit/test_api_error_handling.py][test-auth]
- [scripts/simulate_api_auth_errors.py][sim-script]

[test-auth]: ../../tests/unit/test_api_error_handling.py
[sim-script]: ../../scripts/simulate_api_auth_errors.py
