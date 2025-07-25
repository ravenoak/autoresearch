Feature: API Streaming and Webhook Notifications
  As a developer
  I want to receive streaming updates or webhook callbacks
  So that I can integrate Autoresearch with other systems

  Background:
    Given the Autoresearch application is running

  Scenario: Streaming query responses
    When I send a streaming query "Stream test" to the API
    Then the streaming response should contain multiple JSON lines

  Scenario: Webhook notifications on query completion
    When I send a query with webhook URL "http://hook" to the API
    Then the request should succeed
    And the webhook endpoint should be called
