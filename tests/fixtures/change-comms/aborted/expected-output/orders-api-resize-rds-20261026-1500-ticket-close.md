**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Ticket key (not in draft; the Jira comment is posted on this ticket) | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Phase | 1 of 1 (single phase; ticket-close allowed because the outcome is an abort) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | No, nothing was applied | operator-supplied |
| What | RDS orders-db resize db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| PR | none exists, line omitted (the Execution: line records an abort at the gate) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Applied | not applied | operator-supplied |
| Verification | not run (record: "n/a — nothing applied"; operator gave no verification) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` and operator-supplied |
| Rollback | not needed, nothing was applied (confirmed abort, nothing applied; Change Plan rollback path: "not applicable, nothing was applied") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` and operator-supplied |
| Plan summary (reference only, not in draft) | 1 to add, 0 to change, 1 to destroy | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
