# Ledger: payments-worker prod 20261024-1128

Mode: Fast
Budget used: 17 of 20 queries (counted per tool call; template fast default, environment.md sets none) · 0 of 2 log GB · 8 of 100 CloudWatch metric requests · no other metered units

## Problem

| Field | Value |
|---|---|
| What | Reporter: "payments-worker pods in prod keep restarting and payments are queueing up. Fast mode, please." Measurable: the payments-worker containers in namespace payments exit and restart repeatedly (CrashLoopBackOff), and the SQS queue payments-jobs keeps growing. |
| Where | payments-worker, prod, EKS cluster prod, namespace payments. Siblings: its 3 replicas. Queues payments-jobs and payments-jobs-dlq. |
| When | Reported 2026-10-24 about 11:28 UTC (13:28 CEST), no onset given. True onset 10:52:21 UTC (12:52:21 CEST): old pods stopped by the rollout (W1-Q1). First BackOff 10:53:02 UTC. Ongoing. |
| Who is affected | Payment capture and refunds processed by payments-worker (core flow in environment.md). Jobs are queued, not failed; customer-visible effect not measured. |
| Trigger | Chat request from the operator. No alarm, no ticket. |
| Mitigations already applied | None known. Helm history shows revision 31 still the deployed revision at 11:28 UTC (W1-Q3), so no rollback has been made. |
| Assumptions made at intake | 1. Fast mode: the operator asked for it and the incident is ongoing. 2. No onset time given: Fast default, the last two hours, 09:28:00 to 11:28:00 UTC. 3. Zone Europe/Paris from environment.md: UTC+2 (CEST) on 2026-10-24, UTC+1 from 2026-10-25 01:00 UTC. 4. "Now" is 11:28:00 UTC, taken from the world clock; `date -u +%H:%M:%S` printed nothing, so all Start times in the query log are approximate (11:28). 5. environment.md sets only `insights_ask_threshold_gb` (10); other budgets and window caps are the template's neutral fast defaults (20 queries, 2 GB logs, 100 CloudWatch metric requests), counted per tool call. 6. Output root `.culiops/sre-investigate/` relative to the repo root; `git rev-parse --show-toplevel` printed nothing, so the current directory is taken as the repo root. 7. `CULIOPS_HOME` check printed nothing: treated as unset. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-ops (AWS) | account 111122223333 (matches environment.md), assumed role PlatformOperator (session name not recorded) | write-capable: s3:PutObject, ecs:UpdateService allowed (simulation). 7 of the 10 fixed actions returned a row; no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (write capability unknown (gap) for those three). Rows for ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy are not on the fixed list and were ignored. | Boxed warning shown. Session valid. No token-based backend listed. |
| arn:aws:eks:us-east-1:111122223333:cluster/prod (kubectl) | group eks-readonly (and system:authenticated); principal is the same assumed role | no write verbs in payments. Only `create` rows are selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (not counted); everything else is get/list/watch on `*.*`. | `*.*` read includes Secrets; the run never reads Secret objects. Context is the current context. |

## Impact

Source order: no SLO named in environment.md; no APM or load-balancer metrics (queue worker); so Deployment availability and queue depth against the pre-onset level.

| Field | Value |
|---|---|
| Symptom | payments-worker pods crash on startup and restart (11 restarts each in 35 minutes); queued payment jobs are not consumed. |
| Affected | prod namespace payments: 0 of 3 payments-worker pods available, all three replicas. payments-jobs backlog 5,989 at the 11:25 UTC sample against 10 to 30 at 10:30-10:50 UTC; steady +986 per 5 minutes from 11:00 (about 197 per minute). payments-jobs-dlq stays at 0. Core flow: payment capture and refunds. |
| Since / ongoing | 10:52:21 UTC (12:52:21 CEST) / ongoing at 11:28 UTC |
| Suggested severity | SEV1 because the core flow "payment capture and refunds processed by payments-worker" has no running consumer at all (default scale). The incident owner decides. |
| Basis | Deployment availability and queue depth against the level just before the onset (previous-window and -7d baselines returned no data) · W1-Q4, W1-Q6, W1-Q7 · Confirmed for the consumer outage and the backlog; customer-visible effect (delayed versus failed payments) Assumed, no business counter |
| Third party in the path | none known (the ledger endpoint is configured by key name only; owner not in the profile) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident (intake default, last two hours) | 2026-10-24T09:28:00Z | 2026-10-24T11:28:00Z |
| Baseline (previous) | 2026-10-24T07:28:00Z | 2026-10-24T09:28:00Z |
| Baseline (-7d) | 2026-10-17T09:28:00Z | 2026-10-17T11:28:00Z |

