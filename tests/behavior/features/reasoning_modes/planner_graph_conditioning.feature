@behavior @reasoning_modes
Feature: Planner graph conditioning surfaces knowledge graph cues
  Scenario: Planner prompt incorporates contradiction and neighbour metadata
    Given planner graph conditioning is enabled in configuration
    And the knowledge graph metadata includes contradictions and neighbours
    When I execute the planner for query "graph conditioning rehearsal"
    Then the planner prompt should include contradiction and neighbour cues
    And the planner telemetry should record objectives and tasks
