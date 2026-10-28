# Ledger: payments-worker prod 20261024-1128

Mode: Fast
Budget used: 37 commands (30 backend read calls, 7 local checks); budgets.fast not set in environment.md, so no totals to compare · 0 GB Logs Insights scanned (no Logs Insights query run; ask threshold 10 GB) · 8 CloudWatch metric requests · no other metered units

## Problem

| Field | Value |
|---|---|
| What | Reporter: "payments-worker pods in prod keep restarting and payments are queueing up." Measurable restatement: pods of Deployment `payments-worker` in namespace `payments` restart repeatedly (CrashLoopBackOff), and the `payments-jobs` SQS backlog grows. |
| Where | service payments-worker, environment prod, cluster `prod`, namespace `payments`, 3 replicas (all in scope); queue `payments-jobs` and its DLQ. |
| When | Reported: "now" (no time given); assumed now = 2026-10-24 11:28 UTC (13:28 local). True onset: about 10:52 UTC (12:52 local), the Helm revision 31 rollout; see Timeline. |
| Who is affected | Consumers of `payments-jobs`: payment capture and refund processing (core flow in environment.md). End-user impact not measured (no SLO, APM or payment metric). |
| Trigger | Chat request from the operator; no alarm, ticket or link. |
| Mitigations already applied | none known (operator did not mention any). |
| Assumptions made at intake | (1) No onset given and Fast mode: window = last two hours, 2026-10-24 09:28Z to 11:28Z. (2) `date -u` printed nothing in this environment; "now" is taken as 11:28:00 UTC on 2026-10-24, the reference time of the kubectl event ages. (3) Local zone Europe/Paris from environment.md (UTC+2 until 2026-10-25 01:00 UTC). (4) `git rev-parse --show-toplevel` printed nothing; the working directory is treated as the repo root, so the output root is `.culiops/sre-investigate/`. (5) Wave start times are not recorded (clock call empty); all waves ran at about 11:28 UTC. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| `prod-ops` | account 111122223333 (matches environment.md), role PlatformOperator | write allowed: s3:PutObject, ecs:UpdateService (boxed warning shown) | Simulation reply did not contain rows for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (see Gaps) and contained rows for three actions not requested (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy, all implicitDeny). Session name not recorded. No token-based backend is listed, so no token variables checked. Culibox: `command -v agentbox-env` failed, nothing printed. |
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` | Kubernetes user is the same assumed role (PlatformOperator), groups `eks-readonly`, `system:authenticated` | no write verbs in `payments` (only the default create on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews, which do not count) | Rule `*.*` allows get, list, watch, which includes Secrets; the run never reads Secret objects. `kubectl config current-context` equals this context. |

## Impact

| Field | Value |
|---|---|
| Symptom | 0 of 3 payments-worker pods ready (all CrashLoopBackOff, 11 restarts each); `payments-jobs` backlog rising by about 197 messages per minute since about 10:53 UTC; DLQ stays at 0. |
| Affected | prod / `payments` namespace, all three replicas; the payment capture and refund flow handled by payments-worker (core flow, customer-facing). Backlog 5,989 at 11:25 UTC against 10-30 before 10:50. |
| Since / ongoing | about 10:52 UTC (12:52 local) · ongoing: yes |
| Suggested severity | SEV1 because a customer-facing core flow (payment capture and refunds) is fully stopped: no worker is ready. The incident owner decides. |
| Basis | W1-Q1, W1-Q6, W1-Q10, PB-Q1 · Confirmed for "all workers down, queue not consumed"; Assumed for what customers see (delay or failure): no SLO, APM, payment-throughput or oldest-message-age data (W1-Q11 returned an empty reply). |
| Third party in the path | none known; the ledger API is an internal service (owner not recorded). |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-24 09:28 | 2026-10-24 11:28 |
| Baseline (previous) | 2026-10-24 07:28 | 2026-10-24 09:28 |
| Baseline (-7d) | 2026-10-17 09:28 | 2026-10-17 11:28 |

The Fast default window starts 84 minutes before the onset; the points 10:30-10:50 inside it serve as the in-window baseline.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not applicable: no alarm triggered the run; no alarm named in environment.md |
| Signal, 14d at 1h resolution | `payments-jobs` ApproximateNumberOfMessagesVisible, Maximum per hour (saturation signal) · the 14-day pull returned an empty reply (W1-Q9), so no median, p95 or maximum · only 10:30-11:25 on the day exists (W1-Q6): 10-30 before 10:50, 5,989 at 11:25 |
| Coverage | CloudWatch queue depth: 55 minutes (10:30-11:25 UTC) of the requested 14 days; previous window, -7d window and 14d pull all empty (W1-Q7, Q8, Q9). Alarm history: none. Rollout history: Helm revisions 30 (2026-10-13) and 31; ReplicaSet and Deployment revisions 14 and 15. |
| Class | unclassified · shape: ramp in backlog (constant slope) following a step in consumption at the 10:52 rollout |
| Reason | The rules need a 30-day alarm history or the 14-day signal; neither exists. Indirect evidence: rev 30 ran 11 days with a backlog of 10-30 messages (ReplicaSet age W1-Q4, queue W1-Q6), and no CronJobs exist in `payments` (W2-Q7), so a schedule is not suggested. Recorded as a gap. |
| Label and queries | Assumed (class), W1-Q6, W1-Q7, W1-Q8, W1-Q9, W2-Q7 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-13 15:22:47 | Commit 27c4e91 in payments-deploy: adds `--ledger-retry-budget=3` container arg (#361) | git | W2-Q6, W3-Q1 |
| 2026-10-13 15:40:02 | Helm revision 30 deployed (chart payments-worker-2.3.1, app 5.2.0); this ReplicaSet `payments-worker-84c1e9d3f5` then ran 11 days | helm | W1-Q5, W1-Q4 |
| 2026-10-24 10:41:41 | Commit d81e4b7 in payments-deploy: renames the ledger endpoint config key in values-prod.yaml (#377) | git | W2-Q6, W3-Q1 |
| 2026-10-24 10:30-10:50 | `payments-jobs` backlog 10-30 messages, DLQ 0 | CloudWatch | W1-Q6, W1-Q10 |
| 2026-10-24 10:52:20 | Helm revision 31 deployed (same chart version and app version as rev 30) | helm | W1-Q5, PB-Q5 |
| 2026-10-24 10:52:33 | pod `payments-worker-6d4f8a2b7c-3mfk8` started on its node | kubectl describe | W2-Q1 |
| 2026-10-24 about 10:53 | Events: new ReplicaSet `6d4f8a2b7c` scaled to 3, old `84c1e9d3f5` scaled to 0 from 3, three old pods killed, three new pods Scheduled on three different nodes (ages "35m" against 11:28) | kubectl events | W1-Q2, W1-Q4 |
| 2026-10-24 10:55 | backlog 74 (first rise); 11:00 1,060; then +986 per 5 minutes | CloudWatch | W1-Q6 |
| 2026-10-24 11:25:56 | latest crash of pod `3mfk8`: starts and exits with code 1 in the same second; fatal config error in the previous-container log | kubectl | W2-Q1, W2-Q2 |
| 2026-10-24 11:25 | backlog 5,989; 11 restarts per pod | CloudWatch, kubectl | W1-Q6, W1-Q1 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The Helm revision 31 rollout removed the ConfigMap key LEDGER_API_BASE_URL (renamed to LEDGER_BASE_URL); the 5.2.0 worker requires LEDGER_API_BASE_URL at startup, so every new pod exits 1 during config load | crash loop from the rollout minute; previous-container log names the missing variable; live ConfigMap lacks that key; values diff shows the rename; old pods (old template) were healthy | onset earlier than 10:52 refutes it (queue flat until 10:50: not refuted); a different error in the previous log, or old pods also crashing, refutes it | main | supported: Confirmed |
| H2 | Image pull or scheduling failure | pods Pending, ErrImagePull, FailedScheduling | pod events (W1-Q2): pods Scheduled, image already present, container Started | main | Ruled out |
| H3 | Memory or CPU limits: OOM kill | Reason OOMKilled, exit code 137 | `describe pod` last state (W2-Q1): Reason Error, exit code 1, limit 256Mi | main | Ruled out |
| H4 | Probe failures killing or isolating pods | Unhealthy events; liveness or readiness failing while the process is up | events (W1-Q2) show only BackOff; `describe pod` (W2-Q1) shows no probes; the process exits within the same second it starts (W2-Q1, W2-Q2) | main | Ruled out |
| H5 | `sched:` Kubernetes CronJob or other scheduled job near 10:52 | a schedule firing within 15 minutes of the onset | CronJob listing in `payments` (W2-Q7): none | main | Ruled out (scope: namespace `payments` only; EventBridge not listed in environment.md and not queried) |
| H6 | Downstream (ledger API) outage or timeout | ceiling shape; timeout errors | previous log (W2-Q2): process dies in config load before any call; the ledger API's own health was not queried | main | Ruled out as the cause of the crash |

- H1 status: supported · evidence: W1-Q1, W1-Q2, W1-Q4, W1-Q5, W1-Q6, W2-Q1, W2-Q2, W2-Q3, W2-Q4, W2-Q5, W2-Q6, W3-Q1 · note: Fast mode, main session; tier `main`.
- H2 status: refuted · evidence: W1-Q2
- H3 status: refuted · evidence: W2-Q1
- H4 status: refuted · evidence: W1-Q2, W2-Q1, W2-Q2
- H5 status: refuted · evidence: W2-Q7
- H6 status: refuted for the crash · evidence: W2-Q2
- No `from-history` hypotheses: no `incidents/` directory or `lessons.md` exists (R5).

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/payments-deploy (local clone `~/src/payments-deploy`) | unknown (not queried) | unknown | unknown (clone age not checked) | not verifiable: Helm records no commit SHA and the image tag is a version. Commit d81e4b7 (10:41:41 UTC) is the newest commit touching the chart before Helm revision 31 (10:52:20 UTC); this is "newest commit on the branch read; deployment not verified". |

## Query log

Times: the clock call returned nothing; all waves ran at about 11:28 UTC (see Assumptions). Est. cost: reads are free of query charges; GetMetricData is billed per metric requested.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| R1 | n/a | shell: `echo "${CULIOPS_HOME:-}"` | n/a | free | empty: CULIOPS_HOME unset |
| R2 | n/a | shell: `git rev-parse --show-toplevel` | n/a | free | no output (repo root unknown; cwd used) |
| R3 | n/a | shell: `git check-ignore -q .culiops/sre-investigate` | n/a | free | exit 0: ignored by git |
| R4 | n/a | shell: `cat .culiops/sre-investigate/environment.md` | n/a | free | environment.md read: profile prod-ops, context prod, namespace payments, zone Europe/Paris |
| R5 | n/a | shell: `ls .culiops/sre-investigate` | n/a | free | only environment.md: no profiles/, lessons.md, incidents/ |
| W0-Q1 | n/a | shell: `date -u +%H:%M:%S` | n/a | free | no output |
| W0-Q2 | ~11:28:00 | shell: `command -v agentbox-env` | n/a | free | exit 1: Culibox absent |
| W0-Q3 | ~11:28:00 | aws sts get-caller-identity --profile prod-ops --region us-east-1 | n/a | free | account 111122223333, role PlatformOperator |
| W0-Q4 | ~11:28:00 | aws iam get-role --profile prod-ops --role-name PlatformOperator (role verified by W0-Q3) | n/a | free | role ARN path `/` returned |
| W0-Q5 | ~11:28:00 | aws iam simulate-principal-policy --profile prod-ops (fixed list of 10 write actions) | n/a | free | s3:PutObject and ecs:UpdateService allowed; 3 requested actions missing from reply; 3 unrequested rows returned (Gaps) |
| W0-Q6 | ~11:28:00 | kubectl auth whoami --context `arn:aws:eks:us-east-1:111122223333:cluster/prod` | n/a | free | user = same assumed role, groups eks-readonly |
| W0-Q7 | ~11:28:00 | kubectl config current-context | n/a | free | equals the profile's context |
| W0-Q8 | ~11:28:00 | kubectl auth can-i --list --context ... --namespace payments | n/a | free | no write verbs (default selfsubject*reviews create only); `*.*` get list watch |
| PB-Q1 | ~11:28:00 | [helper PROFILE] kubectl get deploy -n payments (Deployment name verified) | now | free | payments-worker READY 0/3, AVAILABLE 0, AGE 164d. raw/helper/profile-queries.txt |
| PB-Q2 | ~11:28:00 | [helper] kubectl get svc,ingress,hpa -n payments | now | free | no output: none returned (not proof of absence) |
| PB-Q3 | ~11:28:00 | [helper] kubectl get configmap -n payments | now | free | payments-worker-config (4 keys), kube-root-ca.crt |
| PB-Q4 | ~11:28:00 | [helper] aws sqs list-queues --profile prod-ops --region us-east-1 | now | free | payments-jobs, payments-jobs-dlq |
| PB-Q5 | ~11:28:00 | [helper] helm list -n payments | now | free | payments-worker rev 31, deployed 2026-10-24 10:52:20 UTC, chart 2.3.1, app 5.2.0 |
| W1-Q1 | ~11:28:00 | kubectl get pods -n payments (reuses nothing; first pod list) | now | free | 3 pods CrashLoopBackOff, 11 restarts each, age 35m. Confirmed. raw/w1-kube-state.txt |
| W1-Q2 | ~11:28:00 | kubectl get events -n payments --sort-by=.lastTimestamp | last hour | free | new RS scaled to 3, old to 0 from 3 at ~10:53; pods Scheduled on 3 nodes; image already present, Started; only BackOff warnings. Confirmed. |
| W1-Q3 | ~11:28:00 | kubectl rollout history deployment/payments-worker -n payments | now | free | revisions 14 and 15, no change-cause |
| W1-Q4 | ~11:28:00 | kubectl get rs -n payments --sort-by=.metadata.creationTimestamp | now | free | `6d4f8a2b7c` 3 desired 0 ready, 35m; `84c1e9d3f5` 0 desired, 11d. Confirmed. |
| W1-Q5 | ~11:28:00 | helm history payments-worker -n payments --max 10 (release verified by PB-Q5) | now | free | rev 30: 2026-10-13 15:40:02; rev 31: 2026-10-24 10:52:20, same chart 2.3.1 and app 5.2.0. Confirmed. |
| W1-Q6 | ~11:28:00 | CloudWatch get-metric-data, AWS/SQS ApproximateNumberOfMessagesVisible, QueueName=payments-jobs (verified: returned data), Maximum | 09:28-11:28Z, 300 s | est. 1 metric request; actual 1 | 12 points, 10:30-11:25 only (55 min of 120 requested): 14, 16, 10, 30, 19, 74, then 1,060 to 5,989 at +986 per 5 min. Confirmed. |
| W1-Q7 | ~11:28:00 | same metric, previous window | 07:28-09:28Z, 300 s | 1 request | empty reply `{}`: no data, not read as zero (Gap) |
| W1-Q8 | ~11:28:00 | same metric, -7d window | 2026-10-17 09:28-11:28Z | 1 request | empty reply `{}` (Gap) |
| W1-Q9 | ~11:28:00 | same metric, recurrence pull | 2026-10-10 09:28Z - 2026-10-24 09:28Z, 3600 s | 1 request | empty reply `{}` (Gap) |
| W1-Q10 | ~11:28:00 | same metric, QueueName=payments-jobs-dlq (verified: returned data) | 09:28-11:28Z, 300 s | 1 request | 12 points 10:30-11:25, all 0. Confirmed. |
| W1-Q11 | ~11:28:00 | AWS/SQS NumberOfMessagesSent, NumberOfMessagesDeleted, ApproximateAgeOfOldestMessage, payments-jobs | 09:28-11:28Z, 300 s | 3 requests | empty reply `{}` (Gap). Wave 1 had 11 calls because its fixed legs (change, signal, recurrence) needed them. |
| W2-Q1 | ~11:28:00 | kubectl describe pod payments-worker-6d4f8a2b7c-3mfk8 -n payments | now | free | Last State Terminated Reason Error exit code 1, Started=Finished 11:25:56; image 5.2.0; limits 500m/256Mi; envFrom ConfigMap; no probes shown; Start Time 10:52:33. Confirmed. |
| W2-Q2 | ~11:28:00 | kubectl logs payments-worker-6d4f8a2b7c-3mfk8 -n payments --previous --tail=40 | last container | free | fatal: required environment variable LEDGER_API_BASE_URL is not set (config/load.go:58), 11:25:56. Confirmed. |
| W2-Q3 | ~11:28:00 | same, pod `...-q7c2z` | last container | free | identical reply |
| W2-Q4 | ~11:28:00 | same, pod `...-vn5tr` | last container | free | identical reply |
| W2-Q5 | ~11:28:00 | kubectl get configmap payments-worker-config -n payments -o jsonpath=managedFields | now | free | reply was the whole object, no managedFields: keys LEDGER_BASE_URL present, LEDGER_API_BASE_URL absent (names only; values not recorded). Confirmed for the key set; write time not obtained (Gap). |
| W2-Q6 | ~11:28:00 | git -C ~/src/payments-deploy log -- charts/payments-worker | 2026-10-21 to now | free | d81e4b7 (10:41:41Z, #377) and 27c4e91 (2026-10-13 15:22:47Z, #361). |
| W2-Q7 | ~11:28:00 | kubectl get cronjobs -n payments | now | free | no output: no CronJobs in `payments` |
| W3-Q1 | ~11:28:00 | git -C ~/src/payments-deploy diff 27c4e91^ d81e4b7 -- charts/payments-worker | the two commits | free | 27c4e91 adds container arg `--ledger-retry-budget=3`; d81e4b7 renames config key LEDGER_API_BASE_URL to LEDGER_BASE_URL in values-prod.yaml, value unchanged. Confirmed (diff content). |

Not run, on purpose: `helm get values` (prints rendered values), `kubectl describe deploy` (prints environment values), any read of Secret objects, CloudTrail (not listed in environment.md).

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability of `prod-ops`: the simulation reply had no rows for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack | none on the investigation; the box already warned from the two allowed actions | switch to a ReadOnlyAccess or tighter role for incident work |
| CloudWatch baselines: previous window, -7d window and 14-day recurrence pull returned empty replies (W1-Q7, Q8, Q9); the incident pull covers only 10:30-11:25 UTC | recurrence class is `unclassified`; "normal" backlog is known only for 10:30-10:50 on the day; no -7d comparison | ask the queue owner for the queue's 14-day history (console), or check why the pull came back empty |
| Queue throughput and age: NumberOfMessagesSent, NumberOfMessagesDeleted, ApproximateAgeOfOldestMessage returned empty (W1-Q11) | inflow rate and how old the oldest payment is are unknown; "nothing consumes the queue" rests on pods being down (W1-Q1) plus the backlog slope (W1-Q6) | read those three metrics in the CloudWatch console for 10:30-11:30 UTC |
| ConfigMap write time: the jsonpath reply held no managedFields (W2-Q5) | dating the ConfigMap change rests on Helm revision 31, pod start and the backlog step, not on the object's own timestamp | a human reads `metadata.managedFields` of the ConfigMap or the pipeline run that applied revision 31 |
| Deployed commit not verifiable (Helm records no commit SHA; image tag is `5.2.0`) | attribution of the rename to commit d81e4b7 / #377 is Likely, not Confirmed | read the CD pipeline run for Helm revision 31 |
| Application source for payments-worker is not in environment.md | that the 5.2.0 binary requires LEDGER_API_BASE_URL rests on its own startup log (W2-Q2), not on code; whether a newer app version reads LEDGER_BASE_URL is unknown | name the app repo in environment.md, or ask the service owner |
| Rollout strategy, `minReadySeconds` and readiness probe settings were not read in structured form (`describe deploy` avoided, see above); `describe pod` shows no probes | why the rollout removed all three old pods in the same minute is Assumed | read Deployment `spec.strategy` and probes with a names-only `jq` filter |
| No log backend or APM in environment.md | only `kubectl logs --previous` (last container per pod) | n/a |
| CloudTrail and EventBridge not listed in environment.md, not queried | who applied the change, and AWS-side schedules, not checked | add the backends to environment.md if wanted |
| Kubernetes events expire after one hour by default | the rollout events were read at about 35 minutes; later runs may find them gone | none |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: no `lessons.md` exists (R5) |
| Re-verified this run | none |
| History lookup | run after H1-H6 were ranked: `incidents/` does not exist, so no matches (R5) |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| failure-mode | W2-Q2 | A Helm values change that renames a ConfigMap key the app reads at startup gives CrashLoopBackOff with exit code 1 and a fatal "required environment variable ... is not set" line in `--previous` logs, while the image tag is unchanged | W2-Q2 |
| process | W0-Q5 | `aws iam simulate-principal-policy` here returned a different action list than the ten requested (3 missing, 3 extra); check the reply row by row against the fixed list | W0-Q5 |
| process | W2-Q5 | the `managedFields` jsonpath on this ConfigMap returned the whole object without managedFields; use a names-only filter before saving anything and expect the write time to be missing | W2-Q5 |
| identifier | W1-Q6 | CloudWatch AWS/SQS `QueueName` dimension equals the queue names `payments-jobs` and `payments-jobs-dlq`; only a 55-minute slice of data came back, longer ranges came back empty | W1-Q6 |
