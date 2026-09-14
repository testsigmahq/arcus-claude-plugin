# Step Map

| Source Step | Occurrences | Source | Parameter shapes | Expression | Status | Version |
|---|---|---|---|---|---|---|
| `I am signed in` | 2 | `LoginPage.signIn` | none | `signIn()` | reviewed | 1 |
| `I see the record "<param>" in the list` | 6 | `JournalPage.recordAtFirstIndex` | one record | `verifyElementText(element.recordAtFirstIndex, runtime.record)` | reviewed | 1 |
| `I refresh until the record appears` | 2 | `JournalPage.refreshUntilPresent` | none | loop: clear filter, type filter, click refresh, until a row appears | reviewed | 1 |
| `I archive record "<param>"` | 1 | `ArchivePage.archiveRecord` | one record | expand the panel if hidden, clear the search field, type the record, press Enter, click the archive confirmation | reviewed | 1 |
| `I print the receiving label` | 1 | `ReceivingPage.printReceivingLabel` | none | | residue | 1 |
| `I search for record "<param>"` | 2 | `SearchPage.searchForRecord` | one record | | unreviewed | 1 |
| `I select "<param>" reason code` | 1 | `ReceivingPage.selectReasonCode` | one reason code | | unreviewed | 1 |
