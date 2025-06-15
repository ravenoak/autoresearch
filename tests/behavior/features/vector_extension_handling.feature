Feature: DuckDB Vector Extension Handling
  As a system
  I want to handle DuckDB vector extension loading flexibly
  So that I can work in environments with limited network access

  Background:
    Given I have a valid configuration with vector extension enabled

  Scenario: Load vector extension from filesystem
    Given I have a local copy of the vector extension
    And I have configured the vector extension path
    When I initialize the storage system
    Then the vector extension should be loaded from the filesystem
    And vector search functionality should work

  Scenario: Download vector extension automatically
    Given I have no local copy of the vector extension
    And I have not configured the vector extension path
    When I initialize the storage system
    Then the vector extension should be downloaded automatically
    And vector search functionality should work

  Scenario: Fallback to download when local extension is invalid
    Given I have an invalid local copy of the vector extension
    And I have configured the vector extension path
    When I initialize the storage system
    Then the system should attempt to download the extension
    And vector search functionality should work

  Scenario: Handle offline environment with local extension
    Given I have a local copy of the vector extension
    And I have configured the vector extension path
    And I am in an offline environment
    When I initialize the storage system
    Then the vector extension should be loaded from the filesystem
    And vector search functionality should work

  Scenario: Handle offline environment without local extension
    Given I have no local copy of the vector extension
    And I have not configured the vector extension path
    And I am in an offline environment
    When I initialize the storage system
    Then a warning should be logged about missing vector extension
    And basic storage functionality should still work
    But vector search should raise an appropriate error