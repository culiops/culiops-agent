**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT*
State: snapshot and upgrade applied; engine shows 15.4 and available, error rate normal; cleanup not started
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Execution path | PR (apply, apply time and verification come from the operator, not from record Outcome) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| What (title words) | Postgres engine upgrade | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Phase this result covers | phase 2 of 3 | operator-supplied |
| Record outcome | partially completed (phase 2 of 3), so the shape is `⏸ Partial` | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` |
| Phase 2 apply outcome | success | operator-supplied |
| Apply date and time | 2026-10-28 22:40 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Verification | engine shows 15.4 and available, error rate normal (used as given) | operator-supplied |
| Phase 1 state | applied (PR merged, pipeline applied) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |
| Phase 3 state | cleanup not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |
| Next steps | `<TODO: next steps>` | operator-supplied (not given) |
| Ticket | OPS-123 (key parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (phase 2) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>`

## Flags

none
