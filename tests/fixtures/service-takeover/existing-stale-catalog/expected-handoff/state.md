---
state-schema: 2
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
run-started-at: 2026-05-12T14:00:00Z
run-completed-at: 2026-05-12T16:10:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — payments takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-12T14:00:00Z
- **Run completed:** 2026-05-12T16:10:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `payments`, account 123456789012, region us-east-1, intent `takeover`; Pay Team -> Platform Team; handoff 2026-06-15

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-12T14:00:00Z | 2026-05-12T14:03:00Z | alice at 2026-05-12T14:03:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-12T14:03:00Z | 2026-05-12T14:12:00Z | alice approved plan at 2026-05-12T14:12:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagrams + live APIs) | done | 2026-05-12T14:12:00Z | 2026-05-12T14:30:00Z | alice at 2026-05-12T14:30:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-12T14:30:00Z | 2026-05-12T14:33:00Z | alice at 2026-05-12T14:33:00Z |
| 4 | Runtime profile — `runtime-trace` (its own 7 gates: 1, 1a, 2–6) | done | 2026-05-12T14:33:00Z | 2026-05-12T15:05:00Z | alice at 2026-05-12T15:05:00Z |
| 5 | Interview — emit questionnaire; ingest filled version | done | 2026-05-12T15:05:00Z | 2026-05-12T15:45:00Z | alice at 2026-05-12T15:45:00Z; sections: 11 complete / 0 partial / 0 empty |
| 6 | Readiness scorecard — auto-mark, Step 6 verification batch, attestations | done | 2026-05-12T15:45:00Z | 2026-05-12T16:05:00Z | alice at 2026-05-12T16:05:00Z; verdict: partial |
| 7 | Handoff package assembly | done | 2026-05-12T16:05:00Z | 2026-05-12T16:10:00Z | alice at 2026-05-12T16:10:00Z |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-12T14:33:00Z | copied as-is; `service-discovery-schema: 1`; `Live verification: performed 2026-05-12` |
| prior service-discovery catalog (kept for the drift check) | service-catalog.2026-04-28.md | 2026-05-12T14:12:00Z | copied from `.culiops/service-discovery/payments-catalog.md` (generated 2026-04-28T15:00:00Z); the sibling file is untouched |
| runtime-trace profile | runtime-profile.md | 2026-05-12T15:05:00Z | copied as-is; `runtime-profile-schema: 2` |
| Filled interview | interview-questionnaire.md | 2026-05-12T15:45:00Z | snapshot of `filled-interview.md` (variant B) |
| Readiness scorecard | readiness-scorecard.md | 2026-05-12T16:05:00Z | authored by the skill |
| Open questions | open-questions.md | 2026-05-12T16:05:00Z | authored by the skill |
| Execution plan | execution-plan.md | 2026-05-12T14:12:00Z | existing-catalog decision recorded in the plan |
| Handoff README | README.md | 2026-05-12T16:10:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `payments`, account 123456789012, region us-east-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.2026-04-28.md | 123456789012 | us-east-1 | payments | yes | 14 d (generated 2026-04-28T15:00Z) | use / verify / re-run offered at Step 1.5 (Iron Law); operator chose re-run |
| service-catalog.md | 123456789012 | us-east-1 | payments | yes | 3 min (generated 14:30Z, snapshotted 14:33Z) | the new catalog replaced the stale one; < 30 d |
| runtime-profile.md | 123456789012 | us-east-1 | payments | yes | 5 min (generated 15:00Z, snapshotted 15:05Z) | none (< 30 d) |
| catalog vs profile | — | — | — | yes: catalog inventory (8 names) = profile resolved set (8 names) | — | — |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-12T14:05:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region us-east-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-12T14:06:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in us-east-1: yes | 2026-05-12T14:07:00Z |

---

## Drift: prior catalog vs new catalog

| Resource | 2026-04-28 (5) | 2026-05-12 (8) | Drift |
|---|---|---|---|
| `payments-authorizer`, `payments-capture`, `payments-reconciler` | present | present | none |
| `payments-capture-queue`, `payments-ledger` | present | present | none (notes enriched) |
| `payments-capture-dlq` | absent | present | **new** (the old caveat says secrets were untagged then; the DLQ was not listed) |
| `payments/stripe-api-key`, `payments/db-encryption-key` | absent | present | **new** (old catalog: secrets untagged at discovery time) |

---

## Audit trail

