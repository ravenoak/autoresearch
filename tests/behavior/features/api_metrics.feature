Feature: Metrics API
  Background:
    Given the API server is running

  Scenario: Retrieve Prometheus metrics
    When I request the metrics endpoint with authorization
    Then the response status should be 200
    And the response body should contain "process_cpu_seconds_total"

  Scenario: Metrics endpoint without permission
    When I request the metrics endpoint
    Then the response status should be 403
