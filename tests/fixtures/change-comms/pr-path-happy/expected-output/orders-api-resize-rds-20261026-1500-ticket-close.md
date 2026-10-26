**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
Change completed
What: RDS orders-db resized from db.t3.medium to db.t3.large
PR: https://github.com/acme/orders-infra/pull/482
Applied: <TODO: apply date> 14:12 ICT
Verification: connections and error rate normal for 15 min
Rollback: not needed. Revert the PR and re-apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | RDS orders-db resized from db.t3.medium to db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Execution path line) |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Apply time | 14:12 ICT | `operator-supplied` |
| Apply date | <TODO: apply date> | `operator-supplied (not given)` (the window date is not borrowed) |
| Apply outcome | success (confirmed) | `operator-supplied` (record Outcome "completed" on the PR path means the PR was created) |
| Verification | connections and error rate normal for 15 min | `operator-supplied` (operator text: "connections + error rate normal 15 min") |
| Rollback status | not needed (confirmed success) | `operator-supplied` |
| Revert instruction | revert the PR and re-apply if required | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Phase 1, Rollback path line) |
| Phases | 1 of 1, last phase applied | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` and `operator-supplied` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Platform | Jira comment | `operator-supplied` (a ticket-close is always a Jira comment) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: apply date>` (Applied line): the operator gave 14:12 ICT with no date.

## Flags

none
