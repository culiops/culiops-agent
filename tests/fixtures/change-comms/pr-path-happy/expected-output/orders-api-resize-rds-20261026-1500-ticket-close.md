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
| Service / environment | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | RDS orders-db resized db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Apply date | <TODO: apply date> | operator-supplied (not given) |
| Apply time | 14:12 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Apply outcome | success (confirmed) | operator-supplied |
| Verification | connections + error rate normal 15 min | operator-supplied |
| Rollback status | not needed (confirmed success) | operator-supplied |
| Rollback instruction | revert the PR + apply if required | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Phase 1, Rollback path) |
| Ticket | OPS-123 (from https://acme.atlassian.net/browse/OPS-123, not shown in draft) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- <TODO: apply date> (Applied line): the operator gave 14:12 ICT with no date; the window date is not borrowed.

## Flags

none
