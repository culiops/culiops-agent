**Change comms for:** `orders-api` / `prod`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md` (Date 2026-10-27 16:00, execution path PR), operator-supplied

## Draft

```text
⏸ Partial: orders-api Postgres engine upgrade (prod), phase 2 of 3 applied, 22:40 ICT
State: snapshot and upgrade applied, engine shows 15.4 and available, error rate normal, cleanup not started
Next: <TODO: next steps>
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/502
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Platform | Google Chat | `operator-supplied` (chat default; operator confirmed) |
| Service / env | orders-api / prod | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (title line) |
| Execution path | PR | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (`Execution path`) |
| Change (title wording) | Postgres engine upgrade | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#header` (`Change`) |
| Overall outcome | partial, phase 2 of 3 (shown as ⏸ Partial) | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Outcome` ("partially completed (phase 2 of 3)") |
| Phase this result covers | phase 2 of 3 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Change Plan` / `#Execution Log` (Phase 2) |
| Phase 2 apply time | 22:40 ICT (2026-10-28) | `operator-supplied` (the record holds no apply time on the PR path) |
| Phase 2 apply outcome | applied, success | `operator-supplied` |
| Phase 2 verification | engine shows 15.4 and available, error rate normal | `operator-supplied` (used as given) |
| Phase 1 state | snapshot applied | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 1, `Execution:` line, "merged, pipeline applied (operator-confirmed before phase 2)") |
| Phase 3 state | cleanup not started | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 3, `Execution: not started`) |
| Next | `<TODO: next steps>` | no source (operator gave no answer; next steps are operator-supplied only) |
| Ticket | OPS-123 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Ticket Reference` (key parsed from the Ticket Reference URL) |
| PR | https://github.com/acme/orders-infra/pull/502 | `record: .culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md#Execution Log` (Phase 2, `Execution:` line) |
| Emoji and line labels | `⏸ Partial: ...`, `State:`, `Next:`, `Ticket:` | `skill template: examples/messages.md#result` (Partial shape; fixed shape text, no record) |

## Redaction log

Redaction log: nothing masked

## Open TODOs

- `<TODO: next steps>` (operator gave no next steps)

## Flags

none
