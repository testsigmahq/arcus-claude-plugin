# Step Map

| Source Step | Occurrences | Source | Parameter shapes | Expression | Status | Version |
|---|---|---|---|---|---|---|
| `I am signed in` | 4 | `LoginPage.signIn` | none | `signIn()` | reviewed | 1 |
| `I see the record "<param>" in the list` | 4 | `JournalPage.recordAtFirstIndex` | one record | `verifyElementText(element.recordAtFirstIndex, runtime.record)` | reviewed | 1 |
| `I refresh until the record appears` | 2 | `JournalPage.refreshUntilPresent` | none | loop: clear filter, type filter, click refresh, until a row appears | reviewed | 1 |
| `I search for record "<param>"` | 4 | `SearchPage.searchForRecord` | one record | | unreviewed | 1 |
| `I select "<param>" reason code` | 2 | `ReceivingPage.selectReasonCode` | one reason code | | unreviewed | 1 |
