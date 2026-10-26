**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
Change completed
What: RDS orders-db resized db.t3.medium → db.t3.large
PR: https://github.com/acme/orders-infra/pull/482
Applied: 14:12 ICT
Verification: connections + error rate normal for 15 min
Rollback: not needed. Revert PR + apply if required.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| Phases | 1 of 1; last phase applied, so ticket-close is allowed | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan`; apply confirmed by `operator-supplied` |
| Outcome | success (title `Change completed`, no `Outcome:` line) | `operator-supplied` (record Outcome `completed` = PR created only) |
| What | RDS orders-db resized db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Applied | 14:12 ICT | `operator-supplied` (date not given, shown as given) |
| Verification | connections + error rate normal for 15 min | `operator-supplied` |
| Rollback status | not needed (confirmed success) | `operator-supplied` (success outcome) |
| Rollback route | Revert PR + apply if required | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Rollback path: revert the PR and re-apply, summarised; the ~10 min estimate is omitted from this message) |
| Ticket key | OPS-123 (not a line in this shape; key parsed for traceability) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
