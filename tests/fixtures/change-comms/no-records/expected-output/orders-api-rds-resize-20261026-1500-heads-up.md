**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `operator-supplied` (no records found; `.culiops/` holds only `.gitkeep`)

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
| Window date | 2026-10-27 | operator-supplied ("tomorrow", resolved against session date 2026-10-26) |
| Window start | 14:00 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Duration | 15 min | operator-supplied (written as given, no `~` added) |
| What | resize RDS orders-db db.t3.medium → db.t3.large | operator-supplied |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly | operator-supplied (used as given) |
| Risk | <TODO: pre-flight verdict> | operator-supplied (not given); no pre-flight or iac record exists |
| Rollback | revert the PR and re-apply, ~10 min | operator-supplied (no Change Plan available) |
| Ticket | OPS-123 | operator-supplied (key parsed from the ticket URL the operator gave) |
| Ticket URL | https://acme.atlassian.net/browse/OPS-123 | operator-supplied (not shown in the draft) |
| PR | omitted: no PR exists yet | operator-supplied ("No PR raised yet") |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: pre-flight verdict>` (Risk line): no pre-flight record exists and the operator did not supply a verdict.

## Flags

none
