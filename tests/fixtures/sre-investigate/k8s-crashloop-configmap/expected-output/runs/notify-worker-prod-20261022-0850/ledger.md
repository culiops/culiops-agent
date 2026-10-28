# Ledger: notify-worker prod 20261022-0850

Mode: Fast
Budget used: 19 / 20 queries (4 profile build + 7 wave 1 + 5 wave 2 + 3 wave 3; the 6 Phase 0 access calls are logged W0-Q1..Q6 but not counted, see Assumptions) · 0 / 2 log GB · 8 / 100 CloudWatch metric requests · no other metered units
(state: final, after wave 3 and the report. The file was written in stages; the Hypotheses table and profile carry wave-3 results because the wave-2 and wave-3 world files were mapped and read before the corresponding ledger edits, see run-log.md)

## Problem

| Field | Value |
|---|---|
| What | Reporter: "notify-worker pods in prod are crash-looping and emails aren't going out." Measurable restatement: the notify-worker Deployment in namespace notify (prod) has pods in CrashLoopBackOff and transactional email is not being sent (to be measured in wave 1). |
| Where | Service notify-worker, environment prod, cluster `prod` (context from environment.md), namespace `notify`. Siblings: the 3 replicas of the one Deployment; no regions or shards. |
| When | Reported about 08:50 UTC 2026-10-22 (the request time; the reporter gave no onset). True onset: not known yet (to be set from wave 1). |
| Who is affected | Callers of transactional email (order confirmations, password resets, per environment.md core flows); extent to be measured. |
| Trigger | Chat request from the on-call operator; no alarm, ticket or link named. |
| Mitigations already applied | none known (none reported) |
| Assumptions made at intake | 1) Service name `notify-worker` and environment `prod` taken from the request text; both are confirmed or corrected by the profile build. 2) No onset time given: Fast default applies (window rule 5), last two hours, 06:50:00Z to 08:50:00Z. 3) Zone: `Timezone: UTC` in environment.md, so local time equals UTC. 4) "Now" is 08:50:00Z (the simulated clock; `date -u` returned no output in the world, INDEX states event ages are relative to 08:50:00 UTC); all wave start times use it. 5) environment.md has no query budget lines for kubectl or CloudWatch (only Logs Insights ask above 10 GB), so the neutral defaults of environment.template.md apply: fast = 20 queries, 2 log GB, 100 CloudWatch metric requests. 6) Budget unit: the 20 counts profile-build and evidence queries; Phase 0 identity and write-check calls (free describe calls, 6) are recorded in the Access table and logged but not counted. If they do count, the run used 25 of 20 (noted as a lesson candidate). 7) Repo root: `git rev-parse --show-toplevel` printed nothing in the world; the current directory is treated as the repo root. 8) Output root is `.culiops/sre-investigate/` (CULIOPS_HOME unset); in this simulation it is mapped to the `out/` directory. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| `prod-read` (AWS) | account 111122223333 (matches environment.md), assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded) | read-only confirmed (simulation) for the 7 listed actions that returned a row (all `implicitDeny`); 3 of the fixed 10 returned no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) = write capability unknown for those three (gap). Not a full proof; resource-scoped writes are not covered. | Session valid. No token variables listed in environment.md, so none to check. No boxed warning (no action allowed). |
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` (Kubernetes) | group `eks-readonly` via the same SSO read-only role (session name not recorded); current context equals this context | no write verbs in notify (only `create` on the three selfsubject*review resources, which do not count) | `can-i --list` also shows `get list watch` on `*.*`: Secrets are readable by this identity. The run reads no Secret object (Constraint 9). |

Culibox: `command -v agentbox-env` failed (exit 1); nothing said, standalone.

## Impact

| Field | Value |
|---|---|
| Symptom | notify-worker pods crash-loop and never become ready; nothing consumes queue `notify-outbound`, whose backlog grows. Reporter: emails are not going out. |
| Affected | prod, namespace notify, all 3 replicas (0/3 available, 11 restarts each, same ReplicaSet). Queue backlog 9,660 messages at 08:45 against 7-27 between 07:50 and 08:10; dead-letter queue flat at 0. Core flow: transactional email (order confirmations, password resets). |
| Since / ongoing | 08:14:21 UTC (last healthy pod stopped), first failing start 08:14:36 UTC; ongoing: yes |
| Suggested severity | SEV1 because a customer-facing core flow listed in environment.md (transactional email) is down: no worker consumes the queue. The incident owner decides. |
| Basis | W1-Q1, W1-Q2, W1-Q6 · Confirmed (no consumer, backlog growing); Likely (emails not delivered by any path: no delivery-side metric is configured, so non-delivery is inferred from the unconsumed queue). No request-error percentage applies (queue consumer, no HTTP path). |
| Third party in the path | none identified (the SMTP relay is a downstream of the worker, but no query has reached it; no contact route in the profile). The run cannot contact vendors. |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-22 06:50:00 | 2026-10-22 08:50:00 |
| Baseline (previous) | 2026-10-22 04:50:00 | 2026-10-22 06:50:00 |
| Baseline (-7d) | 2026-10-15 06:50:00 | 2026-10-15 08:50:00 |
| Recurrence pull (14d, ends at incident start) | 2026-10-08 06:50:00 | 2026-10-22 06:50:00 |

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none: no CloudWatch alarm was the trigger and none is named in environment.md or the profile |
| Signal, 14d at 1h resolution | `ApproximateNumberOfMessagesVisible` on `notify-outbound`, Maximum per hour (saturation row of the statistic table) · median n/a · p95 n/a · max excluding the incident n/a · incident 9,660 (5-minute peak at 08:45, the hourly pull ends at the incident start and returned nothing) |
| Coverage | W1-Q7 (14d, 1h) returned an empty object; W1-Q6 previous window (04:50-06:50) and -7d window returned empty objects. The only data is 07:50-08:45 on 2026-10-22 (12 five-minute points per queue). Helm history shows two retained revisions (11 on 2026-10-07 and 12 on 2026-10-22); the Deployment is 211 days old. |
| Class | `unclassified` · shape: step (pods stop at 08:14, first failing start 08:14:36) with a ramp in the queue backlog (about +1,590 per 5 minutes from 08:15 to 08:45) |
| Reason | The recurrence rules need the alarm history or the 14-day signal. Neither is available (no alarm; baseline pulls empty, and an empty result is not zero), so no class can be derived. Inside the available data the backlog is 7-27 until 08:10 and climbs from 08:15. A Fast run with no wave left for the drill-down would classify from what it has; here the gap itself is the finding. |
| Label and queries | Assumed (no baseline) · W1-Q6, W1-Q7 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 07:50-08:10 | `notify-outbound` backlog 7-27, dead-letter queue 0 (consumer healthy) | CloudWatch AWS/SQS | W1-Q6 |
| 08:03:41 | Commit `3f9a1c2` in example-org/notify-deploy (local clone): "notify-worker: align config key names with the shared SMTP chart (#214)"; the only commit on `charts/notify-worker` in the 3 days before the onset | git | W2-Q3 |
| 08:14:20 (live state read at 08:50) | ConfigMap `notify-worker-config` now holds key `SMTP_RELAY_HOST` and not `NOTIFY_SMTP_RELAY_HOST` (current state; the Helm revision time dates it) | kubectl | W3-Q2 |
| 08:14:20 | Helm release `notify-worker` upgraded to revision 12 (same chart 1.8.0 and app version 3.8.1 as revision 11 of 2026-10-07 10:02:18) | helm | W0-Q10, W1-Q5 |
| 08:14:21 | Deployment scaled old ReplicaSet `notify-worker-7f6b8c5d2e` to 0 from 3; old pod stopped (`Killing`) | kubectl events | W1-Q2 |
| 08:14:33 | New ReplicaSet `notify-worker-5c8d7b9f4c` scaled to 3; pods scheduled | kubectl events | W1-Q2 |
| 08:14:36 | First container start of the new pod (`Started` first timestamp) | kubectl events | W1-Q2 |
| 08:15:02 / :03 / :05 | First `BackOff` on each of the three new pods | kubectl events | W1-Q2 |
| 08:15 | Backlog steps from 16 (08:10) to 120, then climbs about 1,590 per 5 minutes | CloudWatch AWS/SQS | W1-Q6 |
| 08:45 | Backlog 9,660, dead-letter queue 0 | CloudWatch AWS/SQS | W1-Q6 |
| 08:47:56 | Latest container exit (code 1, same second as start): fatal log "config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set" at config/load.go:58, on all three pods | kubectl describe, kubectl logs --previous | W2-Q1, W2-Q2 |
| 08:49:20-08:49:51 | Latest `BackOff` events (counts 149-151 per pod) | kubectl events | W1-Q2 |
| about 08:50 | Operator reports the crash loop and missing email (from the reporter, not a query) | chat | n/a |

## Hypotheses

Written after wave 1. Siblings: all 3 replicas have 11 restarts and the same `BackOff` pattern from the same ReplicaSet, so the cause is shared, not per pod; per-pod capacity checks are skipped.

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The Helm revision 12 upgrade (08:14:20) delivered a configuration change that makes the process exit at startup. | New pods crash right after the rollout; previous-container logs show a configuration error; the pod template or ConfigMap changed in revision 12. | Previous-container logs and last termination state of the new pods (W2); onset earlier than 08:14:20, or a non-config error in the logs, refutes it. | main | Confirmed (after wave 3; Likely after wave 2) |
| H2 | A new application image (code defect) crashes at startup. | Image tag or Helm app version differs between revision 11 and 12; error is a code panic. | Helm history chart and app version per revision (W1-Q5); identical versions refute it. | main | Ruled out |
| H3 | Memory limit exceeded (OOMKilled). | Last termination reason `OOMKilled`, exit 137. | Pod last termination state (W2); reason `Error` with another exit code refutes it. | main | Ruled out |
| H4 | Probe failures take pods out. | `Unhealthy` events, probe lines in the pod description. | Events (W1-Q2) and pod description (W2); no `Unhealthy` event and no probe refute it. | main | Ruled out |
| H5 | Image pull or scheduling failure. | Pods Pending, `ErrImagePull`, `FailedScheduling`. | Events (W1-Q2): pods `Scheduled` and containers `Started` refute it. | main | Ruled out |
| H6 | Node or instance churn (eviction, drain). | Evictions or node events at the onset; one node out of line. | Events and previous-container logs; exit by the application itself refutes it. | main | Ruled out (pod and namespace scope; node object events not read) |
| H7 | SMTP relay or another dependency is down and the worker exits on connect. | Connection errors in the logs. | Previous-container logs (W2): a failure before any connection refutes it. | main | Ruled out as the cause of the crash (relay health after startup stays Assumed) |
| H8 | `sched:` a timed job or scaling action fired near the onset. | A schedule with a fire time within 15 minutes of 08:14. | CronJob and EventBridge schedule listings (W2); none refute it. | main | Ruled out |

- H1 status: supported · evidence: W0-Q10, W1-Q2, W1-Q4, W1-Q5, W2-Q1, W2-Q2, W2-Q3, W3-Q1, W3-Q2, W3-Q3 · note: after wave 2 only Likely (the diff leg was not read yet); wave 3 supplied the change leg.
- H2 status: refuted · evidence: W1-Q5, W2-Q1, W2-Q2, W3-Q1 · note: chart 1.8.0 and app version 3.8.1 are identical in revisions 11 and 12, the pod runs tag 3.8.1, the exit is a configuration error, and the only commit in the deploy path in the last three days (W2-Q3) touches a values key, no image line. The old ReplicaSet's image itself was not read (caveat).
- H3 status: refuted · evidence: W2-Q1 (last state `Error`, exit code 1, memory limit 256Mi) · note: no `OOMKilled`.
- H4 status: refuted · evidence: W1-Q2 (no `Unhealthy` event), W2-Q1 (no liveness or readiness line in the pod description) · note: a probe that was never configured cannot fail.
- H5 status: refuted · evidence: W1-Q2 (`Scheduled`, `Started` x12), W2-Q1 (image running as `3.8.1`).
- H6 status: refuted at pod scope · evidence: W1-Q2 (no `Evicted`, only the rollout's own `Killing` of the old pod at 08:14:21), W2-Q2 (the process exits itself with a fatal log) · note: node object events were not read; a gap.
- H7 status: refuted for the crash · evidence: W2-Q2 (fatal before any network use: configuration load fails first) · note: whether the relay accepts connections cannot be known until the process starts: Assumed.
- H8 status: refuted · evidence: W2-Q4 (no CronJobs, no scheduled EventBridge rules returned), the onset matches the Helm upgrade at 08:14:20 · note: both listings returned empty output; an empty result is read as none, with the coverage of this account and region.
- History lookup: done after the ranked list above existed; no incidents/ directory exists, so no `from-history:` hypothesis.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/notify-deploy (local clone `~/src/notify-deploy`, read by ref with `git -C`; no pull, fetch or checkout) | unknown (not recorded; all refs searched) | not read | not known (the clone's last fetch time was not read) | `3f9a1c2` (2026-10-22 08:03:41 UTC) is the commit whose key rename is live in the ConfigMap (W3-Q2) and is dated before Helm revision 12 (08:14:20). Merged is not applied: the pipeline apply record was not read (no CI source configured); the live ConfigMap and the Helm revision time stand in. |
| example-org/notify-worker (`gh`, read-only) | unknown | not read | not read | not read: the loader at config/load.go:58 was not opened; the crash mechanism is taken from the process's own fatal log |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 08:50:00 | aws sts get-caller-identity --profile prod-read --region us-east-1 | n/a | free | account 111122223333 matches environment.md; role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` · Confirmed. link: same command |
| W0-Q2 | 08:50:00 | aws iam get-role --profile prod-read --region us-east-1 --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b --query Role.Arn --output text | n/a | free | role ARN resolved (path /aws-reserved/sso.amazonaws.com/) · Confirmed |
| W0-Q3 | 08:50:00 | aws iam simulate-principal-policy --profile prod-read --region us-east-1 --policy-source-arn "$role_arn" --action-names (the fixed 10) | n/a | free | 10 rows all `implicitDeny`, but the rows are for a different action set than asked: 3 asked actions have no row, 3 unasked actions have rows · gap recorded |
| W0-Q4 | 08:50:00 | kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod (cluster `prod`, verified) | n/a | free | group eks-readonly; identity recorded by role only · Confirmed |
| W0-Q5 | 08:50:00 | kubectl config current-context | n/a | free | equals the environment.md context · Confirmed |
| W0-Q6 | 08:50:00 | kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace notify | n/a | free | no write verbs; `*.*` get list watch (Secrets readable, not used) · Confirmed |
| W0-Q7 | 08:50:00 | [helper PROFILE] kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get deploy | now | free | Deployment `notify-worker` 0/3 ready, 0 available, age 211d · Confirmed (identifier verified) |
| W0-Q8 | 08:50:00 | [helper PROFILE] kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get configmap | now | free | ConfigMaps `kube-root-ca.crt`, `notify-worker-config` (4 keys) · Confirmed (identifier verified) |
| W0-Q9 | 08:50:00 | [helper PROFILE] aws sqs list-queues --profile prod-read --region us-east-1 --queue-name-prefix notify | now | free | queues `notify-outbound`, `notify-outbound-dlq` · Confirmed (identifier verified) |
| W0-Q10 | 08:50:00 | [helper PROFILE] helm list --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify | now | free | release `notify-worker` rev 12, deployed 2026-10-22 08:14:20 UTC, chart notify-worker-1.8.0, app 3.8.1 · Confirmed (identifier verified) |
| W1-Q1 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get pods | now | free | 3 pods `notify-worker-5c8d7b9f4c-{8wq2d,jt6kz,x4p9n}` 0/1 CrashLoopBackOff, 11 restarts each, age 35m · Confirmed. link: same command |
| W1-Q2 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get events --sort-by=.lastTimestamp -o json (reduced with jq, first and last timestamps) | events kept 1h | free | old RS scaled to 0 at 08:14:21, new RS to 3 at 08:14:33, first Started 08:14:36, first BackOff 08:15:02-:05 on all 3 pods; no Unhealthy, Evicted, FailedScheduling or image-pull events · Confirmed. raw/c-events.tsv |
| W1-Q3 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify rollout history deployment/notify-worker | n/a | free | revisions 6 and 7, CHANGE-CAUSE `<none>` · Confirmed |
| W1-Q4 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get rs | now | free | `notify-worker-5c8d7b9f4c` 3 desired, 3 current, 0 ready, age 35m; `notify-worker-7f6b8c5d2e` 0/0/0, age 15d · Confirmed |
| W1-Q5 | 08:50:00 | helm history notify-worker --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify --max 10 | last 10 revisions | free | only revisions 11 (2026-10-07 10:02:18, superseded) and 12 (2026-10-22 08:14:20, deployed) retained; chart 1.8.0 and app 3.8.1 in both; helm history prints no zone, the instant matches W0-Q10 (UTC) · Confirmed |
| W1-Q6 | 08:50:00 | aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/q-sqs-300.json (QueueName `notify-outbound`, `notify-outbound-dlq`, both verified), loop over incident, previous, minus7d | incident 06:50-08:50 · previous 04:50-06:50 · -7d 2026-10-15 06:50-08:50 · Period 300 Maximum | 6 metric requests | incident: points only 07:50-08:45 (12 per queue): backlog 11, 13, 7, 27, 16, 120, 1710, 3300, 4890, 6480, 8070, 9660; dead-letter queue 0 throughout. previous and -7d: empty objects (no datapoints, no data is not zero) · Confirmed for the incident window; baselines unavailable (gap). raw not saved (read inline) |
| W1-Q7 | 08:50:00 | aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://raw/q-sqs-3600.json | 2026-10-08 06:50 to 2026-10-22 06:50, Period 3600 Maximum | 2 metric requests | empty object: no datapoints (recurrence cannot be computed) · gap |

