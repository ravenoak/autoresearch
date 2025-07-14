Feature: Agent messaging
  As a developer
  I want agents to exchange data via orchestrator
  So that they can collaborate during a cycle

  Scenario: Messages are delivered between agents
    Given agent messaging is enabled
    When the orchestrator runs a messaging query
    Then the receiver agent should process the message
