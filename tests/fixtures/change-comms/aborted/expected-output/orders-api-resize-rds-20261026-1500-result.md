**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
⛔ Aborted: orders-api RDS resize (prod), nothing applied
Reason: the pre-flight blocked it
Next: <TODO: next steps>
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | Resize RDS orders-db from db.t3.medium to db.t3.large (shown as "RDS resize") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)` |
| Outcome | aborted | `operator-supplied` (message 1: "It got aborted"); matches `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Anything applied | no, nothing applied | `operator-supplied` (message 4: "Nothing was applied"); matches `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Verification: n/a, nothing applied) |
| Reason | the pre-flight blocked it | `operator-supplied` (message 4, used as given); consistent with `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` (Execution: aborted at GATE, pre-flight RED) |
| Pre-flight verdict (context, not shown in draft) | RED (HARD BLOCK) | `record: .culiops/pre-flight/orders-api-resize-rds-20261027-1000.md#Verdict` |
| Next steps | `<TODO: next steps>` | not supplied by the operator |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` (https://acme.atlassian.net/browse/OPS-123) |
| Record Date (not used in draft) | 2026-10-27 10:15, no timezone, time the record was written | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Date)` |
| Timezone | not given; no time appears in this draft | `operator: (no answer in script)` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>`

## Flags

none
