Feature: Ontology reasoning via orchestrator
  As a developer
  I want to infer relations through the orchestrator
  So that ontology queries return inferred triples

  Scenario: Infer subclass relations through orchestrator
    Given the storage system is configured for in-memory RDF
    And I have loaded an ontology defining subclasses
    And I have an instance of the subclass
    When I infer relations via the orchestrator
    Then querying the ontology for the superclass via the orchestrator should include the instance
