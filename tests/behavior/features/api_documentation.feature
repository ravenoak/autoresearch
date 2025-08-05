Feature: API documentation endpoints
  Background:
    Given the API server is running

  Scenario: Access Swagger UI
    When I request the docs endpoint
    Then the response status should be 200
    And the response body should contain "Swagger UI"

  Scenario: Retrieve OpenAPI schema
    When I request the openapi endpoint
    Then the response status should be 200
    And the response body should contain "openapi"