```
2026-05-12T14:00:00Z  Step 1 started — operator inputs accepted
2026-05-12T14:03:00Z  Step 1 gate sign-off by alice
2026-05-12T14:03:00Z  Step 1.5 started — information audit
2026-05-12T14:04:00Z  Existing artifact detected: .culiops/service-discovery/payments-catalog.md (service-discovery, generated-at 2026-04-28T15:00:00Z, 14 days old, 5 resources). Read-only for this skill: never renamed, moved or edited
2026-05-12T14:05:00Z  Probe identity-probe-result: caller account matches intake (derived fact only)
2026-05-12T14:06:00Z  Probe cloudtrail-event-history: Event history readable (lookup-events --max-results 1; derived fact only)
2026-05-12T14:07:00Z  Probe resource-explorer-index: aggregator index present in us-east-1 (derived fact only)
2026-05-12T14:09:00Z  Execution plan emitted to execution-plan.md
2026-05-12T14:12:00Z  Step 1.5 gate sign-off by alice — plan approved
2026-05-12T14:12:00Z  Step 2 started — ONE service-discovery delegation printed (real-discovery: 2 diagrams + live APIs)
2026-05-12T14:12:00Z  Existing catalog: operator chose (C) re-run; prior catalog copied INTO the takeover directory as service-catalog.2026-04-28.md (sibling file untouched)
2026-05-12T14:30:00Z  Step 2 completed — operator returned .culiops/service-discovery/payments-prod.md; Gate 2 sign-off by alice
2026-05-12T14:30:00Z  Step 3 started — catalog snapshot validation
2026-05-12T14:33:00Z  Same-target check (catalog): account/region/service = intake; age 3 min; Live verification performed -> OK
2026-05-12T14:33:00Z  Step 3 completed — snapshot service-catalog.md; Gate 3 sign-off by alice
2026-05-12T14:33:00Z  Same-target check (prior catalog copy): account/region/service = intake; age 14 d (< 30 d)
2026-05-12T14:33:00Z  Drift check, prior (5 resources) vs new (8): +3 (payments-capture-dlq, payments/stripe-api-key, payments/db-encryption-key), -0, changed 0 among the 5 common names -> open question
2026-05-12T14:33:00Z  Step 4 started — runtime-trace invocation printed (tag:service=payments, intent takeover, --redact not set)
2026-05-12T15:05:00Z  Same-target check (profile): account/region/service = intake; age 5 min; resolved set = catalog inventory (8 = 8) -> OK
2026-05-12T15:05:00Z  Step 4 completed — snapshot runtime-profile.md (schema 2); Gate 4 sign-off by alice
2026-05-12T15:05:00Z  Step 5 started — questionnaire emitted; awaiting outgoing team
2026-05-12T15:40:00Z  Filled interview received from Bob L. (Pay Team) — filled-interview.md
2026-05-12T15:45:00Z  Step 5 ingest: 11 complete / 0 partial / 0 empty; Gate 5 sign-off by alice
2026-05-12T15:45:00Z  Step 6 started — auto-marking scorecard from artifacts
2026-05-12T15:46:00Z  Operator confirmed deploy role payments-deploy-role (item 2: ◐ -> ✓ verified)
2026-05-12T15:48:00Z  Step 6 verification batch proposed: 3 read-only AWS commands (items 10, 24, 15) + artifact comparisons
2026-05-12T15:50:00Z  Batch approved by alice; identity re-checked (account 123456789012)
2026-05-12T15:52:10Z  Batch 1/3 describe-alarms: 5 alarms, names match the interview, all with actions -> item 10 ✓ verified
2026-05-12T15:52:40Z  Batch 2/3 describe-continuous-backups: PITR ENABLED -> item 24 stays ◐ (restore test unattested)
2026-05-12T15:53:20Z  Batch 3/3 simulate-principal-policy for platform-team-deploy: 6/6 allowed -> item 15 ✓ verified
2026-05-12T15:58:00Z  Item 3 attested by alice (console + CLI)
2026-05-12T16:00:00Z  Item 11 attested by alice (PagerDuty rotation visible)
2026-05-12T16:02:00Z  Item 12 attested by alice (test page received)
2026-05-12T16:05:00Z  Scorecard written: 15 ✓ verified, 3 ✓ attested, 6 ◐, 0 ✗, 1 ✗ conflict, 0 ?, 0 N/A. Verdict: partial
2026-05-12T16:05:00Z  Step 6 gate sign-off by alice
2026-05-12T16:05:00Z  Step 7 started — handoff package assembly
2026-05-12T16:10:00Z  Handoff package assembled: 9 files (5 written by the skill in expected-handoff/; 4 snapshots: new catalog, prior catalog copy, runtime profile, interview)
2026-05-12T16:10:00Z  Reminder printed: private repo only; check branch and remote visibility before committing
2026-05-12T16:10:00Z  Step 7 gate sign-off by alice. Run complete
```
