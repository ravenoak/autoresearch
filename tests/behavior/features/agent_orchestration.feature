Feature: Agent Orchestration Cycle
  As a user
  I want the orchestrator to rotate agent roles and execute thesis→antithesis→synthesis cycles
  So that each query is processed dialectically with a rotating Primus

  Background:
    Given the agents Synthesizer, Contrarian, and Fact-Checker are enabled
    And loops is set to 2 in configuration

  Scenario: One dialectical cycle
    When I submit a query via CLI `autoresearch search "Test orchestration"`
    Then the system should invoke agents in the order: Synthesizer, Contrarian, Synthesizer
    And each agent turn should be logged with agent name and cycle index

  Scenario: Rotating Primus across loops
    Given loops is set to 3
    When I run two separate queries
    Then the Primus agent should advance by one position between queries
    And the order should reflect the new starting agent each time
