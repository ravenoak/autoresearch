Feature: Batch query API
  Background:
    Given the API server is running

  Scenario: Successful batch submission returning aggregated results
    When I submit a batch query with mixed reasoning modes
    Then I receive aggregated results for each subquery
    And the results maintain submission order
    And each subquery's response records its reasoning mode

  Scenario: Pagination and partial failures
    When I submit a paginated batch query where one subquery fails
    Then I receive the requested page with results and errors preserved
    And failed subqueries include error details

  Scenario: Error recovery when a subquery fails
    When I submit a batch query with a failing subquery followed by a valid one
    Then processing continues and results include error for the failing subquery
