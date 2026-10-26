**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: RDS orders-db Postgres engine 14.9 → 15.4, 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Window start | 2026-10-28 22:00 ICT | `operator-supplied` |
| Window duration | 2h (written as given) | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| What (change) | RDS orders-db Postgres engine 14.9 → 15.4 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (Change line) |
| What (phases) | 3 phases: snapshot → upgrade → cleanup | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` (Phase 1-3 titles) |
| What (this window) | upgrade | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 1 applied, Phase 2 PR pending merge, Phase 3 not started) and `operator-supplied` (impact names the engine upgrade restart) |
| Impact | ~5-10 min of downtime during the engine upgrade restart (as given) | `operator-supplied` |
| Risk | YELLOW | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (Pre-flight record line; Phase 2 Pre-flight verdict line also YELLOW) |
| Rollback | restore from the phase 1 snapshot into a new instance and repoint orders-api, hours not minutes (summarised, Phase 2 rollback path) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (phase 2 of 3) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, Execution line) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
