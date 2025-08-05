Feature: SPARQL CLI
  Scenarios for running SPARQL queries from the command line

  Scenario: Execute a SPARQL query with reasoning
    When I run `autoresearch sparql "SELECT ?s WHERE { ?s a <http://example.com/B> }"`
    Then the CLI should exit successfully

  Scenario: Invalid SPARQL query
    When I run `autoresearch sparql "INVALID QUERY"`
    Then the CLI should exit with an error
