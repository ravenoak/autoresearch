@behavior
# Feature covers reasoning modes: chain-of-thought, dialectical, direct, unsupported
# Recovery paths: retry_with_backoff, fail_gracefully
Feature: Extended Error Recovery
  As a user
  I want the system to recover from timeouts and agent failures
  So queries can continue even when components misbehave

  Scenario: Recovery after agent timeout
    Given an agent that times out during execution
    And reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "Explain the theory of relativity"
    Then the reasoning mode selected should be "chain-of-thought"
    And the loops used should be 1
    And the agent groups should be "Slowpoke"
    And the agents executed should be "Slowpoke"
    And a recovery strategy "retry_with_backoff" should be recorded
    And error category "transient" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list a timeout error

  Scenario: Recovery after agent failure
    Given an agent that fails during execution
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "Describe the process of photosynthesis"
    Then the reasoning mode selected should be "dialectical"
    And the loops used should be 1
    And the agent groups should be "Faulty"
    And the agents executed should be "Faulty"
    And a recovery strategy "fail_gracefully" should be recorded
    And error category "critical" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list an agent execution error

  Scenario: Recovery after agent timeout in direct mode
    Given an agent that times out during execution
    And reasoning mode is "direct"
    When I run the orchestrator on query "Explain the theory of relativity"
    Then the reasoning mode selected should be "direct"
    And the loops used should be 1
    And the agent groups should be "Slowpoke"
    And the agents executed should be "Slowpoke"
    And a recovery strategy "retry_with_backoff" should be recorded
    And error category "transient" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list a timeout error

  Scenario: Recovery after network outage with fallback agent
    Given an agent facing a persistent network outage
    And reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "Explain the theory of relativity"
    Then the reasoning mode selected should be "chain-of-thought"
    And the loops used should be 1
    And the agent groups should be "Offline"
    And the agents executed should be "Offline"
    And a recovery strategy "fallback_agent" should be recorded
    And error category "recoverable" should be recorded
    And recovery should be applied
    And the system state should be restored
    And the logs should include "recovery"
    And the response should list an error of type "AgentError"

  Scenario: Unsupported reasoning mode during extended recovery fails gracefully
    Given an agent that times out during execution
    When I run the orchestrator on query "Explain the theory of relativity" with unsupported reasoning mode "quantum"
    Then a reasoning mode error should be raised
    And no agents should execute
    And the system state should be restored
    And the logs should include "unsupported reasoning mode"
