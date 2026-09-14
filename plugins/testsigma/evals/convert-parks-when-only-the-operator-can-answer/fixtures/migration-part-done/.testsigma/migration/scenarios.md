# Scenarios

Status is one of `pending`, `done`, `parked` or `out-of-scope`. `Reason` is
required by `parked` and `out-of-scope` alike. The unseen count is not a column:
it is computed from this file and `step-map.md`.

| Scenario | Source Steps reached | Status | Reason |
|---|---|---|---|
| `Archive a record` | `I am signed in`, `I archive record "<param>"`, `I see the record "<param>" in the list` | done | |
| `Receive a single record` | `I am signed in`, `I search for record "<param>"`, `I see the record "<param>" in the list`, `I select "<param>" reason code` | pending | |
| `Receive several records` | `I am signed in`, `I search for record "<param>"`, `I see the record "<param>" in the list` | pending | |
| `Print a receiving label` | `I am signed in`, `I print the receiving label`, `I see the record "<param>" in the list` | pending | |
| `A record appears after processing` | `I am signed in`, `I refresh until the record appears`, `I see <number> result`, `I see the record "<param>" in the list` | pending | |
| `Two records appear` | `I am signed in`, `I refresh until the record appears`, `I see <number> results` | pending | |
