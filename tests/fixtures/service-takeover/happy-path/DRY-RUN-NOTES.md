# Dry-run notes — happy-path

## What this fixture validates

- All eight gates fire in order (1, 1.5, 2, 3, 4, 5, 6, 7), each with operator approval. Gates 2-3 are **one** `service-discovery` delegation (real-discovery from the diagrams plus live APIs): there is no separate diagram catalog and live catalog that overwrite each other.
- A **same-target check** runs at every snapshot (account, region, service against intake, plus artifact age) and again compares the catalog inventory with the profile's resolved set.
- Step 1.5 probes record **derived facts only**: identity (`sts get-caller-identity --query Account` = intake account; this is item 1), CloudTrail Event history (`lookup-events --max-results 1`, not `describe-trails`), Resource Explorer index.
- The strict verdict: even with every interview section answered, items are at most `◐` until checked. The **Step 6 verification batch** (3 read-only AWS commands, approved, projected) turns `◐` into `✗` (item 15) or leaves it `◐` (item 10: the 5 alarms are enabled with actions but do not cover the table or Lambda saturation; item 24: PITR enabled, restore test has no record).
- The **conflict check** catches what the interview alone would have passed: deploy frequency (item 18), an unlisted upstream sender (item 19), a DR plan to a Region with nothing in it (item 25).
- Item 5 passes only because the profile states all four cross-Region checks; item 9 means managing principals, and callers come from Wiring (item 19).
- Presence is not coverage: item 4 passes because the Unattributed rows are dispositioned and every profile resource is in the catalog; item 7 is `?` because DynamoDB `payments-ledger` has no baseline row; item 10 is `◐` because alarms exist on only part of the service; item 23 is `◐` because a TTL attribute is not a retention period.
- Gate 7: evidence is as of 14:05Z, 34 days before the 2026-06-15 handoff date, so the skill offers a re-run of the Step 6 checks; alice declines.
- Package: 8 files (5 written by the skill in `expected-handoff/`; 3 snapshots: `mock-artifacts/service-catalog.md`, `mock-artifacts/runtime-profile.md`, `filled-interview.md`).

`mock-artifacts/service-catalog.md` and `mock-artifacts/runtime-profile.md` are the shared mock sibling artifacts (runtime-profile-schema 2; catalog with Owner/Live columns, `Live verification: performed`, Unattributed list, secrets as references). The mock Wiring section deliberately lists one configured caller the interview omits (role `legacy-orders-exec` may send to `payments-capture-queue`), so item 19 is a `✗ conflict` wherever both a profile and Section 8 exist. The interview has two variants: A (happy-path only: incoming role not yet permitted, 3-5 deploys/week, DR to us-west-2) and B (all others: role permitted, 5 deploys/quarter, single-region DR).

---

## Gate transitions

**Gate 1** (14:00Z). Operator supplies the inputs in `input.md`. Skill accepts.

**Gate 1.5** (14:03Z-14:12Z). Probes run with projected `--query`: `identity-probe-result` (caller account = 123456789012), Event history readable, aggregator index present. Only the derived facts go to `state.md`. Plan emitted; operator replies "plan approved".

**Gate 2** (14:12Z-14:30Z). The skill prints one `service-discovery` invocation (real-discovery; inputs: the two PNGs and the live account). The operator runs it and returns `.culiops/service-discovery/payments-catalog.md`.

**Gate 3** (14:30Z-14:33Z). Snapshot validation. Same-target check: catalog account 123456789012 / us-east-1 / payments = intake; age 3 minutes; `Live verification: performed`. Snapshot written to the package.

**Gate 4** (14:33Z-15:05Z). The skill prints the `runtime-trace` invocation (scoping `tag:service=payments`, intent `takeover`, `--redact` not set). The operator runs it (7 gates of its own, $0.0303). Same-target check: account/region/service = intake; age 5 minutes; the profile's 8 resolved resources = the catalog's 8 inventory names.

**Gate 5** (15:05Z-15:45Z). Questionnaire emitted; Bob and Carol fill all 11 sections (incl. 4b IaC & ownership and the incoming role ARN). Ingest: 11 complete / 0 partial / 0 empty.

**Gate 6** (15:45Z-16:05Z).
- Auto-mark from artifacts and interview: nothing from the interview alone is better than `◐`.
- Operator confirms `payments-deploy-role` as the deploy role (item 2: `◐` to `✓ verified`).
- Step 6 batch proposed at 15:48Z, approved 15:50Z, identity re-checked, run: `describe-alarms` (5 alarms, all with actions: item 10 `✓ verified`); `describe-continuous-backups` (`ENABLED`: item 24 stays `◐`); `simulate-principal-policy` for `platform-team-deploy` (6 of 6 `implicitDeny`: item 15 `✗`). Artifact comparisons: items 6, 20 `✓ verified`; items 18, 19 `✗ conflict`.
- Item 25: interview says active-passive to us-west-2; Resource Explorer (complete, tag-visible) shows nothing outside us-east-1 and the interview says cross-region backup is not enabled: `✗ conflict`.
- Operator attests items 3, 11, 12.
- Verdict `not-ready`: `✗` / `✗ conflict` in Deploy & Rollback (15, 18), Dependencies (19) and Compliance (25). Evidence as of 2026-05-12T14:05:00Z.

**Gate 7** (16:05Z-16:10Z). Package assembled; the private-repo reminder is printed (check branch and remote visibility before committing).

---

## Marks

9 ✓ verified, 3 ✓ attested, 8 ◐, 1 ✗, 3 ✗ conflict, 1 ?, 0 N/A (25 items). Per-item detail with citations is in the scorecard.

---

## Acceptance check

A reviewer steps through `input.md`, `mock-artifacts/`, `filled-interview.md`, then confirms the skill would produce `expected-handoff/` with representative results (timestamps and operator names vary).

- `expected-handoff/readiness-scorecard.md`: verdict `not-ready` for any run with this input set; counts as above; items 15, 18, 19, 25 are the failing items; 7 is `?`; 10 and 23 are `◐` beside 13, 14, 17, 21, 22, 24.
- `expected-handoff/open-questions.md`: 4 High, 9 Medium, 1 Low; every question in the README's top 5 appears there under the same ID.
- `expected-handoff/state.md`: all steps `done`; probe table holds derived facts only; same-target table has the catalog, profile and cross-artifact rows.
- `expected-handoff/execution-plan.md`: approved; a single discovery delegation; the Step 6 batch recorded as an addendum.

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
