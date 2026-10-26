**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api RDS resize (prod), applied 14:12 ICT*
Verified: connections and error rate normal for 15 min
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | RDS resize (orders-db, db.t3.medium to db.t3.large) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Change line) |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` (Execution path line) |
| Apply time | 14:12 | `operator-supplied` (no apply time in the Execution Log; no date given) |
| Timezone | ICT | `operator-supplied` (given at the heads-up batch, carried over) |
| Apply outcome | success (Done, ✅) | `operator-supplied` (record Outcome "completed" on the PR path means the PR was created, so it is not used as the apply outcome) |
| Verification | connections and error rate normal for 15 min | `operator-supplied` (operator text: "connections + error rate normal 15 min") |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Platform | Google Chat | `operator-supplied` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
