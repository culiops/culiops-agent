**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
Change aborted
Outcome: aborted, nothing applied
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
What: RDS orders-db resize db.t3.medium → db.t3.large
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: "Nothing was applied, the pre-flight blocked it." | `operator-supplied` |
| Reason | Execution line: "aborted at GATE - pre-flight RED (replace of orders-db)"; written in plain words as "stopped before apply: pre-flight check failed (replace of orders-db)" | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| What | Resize RDS orders-db from db.t3.medium to db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| PR line | omitted: the Execution line records an abort at the gate, so no PR exists | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| Applied | not applied (aborted, nothing applied) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome and operator-supplied` |
| Verification | not run (record: "n/a - nothing applied") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Verification line)` |
| Rollback | not needed, nothing was applied (confirmed abort; Change Plan rollback path: "not applicable, nothing was applied") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan and operator-supplied` |
| Ticket key | OPS-123 (the comment is posted on this ticket, so the draft has no Ticket line) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