| W2-Q1 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify describe pod notify-worker-5c8d7b9f4c-8wq2d (pod name verified by W1-Q1) | now | free | container state Waiting/CrashLoopBackOff, last state Terminated reason `Error`, exit code 1, started and finished 08:47:56; restart count 11; memory limit 256Mi; no liveness or readiness probe lines; env from ConfigMap `notify-worker-config`; env var `SMTP_PASSWORD` from Secret `notify-smtp` (names only, Secret not read); image tag 3.8.1; pod annotation `checksum/config` present · Confirmed. The other two pods have the same status in W1-Q1; not described separately |
| W2-Q2 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify logs <pod> --previous --tail=20, for notify-worker-5c8d7b9f4c-8wq2d, -jt6kz, -x4p9n (chained) | latest terminated container only | free | all three: "notify-worker 3.8.1 starting", "loading configuration from environment", then fatal "config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set" (config/load.go:58), 08:47:56Z · Confirmed for the 08:47 restart; the 08:14 first crash's log is not retrievable (`--previous` keeps only the latest). raw/w2-logs-previous.txt |
| W2-Q3 | 08:50:00 | git -C ~/src/notify-deploy log --all --since=2026-10-19T08:14:00Z --until=2026-10-22T08:50:00Z --date=iso-strict --format='%h %cI %an %s' -- charts/notify-worker (default branch unknown, so all refs; no fetch) | 3 days before the onset to now | free | one commit: `3f9a1c2`, 2026-10-22 08:03:41 UTC, "align config key names with the shared SMTP chart (#214)" · Confirmed (merged is not applied: see W3-Q2, W0-Q10) |
| W2-Q4 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime' ; aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text | now | free | no CronJob rows and no scheduled EventBridge rules returned (empty output / empty object) · Confirmed none visible; coverage: this cluster and us-east-1 only |
| W2-Q5 | 08:50:00 | TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-22T06:14:00Z --end-time 2026-10-22T08:30:00Z --query "Events[?contains(EventSource, 'eks.amazonaws.com') \|\| contains(EventSource, 'sqs.amazonaws.com') \|\| contains(EventSource, 'secretsmanager.amazonaws.com') \|\| contains(EventSource, 'ssm.amazonaws.com')].[EventTime, EventSource, EventName, EventId]" --output text | onset-2h to onset+15m | free | empty object: no matching write events · Confirmed none returned for these four services; Kubernetes API writes are not CloudTrail events (gap: no Kubernetes audit log source) |

