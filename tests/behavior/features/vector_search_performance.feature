Feature: Vector Search Performance
  @requires_vss
  Scenario: Vector search executes quickly
    Given I have persisted claims with embeddings
    When I measure vector search time
    Then the duration should be less than one second
