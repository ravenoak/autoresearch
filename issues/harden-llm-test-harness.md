# Harden LLM test harness

## Context
The LLM adapter test suite contained flakey behaviours from real time delays and noisy
debug prints that masked structured assertions. Strengthening the tests ensures retry
logic remains covered while running quickly in isolation.

## Dependencies
None.

## Acceptance Criteria
- Diagnostic prints are removed from the dialectical agent resilience tests in
  `tests/unit/agents/test_llm_error_resilience.py`.
- Tests interacting with the OpenRouter adapter avoid `time.sleep` in favour of
  deterministic time control, and their environment variables are isolated.
- Retry handling for OpenRouter rate limits is verified via session-level mocks without
  network calls.

## Status
Open
