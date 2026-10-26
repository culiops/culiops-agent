**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

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
| What | RDS orders-db resized db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| PR | https://github.com/acme/orders-infra/pull/482 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Apply date | not given | `operator-supplied (not given)` |
| Apply time | 14:12 ICT | `operator-supplied` |
| Verification | connections + error rate normal 15 min (as given) | `operator-supplied` |
| Apply outcome | success (confirmed, so `Rollback: not needed` is allowed) | `operator-supplied` |
| Rollback instruction | revert PR + apply if required (summarised) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Phase 1, Rollback path) |
| Ticket key (not a line in this shape; the comment is posted on it) | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

Operator-supplied facts: apply time, timezone, verification, apply outcome. The window date (2026-10-27) is not borrowed for the apply date.

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: apply date>` in the Applied line: the operator gave a time (14:12 ICT) but no date.

## Flags
none
