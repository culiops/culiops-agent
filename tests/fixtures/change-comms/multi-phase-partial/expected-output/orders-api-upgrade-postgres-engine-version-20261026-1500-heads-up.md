**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: upgrade RDS orders-db Postgres engine from 14.9 to 15.4, 3 phases: snapshot → engine upgrade → cleanup; this window: engine upgrade (phase 2)
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api, takes hours
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Change | Upgrade RDS orders-db Postgres engine from 14.9 to 15.4 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Phases | 3: Snapshot orders-db → Upgrade engine version → Cleanup | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Phases pending | phase 2 (PR created, applies on merge), phase 3 (not started); phase 1 already applied | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Execution lines, Phases 1-3) |
| Phase this window covers | phase 2 only | operator-supplied |
| Window | 2026-10-28 22:00 ICT, 2h (absolute date given; no relative day to resolve) | operator-supplied |
| Impact | ~5-10 min of downtime during the engine upgrade restart | operator-supplied |
| Risk | YELLOW (phase 2 verdict "YELLOW — PROCEED WITH CAUTION"; header also says verdict YELLOW; no separate pre-flight record) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, Pre-flight verdict line) |
| Rollback | restore from the phase 1 snapshot into a new instance and repoint orders-api; hours, not minutes (phase 2 rollback path, summarised) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Ticket key | OPS-123 (from Jira URL https://acme.atlassian.net/browse/OPS-123) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` |
| PR (covered phase) | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, Execution line) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
