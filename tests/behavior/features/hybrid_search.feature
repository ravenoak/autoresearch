Feature: Hybrid Search
  # Spec: docs/specs/search.md#key-behaviors - Combine keyword and vector retrieval for hybrid search results
  Scenario: Combine keyword and vector results
    Given a directory with text files
    And I have persisted claims with embeddings
    When I perform a hybrid search for "hello"
    Then I should get results from the text files
    And the search results should include vector results

  Scenario: Semantic and hybrid rankings align
    Given a directory with text files
    And I have persisted claims with embeddings
    When I perform a hybrid search for "hello"
    Then the first result should match the semantic search ordering
    And the relevance scores should be normalized
