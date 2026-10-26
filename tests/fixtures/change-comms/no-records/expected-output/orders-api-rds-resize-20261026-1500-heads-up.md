**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `operator-supplied` (no records found in `.culiops/`)

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
| Platform | Google Chat | operator-supplied |
| What | resize RDS orders-db db.t3.medium → db.t3.large | operator-supplied |
| Window start | 2026-10-27 14:00 ICT (operator said "tomorrow"; resolved against session date 2026-10-26) | operator-supplied |
| Window duration | 15 min (as given) | operator-supplied |
| Timezone | ICT | operator-supplied |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly (as given) | operator-supplied |
| Risk (pre-flight verdict) | <TODO: pre-flight verdict> | operator-supplied (not given) |
| Rollback | revert the PR and re-apply, ~10 min | operator-supplied |
| Ticket key | OPS-123 | operator-supplied (parsed from the ticket URL the operator gave) |
| Ticket URL | https://acme.atlassian.net/browse/OPS-123 | operator-supplied |
| PR | none raised yet, so the PR segment is omitted | operator-supplied |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: pre-flight verdict>` (Risk line): no pre-flight record exists and the operator gave no verdict.

## Flags
none
