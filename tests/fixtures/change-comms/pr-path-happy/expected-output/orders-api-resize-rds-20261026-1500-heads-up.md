**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db db.t3.medium → db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: YELLOW (pre-flight)
Rollback: revert PR + apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/482
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Window start | 2026-10-27 14:00 (operator said "tomorrow 14:00"; resolved against session date 2026-10-26) | operator-supplied |
| Timezone | ICT | operator-supplied |
| Duration | 15 min (written as given, no `~` added) | operator-supplied |
| What (Change line) | resize RDS orders-db db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly (used as given) | operator-supplied |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Rollback | revert PR + apply, ~10 min (summarised from "revert PR #482 and re-apply, ~10 min") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Ticket key | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Execution path (not in draft) | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Record Date (not in draft; no timezone, time the record was written, not an event time) | 2026-10-27 10:15 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Pre-flight Date (not in draft) | 2026-10-27 10:00 (UTC) | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Header` |
| Plan summary (not in draft) | 0 to add, 1 to change, 0 to destroy | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Plan hash (not in draft) | sha256:7a1c9e… (truncated in the record) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Commit (not in draft) | e7f8a9b | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
