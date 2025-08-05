Feature: Asynchronous query API
  Background:
    Given the API server is running

  Scenario: Submit async query and retrieve result
    When I submit an async query "Explain AI ethics"
    Then the response should include a query ID
    When I request the status for that query ID
    Then the response should contain an answer

  Scenario: Cancel a running async query
    Given an async query has been submitted
    When I cancel the async query
    Then the response should indicate cancellation
