**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*⏸ Partial: orders-api upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied, cleanup not started; engine shows 15.4 and available, error rate normal
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Change | upgrade (RDS Postgres engine upgrade, shortened to "upgrade" in the title) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (Change line) |
| Outcome | partially completed (phase 2 of 3), so `⏸ Partial` | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` |
| Phase | phase 2 of 3 applied | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` and `operator-supplied` (apply confirmed after merge; PR path, so the record alone does not show an apply) |
| Apply time | 22:40 ICT (date given: 2026-10-28) | `operator-supplied` |
| Phase 2 apply outcome | success | `operator-supplied` |
| State: snapshot applied | snapshot applied | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 1, Execution line: merged, pipeline applied) |
| State: upgrade applied | upgrade applied | `operator-supplied` |
| State: cleanup | not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 3, Execution line) |
| Verification | engine shows 15.4 and available, error rate normal (as given) | `operator-supplied` |
| Next | not given | `operator-supplied (not given)` |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (phase 2 of 3) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, Execution line) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>` (Next line)

## Flags

none
