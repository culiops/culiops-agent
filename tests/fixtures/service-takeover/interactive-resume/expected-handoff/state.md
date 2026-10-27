---
state-schema: 2
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
run-started-at: 2026-05-05T09:00:00Z
run-completed-at: 2026-05-12T10:05:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — payments takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-05T09:00:00Z
- **Run completed:** 2026-05-12T10:05:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `payments`, account 123456789012, region us-east-1, delivery model: CI/CD pipeline (GitHub Actions, on merge); intent `takeover`; Pay Team -> Platform Team; handoff 2026-06-15

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-05T09:00:00Z | 2026-05-05T09:05:00Z | alice at 2026-05-05T09:05:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-05T09:05:00Z | 2026-05-05T09:20:00Z | alice approved plan at 2026-05-05T09:20:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagrams + live APIs) | done | 2026-05-05T09:20:00Z | 2026-05-05T10:20:00Z | alice at 2026-05-05T10:20:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-05T10:20:00Z | 2026-05-05T10:30:00Z | alice at 2026-05-05T10:30:00Z; session paused at Gate 4 (Day 1) |
| 4 | Runtime profile — `runtime-trace` (its own 7 gates: 1, 1a, 2–6) | done | 2026-05-12T08:05:00Z | 2026-05-12T08:35:00Z | alice at 2026-05-12T08:35:00Z (Day 7) |
| 5 | Interview — emit questionnaire; ingest filled version | done | 2026-05-12T08:35:00Z | 2026-05-12T09:15:00Z | alice at 2026-05-12T09:15:00Z; sections: 11 complete / 0 partial / 0 empty |
| 6 | Readiness scorecard — auto-mark, Step 6 verification batch, attestations | done | 2026-05-12T09:15:00Z | 2026-05-12T09:40:00Z | alice at 2026-05-12T09:40:00Z; verdict: not-ready |
| 7 | Handoff package assembly | done | 2026-05-12T09:40:00Z | 2026-05-12T10:05:00Z | alice at 2026-05-12T10:05:00Z |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-05T10:30:00Z | copied as-is on Day 1; `service-discovery-schema: 1`; `Live verification: performed 2026-05-05` |
| runtime-trace profile | runtime-profile.md | 2026-05-12T08:35:00Z | copied as-is; `runtime-profile-schema: 2` |
| Filled interview | interview-questionnaire.md | 2026-05-12T09:15:00Z | snapshot of `filled-interview.md` (variant B) |
| Readiness scorecard | readiness-scorecard.md | 2026-05-12T09:40:00Z | authored by the skill |
| Open questions | open-questions.md | 2026-05-12T09:40:00Z | authored by the skill |
| Execution plan | execution-plan.md | 2026-05-05T09:20:00Z | Day-1 plan; Day-7 resume + Step 6 addenda |
| Handoff README | README.md | 2026-05-12T10:05:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `payments`, account 123456789012, region us-east-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.md (Day 1 snapshot) | 123456789012 | us-east-1 | payments | yes | 10 min (generated 2026-05-05T10:20Z, snapshotted 10:30Z) | none on Day 1 (no pre-existing artifact) |
| service-catalog.md (Day 7 resume) | 123456789012 | us-east-1 | payments | yes | 7 d (generated 2026-05-05T10:20Z) | resume rule: use / verify / re-run offered; operator chose use as-is; age recorded |
| runtime-profile.md | 123456789012 | us-east-1 | payments | yes | 5 min (generated 2026-05-12T08:30Z, snapshotted 08:35Z) | none (< 30 d) |
| catalog vs profile | — | — | — | yes: catalog inventory (8 names) = profile resolved set (8 names), 7 days apart | — | — |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-05T09:08:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region us-east-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-05T09:09:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region us-east-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in us-east-1: yes | 2026-05-05T09:10:00Z |
| identity-probe-recheck-resume | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes (Day 7) | 2026-05-12T08:02:00Z |

---

## Audit trail

