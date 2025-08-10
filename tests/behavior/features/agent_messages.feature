Feature: Agent message exchange
  Scenario: Agents share data through the orchestrator
    Given two communicating agents
    When I execute a query
    Then the receiver should process the message

  Scenario: Coalition broadcast communication
    Given a coalition with a sender and two receivers
    When the sender broadcasts to the coalition
    Then both receivers should process the broadcast

  Scenario: Messaging disabled prevents communication
    Given two communicating agents without messaging
    When I execute a query
    Then the receiver should have no messages
