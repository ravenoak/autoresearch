Feature: Vector Search Performance
  @requires_vss
  # Spec: docs/specs/search.md#key-behaviors - Maintain responsive vector search performance
  Scenario: Vector search executes quickly
    Given I have persisted claims with embeddings
    When I measure vector search time
    Then the duration should be less than one second