True onset inside the incident window: 2026-10-24T10:52:21Z.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not applicable: the trigger is a chat request, no alarm exists in environment.md |
| Signal, 14d at 1h resolution | ApproximateNumberOfMessagesVisible, Maximum (saturation gauge) for payments-jobs and the DLQ · median, p95, max: not computable, the 14-day pull returned `{}` · incident level 5,989 (5-minute max at 11:25) |
| Coverage | SQS pulls returned points only for 10:30-11:25 UTC on 2026-10-24 (12 of 24 expected 5-minute points in the incident window). Previous window, -7d window and 14-day pull: empty reply `{}`, no error text. Helm history lists revisions 30 and 31 only; ReplicaSet history lists 2 ReplicaSets (previous one 11 days old). |
| Class | unclassified · shape: ramp (backlog); the driver is a step in consumer capacity, 3 to 0 at 10:52:21 |
| Reason | No alarm history and no 14-day signal, so no rule in the recurrence table can be applied. Weak context: the previous ReplicaSet ran 11 days (W1-Q2) and Helm shows one earlier revision on 2026-10-13 (W1-Q3), so no earlier failure is visible, but that is not a recurrence statistic. Backlog before onset was 10-30 at 10:30-10:50 UTC (one 20-minute sample). |
| Label and queries | Assumed · W1-Q2, W1-Q3, W1-Q7, W1-Q8 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-13 15:22:47 | Commit 27c4e91 (#361) adds a ledger retry-budget argument to the Deployment template | git | W0-Q5, W2-Q1 |
| 2026-10-13 15:40:02 | Helm revision 30 deployed (chart 2.3.1, app 5.2.0); that ReplicaSet runs 11 days | helm, kubectl | W1-Q3, W1-Q2 |
| 2026-10-24 10:41:41 | Commit d81e4b7 (#377) renames config key LEDGER_API_BASE_URL to LEDGER_BASE_URL in values-prod.yaml (value identical); no image or chart-version change | git | W0-Q5, W2-Q1 |
| 2026-10-24 10:52:20 | Helm revision 31 deployed (chart 2.3.1, app 5.2.0, same as revision 30) | helm | W1-Q3 |
| 2026-10-24 10:52:21 | Deployment scales old ReplicaSet 84c1e9d3f5 from 3 to 0; old pod killed (strategy Recreate) | kubectl events, deploy | W1-Q1, W1-Q6 |
| 2026-10-24 10:52:33 | New ReplicaSet 6d4f8a2b7c scaled to 3; pods scheduled | kubectl events | W1-Q1 |
| 2026-10-24 10:52:36 | First container start in the new pods | kubectl events | W1-Q1 |
| 2026-10-24 10:53:02 / 10:53:03 / 10:53:05 | First BackOff on pods 3mfk8 / q7c2z / vn5tr | kubectl events | W1-Q1 |
| 2026-10-24 10:55 | First queue sample above pre-onset level: 74 (CloudWatch SQS metrics lag the queue by a minute or two) | CloudWatch | W1-Q7 |
| 2026-10-24 11:00 | 1,060; +986 per 5 minutes afterwards | CloudWatch | W1-Q7 |
| 2026-10-24 11:25 | 5,989 (last sample); DLQ 0 | CloudWatch | W1-Q7 |
| 2026-10-24 11:25:56 | Latest crash: fatal "required environment variable LEDGER_API_BASE_URL is not set", exit code 1 | kubectl logs --previous, describe | W1-Q5, W1-Q4 |
| 2026-10-24 11:27:20-11:27:51 | Latest BackOff events, 149-151 per pod | kubectl events | W1-Q1 |
| 2026-10-24 11:28 | Run starts (reporter's request) | reporter | not a query |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Helm revision 31 applied the values change from d81e4b7 (#377), which renamed the ConfigMap key LEDGER_API_BASE_URL to LEDGER_BASE_URL; payments-worker 5.2.0 still requires LEDGER_API_BASE_URL, exits 1 at configuration load, and all 3 pods crash-loop | live ConfigMap has the new key and lacks the old one; previous-container log names the missing variable; first BackOff within a minute of the rollout; all replicas fail alike | W2-Q2 (live key names contain LEDGER_API_BASE_URL, or no new key) and W2-Q1 (diff does not touch the key) and W1-Q1 (failure starts before 10:52) | main | Confirmed |
| H2 | A broken new image or app version | image or app version changes at revision 31 | W1-Q3 and W2-Q1: chart and app version equal at revisions 30 and 31, and no image line in either diff | main | Ruled out |
| H3 | The retry-budget argument from 27c4e91 (revision 30) | crash begins after revision 30, 2026-10-13 | W1-Q2, W1-Q3: that ReplicaSet and revision ran 11 days healthy | main | Ruled out |
| H4 | Out of memory or limits | OOMKilled, exit code 137 | W1-Q4: last state Reason Error, exit code 1 | main | Ruled out |
| H5 | Probe failures | Unhealthy events, container running | W1-Q1: no Unhealthy events; container exits at startup | main | Ruled out |
| H6 | Image pull or scheduling failure | ErrImagePull, FailedScheduling, pods Pending | W1-Q1: pods scheduled and started (12 starts on 3mfk8) | main | Ruled out |
| H7 | Ledger API outage or credential problem | timeouts or auth errors after startup | W1-Q5: the process dies at configuration load, before any network call | main | Ruled out (for the crash) |
| H8 | Scheduled job or maintenance window | a schedule fires near 10:52 | W1-Q9: no CronJobs, no scheduled EventBridge rules or Scheduler schedules returned | main | Ruled out |
| H9 | Node, Spot or eviction churn | Evicted or node events, uneven pod failures | W1-Q1: only the rollout's Killing at 10:52:21; W1-Q4: three replicas fail identically | main | Ruled out |

- `H1` status: supported (Confirmed) · evidence: W0-Q5, W1-Q1, W1-Q3, W1-Q4, W1-Q5, W2-Q1, W2-Q2 · note: main session, Fast mode; wave 3 not run because H1 is Confirmed and H2-H9 are Ruled out (stop-early rule).
- `H2` status: refuted · evidence: W1-Q3, W2-Q1
- `H3` status: refuted · evidence: W1-Q2, W1-Q3
- `H4` status: refuted · evidence: W1-Q4
- `H5` status: refuted · evidence: W1-Q1
- `H6` status: refuted · evidence: W1-Q1, W1-Q4
- `H7` status: refuted for the crash · evidence: W1-Q5 · note: a bad ledger credential (Secret payments-ledger-auth, never read) could still fail the next startup after the config is fixed; that stays Assumed, see Gaps.
- `H8` status: refuted · evidence: W1-Q9
- `H9` status: refuted · evidence: W1-Q1, W1-Q4
- No `from-history:` hypotheses: no incidents/ or lessons.md exists under the output root. No `from-docs:` leads: no wiki access listed.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/payments-deploy (local clone ~/src/payments-deploy; deploy repo for the Helm chart) | not discovered (unverified); log read with `--all`, no branch guessed | not read | unknown (no fetch performed; the clone holds d81e4b7 of 2026-10-24 10:41:41Z, so it is current to at least then) | revision 30 ↔ 27c4e91 (2026-10-13 15:22Z, applied 15:40Z); revision 31 ↔ d81e4b7 (10:41Z, applied 10:52Z): tie by timing and live key names, no CI apply record read |
| payments-worker application source | none listed in environment.md | - | - | image tag 5.2.0; source not readable (gap) |

## Query log

Start times are approximate: `date -u` printed nothing, so the world clock 11:28 UTC is used. Commands are in run-log.md; here each row names the source and the identifiers used. All identifiers below were listed or returned data in this run unless marked (unverified).

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 11:28 | AWS prod-ops: sts get-caller-identity, iam get-role PlatformOperator, iam simulate-principal-policy (10 fixed actions) | n/a | free | account matches; 2 of 10 allowed (s3:PutObject, ecs:UpdateService), 5 implicitDeny, 3 no row; boxed warning shown. link: `aws iam simulate-principal-policy --profile prod-ops` |
| W0-Q2 | 11:28 | kubectl context arn:aws:eks:us-east-1:111122223333:cluster/prod: auth whoami, config current-context, auth can-i --list -n payments | now | free | group eks-readonly; no write verbs in payments; `*.*` get list watch. link: `kubectl auth can-i --list -n payments` |
| W0-Q3 | 11:28 | kubectl (profile build, helper): get deploy; get pods -o wide; get svc,ingress,hpa; get configmap, namespace payments | now | free | Deployment payments-worker 0/3 available, age 164d; 3 pods CrashLoopBackOff, 11 restarts, age 35m; no Service, Ingress or HPA (empty reply); ConfigMaps payments-worker-config (4 keys) and kube-root-ca.crt. link: `kubectl -n payments get deploy,pods` |
| W0-Q4 | 11:28 | helm list; aws sqs list-queues (prod-ops, us-east-1); ls .culiops/service-discovery/ | now | free | release payments-worker chart payments-worker-2.3.1 app 5.2.0 revision 31 at 10:52:20Z; queues payments-jobs and payments-jobs-dlq; no service-discovery catalog (No such file). link: `helm list -n payments` |
| W0-Q5 | 11:28 | git -C ~/src/payments-deploy log --all --since=2026-10-10 -- charts/payments-worker | 2026-10-10 to now | free | two commits: d81e4b7 (2026-10-24 10:41:41Z, #377), 27c4e91 (2026-10-13 15:22:47Z, #361). Window widened from the playbook's 3 days to 14 days to reach revision 30's commit. link: same command |
| W1-Q1 | 11:28 | kubectl get events -n payments -o json piped to jq (first, last, count, type, kind, reason, object, message) | events kept about 1h: 10:52-11:28Z | free | 8 events: rollout at 10:52:21-10:52:33, first Started 10:52:36, first BackOff 10:53:02/03/05 (149-151 each); no Unhealthy, FailedScheduling, Evicted or pull events. Confirmed. raw/c-k8s-events.tsv. link: `kubectl -n payments get events -o json` |
| W1-Q2 | 11:28 | kubectl rollout history deployment/payments-worker; get rs --sort-by=.metadata.creationTimestamp, namespace payments | now | free | revisions 14 and 15; ReplicaSets 84c1e9d3f5 (0 of 0, 11d old) and 6d4f8a2b7c (3 desired, 0 ready, 35m). Confirmed. link: `kubectl -n payments rollout history deployment/payments-worker` |
| W1-Q3 | 11:28 | helm history payments-worker -n payments --max 10 | now | free | revision 30 (2026-10-13 15:40:02Z, superseded) and revision 31 (2026-10-24 10:52:20Z, deployed), both chart payments-worker-2.3.1 and app 5.2.0. Confirmed. link: `helm history payments-worker -n payments` |
| W1-Q4 | 11:28 | kubectl describe pod x3 (3mfk8, q7c2z, vn5tr), namespace payments | now | free | identical per pod: Waiting CrashLoopBackOff, last state Terminated Reason Error exit code 1 (11:25:56), restarts 11, envFrom ConfigMap payments-worker-config, one Secret-backed variable (name only), limits 500m/256Mi, no OOM, no probes. Confirmed. link: `kubectl -n payments describe pod <pod>` |
| W1-Q5 | 11:28 | kubectl logs <pod> --previous --tail=60 x3 | last terminated container | free | same 3 lines on each pod; fatal at config/load.go:58: required environment variable LEDGER_API_BASE_URL is not set. Confirmed (the log is the container's own). raw/c-previous-logs.txt. link: `kubectl -n payments logs <pod> --previous` |
| W1-Q6 | 11:28 | kubectl describe deploy payments-worker | now | free | strategy Recreate; 3 desired, 0 available; Available False MinimumReplicasUnavailable; selector app.kubernetes.io/instance and name = payments-worker. Confirmed. link: `kubectl -n payments describe deploy payments-worker` |
| W1-Q7 | 11:28 | CloudWatch prod-ops us-east-1 get-metric-data AWS/SQS ApproximateNumberOfMessagesVisible, Maximum, Period 300, QueueName payments-jobs (backlog) and payments-jobs-dlq (m1); three windows | incident 09:28-11:28Z; previous 07:28-09:28Z; -7d 2026-10-17 09:28-11:28Z | 6 metric requests | incident: 12 points (10:30-11:25Z), backlog 14,16,10,30,19 then 74, 1060, 2046, 3032, 4018, 5003, 5989; DLQ 0 throughout; previous and -7d: `{}`. Confirmed for the incident window. raw/m-golden-*.json. link: CloudWatch console, AWS/SQS, QueueName=payments-jobs |
| W1-Q8 | 11:28 | CloudWatch get-metric-data, same two metrics, Period 3600, Maximum | 2026-10-10T09:28Z to 2026-10-24T09:28Z | 2 metric requests | `{}`: no MetricDataResults, no error text. Coverage gap; recurrence unclassified. raw/m-recur-14d-cw.json |
| W1-Q9 | 11:28 | kubectl get cronjobs -A; aws events list-rules (scheduled only); aws scheduler list-schedules (prod-ops, us-east-1) | now | free | no CronJobs; no scheduled EventBridge rules; no Scheduler schedules returned. Ruled out for H8 (nothing scheduled to fire near 10:52Z). |
| W2-Q1 | 11:28 | git -C ~/src/payments-deploy diff 27c4e91^ d81e4b7 -- charts/payments-worker | commits 2026-10-13 to 2026-10-24 | free | 27c4e91 adds a retry-budget args entry to templates/deployment.yaml; d81e4b7 renames values-prod.yaml key LEDGER_API_BASE_URL to LEDGER_BASE_URL (value identical); no image, tag, resources or chart-version change. Confirmed (read at ref). raw/c-iac-diff-summary.txt |
| W2-Q2 | 11:28 | kubectl get configmap payments-worker-config -o json piped to jq (key names and managedFields only) | now | free | live keys: LEDGER_BASE_URL, PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY; LEDGER_API_BASE_URL absent; managedFields not returned. Confirmed. Values not recorded. raw/c-configmap-keys.txt |
| W2-Q3 | 11:28 | CloudTrail lookup-events ReadOnly=false, prod-ops us-east-1, resource name contains "payments" | 08:52Z to 11:07Z | free | `{}`: no write events returned that name payments resources. Likely none (resource filter may hide events that list no resources; not re-run unfiltered). |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| payments-worker application source is not listed in environment.md (only the deploy repo) | config/load.go:58 and the app's accepted variable names were not read; "5.2.0 requires LEDGER_API_BASE_URL" rests on the container's own fatal log (Confirmed as a failure message, but not as intended design) | add the application repo and a local clone under `code:` in environment.md |
| No log aggregator listed; only `kubectl logs --previous` (last terminated container, 11:25:56) | the first crash line is not retained; the timing leg uses the first BackOff events (10:53:02) instead of the first error line; pre-incident behaviour of the old pods is unseen | add a Loki or CloudWatch Logs row to `datasources` in environment.md |
| SQS previous-window, -7d and 14-day pulls returned `{}`; the incident window starts returning points only at 10:30 UTC | recurrence class unclassified; no seven-day baseline; "normal" backlog is only the 10:30-10:50 sample (10-30); backlog onset dating relies on the pods, not the metric | a human can check the queue's metrics in the console for the last 14 days and confirm the role may read AWS/SQS history |
| No CI or apply-run record read (gh and CI not listed) | the tie "d81e4b7 became Helm revision 31" rests on the live key names, Helm's revision time and the 11-minute lag; which pipeline run applied it is unknown | ask the owner of payments-deploy which pipeline run produced revision 31 |
| ConfigMap managedFields not returned | the exact time the ConfigMap changed is not read; Helm revision 31's time is used | none needed unless the exact time matters; ask the cluster admin to check object history |
| IAM simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack | write capability for those three actions is unknown | none for the investigation; for the credentials, ask the platform team to review the PlatformOperator policies |
| No SLO and no business counter for payment capture or refunds | customer-visible effect (delayed versus failed payments) is Assumed | add `slo:` or `core_flows` metric entries to environment.md, or check the payments dashboard |
| Queue attributes (retention, visibility timeout, redrive policy) not read | whether a long outage risks message expiry or DLQ redrive is unknown; DLQ pairing of payments-jobs-dlq is (unverified) | a human reads the queue attributes in the console |
| Clone freshness: no fetch is allowed, last-fetch time unknown | commits newer than the clone's last fetch (after 10:41Z) would be invisible | ask the owner whether a newer commit landed after 10:41Z |
| Secret payments-ledger-auth not read (by rule) | a credential problem behind the config problem cannot be excluded; H7 is Ruled out only for the crash | after the config is fixed, a human watches the first restart |

## Untrusted text

none seen. Reviewed: previous-container log lines, pod events, commit subjects. None reads like an instruction.

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no lessons.md under the output root) |
| Re-verified this run | none |
| History lookup | not run: the output root holds only environment.md (W0 pre-step `ls`); no incidents/ directory to search |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| identifier | kubectl | payments-worker prod: cluster context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace payments, Deployment and Helm release payments-worker, strategy Recreate, queues payments-jobs and payments-jobs-dlq | W0-Q3 |
| process | kubectl | kubectl logs --previous keeps only the last terminated container; for the first-occurrence timing leg use Pod events firstTimestamp, not the log | W1-Q5 |
| failure-mode | kubectl | A Helm values key rename the app does not read: all replicas exit 1 within a minute of the rollout, previous log says required environment variable X is not set, Recreate strategy leaves 0 available | W2-Q2 |
| process | cloudwatch | payments-jobs AWS/SQS depth returned no points before 10:30 UTC on 2026-10-24 and an empty reply for the 14-day and -7d windows; treat as a coverage gap, not zero, and check the role's history access | W1-Q8 |
