# Repair API authentication endpoints

## Context
Multiple API integration tests (`test_api_auth*`, `test_api_docs`,
`test_api_additional`, `test_api_streaming`) returned HTTP status codes that
did not match expectations, showing authentication and authorization logic
needs review.

## Acceptance Criteria
- Ensure endpoints require valid API keys or tokens.
- Return correct HTTP status codes for auth success and failure.
- Update tests to cover expected auth flows.
- Document auth configuration in project docs.

## Status
Archived

