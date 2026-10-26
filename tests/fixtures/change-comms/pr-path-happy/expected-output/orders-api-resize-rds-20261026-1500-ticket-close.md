**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
Change completed
What: RDS orders-db resized db.t3.medium → db.t3.large
PR: https://github.com/acme/orders-infra/pull/482
Applied: <TODO: apply date> 14:12 ICT
Verification: connections + error rate normal 15 min
Rollback: not needed. Revert PR + apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| What | RDS orders-db resized db.t3.medium → db.t3.large (past tense of the Change line / Phase 1 of 1 "Resize orders-db") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Apply date | <TODO: apply date> (the operator gave a time only) | operator-supplied (not given) |
| Apply time | 14:12 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Apply outcome | success | operator-supplied |
| Verification | connections + error rate normal 15 min (used as given) | operator-supplied |
| Rollback status | not needed (outcome confirmed success) | operator-supplied |
| Revert instruction | revert PR + apply if required (summarised from "revert PR #482 and re-apply, ~10 min") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Ticket key (not in draft; the comment is posted on this ticket) | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Execution path (not in draft) | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Record Outcome (not in draft) | completed. On the PR path this means the PR was created; it is not used as the apply outcome | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: apply date>` (Applied line): the operator gave the apply time (14:12 ICT) but no date.

## Flags
none
