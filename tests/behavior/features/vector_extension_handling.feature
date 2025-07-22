Feature: DuckDB VSS Extension Handling
  As a system
  I want to handle DuckDB VSS extension loading flexibly
  So that I can work in environments with limited network access

  Background:
    Given I have a valid configuration with VSS extension enabled

  @requires_vss
  Scenario: Load VSS extension from filesystem
    Given I have a local copy of the VSS extension
    And I have configured the VSS extension path
    When I initialize the storage system
    Then the VSS extension should be loaded from the filesystem
    And vector search functionality should work

  @requires_vss
  Scenario: Download VSS extension automatically
    Given I have no local copy of the VSS extension
    And I have not configured the VSS extension path
    When I initialize the storage system
    Then the VSS extension should be downloaded automatically
    And vector search functionality should work

  @requires_vss
  Scenario: Fallback to download when local extension is invalid
    Given I have an invalid local copy of the VSS extension
    And I have configured the VSS extension path
    When I initialize the storage system
    Then the system should attempt to download the extension
    And vector search functionality should work

  @requires_vss
  Scenario: Handle offline environment with local extension
    Given I have a local copy of the VSS extension
    And I have configured the VSS extension path
    And I am in an offline environment
    When I initialize the storage system
    Then the VSS extension should be loaded from the filesystem
    And vector search functionality should work

  @requires_vss
  Scenario: Handle offline environment without local extension
    Given I have no local copy of the VSS extension
    And I have not configured the VSS extension path
    And I am in an offline environment
    When I initialize the storage system
    Then a warning should be logged about missing VSS extension
    And basic storage functionality should still work
    But vector search should raise an appropriate error

  @requires_vss
  Scenario: Embedding search wrapper dispatches to backend
    Given I have persisted claims with embeddings
    When I perform an embedding lookup with a query embedding
    Then I should receive embedding search results
