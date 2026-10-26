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
| Service / environment | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | resize RDS orders-db db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| Window start | 2026-10-27 14:00 | `operator-supplied` ("tomorrow 14:00", resolved against session date 2026-10-26) |
| Window duration | 15 min (written as given, no `~`) | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Rollback | revert PR + apply, ~10 min (summarised) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Phase 1, Rollback path) |
| Ticket key | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Context, not in draft: commit, plan summary, plan hash | e7f8a9b; 1 to change, 0 to add, 0 to destroy; sha256:7a1c9e… | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header and #Execution Log` |

Operator-supplied facts: window start and duration, timezone, impact. Record `Date` (2026-10-27 10:15, no timezone) is the time the record was written and is not used as any event time.

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
