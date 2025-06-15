Feature: Storage and Search Integration
  As a user of the Autoresearch system
  I want the storage and search systems to work together seamlessly
  So that I can efficiently retrieve relevant information

  Background:
    Given the storage system is initialized
    And the search system is configured

  Scenario: Store and retrieve claims using vector search
    When I store a claim with text "Artificial intelligence has made significant progress in recent years"
    And I store a claim with text "Machine learning is a subset of artificial intelligence"
    And I store a claim with text "Climate change is a global challenge requiring immediate action"
    And I perform a vector search for "AI advancements"
    Then the search results should include claims about artificial intelligence
    And the search results should be ordered by relevance
    And the search results should not include claims about climate change

  Scenario: Search results respect LRU eviction policy
    Given the storage system has a maximum capacity of 2 claims
    And the storage system uses "lru" eviction policy
    When I store a claim with text "First claim for testing"
    And I store a claim with text "Second claim for testing"
    And I store a claim with text "Third claim for testing"
    And I perform a vector search for "testing"
    Then the search results should include "Second claim for testing"
    And the search results should include "Third claim for testing"
    And the search results should not include "First claim for testing"

  Scenario: Search results respect score-based eviction policy
    Given the storage system has a maximum capacity of 2 claims
    And the storage system uses "score" eviction policy
    When I store a claim with text "Low relevance claim" with relevance score 0.2
    And I store a claim with text "Medium relevance claim" with relevance score 0.5
    And I store a claim with text "High relevance claim" with relevance score 0.9
    And I perform a vector search for "relevance"
    Then the search results should include "Medium relevance claim"
    And the search results should include "High relevance claim"
    And the search results should not include "Low relevance claim"

  Scenario: LRU eviction policy respects claim access patterns
    Given the storage system has a maximum capacity of 2 claims
    And the storage system uses "lru" eviction policy
    When I store a claim with text "First claim for testing"
    And I store a claim with text "Second claim for testing"
    And I access the claim "First claim for testing"
    And I store a claim with text "Third claim for testing"
    And I perform a vector search for "testing"
    Then the search results should include "First claim for testing"
    And the search results should include "Third claim for testing"
    And the search results should not include "Second claim for testing"

  Scenario: Search handles storage errors gracefully
    Given the storage system will raise an error on vector search
    When I perform a vector search for "test query"
    Then the search should return an empty result
    And the error should be logged

  Scenario: Update existing claims and search for updated content
    When I store a claim with text "Original claim about biology"
    And I perform a vector search for "biology"
    Then the search results should include "Original claim about biology"
    When I update the claim "Original claim about biology" with new text "Updated claim about genetics"
    And I perform a vector search for "biology"
    Then the search results should not include "Original claim about biology"
    When I perform a vector search for "genetics"
    Then the search results should include "Updated claim about genetics"
