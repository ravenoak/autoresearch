Feature: Synthesis utilities
  As a developer
  I want synthesis helpers to produce concise results
  So that answers remain clear and within token budgets

  Scenario: Generating concise answers from more than three claims
    Given a query "test question" and five claims
    When I build the answer from the claims
    Then the answer should include only the first three claims and the total count
    And the answer token count should be 10

  Scenario: Producing no answer when claims list is empty
    Given a query "test question" and no claims
    When I build the answer from the claims
    Then the answer should be "No answer found for 'test question'."
    And the answer token count should be 6

  Scenario: Compressing prompts and claims when token budget is exceeded
    Given a long prompt and verbose claims
    When I compress the prompt to 5 tokens
    And I compress the claims to 10 tokens
    Then the compressed prompt should be within the token budget and contain an ellipsis
    And the compressed claims should fit within the token budget with truncation
