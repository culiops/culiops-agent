**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api RDS resize (prod), applied 14:12 ICT*
Verified: connections + error rate normal 15 min
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Change label | RDS resize (from the Change line "Resize RDS orders-db from db.t3.medium to db.t3.large") | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Apply outcome | success | operator-supplied |
| Apply time | 14:12 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Verification | connections + error rate normal 15 min (used as given) | operator-supplied |
| Ticket key | OPS-123 (parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |
| Execution path (not in draft) | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Header` |
| Record Outcome (not in draft) | completed. On the PR path this means the PR was created; it is not used as the apply outcome | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Record Verification (not in draft) | "pending — pipeline applies after merge"; not used, the operator's verification replaces it | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Execution Log` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
