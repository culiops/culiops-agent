**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md` (Date 2026-10-27 10:15), `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` (read, not cited in the draft), operator-supplied

## Draft

```text
Change aborted
Outcome: aborted, nothing applied
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
What: Resize RDS orders-db from db.t3.medium to db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | Resize RDS orders-db from db.t3.medium to db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR (no PR was created; the abort was at the gate) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | no, nothing was applied (gives "nothing applied", "Applied: not applied", "Rollback: not needed, nothing was applied") | `operator-supplied` |
| Reason | stopped before apply: pre-flight check failed (replace of orders-db) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| PR | none exists (Execution line records an abort at the gate); PR line omitted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Verification | not run (record: n/a, nothing applied) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Verification line) |
| Rollback | not needed, nothing was applied (Change Plan rollback path: not applicable, nothing was applied) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan and operator-supplied` |
| Ticket key | OPS-123 (not shown in the draft; Jira comment is posted on that ticket) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
