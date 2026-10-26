**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
🔧 Heads-up: infra change on orders-api (prod)
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
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| Platform | Google Chat | `operator-supplied` (default, confirmed) |
| Window start | 2026-10-27 14:00 | `operator-supplied` ("tomorrow 14:00", resolved against session date 2026-10-26) |
| Duration | 15 min | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| What | resize RDS orders-db db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)`; `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#header (Action)` |
| Phases | 1 of 1 (no phase line needed) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly | `operator-supplied` (used as given) |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Rollback | revert PR + apply, ~10 min | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Rollback path, summarised) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` (key parsed from the URL) |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Closing line | Reply here if this window conflicts. | fixed shape text, `skills/change-comms/examples/messages.md#heads-up` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
