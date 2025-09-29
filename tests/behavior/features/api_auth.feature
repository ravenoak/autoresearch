Feature: API Authentication and Rate Limiting
  As a user of the Autoresearch API
  I want authentication and throttling enforced
  So that unauthorized or excessive usage is prevented

  Background:
    Given the API server is running

  Scenario: Invalid API key
    Given the API requires an API key "secret"
    When I send a query "test" with header "X-API-Key" set to "bad"
    Then the response status should be 401

  Scenario: Invalid bearer token
    Given the API requires a bearer token "token"
    When I send a query "test" with header "Authorization" set to "Bearer bad"
    Then the response status should be 401
    And the response should include header "WWW-Authenticate" with value "Bearer"

  Scenario: Missing credentials
    Given the API requires an API key "secret"
    When I send a query "test" without credentials
    Then the response status should be 401
    And the response should include header "WWW-Authenticate" with value "API-Key"

  Scenario: Insufficient permission
    Given the API requires an API key "secret" with role "user" and no permissions
    When I send a query "test" with header "X-API-Key" set to "secret"
    Then the response status should be 403

  Scenario: Rate limit exceeded
    Given the API rate limit is 1 request per minute
    When I send two queries to the API
    Then the first response status should be 200
    And the second response status should be 429
    And the request logger should record 2 hits
