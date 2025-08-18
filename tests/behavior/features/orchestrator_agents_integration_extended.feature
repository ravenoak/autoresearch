Feature: Extended orchestrator and agents integration
  As a developer
  I want to ensure that the orchestrator and agents work together correctly
  So that the system can produce high-quality research results

  Background:
    Given the system is configured with multiple agents
    And the system is using a dummy LLM adapter for testing

  # Spec: docs/specs/orchestration.md#key-behaviors - Support multiple reasoning loops and modes while preserving agent state
  Scenario: Orchestrator executes multiple loops correctly
    Given the system is configured to run multiple reasoning loops
    When I run a query with multiple loops
    Then each loop should execute the agents in the correct sequence
    And the state should be preserved between loops
    And the final result should include contributions from all loops

  # Spec: docs/specs/orchestration.md#key-behaviors - Support multiple reasoning loops and modes while preserving agent state
  Scenario: Orchestrator supports different reasoning modes
    Given the system is configured with the "direct" reasoning mode
    When I run a query with the direct reasoning mode
    Then only the primary agent should be executed
    And the final result should include only the primary agent's contribution

  # Spec: docs/specs/orchestration.md#key-behaviors - Support multiple reasoning loops and modes while preserving agent state
  Scenario: Orchestrator preserves agent state between loops
    Given the system is configured to run multiple reasoning loops
    And an agent that modifies the state in a specific way
    When I run a query with multiple loops
    Then the state modifications should be preserved between loops
    And the final result should reflect the cumulative state changes