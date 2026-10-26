**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `operator-supplied` (no records found: `.culiops/` holds only `.gitkeep`)

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
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
| Service | orders-api | operator-supplied |
| Environment | prod | operator-supplied |
| What | resize RDS orders-db db.t3.medium to db.t3.large (shown with the shape's arrow) | operator-supplied |
| Window start | 2026-10-27 14:00 (operator said "tomorrow 14:00"; resolved against session date 2026-10-26) | operator-supplied |
| Timezone | ICT | operator-supplied |
| Duration | 15 min (as given, no `~` added) | operator-supplied |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly (used as given) | operator-supplied |
| Risk | not available: no pre-flight record, no iac record | operator-supplied (not given) |
| Rollback | revert the PR and re-apply, ~10 min | operator-supplied |
| Ticket | OPS-123 (key from ticket URL https://acme.atlassian.net/browse/OPS-123) | operator-supplied |
| PR | none raised yet, so the PR segment is omitted | operator-supplied |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: pre-flight verdict>` (Risk line): no pre-flight record exists and the operator gave none.

## Flags

none
