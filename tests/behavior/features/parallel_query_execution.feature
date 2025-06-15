Feature: Parallel Query Execution
  As a user
  I want to run queries with multiple agent groups in parallel
  So that I can get faster results and compare different agent combinations

  Background:
    Given the system is configured with multiple agent groups
    And the system is using a dummy LLM adapter for testing

  Scenario: Running multiple agent groups in parallel
    When I run a parallel query with multiple agent groups
    Then each agent group should be executed
    And the final result should include contributions from all agent groups
    And the execution should be faster than running the groups sequentially

  Scenario: Handling errors in parallel execution
    Given an agent group that will raise an error
    When I run a parallel query with that agent group
    Then the orchestrator should catch and log the error
    And the orchestrator should continue with other agent groups
    And the final result should include information about the error

  Scenario: Synthesizing results from multiple agent groups
    When I run a parallel query with multiple agent groups
    Then the orchestrator should synthesize the results from all agent groups
    And the final result should be a coherent answer that combines insights from all groups