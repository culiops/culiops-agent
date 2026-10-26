**Change comms for:** `orders-api` / `prod`
**Type:** `heads-up`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md`, operator-supplied

## Draft

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-28 22:00 ICT, 2h
What: 3 phases: snapshot → upgrade → cleanup; this window: upgrade
Impact: ~5-10 min of downtime during the engine upgrade restart
Risk: YELLOW (pre-flight)
Rollback: restore from the phase 1 snapshot into a new instance and repoint orders-api (hours, not minutes)
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
Reply here if this window conflicts.
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | orders-api | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Environment | prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |
| Platform | Google Chat | operator-supplied |
| Timezone | ICT | operator-supplied |
| Window | 2026-10-28 22:00 ICT, 2h (written as given) | operator-supplied |
| Phases (names) | snapshot → upgrade → cleanup (3 phases) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` |
| Phase state | phase 1 applied; phase 2 PR created, pipeline applies on merge (pending); phase 3 not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (each phase, Execution line)` |
| Phase this window covers | upgrade (phase 2) | operator-supplied |
| Impact | ~5-10 min of downtime during the engine upgrade restart (as given) | operator-supplied |
| Risk | YELLOW | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (Phase 2, Pre-flight verdict line); also #header Pre-flight record line` |
| Rollback | restore from the phase 1 snapshot into a new instance and repoint orders-api (hours, not minutes); summarised from the Phase 2 rollback path | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan (Phase 2, Rollback path)` |
| Ticket key | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` (key parsed from the URL) |
| PR | https://github.com/acme/orders-infra/pull/502 (phase 2 PR) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log (Phase 2, Execution line)` |
| Record Date (not shown in draft) | 2026-10-27 16:00, no timezone, time the record was written; not used as an event time | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` |

## Redaction log

Redaction log: nothing masked

(Patterns 1-7 scanned over the full text of the iac record, and the full pattern pass over the draft; no matches. `sha256:11aa22…` is a hash prefix and `16:00` is a time, both excluded from the IPv6 pattern.)

## Open TODOs

none

## Flags

none
