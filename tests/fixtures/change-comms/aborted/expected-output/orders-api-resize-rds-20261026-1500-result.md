**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
Next: <TODO: next steps>
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Change | Resize RDS orders-db from db.t3.medium to db.t3.large (shown as "RDS resize") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR (no PR was created; see PR row) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: "Nothing was applied, the pre-flight blocked it." | `operator-supplied` |
| Reason | Execution line: "aborted at GATE - pre-flight RED (replace of orders-db)"; written in plain words as "stopped before apply: pre-flight check failed (replace of orders-db)" | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Next steps | <TODO: next steps> | `operator-supplied (not given)` |
| PR line | omitted: the Execution line records an abort at the gate, so no PR exists | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| Apply time | not shown: an aborted result carries no apply time | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: next steps>`

## Flags
none
