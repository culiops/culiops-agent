**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*❌ Aborted: orders-api RDS resize (prod), nothing applied*
Reason: aborted at GATE, pre-flight RED (replace of orders-db)
Next: <TODO: next steps>
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Change (title words "RDS resize") | Resize RDS orders-db from db.t3.medium to db.t3.large | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Phase | 1 of 1 (single phase, so no "phase N of M" in the draft) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | No, nothing was applied | operator-supplied |
| Reason | aborted at GATE, pre-flight RED (replace of orders-db) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Plan summary (reference only, not in draft) | 1 to add, 0 to change, 1 to destroy | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| PR | none exists, line omitted (the Execution: line records an abort at the gate) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |
| Next | `<TODO: next steps>` | operator-supplied (not given) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>` (Next line of the result)

## Flags

none
