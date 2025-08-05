Feature: A2A interface
  As a user of the A2A protocol
  I want the interface to handle queries and errors
  So that agents can communicate reliably

  Scenario: Successful query
    When I send a valid A2A query "What is 2+2?"
    Then the response status code should be 200
    And the response should include a JSON message with an answer

  Scenario: Malformed JSON
    When I send malformed JSON to the A2A interface
    Then the response status code should be 400
    And the error message should contain "Invalid JSON"

  Scenario: Server-side error
    When the A2A interface returns a server error
    Then the response status code should be 500
    And the error message should contain "Internal Server Error"
