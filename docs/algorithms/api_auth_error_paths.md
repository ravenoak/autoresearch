# API Auth Error Paths

Enumerates failure responses for API credential verification.

## Missing Credential

- Request without `X-API-Key` or `Authorization` header returns **400 Bad
  Request**.

## Invalid Credential

- Credentials that do not match stored secrets return **401 Unauthorized** and
  log the failure.

## Rate Limit Exceeded

- Excess requests trigger a **429 Too Many Requests** response via rate limiting
  middleware.

## Probabilistic Modeling

Credential checks can be described by probabilities for missing, invalid, and
rate limited requests. Let `p_m`, `p_i`, and `p_r` denote those values.

- **400 Bad Request:** `p_m`
- **401 Unauthorized:** `p_i`
- **429 Too Many Requests:** `p_r`

Expected response rates follow from the chosen distribution. The simulation
script illustrates outcome frequencies:

```
uv run scripts/simulate_api_auth_errors.py --requests 1000 \
    --missing 0.2 --invalid 0.3 --rate-limit 0.1 --seed 0
```

## References

- [src/autoresearch/api/](../../src/autoresearch/api/)
- [tests/unit/test_api_error_handling.py][test-auth]
- [scripts/simulate_api_auth_errors.py][sim-script]

[test-auth]: ../../tests/unit/test_api_error_handling.py
[sim-script]: ../../scripts/simulate_api_auth_errors.py
