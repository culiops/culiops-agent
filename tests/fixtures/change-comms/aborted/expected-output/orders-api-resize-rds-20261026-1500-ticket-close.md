**Change comms for:** `orders-api` / `prod`
**Type:** `ticket-close`
**Platform:** `Jira comment`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
Change aborted
Outcome: aborted, nothing applied
What: RDS orders-db resize db.t3.medium → db.t3.large
PR: <TODO: PR link>
Applied: not applied
Verification: not run
Rollback: not needed, nothing was applied
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | RDS orders-db resize db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| Outcome | aborted | `operator-supplied` (message 1: "It got aborted"); matches `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | no, nothing applied (confirmed abort) | `operator-supplied` (message 4: "Nothing was applied"); matches `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Applied | not applied | `operator-supplied` (nothing applied, no apply time); `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Verification | not run | `operator-supplied` (message 4: no verification); `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Verification: n/a, nothing applied) |
| Rollback | not needed, nothing was applied | `operator-supplied` (confirmed nothing applied); `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` (Rollback path: not applicable, nothing was applied) |
| PR link | `<TODO: PR link>` | no `Execution:` line holds a PR URL; operator gave none (`operator: (no answer in script)`) |
| Pre-flight verdict (context, not shown in draft) | RED (HARD BLOCK) | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Ticket key (for the Jira ticket this comment is posted on) | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` (https://acme.atlassian.net/browse/OPS-123) |
| Record Date (not used in draft) | 2026-10-27 10:15, no timezone, time the record was written | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Date)` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: PR link>`

## Flags

none
