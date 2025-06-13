Feature: Hybrid Dynamic Knowledge Graph (DKG) Persistence
  As a system
  I want to persist new claims into in-memory and on-disk stores
  So that evidence can be stored reliably and retrieved efficiently

  Background:
    Given I have a valid claim with source metadata

  Scenario: Persist claim in RAM
    When an agent asserts a new claim
    Then the claim node should be added to the NetworkX graph in RAM

  Scenario: Persist claim in DuckDB
    When an agent commits a new claim
    Then a row should be inserted into the `nodes` table
    And the corresponding `edges` table should reflect relationships
    And the embedding should be stored in the `embeddings` vector column

  Scenario: Persist claim in RDF quad-store
    When the system writes provenance data
    Then a new quad should appear in the RDFlib store
    And queries should return the quad via SPARQL

  Scenario: Clear DKG removes persisted data
    When an agent commits a new claim
    And I clear the knowledge graph
    Then the NetworkX graph should be empty
    And the DuckDB tables should be empty