| W3-Q1 | 08:50:00 | git -C ~/src/notify-deploy show 3f9a1c2 -- charts/notify-worker/values-prod.yaml (commit hash verified by W2-Q3) | n/a | free | one-line change in the `config:` block: key `NOTIFY_SMTP_RELAY_HOST` removed, key `SMTP_RELAY_HOST` added with the same value (values not recorded here); other keys (`NOTIFY_FROM_ADDRESS`, `NOTIFY_QUEUE_URL`, `NOTIFY_WORKER_CONCURRENCY`) unchanged · Confirmed |
| W3-Q2 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get configmap notify-worker-config -o json, reduced with jq to key names and managedFields (values not printed) | now | free | live keys: `NOTIFY_FROM_ADDRESS`, `NOTIFY_QUEUE_URL`, `NOTIFY_WORKER_CONCURRENCY`, `SMTP_RELAY_HOST`; `NOTIFY_SMTP_RELAY_HOST` is absent; no managedFields entries came back, so the object's last-write time is not available (the Helm revision time stands in) · Confirmed (the rename is live). The reply carried values; only key names were kept |
| W3-Q3 | 08:50:00 | kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify describe deploy notify-worker | now | free | StrategyType `Recreate`; 3 desired, 3 updated, 0 available; Available=False `MinimumReplicasUnavailable`; old RS 0/0, new RS 3/3 created; image tag 3.8.1; envFrom ConfigMap `notify-worker-config`; no probes; Events none · Confirmed |

