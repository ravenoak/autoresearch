Feature: Visualization CLI
  Scenarios for graph visualization commands

  Scenario: Generate a query graph PNG
    When I run `autoresearch visualize "What is quantum computing?" graph.png`
    Then the CLI should exit successfully
    And the file "graph.png" should be created

  Scenario: Render RDF graph to PNG
    When I run `autoresearch visualize-rdf rdf_graph.png`
    Then the CLI should exit successfully

  Scenario: Missing output file for visualization
    When I run `autoresearch visualize "What is quantum computing?"`
    Then the CLI should exit with an error
