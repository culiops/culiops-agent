**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` (read for redaction scan; no fact in the draft is taken from it), operator-supplied

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
| Execution path | PR (no PR was created) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Phases | 1 of 1, so ticket-close is allowed (work finished by abort) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| What | RDS orders-db resize db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change line)` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: nothing was applied | `operator-supplied` |
| Reason | stopped before apply because pre-flight check failed (replace of orders-db); jargon rewritten in plain words | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| PR line | omitted: the Execution line records an abort at the gate, so no PR exists | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| Applied | not applied | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Verification line) and operator-supplied` |
| Verification | not run | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Verification line: n/a, nothing applied) and operator-supplied` |
| Rollback | not needed, nothing was applied | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan (Rollback path line) and operator-supplied` |
| Ticket key | OPS-123 (not shown in the draft; the comment is posted on the ticket) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

Operator-supplied: "nothing applied" confirmation only. All else is from the record.

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
