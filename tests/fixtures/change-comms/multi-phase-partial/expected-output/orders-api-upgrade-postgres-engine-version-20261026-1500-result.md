**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied, cleanup not started; engine shows 15.4 and available, error rate normal
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Change (title wording) | Postgres engine upgrade | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header (Change line)` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Platform | Google Chat | operator-supplied |
| Recorded outcome | partially completed (phase 2 of 3), so the partial shape applies | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` |
| Phase covered | phase 2 of 3 (upgrade engine version) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome and #Execution Log` |
| Phase 2 applied at | 2026-10-28 22:40 ICT (draft shows 22:40 ICT per the shape; date kept here) | operator-supplied |
| Phase 2 apply outcome | success | operator-supplied |
| Phase 1 state | applied (merged, pipeline applied) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (Phase 1, Execution line)` |
| Phase 3 state | not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (Phase 3, Execution line)` |
| Verification (as given) | engine shows 15.4 and available, error rate normal | operator-supplied |
| Next steps | not given | operator-supplied (not given) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` (key parsed from the URL) |
| PR | https://github.com/acme/orders-infra/pull/502 (phase 2 PR) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (Phase 2, Execution line)` |
| Record Date (not shown in draft) | 2026-10-27 16:00, no timezone, time the record was written; not used as the apply time | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>` (Next line): the operator gave no next steps.

## Flags

none
