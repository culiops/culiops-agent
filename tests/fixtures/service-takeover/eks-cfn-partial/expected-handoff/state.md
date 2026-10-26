---
state-schema: 2
service-takeover-version: 0.6.0
service: search-api
account: "123456789012"
region: eu-west-1
run-started-at: 2026-05-12T13:30:00Z
run-completed-at: 2026-05-12T16:00:00Z
operator: arn:aws:iam::123456789012:user/alice
---

# Workflow State — search-api takeover

## Run identity

- **Operator:** arn:aws:iam::123456789012:user/alice
- **Run started:** 2026-05-12T13:30:00Z
- **Run completed:** 2026-05-12T16:00:00Z
- **Skill version:** service-takeover v0.6.0
- **Intake:** service `search-api`, account 123456789012, region eu-west-1, intent `takeover`; Search Team -> Platform Team; handoff 2026-06-22

---

## Step status

| Step | Description | Status | Started | Completed | Gate sign-off |
|---|---|---|---|---|---|
| 1 | Intake — accept operator inputs | done | 2026-05-12T13:30:00Z | 2026-05-12T13:33:00Z | alice at 2026-05-12T13:33:00Z |
| 1.5 | Information audit — identity probe, execution plan | done | 2026-05-12T13:33:00Z | 2026-05-12T13:42:00Z | alice approved plan at 2026-05-12T13:42:00Z |
| 2 | Discovery — one `service-discovery` real-discovery delegation (diagram + AWS + Kubernetes) | done | 2026-05-12T13:42:00Z | 2026-05-12T14:28:00Z | alice at 2026-05-12T14:28:00Z |
| 3 | Discovery snapshot — validate, same-target check, snapshot | done | 2026-05-12T14:28:00Z | 2026-05-12T14:30:00Z | alice at 2026-05-12T14:30:00Z |
| 4 | Runtime profile — `runtime-trace` (its own 7 gates: 1, 1a, 2–6) | done | 2026-05-12T14:30:00Z | 2026-05-12T15:00:00Z | alice at 2026-05-12T15:00:00Z |
| 5 | Interview — emit questionnaire; ingest filled version | done | 2026-05-12T15:00:00Z | 2026-05-12T15:30:00Z | alice at 2026-05-12T15:30:00Z; sections: 11 complete / 0 partial / 0 empty |
| 6 | Readiness scorecard — auto-mark, Step 6 verification batch, attestations | done | 2026-05-12T15:30:00Z | 2026-05-12T15:55:00Z | alice at 2026-05-12T15:55:00Z; verdict: partial |
| 7 | Handoff package assembly | done | 2026-05-12T15:55:00Z | 2026-05-12T16:00:00Z | alice at 2026-05-12T16:00:00Z |

---

## Artifact paths

Package-relative names; the fixture keeps the snapshots under `mock-artifacts/` and `filled-interview.md`.

| Artifact | Package file | Snapshotted at | Notes |
|---|---|---|---|
| service-discovery catalog | service-catalog.md | 2026-05-12T14:30:00Z | copied as-is; `service-discovery-schema: 1`; `Live verification: performed 2026-05-12` |
| runtime-trace profile | runtime-profile.md | 2026-05-12T15:00:00Z | copied as-is; `runtime-profile-schema: 2`; spend = account context |
| Filled interview | interview-questionnaire.md | 2026-05-12T15:30:00Z | snapshot of `filled-interview.md` |
| Readiness scorecard | readiness-scorecard.md | 2026-05-12T15:55:00Z | authored by the skill |
| Open questions | open-questions.md | 2026-05-12T15:55:00Z | authored by the skill |
| Execution plan | execution-plan.md | 2026-05-12T13:42:00Z | Step 6 addendum added at 2026-05-12T15:33:00Z |
| Handoff README | README.md | 2026-05-12T16:00:00Z | authored by the skill |

---

## Same-target checks (run at every snapshot)

Each snapshot is compared with the intake values (service `search-api`, account 123456789012, region eu-west-1) and its age is recorded against the snapshot time. A mismatch stops the run; an age over 30 days, or any artifact reused on resume, triggers the use / verify / re-run offer.

| Artifact | Account | Region | Service | Matches intake | Age at snapshot | Offer |
|---|---|---|---|---|---|---|
| service-catalog.md | 123456789012 | eu-west-1 | search-api (context platform-eks, ns search) | yes | 2 min (generated 14:28Z, snapshotted 14:30Z) | none (< 30 d) |
| runtime-profile.md | 123456789012 | eu-west-1 | search-api | yes | 2 min (generated 14:58Z, snapshotted 15:00Z) | none (< 30 d) |
| catalog vs profile | — | — | — | yes: catalog AWS rows (7) = profile resolved set (7) | — | — |

---

## Step 1.5 probe results (derived facts only — raw command output is never recorded)

