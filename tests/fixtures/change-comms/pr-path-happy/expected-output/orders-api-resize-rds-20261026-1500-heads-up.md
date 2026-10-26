**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: resize RDS orders-db from db.t3.medium to db.t3.large
Impact: ~30-60s Multi-AZ failover, writes may fail briefly
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/482
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | Resize RDS orders-db from db.t3.medium to db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| Timezone | ICT | `operator-supplied` |
| Window start | tomorrow 14:00 → 2026-10-27 14:00 ICT | `operator-supplied` (relative day resolved to 2026-10-27 in ICT) |
| Window duration | 15 min | `operator-supplied` |
| Impact | ~30-60s Multi-AZ failover, writes may fail briefly | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Rollback | revert the PR and re-apply, ~10 min | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Phase 1, Rollback path line) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Platform | Google Chat | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
