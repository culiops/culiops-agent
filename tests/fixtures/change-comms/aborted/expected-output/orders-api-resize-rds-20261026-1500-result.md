**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md` (read for redaction scan and verdict context; no fact in the draft is taken from it), operator-supplied

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
| Execution path | PR (no PR was created) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Change | RDS resize (orders-db db.t3.medium → db.t3.large), phase 1 of 1 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change line) and #Change Plan` |
| Outcome | aborted | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Nothing applied | confirmed: nothing was applied | `operator-supplied` |
| Reason | aborted before apply because pre-flight check failed (replace of orders-db); jargon ("GATE", "RED") rewritten in plain words | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| PR line | omitted: the Execution line records an abort at the gate, so no PR exists | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log (Phase 1, Execution line)` |
| Next | `<TODO: next steps>` | `operator-supplied (not given)` |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

Operator-supplied: "nothing applied" confirmation only. All else is from the record.

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>` (Next line)

## Flags

none
