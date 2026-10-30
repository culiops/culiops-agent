# Ledger: payments-worker prod 20261024-1128

Mode: Fast
Budget used: 18/20 evidence queries (W0-Q1..Q4 access checks counted separately) · 0 / 2 GB log scanned · 15 / 100 CloudWatch metric requests

## Problem

| Field | Value |
|---|---|
| What | Reporter: "payments-worker pods in prod keep restarting and payments are queueing up." Measurable restatement: payments-worker pods in namespace payments restart repeatedly (restart count rising, pods not Ready) and the payments job queue backlog grows. |
| Where | Service payments-worker, environment prod (account 111122223333, us-east-1, EKS cluster prod, namespace payments). No sibling regions/shards named in environment.md; the replicas (3 pods) are the sibling set. |
| When | Reported 2026-10-24 ~11:28 UTC (13:28 Europe/Paris), "keep restarting" = ongoing. True onset 2026-10-24 10:52 UTC (12:52 Europe/Paris): Helm revision 31 applied 10:52:20, first container start 10:52:36, first BackOff 10:53:02 (W0-Q7, W1-Q2); 36 minutes before the report; found in wave 1, not guessed. |
| Who is affected | Callers of the payments flow (payment capture and refunds are processed by payments-worker per environment.md); jobs queueing. Measured: 0/3 workers available, payments-jobs backlog 5,989 at 11:25 UTC (W1-Q7); payment flows impact Assumed. |
| Trigger | Chat report from the on-call operator. No alarm, no ticket link. |
| Mitigations already applied | none known (not stated by the reporter) |
| Assumptions made at intake | (1) Operator gave no time: Phase 0 rule 5, Fast mode, window = last two hours, 09:28-11:28 UTC (11:28-13:28 Europe/Paris, UTC+2 on 2026-10-24 per environment.md). (2) "Now" = 11:28:00 UTC: `date -u` has no canned output in this simulation, so the clock is taken from the world's stated reference time. (3) environment.md sets no `budgets.fast`; the template neutral fast defaults (20 evidence queries, 2 GB logs, 100 CloudWatch metric requests) are used; the wave 0 identity and write-check calls are access checks and are not counted against the 20. (4) No Prometheus/Loki/trace/error-tracker/log backend is listed in environment.md; kubectl, Helm and CloudWatch (SQS) are the only sources. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| AWS profile `prod-ops` | account 111122223333 (matches environment.md), assumed role `PlatformOperator` (session name not recorded) | write-capable: s3:PutObject, ecs:UpdateService allowed (boxed warning shown). Other returned rows implicitDeny. 3 of the 10 fixed actions were not returned (see Gaps). | Session valid. No token variables listed. Culibox: `command -v agentbox-env` failed, nothing said. Warning shown, read-only role suggested, run continued. |
| kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod` | user is the same assumed role `PlatformOperator` (via aws-iam-authenticator), groups `eks-readonly`, `system:authenticated`; current context = this context | no write verbs in payments (only `create` on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews, which are excluded) | `*.*` has `[get list watch]`, so this identity can read Secrets (broader than the built-in `view` ClusterRole). The run never opens Secret objects. Rule list showed no "possibly incomplete" notice. |

## Impact

| Field | Value |
|---|---|
| Symptom | payments-worker pods crash on start (exit 1, CrashLoopBackOff); Deployment 0/3 available; payments-jobs backlog grows with no consumption |
| Affected | prod, namespace payments, all 3 replicas (no sibling is healthy). Queue payments-jobs visible messages 5,989 at 11:25 UTC against 10-30 at 10:30-10:50; DLQ 0. Payment capture and refunds are the core flows served by payments-worker (per environment.md): delayed, not shown failing (DLQ empty). Customer-facing: Assumed (queue-to-flow link not verified). |
| Since / ongoing | 10:52 UTC (12:52 Europe/Paris) first crash-loop sequence; ongoing: yes at 11:28 |
| Suggested severity | SEV1 because a core flow's worker (payment capture and refunds, payments-worker) has 0 of 3 replicas available and its queue is growing (default scale: customer-facing core flow down). The queue-to-flow link is Assumed. The incident owner decides. |
| Basis | W1-Q7, W1-Q4, W0-Q5 · Likely (pod and queue measurements are Confirmed; no SLO, no load-balancer/APM metrics, no business counter, baseline only 20 minutes) |
| Third party in the path | none known (a "shared ledger client" and LEDGER_API_* variable names suggest an internal ledger service, not queried) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident (initial, Fast default: last two hours) | 2026-10-24 09:28:00 | 2026-10-24 11:28:00 |
| Baseline (previous), initial | 2026-10-24 07:28:00 | 2026-10-24 09:28:00 |
| Baseline (-7d), initial | 2026-10-17 09:28:00 | 2026-10-17 11:28:00 |
| Incident (re-anchored) | 2026-10-24 10:22:00 | 2026-10-24 11:28:00 |
| Baseline (previous), re-anchored | 2026-10-24 09:16:00 | 2026-10-24 10:22:00 |
| Baseline (-7d), re-anchored | 2026-10-17 10:22:00 | 2026-10-17 11:28:00 |

Re-anchored: yes, at the start of wave 2: from incident 09:28-11:28 to 10:22-11:28 (30 minutes before the onset), because the default window came from "last two hours" (Phase 0 rule 5) and W0-Q7/W1-Q2/W1-Q3 put the true onset at 10:52 (Helm apply 10:52:20, first container start 10:52:36, first BackOff 10:53:02), 84 minutes after the assumed start. Previous, -7d and the recurrence pull move with it; queries already run keep their rows and old windows.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none: no CloudWatch alarm is the trigger and none is named in environment.md |
| Signal, 14d at 1h resolution | statistic Maximum (saturation-type gauge) of payments-jobs ApproximateNumberOfMessagesVisible, re-anchored pull ending at the onset 10:52 (W2-Q1): one hourly point, 30 (hour 10:00 on 2026-10-24); the assumed-window pull was empty (W1-Q8). Median, p95 and 14-day max cannot be computed. Incident value: 5,989 at 11:25 (5-minute resolution). |
| Coverage | CloudWatch SQS: nothing before 10:30 UTC on 2026-10-24 in any window (W1-Q7, W1-Q8, W2-Q1). Kubernetes events: one hour (first retained row 10:52:21, no Warning for old-hash pods). Helm: revisions 30 (Oct 13) and 31. ReplicaSets: revision 14 (11 days) and 15. |
| Class | `unclassified` · shape: step at 10:52 (pods fail and stay failed) with the queue backlog as a ramp behind it (about 197 messages/minute) |
| Reason | No alarm history and no usable 14-day signal, so no rule of the table can be applied. Nothing in the retained evidence shows an earlier occurrence (no BackOff for old-hash pods, backlog 10-30 before 10:50), but retention is too short to say so with a label. Recorded as a gap. |
| Label and queries | Assumed (the class) · W1-Q7, W1-Q8, W2-Q1 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-13 15:40:02 | Helm revision 30 deployed (old revision; ReplicaSet payments-worker-84c1e9d3f5, Deployment revision 14, ran 11 days) | helm history, rollout history, get rs | W1-Q3, W1-Q1 |
| 2026-10-24 10:30-10:50 | payments-jobs backlog 10-30 messages (working consumers, Assumed link) | CloudWatch SQS | W1-Q7 |
| 2026-10-24 10:41:41 | Commit d81e4b7 (#377) "rename ledger endpoint key to match the shared ledger client": in values-prod.yaml the config key LEDGER_API_BASE_URL becomes LEDGER_BASE_URL | git log, git show | W0-Q8, W2-Q2 |
| 2026-10-24 10:52:20 | Helm revision 31 applied (values-only change: same chart 2.3.1 and app 5.2.0) | helm history/list | W0-Q7, W1-Q3 |
| 2026-10-24 10:52:21 | Recreate strategy: old ReplicaSet scaled 3 to 0; old pod ...6dk2p Killing | events | W1-Q2 |
| 2026-10-24 10:52:33 | New ReplicaSet 6d4f8a2b7c scaled to 3; pods scheduled | events | W1-Q2 |
| 2026-10-24 10:52:36 | First container start on payments-worker-6d4f8a2b7c-3mfk8 (12 starts by 11:25:56) | events | W1-Q2 |
| 2026-10-24 10:53:02-10:53:05 | First BackOff on the three new pods (first occurrence of the symptom) | events | W1-Q2 |
| 2026-10-24 10:55 | Backlog 74 (19 at 10:50); grows about 197 per minute afterwards | CloudWatch SQS | W1-Q7 |
| 2026-10-24 11:00-11:25 | Backlog 1,060 to 5,989; DLQ 0 | CloudWatch SQS | W1-Q7 |
| 2026-10-24 11:25:56 | Latest restart of each pod fails: fatal "config: required environment variable LEDGER_API_BASE_URL is not set", exit 1 | kubectl logs --previous, describe pod | W1-Q6, W1-Q5 |
| 2026-10-24 ~11:28 | Report from the on-call operator (reporter's statement, not a query): pods restarting, payments queueing | chat | - |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Crash loop after a config change: Helm revision 31 (commit d81e4b7) renamed the config key LEDGER_API_BASE_URL to LEDGER_BASE_URL; the app (same image 5.2.0) still requires LEDGER_API_BASE_URL, exits 1 at config load, and no consumer processes payments-jobs | previous-container log shows the missing variable in every new pod; live ConfigMap lacks that key; the diff renames it; the old revision ran without restarts; onset at the rollout | ConfigMap containing LEDGER_API_BASE_URL (refutes), the old revision crashing the same way, or an onset before 10:52:20 | main | Confirmed for the crash loop (W0-Q7, W1-Q3, W1-Q6, W2-Q2, W2-Q3); Likely for "and this is why the backlog grows" (see note) |
| H2 | Probe failures take pods out of service | Unhealthy events, process up | no Unhealthy events and no probes configured | main | Ruled out (W1-Q2, W1-Q4, W1-Q5) |
| H3 | Image pull or scheduling failure | Pending, ErrImagePull, FailedScheduling | pods Scheduled and Started | main | Ruled out (W1-Q2, W1-Q5) |
| H4 | Memory/OOM | exit 137, OOMKilled | last termination Reason Error, exit 1 | main | Ruled out (W1-Q5, W1-Q2) |
| H5 | Downstream (ledger) outage or timeout | timeout errors, calls made | process exits before any network call | main | Ruled out (W1-Q6) |
| H6 | Credential problem (secret payments-ledger-auth, variable LEDGER_API_TOKEN) | auth errors, CreateContainerConfigError | pods Started and the logged fatal is a different error | main | Ruled out as the cause of the observed exit (W1-Q6, W1-Q2); a second failure behind the first is not excluded (Secret not read by design) |
| H7 | Evictions or node churn | Evicted, node events lining up with onset | no such events in the namespace, app-level exit code | main | Ruled out for pod evictions (W1-Q2, W1-Q5); node-level events not read |
| H8 | sched: a schedule or scheduled action caused the 10:52 change | schedule fires within +-15 minutes of the onset | schedule listings | main | Ruled out within scope: no CronJob, no EventBridge rule or Scheduler schedule named payments* (W2-Q4), no CloudTrail writes on payments resources (W2-Q5). What triggered the apply (human, pipeline, GitOps sync) is not known. |

- H1 status: supported · evidence: W0-Q7, W0-Q8, W1-Q1..Q6, W2-Q2, W2-Q3 · note: old against new: new ReplicaSet 6d4f8a2b7c 3/3 pods crash-looping, mechanism in each pod's own previous log (W1-Q6); old ReplicaSet 84c1e9d3f5 0/3 pods with Warning events before scale-down (W1-Q2), backlog 10-30 until 10:50 (W1-Q7), and the pre-change values file supplied LEDGER_API_BASE_URL (W2-Q2 removed line). Onset not earlier than the rollout (first BackOff 10:53:02, apply 10:52:20). No earlier occurrence evidence. Link between the crash loop and the backlog: PAYMENTS_QUEUE_URL names payments-jobs (W2-Q3), growth starts between 10:50 and 10:55 (W1-Q7); consumption metrics returned an empty reply (W3-Q1), other consumers not enumerated, so the backlog link stays Likely.
- H2..H7 status: refuted · evidence as listed.
- H8 status: refuted within scope · evidence: W2-Q4, W2-Q5.
- Ranking order is by fit to onset, shape and blast radius. No second plausible hypothesis remains.
## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/payments-deploy (local clone ~/src/payments-deploy, Helm values) | unknown (remote-tracking refs read with `--remotes=origin`) | not read | clone freshness not checked (no fetch performed) | d81e4b7 for Helm revision 31 by time and content (only chart commit in 3 days, committed 10:41:41, applied 10:52:20; the live ConfigMap matches its key set, W2-Q3); not tied by a pipeline record |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 11:28:00 (clock assumed; `date -u` printed nothing) | aws sts get-caller-identity --profile prod-ops | n/a | free | Account 111122223333, role PlatformOperator, matches environment.md. Confirmed. link: same CLI command |
| W0-Q2 | 11:28 | aws sts get-caller-identity + aws iam get-role --role-name PlatformOperator + aws iam simulate-principal-policy (fixed 10 actions) --profile prod-ops | n/a | free | get-role resolved the role ARN (path /). Simulation: s3:PutObject allowed, ecs:UpdateService allowed; 7 others implicitDeny; ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack not returned (gap); 3 unrequested rows returned (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy, all implicitDeny). link: same CLI command |
| W0-Q3 | 11:28 | kubectl auth whoami + kubectl config current-context, context arn:aws:eks:us-east-1:111122223333:cluster/prod | n/a | free | User = assumed role PlatformOperator, groups eks-readonly, system:authenticated; current context is the prod cluster. link: same CLI command |
| W0-Q4 | 11:28 | kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace payments | n/a | free | No write verbs; `*.*` get/list/watch. link: same CLI command |
| W0-Q5 | 11:28 | [helper] kubectl get deploy, pods, configmap, svc, ingress, hpa; context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace payments | current state | free | Deployment payments-worker 0/3 ready, 3 up-to-date, 0 available, age 164d. 3 pods payments-worker-6d4f8a2b7c-{3mfk8,q7c2z,vn5tr} all CrashLoopBackOff, 11 restarts each, age 35m. ConfigMaps payments-worker-config (4 keys) and kube-root-ca.crt. No svc, ingress or hpa output. Confirmed (current state at 11:28). link: same CLI command |
| W0-Q6 | 11:28 | [helper] aws sqs list-queues --profile prod-ops --region us-east-1 --queue-name-prefix payments | current | free | queues payments-jobs and payments-jobs-dlq. Names verified; consumer link unverified. link: same CLI command |
| W0-Q7 | 11:28 | [helper] helm list --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments | current | free | release payments-worker revision 31, updated 2026-10-24 10:52:20 UTC, status deployed, chart payments-worker-2.3.1, app version 5.2.0. Confirmed. link: same CLI command |
| W0-Q8 | 11:28 | git -C ~/src/payments-deploy log --remotes=origin --since=2026-10-21T11:28:00Z --until=2026-10-24T11:28:00Z --date=iso-strict -- charts/payments-worker (main session, parallel with helper) | 2026-10-21 11:28 to 2026-10-24 11:28 UTC | free | one commit in 3 days: d81e4b7 "payments-worker: rename ledger endpoint key to match the shared ledger client (#377)", committed 2026-10-24 10:41:41 UTC. Merged, apply time not shown by git (Helm shows the apply at 10:52:20). link: same git command |
| W1-Q1 | 11:29 (clock assumed) | kubectl -n payments rollout history deployment/payments-worker; kubectl -n payments get rs --sort-by=.metadata.creationTimestamp -o custom-columns=... (context arn:aws:eks:us-east-1:111122223333:cluster/prod) | current | free | Deployment revisions 14 and 15 (CHANGE-CAUSE none). ReplicaSet payments-worker-84c1e9d3f5 (rev 14): desired 0, age 11d. ReplicaSet payments-worker-6d4f8a2b7c (rev 15): desired 3, ready 0, age 35m. Confirmed. link: same CLI command |
| W1-Q2 | 11:29 | kubectl -n payments get events --sort-by=.lastTimestamp -o json \| jq (firstTimestamp, lastTimestamp, count, reason, object, message[:300]) | events retained, first row 10:52:21 UTC | free | 10:52:21 ScalingReplicaSet old RS 84c1e9d3f5 scaled to 0 from 3; Killing on old pod ...84c1e9d3f5-6dk2p. 10:52:33 new RS 6d4f8a2b7c scaled to 3, pods Scheduled. 10:52:36 Started container (3mfk8; x12 by 11:25:56). BackOff first seen 10:53:02 (3mfk8, x151), 10:53:03 (q7c2z, x149), 10:53:05 (vn5tr, x150), last 11:27:20-11:27:51. No Unhealthy, OOMKilling, Evicted, FailedScheduling, Failed (image pull) or BackOff events for any old-hash pod. Confirmed. link: same CLI command |
| W1-Q3 | 11:29 | helm history payments-worker --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments --max 10 | all revisions | free | rev 30 Oct 13 15:40:02 superseded, rev 31 Oct 24 10:52:20 deployed; both chart payments-worker-2.3.1, app 5.2.0, "Upgrade complete". Same chart and app version: values-only change between the two. Confirmed. link: same CLI command |
| W1-Q4 | 11:29 | kubectl -n payments describe deployment payments-worker | current | free | StrategyType Recreate; 3 desired, 3 updated, 0 available; image payments-worker:5.2.0 (ECR, account 111122223333); config from ConfigMap payments-worker-config via envFrom (Optional: false); Available=False MinimumReplicasUnavailable; no probes listed; no Deployment events. Confirmed (current state at 11:29). link: same CLI command |
| W1-Q5 | 11:29 | for each of the 3 pods: kubectl -n payments describe pod <pod> | current | free | Same for each pod apart from the name: owned by ReplicaSet payments-worker-6d4f8a2b7c, Last State Terminated Reason Error, Exit Code 1, Started and Finished both 11:25:56 UTC, Restart Count 11, State Waiting CrashLoopBackOff; limits cpu 500m / memory 256Mi (not OOM: exit 1, reason Error); no liveness or readiness probe; env var names: LEDGER_API_TOKEN (from a Secret key reference, value not read) plus envFrom ConfigMap payments-worker-config; pod annotation checksum/config present; node ip-198-51-100-31 (pod 3mfk8). Oddity: pod label pod-template-hash=5c8d7b9f4c differs from the hash in the owning ReplicaSet and pod names (6d4f8a2b7c); ownership (Controlled By) used for mapping. Confirmed. link: same CLI command |
| W1-Q6 | 11:29 | for each of the 3 pods: kubectl -n payments logs <pod> --previous --tail=50 | last terminated container (11:25:56 UTC) | free | 3 lines: 11:25:56.102 "payments-worker 5.2.0 starting"; 11:25:56.118 "loading configuration from environment"; 11:25:56.121 level fatal "config: required environment variable LEDGER_API_BASE_URL is not set" (config/load.go:58). Same output for each of the 3 pods. Confirmed for the last restart of each pod; earlier restarts' logs are not retrievable. link: same CLI command |
| W1-Q7 | 11:29 | aws cloudwatch get-metric-data --profile prod-ops --region us-east-1, AWS/SQS ApproximateNumberOfMessagesVisible Maximum Period 300, QueueName payments-jobs and payments-jobs-dlq (names verified by W0-Q6), three windows: incident 2026-10-24 09:28-11:28, previous 07:28-09:28, -7d 2026-10-17 09:28-11:28 | three windows | 6 metric requests | incident window: points exist 10:30-11:25 only. payments-jobs: 14, 16, 10, 30, 19 (10:30-10:50), 74 (10:55), 1060 (11:00), 2046, 3032, 4018, 5003, 5989 (11:25). payments-jobs-dlq: 0 at all 12 points. Growth about 197 messages/minute from 10:55 to 11:25. Previous window and -7d window: empty reply `{}` (no datapoints; not read as zero). No points before 10:30 although the window starts 09:28. Confirmed as measurements; baseline weak (20 minutes). link: same CLI command |
| W1-Q8 | 11:29 | same metrics, Period 3600 Maximum, 2026-10-10T09:28Z to 2026-10-24T09:28Z (14d recurrence pull, ending at the assumed window start) | 14d | 2 metric requests | empty reply `{}`; no datapoints in 14 days before 09:28. Coverage gap, not zero. link: same CLI command |
| W2-Q1 | 11:31 (clock assumed) | aws cloudwatch get-metric-data --profile prod-ops --region us-east-1, AWS/SQS ApproximateNumberOfMessagesVisible Maximum, payments-jobs and payments-jobs-dlq: (a) re-anchored previous window 2026-10-24 09:16-10:22, Period 300; (b) re-anchored recurrence pull 2026-10-10T10:52Z to 2026-10-24T10:52Z, Period 3600. The re-anchored -7d window 2026-10-17 10:22-11:28 lies inside the -7d window of W1-Q7: reused W1-Q7 (empty), not re-run | previous 09:16-10:22; 14d ending 10:52 | 4 metric requests | (a) empty reply `{}`. (b) one hourly point only (2026-10-24 10:00Z): payments-jobs Maximum 30, DLQ 0, built from the 5-minute points 10:30-10:50; nothing earlier in the 14 days. Coverage about 22 minutes. Maximum used as the aggregate for a gauge. link: same CLI command |
| W2-Q2 | 11:31 | git -C ~/src/payments-deploy show d81e4b7 -- charts/payments-worker | commit d81e4b7 | free | One file, charts/payments-worker/values-prod.yaml, under `config:`: the key LEDGER_API_BASE_URL is renamed to LEDGER_BASE_URL (value line otherwise unchanged; value not recorded). The other config keys (PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY) are untouched. Confirmed (diff on the failing path). link: same git command |
| W2-Q3 | 11:31 | kubectl -n payments get configmap payments-worker-config -o json \| jq (key names and managedFields only) | current state at 11:31 | free | 4 keys: PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY, LEDGER_BASE_URL. LEDGER_API_BASE_URL is absent. managedFields: none in the reply (change time not read here; Helm rev 31 is the apply record). PAYMENTS_QUEUE_URL refers to the payments-jobs queue (name only). Confirmed (current state; matches the post-change values file). link: same CLI command |
| W2-Q4 | 11:31 | kubectl -n payments get cronjob; aws events list-rules --profile prod-ops --region us-east-1 --name-prefix payments; aws scheduler list-schedules --profile prod-ops --region us-east-1 --name-prefix payments | current | free | no CronJob output; no EventBridge rule and no Scheduler schedule returned for prefix payments. Scope limit: other names, other event buses and CI-side schedules not listed. link: same CLI commands |
| W2-Q5 | 11:31 | TZ=UTC aws cloudtrail lookup-events (ReadOnly=false) --profile prod-ops --region us-east-1, 08:52-11:07 UTC, resource name containing payments | 08:52-11:07 UTC | free | no events matched. Scope limit: CloudTrail does not record in-cluster Helm or kubectl changes. link: same CLI command |
| W3-Q1 | 11:33 (clock assumed) | aws cloudwatch get-metric-data --profile prod-ops --region us-east-1, AWS/SQS NumberOfMessagesSent, NumberOfMessagesReceived, NumberOfMessagesDeleted (Sum, Period 300), QueueName payments-jobs | 2026-10-24 10:22-11:28 (re-anchored incident window) | 3 metric requests | empty reply `{}`: no datapoints for any of the three metrics. Not read as zero consumption. The attempt to show consumption stopping at 10:52 failed for lack of data. link: same CLI command |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| AWS write-check incomplete: the simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack (W0-Q2), and returned three rows that were not asked for | None on the cause. The statement "no broad write found" cannot be extended to those three actions; write capability is already established by s3:PutObject and ecs:UpdateService (allowed). | Review the PlatformOperator role's policies in IAM, or use a read-only role for incident work. |
| No log aggregator, metrics store (Prometheus), trace store or error tracker in environment.md; only `kubectl logs --previous` (last container only) and kubectl events (about one hour of retention) | No error counts per revision from logs, no request-level latency, no history beyond what the pods and events still hold. Claims about when the first error occurred rest on events and container state, so they are at most Likely unless a pod's own timestamps show it. | Add a log or metrics backend (with a token variable name) to environment.md. |

| CloudWatch SQS depth for payments-jobs returned nothing for the previous window, the -7d window and the 14-day pull, and nothing before 10:30 UTC on 2026-10-24 inside the incident window (W1-Q7, W1-Q8) | No baseline beyond 20 minutes (10:30-10:50) and no 14-day recurrence statistics, so the recurrence class cannot be computed and the size of the backlog against normal is only Likely. Empty is not read as zero. | Ask the platform team whether the metric is retained or emitted for that queue; check the queue in the CloudWatch console; add a depth alarm with history. |
| No application log aggregator: only the last terminated container's log per pod is readable (W1-Q6), so the log of the first crash at 10:52:36 is not available | The mechanism is Confirmed for the latest restart of each pod; that the first crash had the same message is inferred from identical container spec, exit code and restart cadence. | Add log shipping to environment.md, or check the cluster's log store for the 10:52-10:53 lines. |
| Application source repo for payments-worker 5.2.0 is not in environment.md | Cannot read config/load.go to see which key names the app expects; the name LEDGER_API_BASE_URL comes only from the log line. | Name the app repo and a clone path in environment.md. |
| No pipeline (apply) record read for payments-deploy | The deployed commit for Helm revision 31 is d81e4b7 by time (the only chart commit in 3 days, merged 10:41:41, applied 10:52:20), not by a pipeline record. | Open the apply run for the payments-deploy repo around 10:52 UTC. |
| Schedule listings limited to the name prefix `payments` on the default EventBridge bus and Scheduler, plus CronJobs in namespace payments (W2-Q4); CloudTrail cannot see in-cluster Helm or kubectl changes (W2-Q5) | H8 is Ruled out only within that scope. Who or what triggered the Helm apply at 10:52:20 (person, pipeline, GitOps sync) is not known. | Open the payments-deploy apply run (or the GitOps controller's sync record) for 10:52 UTC. |
| Consumption metrics of payments-jobs (NumberOfMessagesSent/Received/Deleted) returned an empty reply (W3-Q1); other consumers of the queue not enumerated | The link "the crash loop is why the backlog grows" stays Likely: consumption was not shown to stop at 10:52 and a second consumer was not excluded. Empty is not read as zero. | Check the three metrics for payments-jobs in the CloudWatch console, or list the queue's consumers with the owning team; a rising NumberOfMessagesSent with NumberOfMessagesDeleted at 0 after 10:52 would settle it. |
## Untrusted text

none seen (kubectl output, Helm output, git diff, container log lines and ConfigMap keys were read; no instruction-like text)

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: the output root holds only environment.md (W0 `ls`), so no lessons.md |
| Re-verified this run | none |
| History lookup | run after the ranked list existed: `grep -ril -e payments-worker -e payments-jobs -e CrashLoopBackOff .culiops/sre-investigate/incidents/` returned nothing, and `grep -i failure-mode .culiops/sre-investigate/lessons.md` returned nothing. No matched files, no matched fields. No `from-history:` entries. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| failure-mode | kubectl | payments-worker: a rename of a key under config in the Helm values file, with an unchanged app image, leaves a required env var unset; pods exit 1 within 20 ms and the previous-container log says required environment variable X is not set | W1-Q6, W2-Q2, W2-Q3 |
| process | kubectl | with no log store, kubectl logs --previous holds only the last terminated container of each pod, so the first crash's line is not readable; read events (firstTimestamp) for the first occurrence | W1-Q6, W1-Q2 |
| identifier | kubectl | payments-worker pods carry label pod-template-hash=5c8d7b9f4c while the owning ReplicaSet and pod names carry 6d4f8a2b7c; map pods to a ReplicaSet through Controlled By, not the label | W1-Q5 |
| process | aws | the IAM simulation reply for this role did not match the requested action list (3 requested actions missing, 3 unrequested rows returned); compare the reply rows with the fixed list | W0-Q2 |
| process | cloudwatch | for payments-jobs, ApproximateNumberOfMessagesVisible returns nothing before 10:30 UTC on 2026-10-24 and nothing for the previous, -7d and 14-day windows; NumberOfMessagesSent/Received/Deleted return empty replies; recurrence for this service cannot come from queue depth | W1-Q7, W1-Q8, W2-Q1, W3-Q1 |

