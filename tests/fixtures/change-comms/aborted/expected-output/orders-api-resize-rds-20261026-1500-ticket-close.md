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
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: nothing was applied, the pre-flight blocked it | operator-supplied |
| What | RDS orders-db resize db.t3.medium → db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| Applied | not applied (aborted, nothing applied) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Verification | not run (record: "n/a — nothing applied") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Rollback | not needed, nothing was applied (confirmed abort; Change Plan: "not applicable, nothing was applied") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Ticket key | OPS-123 (not shown in the comment; it is posted on that ticket) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| PR line | omitted: aborted at GATE, no `Execution:` line carries a PR URL and the operator gave none | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Phases | 1 of 1, so no per-phase PR / Outcome lines | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | plan output (counts) | `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Risk Scorecard` | (dropped) |
| 2 | plan output (diff line) | `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Evidence` | (dropped) |
| 3 | plan output (counts) | `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` | (dropped) |

## Open TODOs
none

## Flags
none
