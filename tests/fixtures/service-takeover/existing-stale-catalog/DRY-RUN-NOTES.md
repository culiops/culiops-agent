# Dry-run notes — existing-stale-catalog

## What this fixture validates

- Step 1.5 detects a pre-existing catalog (generated 2026-04-28T15:00:00Z, 14 days old, 5 resources) and offers three options for it (A use as-is, B thin re-scan, C re-run). Operator selects C. The offer is the Iron Law "existing artifacts first" rule; it does not depend on the 30-day age flag.
- **M1 fix:** the sibling's `payments-catalog.md` is never renamed or edited. The old snapshot is kept **inside the takeover directory** as `service-catalog.2026-04-28.md`; the re-run writes to `.culiops/service-discovery/payments-prod.md` so it cannot overwrite the sibling's file.
- **Drift check:** the old (5) and new (8) resource lists are diffed after the snapshot; +3 new rows are listed in `state.md` and become MED-1 in `open-questions.md` (were the DLQ and secrets created after 2026-04-28, or only newly tagged?).
- Same-target check also runs on the old copy (account/region/service = intake; age 14 d).
- One discovery delegation; derived-facts-only probes; strict verdict `partial`; Step 6 batch run (item 15 `✓ verified` because variant B's incoming role is permitted).

`mock-artifacts/service-catalog.md` and `mock-artifacts/runtime-profile.md` are the shared mock sibling artifacts (runtime-profile-schema 2; catalog with Owner/Live columns, `Live verification: performed`, Unattributed list, secrets as references). The mock Wiring section deliberately lists one configured caller the interview omits (role `legacy-orders-exec` may send to `payments-capture-queue`), so item 19 is a `✗ conflict` wherever both a profile and Section 8 exist. The interview has two variants: A (happy-path only: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) and B (all others: role permitted, 5 deploys/quarter, single-region DR).

---

## Gate transitions

**Gate 1** (14:00Z). As happy-path, plus the "existing catalog" note.

**Gate 1.5** (14:03Z-14:12Z). Probes as happy-path. The skill detects the existing catalog at 14:04Z and adds the existing-artifact row with options A / B / C. Operator selects C at 14:12Z.

**Pre-Gate 2 action** (14:12Z). The skill copies the old catalog into the takeover directory as `service-catalog.2026-04-28.md` (the sibling file stays where it is, untouched) and prints the new invocation with `output: .culiops/service-discovery/payments-prod.md`.

**Gates 2-3** (14:12Z-14:33Z). One delegation; same-target checks on the new catalog (age 3 min) and on the old copy (age 14 d). Drift diff: +3 / -0 / 0 changed.

**Gate 4** (14:33Z-15:05Z). As happy-path.

**Gate 5** (15:05Z-15:45Z). 11 complete (variant B interview).

**Gate 6** (15:45Z-16:05Z). Batch approved and run: alarms `✓ verified` (item 10), PITR `ENABLED` (item 24 stays `◐`), simulation 6 of 6 `allowed` (item 15 `✓ verified`). Item 18 `✓ verified` (5 deploys/quarter vs 5 runs), item 19 `✗ conflict`, item 25 `✓ verified` (single-region plan matches the footprint). Verdict `partial`.

**Gate 7** (16:05Z-16:10Z). 9 files.

---

## Marks

15 ✓ verified, 3 ✓ attested, 6 ◐, 0 ✗, 1 ✗ conflict, 0 ?, 0 N/A (25 items).

## Acceptance check

- `expected-handoff/execution-plan.md` has the existing-catalog row with all three options and the operator's choice (C).
- `expected-handoff/state.md` shows the prior-catalog copy, its same-target row, the drift table, and the audit lines; no rename event exists.
- `expected-handoff/service-catalog.2026-04-28.md` equals `preexisting/payments-catalog.md`; `mock-artifacts/service-catalog.md` has `generated-at` from today (2026-05-12).
- Verdict `partial`; `open-questions.md` lists the 3-resource drift (MED-1).

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
