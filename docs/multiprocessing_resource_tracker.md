# Multiprocessing Resource Tracker

The Python multiprocessing module tracks shared resources such as
semaphores. When processes or queues are not closed, the resource tracker
may try to clean up a missing semaphore and emit `KeyError` messages like
`KeyError: '/mp-####'` during test teardown.

## Root cause

Previous test runs left semaphores registered after queues were closed.
The resource tracker attempted to unlink them a second time after unit
tests completed, leading to `KeyError` and halting coverage and
integration tests.

## Mitigation

- Ensure every `multiprocessing.Queue` is closed and `join_thread` is
  called in a `finally` block.
- An autouse fixture now drains the resource tracker cache after each
  test to unregister any leaked semaphores.

These steps prevent stray resources from triggering `KeyError` and allow
coverage and integration tests to run to completion.
