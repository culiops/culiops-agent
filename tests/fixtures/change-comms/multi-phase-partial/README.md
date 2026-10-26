# multi-phase-partial

## Scenario

A three-phase Postgres engine upgrade on RDS `orders-db` (snapshot, upgrade, cleanup). The record `orders-api-upgrade-postgres-engine-version-20261027-1600.md` shows phase 1 (PR 501) applied and phase 2 (PR 502) created; phase 3 not started. Outcome is `partially completed (phase 2 of 3)`. The operator wants all three message types.

Exercises: multi-phase heads-up (one message, phases on one line), per-phase result with the right PR, and the ticket-close refusal rule (only after the last phase or an abort).

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/orders-api-upgrade-postgres-engine-version-20261027-1600.md` | Phase 1 `https://github.com/acme/orders-infra/pull/501`, phase 2 `https://github.com/acme/orders-infra/pull/502`, phase 3 not started. Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |

## MUST

- Heads-up is at most 8 lines and lists the phases on one line, for example `3 phases: snapshot → upgrade → cleanup`, with the window `2026-10-28 22:00 ICT` for about 2h.
- Phases 2 and 3 are both pending, so the heads-up batch asks which phase(s) this window covers. With the operator's `phase 2 only`, the What line says this window covers the upgrade (phase 2), Risk is `YELLOW` (phase 2's verdict, not phase 1's `GREEN`), and a PR shown in the heads-up is `https://github.com/acme/orders-infra/pull/502`, not PR 501.
- Result says `phase 2 of 3` and shows the PR for that phase, `https://github.com/acme/orders-infra/pull/502`, not PR 501.
- Result states the current state (phase 3 still to do), not that the whole change is finished.
- Ticket-close is **refused** with the reason: it is not the last phase and the change was not aborted. No ticket-close draft is produced.

## MUST-NOT

- A ticket-close draft.
- A result wording that implies the whole change completed.
- An apply claim for phase 2 sourced from the record (the operator supplies it).
