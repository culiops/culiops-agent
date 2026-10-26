**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: orders-db Postgres 14.9 → 15.4, 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Execution path | PR (heads-up runs before the merge that triggers apply) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Window start | 2026-10-28 22:00 | operator-supplied |
| Timezone | ICT | operator-supplied |
| Duration | 2h (written as given, no `~` added) | operator-supplied |
| What (change) | RDS orders-db Postgres engine 14.9 → 15.4 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Header` |
| Phases | 3: snapshot → upgrade → cleanup | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Phase this window covers | upgrade (phase 2 of 3). Taken from the record, not stated by the operator: phase 1 applied, phase 2 PR open and applies on merge, phase 3 not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |
| Impact | ~5-10 min of downtime during the engine upgrade restart (used as given) | operator-supplied |
| Risk | YELLOW (phase 2 `Pre-flight verdict` line; header `Pre-flight record` also says YELLOW; no pre-flight record file on disk) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |
| Rollback | restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes (phase 2 rollback path, summarised) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Ticket | OPS-123 (key parsed from the Ticket Reference URL) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (phase 2) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
