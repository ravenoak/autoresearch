Feature: Agent Orchestration Cycle
  As a user
  I want the orchestrator to rotate agent roles and execute thesis→antithesis→synthesis cycles
  So that each query is processed dialectically with a rotating Primus

  Background:
    Given the agents Synthesizer, Contrarian, and Fact-Checker are enabled
    And loops is set to 2 in configuration

  # Spec: docs/specs/orchestration.md#key-behaviors - Rotate agents through thesis→antithesis→synthesis cycles and track the Primus agent
  Scenario: One dialectical cycle
    When I submit a query via CLI `autoresearch search "Test orchestration"`
    Then the system should invoke agents in the order: Synthesizer, Contrarian, Synthesizer
    And each agent turn should be logged with agent name and cycle index

  # Spec: docs/specs/orchestration.md#key-behaviors - Rotate agents through thesis→antithesis→synthesis cycles and track the Primus agent
  Scenario: Rotating Primus across loops
    Given loops is set to 3
    When I run two separate queries
    Then the Primus agent should advance by one position between queries
    And the order should reflect the new starting agent each time

  # Spec: docs/specs/orchestration.md#key-behaviors - Integrate multiple agents, propagating state and capturing errors
  Scenario: CLI orchestrator error
    Given the orchestrator is configured to raise an error
    When I submit a query via CLI `autoresearch search "Failing orchestration"`
    Then the CLI should report an orchestration error
