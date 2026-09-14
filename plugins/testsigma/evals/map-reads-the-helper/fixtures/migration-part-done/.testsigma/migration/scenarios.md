# Scenarios

Status is one of `pending`, `done`, `parked` or `out-of-scope`. `Reason` is
required by `parked` and `out-of-scope` alike. The unseen count is not a column:
it is computed from this file and `step-map.md`.

| Scenario | Source Steps reached | Status | Reason |
|---|---|---|---|
| `Record a journal entry` | `I am signed in`, `I see the record "<param>" in the list` | done | |
| `Search the journal` | `I am signed in`, `I search for record "<param>"` | pending | |
| `Receive against a reason code` | `I am signed in`, `I select "<param>" reason code` | parked | the reason code element could not be resolved |
| `Print the nightly batch` | `I am signed in` | out-of-scope | drives a desktop print dialogue the platform has no catalogue for |
