**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md` (Date 2026-10-27 16:00, execution path PR; the pre-flight verdict is read from this record, no standalone pre-flight record exists), operator-supplied

## Draft

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-28 22:00 ICT, 2h
What: phase 2 of 3: upgrade RDS orders-db Postgres engine 14.9 → 15.4
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance, repoint orders-api (takes hours)
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Platform | Google Chat | `operator-supplied` (chat default; operator confirmed) |
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (title line) |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (`Execution path`) |
| Window start | 2026-10-28 22:00 | `operator-supplied` |
| Window duration | 2h | `operator-supplied` |
| Timezone | ICT | `operator-supplied` |
| Scope of this heads-up | phase 2 of 3 only (the operator's window is for phase 2) | `operator-supplied` |
| What | upgrade RDS orders-db Postgres engine 14.9 → 15.4 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` (Phase 2 of 3) and `#header` (`Change`) |
| Impact | ~5-10 min of downtime during the engine upgrade restart | `operator-supplied` (used as given) |
| Risk | YELLOW | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, `Pre-flight verdict`) and `#header` (`Pre-flight record`: inline, verdict YELLOW) |
| Rollback | restore from the phase 1 snapshot into a new instance, repoint orders-api (takes hours) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` (Phase 2 of 3, Rollback path; summarised) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` (key parsed from the Ticket Reference URL) |
| PR | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, `Execution:` line) |
| Title emoji and closing line | `🔧 Heads-up: infra change on <service> (<env>)`, `Reply here if this window conflicts.` | `skill template: examples/messages.md#heads-up` (fixed shape text, no record) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

none

## Flags

none
