@behavior @error_recovery @slow
# Feature covers reasoning modes: direct, chain-of-thought, dialectical, unsupported
# Recovery paths: retry_with_backoff, fail_gracefully, fallback_agent
Feature: Error Recovery
  As a user
  I want the system to apply recovery strategies
  So transient errors do not halt execution

  Scenario: Error recovery in dialectical reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Flaky"
    And the agents executed should be "Flaky"
    And a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"

  Scenario: Error recovery in direct reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "direct"
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "direct"
    And the loops used should be 1
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"
    And a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"

  Scenario: Error recovery in chain-of-thought reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "chain-of-thought"
    And the loops used should be 1
    And the agent groups should be "Flaky"
    And the agents executed should be "Flaky"
    And a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"

  Scenario: Recovery after storage failure
    Given a storage layer that raises a StorageError
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "StoreFail"
    And the agents executed should be "StoreFail"
    And a recovery strategy "fail_gracefully" should be recorded
    And error category "critical" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list an error of type "StorageError"

  Scenario: Recovery after persistent network outage
    Given an agent facing a persistent network outage
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Offline"
    And the agents executed should be "Offline"
    And a recovery strategy "fallback_agent" should be recorded
    And error category "recoverable" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list an error of type "AgentError"

  Scenario: Recovery after agent timeout
    Given an agent that times out during execution
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Slowpoke"
    And the agents executed should be "Slowpoke"
    And a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list a timeout error

  Scenario: Recovery after critical agent failure
    Given an agent that fails during execution
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Faulty"
    And the agents executed should be "Faulty"
    And a recovery strategy "fail_gracefully" should be recorded
    And error category "critical" should be recorded
    And recovery should be applied
    And the logs should include "recovery"
    And the response should list an agent execution error

  Scenario: Recovery after agent failure with fallback
    Given an agent that fails triggering fallback
    When I run the orchestrator on query "recover test"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Faulty"
    And the agents executed should be "Faulty"
    And a recovery strategy "fallback_agent" should be recorded
    And error category "recoverable" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list an agent execution error

  Scenario: Error recovery with a realistic query
    Given an agent that raises a transient error
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "What is the capital of France?"
    Then the reasoning mode selected should be "dialectical"
    And a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
    And the system state should be restored

  Scenario: Unsupported reasoning mode during recovery fails gracefully
    Given an agent that raises a transient error
    When I run the orchestrator on query "recover test" with unsupported reasoning mode "quantum"
    Then a reasoning mode error should be raised
    And no agents should execute
    And the system state should be restored
    And the logs should include "unsupported reasoning mode"

  Scenario: Successful run does not trigger recovery
    Given a reliable agent
    When I run the orchestrator on query "recover test"
    Then no recovery should be recorded
