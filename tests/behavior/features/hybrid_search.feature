Feature: Hybrid Search
  Scenario: Combine keyword and vector results
    Given a directory with text files
    And I have persisted claims with embeddings
    When I perform a hybrid search for "hello"
    Then I should get results from the text files
    And the search results should include vector results
