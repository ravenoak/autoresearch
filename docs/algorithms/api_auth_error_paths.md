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

## References

- [src/autoresearch/api/](../../src/autoresearch/api/)
- [tests/unit/test_api_error_handling.py](../../tests/unit/test_api_error_handling.py)
