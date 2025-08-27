@behavior @error_recovery
Feature: Circuit breaker recovery
  Scenario: Breaker resets after cooldown and success
    Given a circuit breaker with threshold 3 and cooldown 1
    When three critical failures occur
    And a cooldown period elapses
    And a success is recorded
    Then the breaker state should be "closed"
    And the failure count should be 0
