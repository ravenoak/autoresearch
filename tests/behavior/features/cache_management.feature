Feature: Cache management
  As a developer
  I want to cache search results
  So that repeated queries are faster

  Scenario: Store results in cache
    Given an empty cache
    When I store results for query "my query" and backend "test"
    Then retrieving results for query "my query" and backend "test" yields the stored data

  Scenario: Retrieve cached results
    Given cached results for query "foo" and backend "bar"
    When I retrieve results for query "foo" and backend "bar"
    Then the cached data is returned

  Scenario: Cache miss returns None
    Given an empty cache
    When I retrieve results for query "missing" and backend "test"
    Then no cached data is returned

  Scenario: Clear cache removes stored results
    Given cached results for query "clear" and backend "test"
    When I clear the cache
    Then retrieving results for query "clear" and backend "test" yields no data
