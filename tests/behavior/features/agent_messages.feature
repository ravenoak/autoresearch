Feature: Agent message exchange
  Scenario: Agents share data through the orchestrator
    Given two communicating agents
    When I execute a query
    Then the receiver should process the message
