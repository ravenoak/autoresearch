@behavior
Feature: Extended Error Recovery
  As a user
  I want the system to recover from timeouts and agent failures
  So queries can continue even when components misbehave

  Scenario: Recovery after agent timeout
    Given an agent that times out during execution
    When I run the orchestrator on query "Explain the theory of relativity"
    Then the response should list a timeout error

  Scenario: Recovery after agent failure
    Given an agent that fails during execution
    When I run the orchestrator on query "Describe the process of photosynthesis"
    Then the response should list an agent execution error
