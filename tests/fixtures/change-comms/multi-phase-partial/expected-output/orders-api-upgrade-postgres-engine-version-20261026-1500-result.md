**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3, 2026-10-28 22:40 ICT*
State: snapshot and engine upgrade applied, cleanup not started; engine shows 15.4 and available, error rate normal
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Change | Postgres engine upgrade (Upgrade RDS orders-db Postgres engine from 14.9 to 15.4) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Outcome word | Partial (partially completed, phase 2 of 3; ⏸) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` |
| Phase | phase 2 of 3 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` |
| Phase 2 apply date and time | 2026-10-28 22:40 ICT (the Phase 2 Execution line only records PR created; no apply time in the record) | operator-supplied |
| Phase 2 apply outcome | success | operator-supplied |
| Phase 2 verification | engine shows 15.4 and available, error rate normal | operator-supplied |
| Phase 1 applied | yes (merged, pipeline applied, operator-confirmed) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 1, Execution line) |
| Phase 3 state | not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 3, Execution line) |
| Next | <TODO: next steps> (operator did not give any) | operator-supplied (not given) |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (phase 2) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, Execution line) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- <TODO: next steps>

## Flags

none
