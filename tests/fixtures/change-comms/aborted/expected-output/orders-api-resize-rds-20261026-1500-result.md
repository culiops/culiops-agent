**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md` (Date 2026-10-27 10:15), `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` (read, not cited in the draft), operator-supplied

## Draft

```text
*❌ Aborted: orders-api RDS orders-db resize (prod), nothing applied*
Reason: stopped before apply: pre-flight check failed (replace of orders-db)
Next: <TODO: next steps>
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Change summary (title) | RDS orders-db resize (from "Resize RDS orders-db from db.t3.medium to db.t3.large") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR (no PR was created; the abort was at the gate) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | no, nothing was applied | `operator-supplied` |
| Reason | stopped before apply: pre-flight check failed (replace of orders-db) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| PR | none exists (Execution line records an abort at the gate); PR segment omitted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Phase 1, Execution line) |
| Next steps | <TODO: next steps> | `operator-supplied (not given)` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>`

## Flags

none
