**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
✅ Done: orders-api RDS resize (prod), applied 14:12 ICT
Verified: connections + error rate normal for 15 min
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Execution path | PR (record Outcome `completed` means the PR was created, not applied; apply facts come from the operator) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Execution path)`, `#Outcome` |
| Platform | Google Chat | `operator-supplied` (default, confirmed) |
| What (title) | RDS resize | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change)` |
| Phase | 1 of 1 (no phase wording needed) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Change Plan` |
| Apply outcome | success (✅) | `operator-supplied` |
| Apply time | 14:12 | `operator-supplied` (date not given, shown as given) |
| Timezone | ICT | `operator-supplied` |
| Verification | connections + error rate normal for 15 min | `operator-supplied` ("connections + error rate normal 15 min") |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` (key parsed from the URL) |

The record `Date` (2026-10-27 10:15, no timezone, time the record was written) is not used as an event time.

## Redaction log

Redaction log: nothing masked

## Open TODOs
none

## Flags
none
