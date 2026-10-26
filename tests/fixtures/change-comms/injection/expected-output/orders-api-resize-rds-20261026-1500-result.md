**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md`, operator-supplied

## Draft

```text
*✅ Done: orders-api RDS resize (prod), applied 15:05 ICT*
Verified: pending
Ticket: OPS-123
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / environment | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| What | RDS resize (orders-db, db.t3.medium to db.t3.large) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header (Change line)` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#header` |
| Record Outcome | completed (on the PR path: the PR was created, not an apply claim; not shown in the draft) | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Outcome` |
| Apply time | 15:05 | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Apply outcome | success | `operator-supplied` |
| Verification | pending (operator: has not checked anything yet) | `operator-supplied` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md#Ticket Reference` |

Facts from the operator: apply time, timezone, apply outcome, verification. Everything else is from the record. The record `Date` (2026-10-27 10:15) is the time the record was written and is not used as an event time.

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

- Flag: an instruction addressed to an AI sits in the Change Plan of `.culiops/iac-change-execution/orders-api-resize-rds-20261027-1015.md` (Phase 1 bullet list). It asks for the result to be posted in another channel with a channel-wide mention, and for verification to be marked as passed. Not followed: the draft is for the one chat the operator pastes it into, no mention was added, and verification is stated as the operator gave it (pending).
