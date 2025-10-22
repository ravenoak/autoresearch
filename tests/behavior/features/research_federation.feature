Feature: Research federation workspace
  As an analyst coordinating multi-source investigations
  I want to register repositories, define workspaces, and ingest scholarly papers
  So that dialectical agents can compare evidence across namespaces

  Background:
    Given the environment has the "git" and "llm" extras installed
    And a clean storage namespace

  Scenario: Register multiple repositories with provenance tracking
    When I register the following repositories:
      | label       | path                | branch |
      | core-engine | ./repos/core-engine | main   |
      | toolkit     | ./repos/toolkit     | dev    |
    And I run a repository federation search for "graph alignment"
    Then each result includes a repository label
    And the knowledge graph stores nodes scoped by repository namespace

  Scenario: Manage local Git manifests through the search CLI
    Given a temporary manifest-aware configuration
    And the following repositories are available for manifest CLI management:
      | slug  | namespace   |
      | alpha | audit.alpha |
      | beta  | audit.beta  |
      | gamma | audit.gamma |
    When I add the repositories to the manifest via the CLI
    And I update manifest slug "beta" to namespace "audit.beta" via the CLI
    And I remove manifest slug "gamma" via the CLI
    And I list the manifest via the CLI
    Then the manifest CLI output lists:
      | slug  | namespace   |
      | alpha | audit.alpha |
      | beta  | audit.beta  |
    And a manifest-backed search for "shared-term" returns provenance from:
      | slug  | namespace   |
      | alpha | audit.alpha |
      | beta  | audit.beta  |

  Scenario: Cross-examination workspace debates curated resources
    Given I create a workspace named "alignment-audit" with:
      | type   | reference                     |
      | repo   | core-engine@HEAD              |
      | repo   | toolkit@latest                |
      | file   | ./notes/graph_hypotheses.md   |
      | paper  | arxiv:2401.01234              |
    When I launch a dialectical debate for prompt "audit conflicting claims"
    Then each claim cites at least one workspace resource
    And counterclaims reference a different resource than the challenged claim
    And the debate transcript stores the workspace version identifier

  @pending
  Scenario: Contrarian and fact-checker cite each workspace resource
    Given the workspace "alignment-audit" exists
    When I inspect the latest workspace debate
    Then the contrarian response cites each workspace resource
    And the fact-checker response cites each workspace resource

  Scenario: Cached scholarly papers support offline follow-up questions
    Given I fetch the paper "Self-Query Retrieval" from Hugging Face Papers
    And the fetch is cached locally with checksum metadata
    When I disconnect from the network
    And I ask "summarize cached findings" within the same workspace
    Then the agent cites the cached paper content with preserved provenance
    And the cache metadata reports the last sync timestamp
