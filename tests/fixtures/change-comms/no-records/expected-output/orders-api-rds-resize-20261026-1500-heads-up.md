**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `operator-supplied` (no `.culiops/iac-change-execution/` or `.culiops/pre-flight/` records exist)

## Draft

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: <TODO: pre-flight verdict>
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `operator-supplied` |
| Environment | prod | `operator-supplied` |
| Platform | Google Chat | `operator-supplied` (also the skill default) |
| Execution path | not stated (not needed for a heads-up; nothing is claimed about apply) | `operator-supplied`: no answer given |
| What | resize RDS orders-db db.t3.medium to db.t3.large (drawn as `→` in the draft) | `operator-supplied` |
| Window start | 2026-10-27 14:00 ICT (operator said "tomorrow 14:00 ICT"; "tomorrow" resolved against the local session date 2026-10-26) | `operator-supplied` |
| Window duration | 15 min (as given, no "~") | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly (verbatim) | `operator-supplied` |
| Risk | `<TODO: pre-flight verdict>` (no pre-flight record) | none |
| Rollback | revert the PR and re-apply, ~10 min | `operator-supplied` |
| Ticket reference | https://acme.atlassian.net/browse/OPS-123 | `operator-supplied` |
| Ticket key | OPS-123 (parsed from the ticket URL) | `operator-supplied` (parsed from the Ticket Reference URL) |
| PR | none raised yet; PR segment omitted from the draft | `operator-supplied` |
| Title, `Reply here if this window conflicts.` | fixed shape text | skill shape `examples/messages.md#heads-up` |
| Saved at (local session time) | 2026-10-26 15:00 | session |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: pre-flight verdict>` (Risk line): no pre-flight record exists for this change.

## Flags

none
