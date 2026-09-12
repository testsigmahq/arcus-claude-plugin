# Step Map

| Source Step | Occurrences | Parameter shapes | Expression | Status |
|---|---|---|---|---|
| `I am signed in` | 4 | none | `signIn()` | reviewed |
| `I see the record "<param>" in the list` | 4 | one record | `verifyElementText(element.recordAtFirstIndex, runtime.record)` | reviewed |
| `I refresh until the record appears` | 2 | none | loop: clear filter, type filter, click refresh, until a row appears | reviewed |
