# Dry-run notes — runtime-trace-skipped

## What this fixture validates

- A skipped sibling step is recorded cleanly: `skipped` (not `done`, not `failed`) with a traceable reason; no runtime profile is synthesized.
- **Scenario rescope:** the reason is an operator time-constraint choice. The earlier "Cost Explorer denied" scenario was overbroad (runtime-trace runs without Cost Explorer: only the spend section is affected, the other sources still work) and asked the operator for a Cost Explorer permission the skill never needs. Both are gone, along with the policy attribution.
- Scorecard degradation is exact: items 5, 7, 8, 9 depend only on the profile and become `?` (4 items). Items 2, 16, 18, 19 and 25 need the profile to be cross-checked, so they are `◐` rather than `✓`; item 4 is `◐` too, because without the profile's resource list the catalog's coverage cannot be compared; no `✗` and no false `✓`.
- The Step 6 batch is independent of the profile: alarms present but not covering the table or Lambda saturation (10 `◐`), simulation `allowed` plus an empty context-key list (15 `✓ verified`), PITR `ENABLED` (24 stays `◐`, no restore record). Item 1 rests on the live `service-discovery` reads, since the CloudTrail probe was not run.
- Same-target check on the catalog; one discovery delegation; the Step 1.5 probes that have no consumer are not emitted.

`mock-artifacts/service-catalog.md` and `mock-artifacts/runtime-profile.md` are the shared mock sibling artifacts (runtime-profile-schema 2; catalog with Owner/Live columns, `Live verification: performed`, Unattributed list, secrets as references). The mock Wiring section deliberately lists one configured caller the interview omits (role `legacy-orders-exec` may send to `payments-capture-queue`), so item 19 is a `✗ conflict` wherever both a profile and Section 8 exist. The interview has two variants: A (happy-path only: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) and B (all others: role permitted, 5 deploys/quarter, single-region DR).
(Here Wiring does not exist, so item 19 is `◐`, not a conflict.)

---

## Gate transitions

**Gate 1** (14:00Z). Inputs as happy-path.

**Gate 1.5** (14:03Z-14:12Z). Identity probe (derived fact: account matches intake). Operator chooses to skip runtime-trace at 14:09Z; options shown: run now / run later / skip. The plan lists the consequences for items 2, 5, 7, 8, 9, 16, 18, 19, 25. Approved 14:12Z.

**Gates 2-3** (14:12Z-14:33Z). One delegation; same-target check OK; snapshot.

**Gate 4** (14:33Z). Skipped. State row:
`| 4 | Runtime profile — runtime-trace | skipped | — | — | skipped: operator choice at Gate 1.5 (time constraint) |`
Audit line: `Step 4 SKIPPED (operator choice, Gate 1.5). No runtime-trace invocation printed; no runtime-profile.md produced or synthesized`.

**Gate 5** (14:33Z-15:10Z). Interview variant B, 11 complete.

**Gate 6** (15:10Z-15:35Z). Auto-mark with no profile; batch run; attestations of items 3, 11, 12. Verdict `partial`.

**Gate 7** (15:35Z-15:40Z). Evidence is 34 days older than the 2026-06-15 handoff date, so the skill offers a re-run of the Step 6 checks; alice declines. Package of 7 files (no runtime profile); README gate list says Gate 4 was skipped by operator choice.

---

## Marks

4 ✓ verified, 3 ✓ attested, 14 ◐, 0 ✗, 0 ✗ conflict, 4 ?, 0 N/A (25 items): 4 + 3 + 14 + 4 = 25.

## Acceptance check

- `runtime-profile.md` is absent from the package and from `mock-artifacts/`; `.runtime-trace-not-run` explains why.
- Items 5, 7, 8, 9 are `?`; the summary table rows add up to 25 and the `?` column to 4.
- `open-questions.md` has no High item (no `✗`); MED-1 is "run runtime-trace and resume at Step 4"; nothing asks for a Cost Explorer permission.

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
