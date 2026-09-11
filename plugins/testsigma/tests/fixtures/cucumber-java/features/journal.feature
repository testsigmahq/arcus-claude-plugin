Feature: Printing journal

  Background:
    Given I am signed in

  Scenario: A record appears after processing
    When I refresh until the record appears
    Then I see 1 result
    And I see the record "REC05ALPHA" in the list

  Scenario: Two records appear
    When I refresh until the record appears
    Then I see 2 results
