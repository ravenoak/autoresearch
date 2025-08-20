Feature: Query Interface
  As a user of Autoresearch,
  I want to submit natural-language queries via different interfaces,
  so that I can receive evidence-driven answers.

  Background:
    Given the Autoresearch application is running

  Scenario: Submit query via CLI
    When I run `autoresearch search "What is Promise Theory?"` in a terminal
    Then I should receive a readable Markdown answer with `answer`, `citations`, `reasoning`, and `metrics` sections

  Scenario: Submit query via HTTP API
    When I send a POST request to `/query` with JSON `{ "query": "What is Promise Theory?" }`
    Then the response should be a valid JSON document with keys `answer`, `citations`, `reasoning`, and `metrics`

  Scenario: Submit query via MCP tool
    When I run `autoresearch.search("What is Promise Theory?")` via the MCP CLI
    Then I should receive a JSON output matching the defined schema for `answer`, `citations`, `reasoning`, and `metrics`

  Scenario: Refine query interactively via CLI
    When I run `autoresearch search "What is Promise Theory?" -i` and refine to "Define Promise Theory" then exit
    Then I should receive a readable Markdown answer with `answer`, `citations`, `reasoning`, and `metrics` sections

  Scenario: Visualize query results via CLI
    When I run `autoresearch visualize "What is Promise Theory?" graph.png`
    Then the visualization file "graph.png" should exist

  Scenario: Visualize RDF graph via CLI
    When I run `autoresearch visualize-rdf rdf_graph.png`
    Then the visualization file "rdf_graph.png" should exist

  Scenario: Submit query via CLI with reasoning mode
    When I run `autoresearch search "What is Promise Theory?" --reasoning-mode direct` in a terminal
    Then I should receive a readable Markdown answer with `answer`, `citations`, `reasoning`, and `metrics` sections
