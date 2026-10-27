# Dry-run notes — interactive-resume

## What this fixture validates

- State persistence across sessions (Day 1 2026-05-05, Day 7 2026-05-12), explicit resume confirmation (never silent), no intake re-entry, merged audit trail.
- **H3 on resume:** the Day-1 catalog is 7 days old when reused. The skill offers use / verify / re-run; the operator picks use as-is; the **age is recorded** (state same-target table, plan addendum, scorecard notes on items 4 and 6). After Step 4 the profile's resolved set (8 names) is compared with the catalog inventory (8 names): no difference.
- Timestamps are coherent: the catalog is generated and snapshotted on Day 1 (`generated-at: 2026-05-05T10:20:00Z`, `Live verification: performed 2026-05-05`); the runtime profile on Day 7 (`generated-at: 2026-05-12T08:30:00Z`); the interview, scorecard and package on Day 7.
- Identity is re-probed on resume (`identity-probe-recheck-resume`).
- Strict verdict with a batch that finds a conflict: item 10 `✗ conflict` (the interview names `payments-latency-p99`; `describe-alarms` does not return it). Any `✗ conflict` makes the verdict `not-ready`, here with item 19.
- Evidence as of the Day-1 identity probe (2026-05-05T09:08Z); at Gate 7 that is 41 days before the handoff date, so the skill offers a re-run of the Step 6 checks and alice declines.
- One discovery delegation; derived-facts-only probes; runtime-trace's own 7 gates.

`mock-artifacts/service-catalog.md` and `mock-artifacts/runtime-profile.md` are the shared mock sibling artifacts (runtime-profile-schema 2; catalog with Owner/Live columns, `Live verification: performed`, Unattributed list, secrets as references). The mock Wiring section deliberately lists one configured caller the interview omits (role `legacy-orders-exec` may send to `payments-capture-queue`), so item 19 is a `✗ conflict` wherever both a profile and Section 8 exist. The interview has two variants: A (happy-path only: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) and B (all others: role permitted, 5 deploys/quarter, single-region DR).

---

## Session 1 — Day 1 (2026-05-05)

1. Operator invokes `service-takeover` for `payments`. Gate 1 (09:00-09:05Z): intake.
2. Gate 1.5 (09:05-09:20Z): probes (identity 09:08, Event history 09:09, RE index 09:10); plan emitted 09:12, approved 09:20.
3. Gates 2-3 (09:20-10:30Z): one `service-discovery` delegation; catalog returned 10:20; same-target check on snapshot (age 10 min); snapshot 10:30.
4. At Gate 4 (10:30Z) the operator types "pause". `day-1-state/state.md` is written (Steps 4-7 `pending`, pause note).

## Session 2 — Day 7 (2026-05-12)

1. 08:00Z: re-invocation. The skill reads `state.md` first and prints the Day-1 state, artifacts and the resume question (resume from Step 4 / jump / restart). Operator: "resume from Step 4". Recorded.
2. 08:02Z: identity re-check (account matches intake).
3. 08:03Z: existing artifact `service-catalog.md` (7 days old): use / verify / re-run offered; **use as-is** chosen; age recorded.
4. Gate 4 (08:05-08:35Z): runtime-trace invocation (saved from the Day-1 plan); profile generated 08:30Z; same-target check (age 5 min; resolved set = catalog inventory).
5. Gate 5 (08:35-09:15Z): questionnaire; filled interview received 09:10Z (variant B, 11 complete).
6. Gate 6 (09:15-09:40Z): deploy role confirmed (09:16); batch proposed 09:18, approved 09:20, run: alarms (4 of 5 present: item 10 `✗ conflict`), PITR `ENABLED` (item 24 `◐`), simulation 6 of 6 `allowed` plus an empty context-key list (item 15 `✓ verified`). Item 19 `✗ conflict`. Item 7 `?` (no baseline for the table), item 23 `◐` (TTL is not a period). Attestations 09:30-09:34. Verdict `not-ready`.
7. Gate 7 (09:40-10:05Z): 8 files.

---

## Fixture files

| File | Role |
|---|---|
| `input.md` | The two-session scenario |
| `day-1-state/state.md` | State at the end of Day 1 (Steps 4-7 pending, pause note) |
| `day-7-state/state.md` | State at the end of Day 7 (also `expected-handoff/state.md`) |
| `mock-artifacts/service-catalog.md` | Produced Day 1, reused Day 7 (age 7 d, recorded) |
| `mock-artifacts/runtime-profile.md` | Produced Day 7 |
| `filled-interview.md` | Variant B, received Day 7 |
| `expected-handoff/` | Package files; distinct from happy-path (marks, verdict, timestamps, plan addendum) |

## Marks

12 ✓ verified, 3 ✓ attested, 7 ◐, 0 ✗, 2 ✗ conflict, 1 ?, 0 N/A (25 items).

## Acceptance check

- Verdict `not-ready`; items 10 and 19 `✗ conflict`; both in the High section of `open-questions.md`.
- `state.md` carries both sessions' timestamps and the same-target row "7 d ... operator chose use as-is".
- No timestamp in the handoff pre-dates its source artifact or conflicts with the Day-1 / Day-7 split.

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
