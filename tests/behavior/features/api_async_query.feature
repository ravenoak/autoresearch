Feature: Asynchronous query API
  Background:
    Given the API server is running

  Scenario: Submit async query and retrieve result
    When I submit an async query "Explain AI ethics"
    Then the response should include a query ID
    When I request the status for that query ID
    Then the response should contain an answer

  Scenario: Cancel a running async query
    Given an async query has been submitted
    When I cancel the async query
    Then the response should indicate cancellation

  Scenario: Async query timeout triggers retry with backoff
    When a failing async query is submitted that times out
    Then a recovery strategy "retry_with_backoff" should be recorded
    And error category "transient" should be recorded
    And the system state should be restored
    And the logs should include "retry_with_backoff"

  Scenario: Async query agent crash fails gracefully
    When a failing async query is submitted that crashes
    Then a recovery strategy "fail_gracefully" should be recorded
    And error category "critical" should be recorded
    And the system state should be restored
    And the logs should include "fail_gracefully"

  Scenario: Async query uses fallback agent after failure
    When a failing async query is submitted that triggers fallback
    Then a recovery strategy "fallback_agent" should be recorded
    And error category "recoverable" should be recorded
    And the system state should be restored
    And the logs should include "fallback_agent"
