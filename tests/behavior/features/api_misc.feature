Feature: Misc API endpoints
  Background:
    Given the API server is running

  Scenario: Health endpoint returns status
    When I request the health endpoint
    Then the response status should be 200
    And the response body should contain "status" "ok"

  Scenario: Capabilities endpoint lists reasoning modes
    When I request the capabilities endpoint
    Then the response status should be 200
    And the response should include supported reasoning modes
