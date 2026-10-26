**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `operator-supplied` (no records exist)

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium to db.t3.large
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
| What | resize RDS orders-db db.t3.medium to db.t3.large | operator-supplied |
| Window date | tomorrow → 2026-10-27 (resolved in ICT, from run date 2026-10-26) | operator-supplied |
| Window start | 14:00 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Duration | 15 min | operator-supplied |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly | operator-supplied |
| Risk | <TODO: pre-flight verdict> | operator-supplied (not given) |
| Rollback | revert the PR and re-apply, ~10 min | operator-supplied |
| Ticket key | OPS-123 (parsed from the ticket URL) | operator-supplied |
| Ticket URL | https://acme.atlassian.net/browse/OPS-123 (not shown in the draft) | operator-supplied |
| PR | none raised yet, so the `PR:` segment is omitted | operator-supplied |
| Platform | Google Chat | operator-supplied |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: pre-flight verdict>` (Risk line): no records exist and the operator gave no GREEN / YELLOW / RED verdict.

## Flags

none
