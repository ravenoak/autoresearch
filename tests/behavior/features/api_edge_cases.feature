Feature: API Edge Cases
  As a developer
  I want the API to handle invalid input and permission errors
  So that clients receive proper error responses

  Background:
    Given the API server is running

  Scenario: Invalid JSON returns 422
    When I send invalid JSON to the API
    Then the response status should be 422

  Scenario: Permission denied for metrics endpoint
    When I request the metrics endpoint
    Then the response status should be 403