Wave 3 notes: 3 calls; this is the last Fast wave. Wave 2 notes: 5 calls. Wave 1 notes: 7 calls (under the ten-call size). Availability cross-check not applicable: no load balancer or HTTP path; errors are process exits. Core flow counter: environment.md names the email flow but no metric, so no business-counter comparison was possible (gap). Latency queries not applicable (symptom is crash and backlog, not latency). No ReplicaSet/Deployment events for FailedCreate.

Wave 0 notes: no log probe was run: environment.md lists no Logs Insights, Loki or other metered log backend; the only log source is `kubectl logs`, which is unmetered and has no size estimate. No alarm or Grafana alert trigger, no ticket, no error-tracker project. No stored profile, no lessons.md, no incidents/ (ls of the output root showed only environment.md), so nothing to reuse from earlier runs.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Baselines: the previous window, the -7d window and the 14-day 1-hour pull returned empty objects (W1-Q6, W1-Q7); no alarm history exists | Recurrence is `unclassified`; "normal backlog" rests on a 20-minute sample (07:50-08:10). Severity and the sudden-vs-recurring question are not weakened (the crash is dated by events), but no claim about earlier occurrences can be made. | Ask the queue's owner for the usual `notify-outbound` backlog, or check the CloudWatch retention and whether the SQS metrics were published for those days. |
| No delivery-side signal: environment.md lists no email-sent counter, SMTP relay metric or provider backend | "Emails are not going out" is Likely (inferred from the unconsumed queue and 0 available workers), not measured. Whether any email leaves by another path is Assumed none. | Add a datasource for the sending counter or relay to environment.md; or have the owner check the mail provider's sent log. |
| Logs: only `kubectl logs --previous`, which keeps the latest terminated container (08:47:56); the first crash at 08:14:36 has no log in hand | The mechanism is read at the 08:47 restart and carried to the 08:14 onset by an unchanged pod template (same ReplicaSet hash, same ConfigMap since 08:14:20) and 11 identical exit-1 restarts; the first-crash log line itself is Assumed identical. Timing uses event first timestamps, not log lines. | Query a log backend for the first start after 08:14:33, if the team ships pod logs anywhere (none listed in environment.md). |
| Pipeline apply record for commit `3f9a1c2` not read; deploy clone freshness unknown; default branch unknown | "Merged is not applied": the apply is tied by the live ConfigMap keys (W3-Q2) and Helm revision 12 (W1-Q5), not by a CI run. | Open the deploy pipeline run for PR #214 (named in the commit subject) and compare its time with 08:14:20. |
| Node object events and Kubernetes API audit log not read | H6 is ruled out at pod and namespace scope only; who or what triggered the Helm upgrade at 08:14:20 is not known (CloudTrail does not log Kubernetes writes). | Ask the team who ran or which pipeline ran the upgrade; read the EKS audit log if enabled. |
| Application code at the deployed ref not read (example-org/notify-worker via `gh`) | Which names the 3.8.1 loader accepts (only the old key, or both) is not checked; it does not change the crash explanation, only the fix options. | Read config/load.go at the 3.8.1 tag (read-only `gh api`). |
| Write capability unknown (gap), prod-read: the simulation reply carried rows for ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy (not asked) and none for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (asked) | The Access line cannot say "none of the 10 broad write actions is allowed"; it says 7 of 10 evaluated, none allowed. Does not affect any cause. | Ask the account owner to confirm that the role is read-only, or re-run the simulation with an identity that has iam:SimulatePrincipalPolicy; treated as operator-assertable only. |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no lessons.md) |
| Re-verified this run | none |
| History lookup | not done yet (after the ranked hypotheses exist; no incidents/ directory exists) |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | The IAM simulation reply listed a different set of actions than the 10 requested; compare the action names in the reply with the requested list and treat missing ones as gaps. | W0-Q3 |
| process | kubectl | `kubectl logs --previous` keeps only the latest terminated container, so it shows the newest crash and not the first one; date the onset from event first timestamps. | W2-Q2 |
| process | cloudwatch | get-metric-data for windows outside the range the account has published returned empty objects for SQS; an empty object is not zero, so record baselines as a gap and use the in-window pre-incident points. | W1-Q6 |
| process | kubectl | The EKS read-only group has `get list watch` on all resources, Secrets included; the run must still never read a Secret object. | W0-Q6 |
| identifier | kubectl | notify-worker pods carry labels app.kubernetes.io/name=notify-worker and app.kubernetes.io/instance=notify-worker in namespace notify; queues are notify-outbound and notify-outbound-dlq. | W2-Q1 |
| failure-mode | git | A Helm values key rename (NOTIFY_SMTP_RELAY_HOST to SMTP_RELAY_HOST) renamed the ConfigMap key while the app still required the old name; the Recreate strategy then left 0 pods and the queue backlog grew. | W3-Q1 |
| process | any | The fast-mode query budget (20) is ambiguous about whether Phase 0 identity and write-check calls count; this run counted 19 without them, 25 with them. | W0-Q1 |
