**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: pre-flight RED, replace of orders-db
Next: <TODO: next steps>
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| What | RDS resize (orders-db db.t3.medium → db.t3.large) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: nothing was applied, the pre-flight blocked it | operator-supplied |
| Reason | pre-flight RED, replace of orders-db (record text: "aborted at GATE — pre-flight RED (replace of orders-db)") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Pre-flight verdict | RED — HARD BLOCK | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Next steps | not given | operator-supplied (not given) |
| Ticket | OPS-123 (from Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| PR line | omitted: aborted at GATE, no `Execution:` line carries a PR URL and the operator gave none | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Apply time | none shown (aborted result carries no apply time) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |

## Redaction log

| # | Type | Found in (record#section) | Replaced with |
|---|------|---------------------------|---------------|
| 1 | plan output (counts) | `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Risk Scorecard` | (dropped) |
| 2 | plan output (diff line) | `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Evidence` | (dropped) |
| 3 | plan output (counts) | `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` | (dropped) |

## Open TODOs
- `<TODO: next steps>` (Next line): the operator did not give next steps.

## Flags
none
