**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api RDS resize (prod), applied 14:12 ICT*
Verified: connections + error rate normal 15 min
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / environment | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What (used in title) | RDS resize | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| Apply outcome | success | `operator-supplied` |
| Apply time | 14:12 | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Verification | connections + error rate normal 15 min (as given) | `operator-supplied` |
| Ticket key | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Context, not in draft: record Outcome | completed = PR created, pipeline applies on merge; not used as an apply claim | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |

Operator-supplied facts: apply outcome, apply time, timezone, verification. Execution path is PR, so none of these come from the record.

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