```
2026-05-05T09:00:00Z  Step 1 started — operator inputs accepted
2026-05-05T09:05:00Z  Step 1 gate sign-off by alice
2026-05-05T09:05:00Z  Step 1.5 started — information audit
2026-05-05T09:08:00Z  Probe identity-probe-result: caller account matches intake (derived fact only)
2026-05-05T09:09:00Z  Probe cloudtrail-event-history: Event history readable (lookup-events --max-results 1; derived fact only)
2026-05-05T09:10:00Z  Probe resource-explorer-index: aggregator index present in us-east-1 (derived fact only)
2026-05-05T09:12:00Z  Execution plan emitted to execution-plan.md
2026-05-05T09:20:00Z  Step 1.5 gate sign-off by alice — plan approved
2026-05-05T09:20:00Z  Step 2 started — ONE service-discovery delegation printed (real-discovery: 2 diagrams + live APIs)
2026-05-05T10:20:00Z  Step 2 completed — operator returned .culiops/service-discovery/payments-catalog.md; Gate 2 sign-off by alice
2026-05-05T10:20:00Z  Step 3 started — catalog snapshot validation
2026-05-05T10:30:00Z  Same-target check (catalog): account/region/service = intake; age 10 min; Live verification performed 2026-05-05 -> OK
2026-05-05T10:30:00Z  Step 3 completed — snapshot service-catalog.md; Gate 3 sign-off by alice
2026-05-05T10:30:00Z  Step 4 invocation printed (runtime-trace); operator typed "pause" — session paused at Gate 4. State written.
2026-05-12T08:00:00Z  Operator re-invoked service-takeover for payments. state.md read first; no intake re-entered. Resume point confirmed by operator: Step 4
2026-05-12T08:02:00Z  Probe identity-probe-result (re-check on resume): caller account matches intake (derived fact only)
2026-05-12T08:03:00Z  Existing artifact on resume: service-catalog.md (generated 2026-05-05T10:20:00Z, 7 days old). Offered use as-is / verify / re-run (resume rule). Operator chose USE AS-IS; age (7 d) recorded here and in the scorecard note
2026-05-12T08:05:00Z  Step 4 started — runtime-trace invocation printed (from the saved execution plan)
2026-05-12T08:35:00Z  Same-target check (profile): account/region/service = intake; age 5 min; resolved set = catalog inventory (8 = 8) -> OK
2026-05-12T08:35:00Z  Step 4 completed — snapshot runtime-profile.md (schema 2); Gate 4 sign-off by alice
2026-05-12T08:35:00Z  Step 5 started — questionnaire emitted; awaiting outgoing team
2026-05-12T09:10:00Z  Filled interview received from Bob L. (Pay Team) — filled-interview.md
2026-05-12T09:15:00Z  Step 5 ingest: 11 complete / 0 partial / 0 empty; Gate 5 sign-off by alice
2026-05-12T09:15:00Z  Step 6 started — auto-marking scorecard from artifacts
2026-05-12T09:16:00Z  Operator confirmed deploy role payments-deploy-role (item 2: ◐ -> ✓ verified)
2026-05-12T09:18:00Z  Step 6 verification batch proposed: 4 read-only AWS commands (items 10, 24, 15 x2) + artifact comparisons
2026-05-12T09:20:00Z  Batch approved by alice; identity re-checked (account 123456789012)
2026-05-12T09:22:10Z  Batch 1/4 describe-alarms: 4 of 5 named alarms exist, enabled, state OK; payments-latency-p99 absent -> item 10 ✗ conflict
2026-05-12T09:22:40Z  Batch 2/4 describe-continuous-backups: PITR ENABLED -> item 24 stays ◐ (restore test has no record)
2026-05-12T09:23:20Z  Batch 3/4 simulate-principal-policy for platform-team-deploy: 6/6 allowed
2026-05-12T09:23:40Z  Batch 4/4 get-context-keys-for-principal-policy for platform-team-deploy: empty list (no unresolved condition key) -> item 15 ✓ verified
2026-05-12T09:30:00Z  Item 3 attested by alice (console + CLI)
2026-05-12T09:32:00Z  Item 11 attested by alice (PagerDuty rotation visible)
2026-05-12T09:34:00Z  Item 12 attested by alice (test page received)
2026-05-12T09:40:00Z  Scorecard written: 12 ✓ verified, 3 ✓ attested, 7 ◐, 0 ✗, 2 ✗ conflict, 1 ?, 0 N/A. Verdict: not-ready. Evidence as of 2026-05-05T09:08:00Z
2026-05-12T09:40:00Z  Step 6 gate sign-off by alice
2026-05-12T09:40:00Z  Step 7 started — handoff package assembly
2026-05-12T10:05:00Z  Evidence is 41 days older than the handoff date 2026-06-15 (freshness window 7 days): offered a re-run of the Step 6 checks before assembly; alice declined and will re-run them in the week before the handoff
2026-05-12T10:05:00Z  Handoff package assembled: 8 files (5 written by the skill in expected-handoff/; 3 snapshots from mock-artifacts/ and filled-interview.md)
2026-05-12T10:05:00Z  Reminder printed: private repo only; check branch and remote visibility before committing
2026-05-12T10:05:00Z  Step 7 gate sign-off by alice. Run complete
```
