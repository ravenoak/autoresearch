Feature: API and Orchestrator Integration
  As a user of the Autoresearch system
  I want the API to properly interact with the orchestrator
  So that I can get research results through the HTTP interface

  Background:
    Given the API server is running
    And the orchestrator is configured with test agents

  Scenario: API forwards queries to the orchestrator
    When I send a query "What is artificial intelligence?" to the API
    Then the orchestrator should receive the query
    And the API should return the orchestrator's response
    And the response should include an answer
    And the response should include citations
    And the response should include reasoning

  Scenario: API handles orchestrator errors gracefully
    Given the orchestrator is configured to raise an error
    When I send a query "Test query" to the API
    Then the API should return an error response
    And the error response should include a helpful message
    And the error should be logged

  Scenario: API respects query parameters
    When I send a query with custom parameters to the API
    Then the orchestrator should receive the query with those parameters
    And the API should return a response that reflects the custom parameters

  Scenario: API handles concurrent requests
    When I send multiple concurrent queries to the API
    Then all queries should be processed
    And each response should be correct for its query

  Scenario: API paginates batch queries
    When I send a batch query with page 2 and page size 2 to the API
    Then the API should return the second page of results

  Scenario: API returns 404 for unknown async query ID
    When I request the status of an unknown async query
    Then the API should respond with status 404

  Scenario: API configuration CRUD
    When I replace the configuration via the API
    Then the API should report the updated value
    When I reset the configuration via the API
    Then the API should return the default configuration