| Probe | Command (projected) | Derived fact | Timestamp |
|---|---|---|---|
| identity-probe-result | `aws sts get-caller-identity --profile prod-main --query Account` | caller account = intake account (123456789012): yes | 2026-05-12T13:35:00Z |
| cloudtrail-event-history | `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region eu-west-1 --query 'Events[0].EventTime'` | Event history readable: yes | 2026-05-12T13:36:00Z |
| resource-explorer-index | `aws resource-explorer-2 list-indexes --profile prod-main --region eu-west-1 --query 'Indexes[].{Region:Region,Type:Type}'` | aggregator index in eu-west-1: yes | 2026-05-12T13:37:00Z |

---

## Audit trail

```
2026-05-12T13:30:00Z  Step 1 started — operator inputs accepted
2026-05-12T13:33:00Z  Step 1 gate sign-off by alice
2026-05-12T13:33:00Z  Step 1.5 started — information audit
2026-05-12T13:35:00Z  Probe identity-probe-result: caller account matches intake (derived fact only)
2026-05-12T13:36:00Z  Probe cloudtrail-event-history: Event history readable in eu-west-1 (lookup-events --max-results 1; derived fact only)
2026-05-12T13:37:00Z  Probe resource-explorer-index: aggregator index present in eu-west-1 (derived fact only)
2026-05-12T13:40:00Z  Execution plan emitted to execution-plan.md
2026-05-12T13:42:00Z  Step 1.5 gate sign-off by alice — plan approved
2026-05-12T13:42:00Z  Step 2 started — ONE service-discovery delegation printed (real-discovery: 1 diagram + live AWS APIs + kube context platform-eks, namespace search)
2026-05-12T14:28:00Z  Step 2 completed — operator returned .culiops/service-discovery/search-api-prod.md; Gate 2 sign-off by alice
2026-05-12T14:28:00Z  Step 3 started — catalog snapshot validation
2026-05-12T14:30:00Z  Same-target check (catalog): account/region/service = intake; cluster context platform-eks; age 2 min; Live verification performed -> OK
2026-05-12T14:30:00Z  Ownership recognised from the catalog: 5 rows cloudformation (search-data-stack | search-iam-stack), 3 helm search-api. Recorded; no action taken
2026-05-12T14:30:00Z  Step 3 completed — snapshot service-catalog.md; Gate 3 sign-off by alice
2026-05-12T14:30:00Z  Step 4 started — runtime-trace invocation printed (scoping: the catalog AWS resource set; no tag -> spend will be account context; intent takeover)
2026-05-12T15:00:00Z  Same-target check (profile): account/region/service = intake; age 2 min; resolved set (7) = catalog AWS rows (7) -> OK. Profile records "EKS in-cluster workloads not traced" as a gap
2026-05-12T15:00:00Z  Step 4 completed — snapshot runtime-profile.md (schema 2); Gate 4 sign-off by alice
2026-05-12T15:00:00Z  Step 5 started — questionnaire emitted (incl. 4b IaC & ownership); awaiting outgoing team
2026-05-12T15:25:00Z  Filled interview received from Lena M. (Search Team) — filled-interview.md
2026-05-12T15:30:00Z  Step 5 ingest: 11 complete / 0 partial / 0 empty; Gate 5 sign-off by alice
2026-05-12T15:30:00Z  Step 6 started — auto-marking scorecard from artifacts
2026-05-12T15:32:00Z  Step 6 verification batch proposed: 2 read-only AWS commands (items 10, 24)
2026-05-12T15:33:00Z  Batch approved by alice; identity re-checked (account 123456789012)
2026-05-12T15:35:10Z  Batch 1/2 describe-alarms: 4 alarms, names match the interview, all with actions -> item 10 ✓ verified
2026-05-12T15:35:40Z  Batch 2/2 describe-replication-groups: SnapshotRetentionLimit 7 -> item 24 stays ◐ (restore test unattested)
2026-05-12T15:38:00Z  Operator opened 3 runbook links, the rollback runbook and the postmortem (items 13, 14, 17: ◐ -> ✓ verified)
2026-05-12T15:42:00Z  Item 3 attested by alice (console + CLI)
2026-05-12T15:44:00Z  Item 11 attested by alice (PagerDuty rotation visible)
2026-05-12T15:46:00Z  Item 12 attested by alice (test page received)
2026-05-12T15:55:00Z  Scorecard written: 12 ✓ verified, 3 ✓ attested, 8 ◐, 0 ✗, 0 ✗ conflict, 1 ?, 1 N/A. Verdict: partial
2026-05-12T15:55:00Z  Step 6 gate sign-off by alice
2026-05-12T15:55:00Z  Step 7 started — handoff package assembly
2026-05-12T16:00:00Z  Handoff package assembled: 8 files (5 written by the skill in expected-handoff/; 3 snapshots from mock-artifacts/ and filled-interview.md)
2026-05-12T16:00:00Z  Reminder printed: private repo only; check branch and remote visibility before committing
2026-05-12T16:00:00Z  Step 7 gate sign-off by alice. Run complete
```
