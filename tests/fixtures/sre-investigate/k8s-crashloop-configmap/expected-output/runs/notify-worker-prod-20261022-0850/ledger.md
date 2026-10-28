# Ledger: notify-worker prod 20261022-0850

Mode: Fast
Budget used: 20 queries / 20 · 0 GB log scanned / 2 · 14 CloudWatch metric requests / 100 · no other metered units
(final, after wave 2; wave 1 had 8 calls, wave 2 had 5; no third wave needed; budgets are the neutral Fast defaults from environment.template.md because the team's environment.md sets none)

## Problem

| Field | Value |
|---|---|
| What | Reporter: "notify-worker pods in prod are crash-looping and emails aren't going out." Measurable restatement: notify-worker pods in namespace notify restart repeatedly (CrashLoopBackOff); transactional email is not being sent (to be measured: queue consumption). |
| Where | notify-worker, prod, EKS cluster `prod`, namespace `notify`. Siblings: the Deployment's replicas (to be counted in wave 1). |
| When | Reported 08:50 UTC (08:50 local; zone is UTC). True onset unknown at intake. |
| Who is affected | Recipients of transactional email (order confirmations, password resets), the core flow named in environment.md. |
| Trigger | Chat message from the on-call operator (no alarm, no ticket, no link). |
| Mitigations already applied | none known |
| Assumptions made at intake | (1) No onset given, so the Fast default window applies: last two hours, 06:50-08:50 UTC (Phase 0 step 6 rule 5). (2) Zone = UTC, from `Timezone: UTC` in environment.md. (3) "Now" = 08:50:00 UTC on 2026-10-22; `date -u` returned no output here, so the clock is taken from the case reference time. (4) Budgets: environment.md sets none, so the template's Fast defaults apply (20 queries, 2 GB logs, 100 metric requests). |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | read-only confirmed (simulation) for the 7 requested actions that returned a row (all implicitDeny); 3 of the 10 requested actions returned no row (gap) | session valid. Reply carried 3 actions that were not requested (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; all implicitDeny). No token-based backend listed in environment.md, so no token check. Culibox: `command -v agentbox-env` failed, nothing said. |
| arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace notify) | Kubernetes user = role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b, group eks-readonly | no write verbs in notify | `can-i --list` shows `*.*` get/list/watch (this includes Secrets: the run does not read any Secret). Only other rows: `create` on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (the excluded access-review APIs). |

## Impact

Source order: no SLO named in environment.md; no load-balancer or APM metrics listed; so magnitude is `Assumed`, with queue depth and pod availability as the closest measured proxies.

| Field | Value |
|---|---|
| Symptom | All 3 notify-worker pods are in CrashLoopBackOff (0/3 ready, 11 restarts each, W1-Q1). The outbound queue is not being drained: notify-outbound visible messages 16 at 08:10, 120 at 08:15, 9,660 at 08:45 (about +318 per minute from 08:15); the DLQ stays at 0 (W1-Q8). |
| Affected | prod only (the only environment in scope); 3 of 3 replicas; core flow transactional email (customer-facing). That emails are not being sent is inferred from the unconsumed queue; no sent-mail counter was available. |
| Since / ongoing | 08:14:21 UTC (old pods stopped; first BackOff event 08:15:02 UTC) / ongoing: yes |
| Suggested severity | SEV1 because a customer-facing core flow (transactional email) has no worker available. The incident owner decides. |
| Basis | Assumed for magnitude (no SLO, no APM or load-balancer metrics; named gap) · W1-Q1, W1-Q8 · pod availability 0/3 is Confirmed; "emails not delivered" is Likely |
| Third party in the path | none identified for the failure; the SMTP relay is on the success path of a send, no contact route is recorded in environment.md or the profile |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-22 06:50:00 | 2026-10-22 08:50:00 |
| Baseline (previous) | 2026-10-22 04:50:00 | 2026-10-22 06:50:00 |
| Baseline (-7d) | 2026-10-15 06:50:00 | 2026-10-15 08:50:00 |

Re-anchored: yes. From incident 06:50:00-08:50:00 (previous 04:50:00-06:50:00, -7d 2026-10-15 06:50:00-08:50:00) to the windows below at 08:50 UTC, because W1-Q2 (first BackOff 08:15:02, old pods stopped 08:14:21) and W1-Q6 (Helm revision 12 at 08:14:20) showed the true onset at 08:14:21 UTC, 84 minutes after the default window's start and 36 minutes before now. The recurrence pull moved with it and now ends at the onset.

| Window (re-anchored) | From | To |
|---|---|---|
| Incident | 2026-10-22 07:44:00 (onset minus 30 min, rounded) | 2026-10-22 08:50:00 |
| Baseline (previous) | 2026-10-22 06:38:00 | 2026-10-22 07:44:00 |
| Baseline (-7d) | 2026-10-15 07:44:00 | 2026-10-15 08:50:00 |
| Recurrence pull (14d, Period 3600) | 2026-10-08 08:14:21 | 2026-10-22 08:14:21 |

Queries already run keep their rows and their old windows (W1-Q8). The re-anchored incident window lies inside W1-Q8's incident window, so it is reused, not re-run.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none: the run was started by a report, not an alarm; no alarm was named, so no alarm history was pulled |
| Signal, 14d at 1h resolution | Statistic: Maximum per hour (saturation-style gauge). Wave 1 pull ended at the default window start (06:50): no datapoints (W1-Q8). Wave 2 pull re-anchored to end at the onset 08:14:21: 2 hourly points out of 336 expected (07:00 bucket max 13, 08:00 bucket max 27; DLQ 0), from the 07:50-08:10 datapoints only (W2-Q5). Median, p95 and 14-day max not computed: 2 points is not a baseline. Incident level: 9,660 at 08:45 (hourly peak). |
| Coverage | CloudWatch SQS returned datapoints only from 07:50 to 08:45 UTC today; previous (W2-Q5), -7d (W2-Q5) and the 14d window before 07:50 came back empty. Kubernetes events cover about the last hour (no BackOff, Killing or Unhealthy event for the old ReplicaSet in it, W1-Q2). Helm history shows only revisions 11 and 12 in the last 10 revisions, 15 days apart. |
| Class | unclassified · shape: step (pods go from serving to 0 ready at one minute and stay; the queue backlog then ramps) |
| Reason | No alarm to pull (report-triggered) and 2 of 336 hourly points: no rule can be computed, recorded as a gap. Not `scheduled`: no CronJob listed (W1-Q7) and the onset is 1 s after the Helm upgrade of revision 12 (W1-Q6). For context: backlog was 7-27 messages for the 20 minutes before onset against 9,660 now, and no earlier failure of this Deployment shows in the retained events (W1-Q2); this does not make it `sudden`. |
| Label and queries | Assumed · W1-Q8, W2-Q5, W1-Q2, W1-Q7 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-07 09:51:09 | Commit 9e8d7c6 "raise concurrency to 8 (#201)" (author date) | git, W0-Q7 | W0-Q7 |
| 2026-10-07 10:02:18 | Helm revision 11 deployed (chart notify-worker-1.8.0, app 3.8.1); the Deployment's revision 6 ReplicaSet notify-worker-7f6b8c5d2e dates from here (15d) | helm history, W1-Q6, W1-Q4 | W1-Q6 |
| 08:03:41 | Commit 3f9a1c2 "align config key names with the shared SMTP chart (#214)" touches charts/notify-worker/values-prod.yaml (author date; merge and push time unknown) | git, W0-Q7 | W0-Q7 |
| 08:14:20 | Helm revision 12 deployed (same chart version 1.8.0, same app version 3.8.1) | helm history, W1-Q6 | W1-Q6 |
| 08:14:21 | Deployment scaled old ReplicaSet 7f6b8c5d2e to 0 from 3 (Recreate strategy); old pod Killing event | kubectl events, W1-Q2, W1-Q5 | W1-Q2 |
| 08:14:33 | New ReplicaSet 5c8d7b9f4c scaled to 3; pods scheduled | kubectl events, W1-Q2 | W1-Q2 |
| 08:14:36 | First container start of a new pod (Started event, firstTimestamp) | kubectl events, W1-Q2 | W1-Q2 |
| 08:15:02-08:15:05 | First BackOff event on each of the 3 new pods (firstTimestamp) | kubectl events, W1-Q2 | W1-Q2 |
| 08:15 | Queue backlog 120 (16 at 08:10): first bad sample | CloudWatch, W1-Q8 | W1-Q8 |
| 08:45 | Queue backlog 9,660; DLQ 0 | CloudWatch, W1-Q8 | W1-Q8 |
| 08:47:56 | Latest crash of a pod: fatal "required environment variable NOTIFY_SMTP_RELAY_HOST is not set" at config/load.go:58, 19 ms after start; Terminated Reason Error, exit code 1 | kubectl logs --previous, describe pod, W2-Q2, W2-Q1 | W2-Q2 |
| 08:49:20-08:49:51 | Latest BackOff events; pods still CrashLoopBackOff, 11 restarts each | kubectl, W1-Q1, W1-Q2 | W1-Q1 |
| 08:50 | Operator reports the crash loop and missing emails | reporter (not a query) | chat |

## Hypotheses

Ranked by fit to the onset (1 s after Helm revision 12), the step shape and the blast radius (3 of 3 replicas). Fast mode: labels are given by the main session.

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The prod values change in commit 3f9a1c2 (key NOTIFY_SMTP_RELAY_HOST renamed to SMTP_RELAY_HOST), applied by Helm revision 12 at 08:14:20, leaves the new pods without the variable that notify-worker 3.8.1 requires, so each pod exits at startup | New-ReplicaSet pods crash at start with a config error naming the variable; the live ConfigMap lacks the key; old-ReplicaSet pods did not crash; onset after 08:14:20 | Old against new (per-pod form): onset before 08:14:20, or old pods crashing the same way, or a different error in the previous-container log, or the ConfigMap still holding NOTIFY_SMTP_RELAY_HOST, would refute it: W1-Q2 (events before 08:14), W2-Q2, W2-Q3 | main | Confirmed |
| H2 | Image pull or scheduling failure on the new pods | pods Pending, ErrImagePull or FailedScheduling | W1-Q2 events: pods Scheduled and Started would refute it | main | Ruled out |
| H3 | Memory or resource limit kill (OOM) | last state OOMKilled or exit 137 | W2-Q1 describe pod: any other termination reason refutes it | main | Ruled out |
| H4 | Probe failures keep the pods out of service | Unhealthy events, a failing probe on a running process | W1-Q5 (probes defined?) and W1-Q2 (Unhealthy events): none refutes it | main | Ruled out |
| H5 | A dependency (SMTP relay, SQS, the notify-smtp secret) fails at startup | the crash log names a connection, auth or secret error | W2-Q2: a crash before any network call refutes it; W1-Q2: no CreateContainerConfigError | main | Ruled out |
| H6 | A scheduled job or node/instance churn caused the stop | onset within 15 min of a schedule; node events | W1-Q7 (CronJobs), W1-Q2 (node events, onset against the Helm upgrade) | main | Ruled out |

- H1 status: supported · evidence: W1-Q1, W1-Q2, W1-Q4, W1-Q5, W1-Q6, W2-Q1, W2-Q2, W2-Q3, W2-Q4 · note: the deploy is a candidate first; the old-against-new split was run before any label (see below). Main session tier (Fast mode).
- H2 status: refuted · evidence: W1-Q2, W2-Q1.
- H3 status: refuted · evidence: W2-Q1 (Reason Error, exit code 1; limit 256Mi), W1-Q2 (no OOM event).
- H4 status: refuted · evidence: W1-Q5 (no probe lines), W1-Q2 (no Unhealthy event). The container exits by itself, so a probe could not be the reason.
- H5 status: refuted · evidence: W2-Q2 (fatal at config load, before any dependency call; process lives about 19 ms), W1-Q2 (the secret reference resolved: the container started).
- H6 status: refuted · evidence: W1-Q7 (no CronJob listed; output empty, so unverified), W1-Q2 (no node events), W1-Q6 (upgrade at 08:14:20). Caveat: the empty CronJob listing alone would be weak; the Helm timing and the logged mechanism carry the ruling.
- No `from-history:` entries: `incidents/` does not exist yet.

**Old against new (H1), quoted per revision.** New revision (RS notify-worker-5c8d7b9f4c, Deployment revision 7, rolled out 08:14:21-08:14:33): 3 of 3 pods crash-looping (11 restarts each, W1-Q1); the previous-container log of each pod shows the same fatal line naming NOTIFY_SMTP_RELAY_HOST (W2-Q2). Old revision (RS notify-worker-7f6b8c5d2e, Deployment revision 6, 15 days old): 0 BackOff, Unhealthy or restart events in the retained events (about 07:50 to 08:14:21; only the Normal Killing at 08:14:21, W1-Q2); the outbound queue stayed at 7-27 messages from 07:50 to 08:10 (consumers draining, W1-Q8). The onset is not earlier than the rollout (backlog 16 at 08:10, first BackOff 08:15:02); no failure of this kind recurred before the new revision existed in the retained window. Gap: no per-revision log counts (no log backend; old pods' logs are gone), so the old side rests on the absence of events and on the queue.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/notify-deploy (clone ~/src/notify-deploy) | unknown (read through origin/HEAD) | newest commit on origin/HEAD for charts/notify-worker: 3f9a1c2e7b8d4f60a1b2c3d4e5f60718293a4b5c (the default branch is not the deployed state) | unknown (clone not fetched by the run; it already holds today's 08:03:41 commit) | Helm records no commit. 3f9a1c2 is tied to what ran by W2-Q3: the live ConfigMap holds SMTP_RELAY_HOST and lacks NOTIFY_SMTP_RELAY_HOST, exactly the post-state of that commit (W2-Q4). Apply record: Helm revision 12, 08:14:20 (W1-Q6). |
| example-org/notify-worker | not read | n/a | n/a | image tag 3.8.1 in both Helm revisions (app version unchanged), so no app diff exists to read; the requirement itself is shown by the crash log (config/load.go:58) |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 08:50:00* | aws sts get-caller-identity --profile prod-read | n/a | free | Account 111122223333 = environment.md; role AWSReservedSSO_ReadOnly_*; Confirmed. link: the same CLI call |
| W0-Q2 | 08:50:00* | aws sts get-caller-identity --query Arn; aws iam get-role --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b; aws iam simulate-principal-policy (fixed list), profile prod-read | n/a | free | 7 of 10 requested actions implicitDeny; ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no row (gap); 3 unrequested rows also implicitDeny. link: the same CLI calls |
| W0-Q3 | 08:50:00* | kubectl auth whoami; kubectl config current-context (context arn:aws:eks:us-east-1:111122223333:cluster/prod) | n/a | free | user = role ReadOnly, group eks-readonly; current context is the environment.md context. |
| W0-Q4 | 08:50:00* | kubectl auth can-i --list -n notify | n/a | free | no write verbs; `*.*` get/list/watch (includes Secrets, not read). |
| W0-Q5 (helper) | 08:50:00* | kubectl get deploy; kubectl get svc,ingress,hpa; kubectl get configmap, all -n notify | current state | free | Deployment notify-worker 0/3 ready, 211d; svc/ingress/hpa: empty output (unverified whether none exist); ConfigMaps kube-root-ca.crt, notify-worker-config (4 keys). |
| W0-Q6 (helper) | 08:50:00* | aws sqs list-queues --profile prod-read --region us-east-1 | n/a | free | queues notify-outbound, notify-outbound-dlq (unverified until a metric returns data). |
| W0-Q7 (helper) | 08:50:00* | git -C ~/src/notify-deploy log origin/HEAD -n 10 -- charts/notify-worker | n/a | free | commits 3f9a1c2 (2026-10-22 08:03:41 +0000, "align config key names with the shared SMTP chart (#214)") and 9e8d7c6 (2026-10-07 09:51:09 +0000, "raise concurrency to 8 (#201)"). Date shown is the author date. |

| W1-Q1 | 08:50:00* | kubectl get pods -n notify -o wide (context arn:aws:eks:us-east-1:111122223333:cluster/prod) | current state | free | 3 pods, all 0/1 CrashLoopBackOff, 11 restarts each, age 35m, one ReplicaSet hash 5c8d7b9f4c; Confirmed. raw/k-pods.txt |
| W1-Q2 | 08:50:00* | kubectl get events -n notify --sort-by=.lastTimestamp -o json, jq to tsv | retained events (about the last hour) | free | scale-down of RS 7f6b8c5d2e at 08:14:21, scale-up of RS 5c8d7b9f4c at 08:14:33, first Started 08:14:36, first BackOff 08:15:02/03/05 (151/149/150 occurrences by 08:49); no FailedScheduling, ErrImagePull, Unhealthy, OOM or node events; Confirmed. raw/k-events.tsv |
| W1-Q3 | 08:50:00* | kubectl rollout history deployment/notify-worker -n notify | n/a | free | revisions 6 and 7; Confirmed. |
| W1-Q4 | 08:50:00* | kubectl get rs -n notify --sort-by=.metadata.creationTimestamp | current state | free | RS 5c8d7b9f4c: 3 desired, 3 current, 0 ready, 35m; RS 7f6b8c5d2e: 0/0, 15d; Confirmed. |
| W1-Q5 | 08:50:00* | kubectl describe deploy notify-worker -n notify | current state | free | strategy Recreate; image tag 3.8.1; env from ConfigMap notify-worker-config; selector app.kubernetes.io/name and app.kubernetes.io/instance = notify-worker; Helm-managed; 0 available; no probes listed; Confirmed. |
| W1-Q6 | 08:50:00* | helm history notify-worker --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify --max 10 | last 10 revisions | free | rev 11 Oct 7 10:02:18 superseded, rev 12 Oct 22 08:14:20 deployed; chart notify-worker-1.8.0 and app 3.8.1 in both; Confirmed. |
| W1-Q7 | 08:50:00* | kubectl get cronjobs -A -o custom-columns=... | current state | free | no output (no CronJob listed; unverified whether the listing is empty or filtered); schedule hypothesis not supported. |
| W1-Q8 | 08:50:00* | aws cloudwatch get-metric-data, AWS/SQS ApproximateNumberOfMessagesVisible, QueueName notify-outbound and notify-outbound-dlq, Period 300, Maximum; four windows: incident 06:50-08:50, previous 04:50-06:50, -7d 2026-10-15 06:50-08:50, 14d recurrence 2026-10-08 06:50 to 2026-10-22 06:50 (Period 3600) | as listed | 8 metric requests / free tier not assumed; about $0 | incident window: 12 datapoints 07:50-08:45 per queue (backlog 11, 13, 7, 27, 16, 120, 1710, 3300, 4890, 6480, 8070, 9660; DLQ 0 throughout); previous, -7d and 14d: no datapoints. Confirmed for the incident window. raw/m-sqs-incident.tsv |

| W2-Q1 | 08:50:00* | kubectl describe pod notify-worker-5c8d7b9f4c-8wq2d, then -jt6kz, then -x4p9n, -n notify | current state | free | same content for each pod: Last State Terminated, Reason Error, Exit Code 1, started and finished in the same second (08:47:56 on the first pod), Restart Count 11, memory limit 256Mi, env from ConfigMap notify-worker-config plus SMTP_PASSWORD from a key of secret notify-smtp (reference only; Secret not read); Events: Started x12 over 35m, BackOff x151 over 34m; Confirmed. |
| W2-Q2 | 08:50:00* | kubectl logs <pod> -n notify -c notify-worker --previous --timestamps, run for each of the 3 pods | previous container instance of each pod | free | each pod: "notify-worker 3.8.1 starting", "loading configuration from environment", then fatal "config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set" (config/load.go:58), 19 ms after start; the same lines (same timestamp) came back for the 3 pods; Confirmed for the latest crash of each pod. Earlier crashes are not readable (`--previous` is one instance deep). raw/k-previous-logs.txt |
| W2-Q3 | 08:50:00* | kubectl get configmap notify-worker-config -n notify -o json, jq keys of .data; then the same object with jsonpath on .metadata.managedFields | current state | free | keys: NOTIFY_FROM_ADDRESS, NOTIFY_QUEUE_URL, NOTIFY_WORKER_CONCURRENCY, SMTP_RELAY_HOST; NOTIFY_SMTP_RELAY_HOST is absent; managedFields not returned (when the object was last written is unknown). Values not recorded. Confirmed. raw/c-configmap-keys.txt |
| W2-Q4 | 08:50:00* | git -C ~/src/notify-deploy show 3f9a1c2 -- charts/notify-worker/values-prod.yaml, values stripped with sed | commit 3f9a1c2 | free | the config: block of values-prod.yaml loses key NOTIFY_SMTP_RELAY_HOST and gains key SMTP_RELAY_HOST; every other key unchanged; Confirmed. raw/c-iac-diff-names.txt |
| W2-Q5 | 08:50:00* | aws cloudwatch get-metric-data, AWS/SQS ApproximateNumberOfMessagesVisible for notify-outbound and notify-outbound-dlq: previous 2026-10-22 06:38-07:44 (Period 300), -7d 2026-10-15 07:44-08:50 (Period 300), recurrence 2026-10-08 08:14:21 to 2026-10-22 08:14:21 (Period 3600, Maximum); the re-anchored incident window is reused from W1-Q8 | as listed | 6 metric requests; about $0 | previous: no datapoints; -7d: no datapoints; 14d: 2 hourly points of 336 (07:00 bucket max 13, 08:00 bucket max 27; DLQ 0). Recurrence class unclassified. |

*`date -u` returned no output in this environment; 08:50:00 is the case reference time, so Start times are indicative.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability only partly checked: 3 of the 10 simulated actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no row, and the reply held 3 unrequested rows (W0-Q2) | "read-only" holds for 7 actions only; no claim about the cause changes | Re-run the simulation by hand with the fixed list, or confirm with the IAM owner that the role is read-only. |
| No log backend in environment.md; pod logs only (current and previous container) | The first crash's log and the old pods' logs are gone, so there are no log counts per revision; the old-revision side of the split rests on events and queue depth | Add a log backend (a CloudWatch log group or a Loki instance) to environment.md. |
| No CloudWatch datapoints outside 07:50-08:45 UTC today (W1-Q8, W2-Q5) | No baseline, no -7d comparison, no recurrence statistics; class is `unclassified` | Check in the console whether the SQS queue metrics exist for earlier ranges; ask the metrics owner whether retention or queue activity explains it. |
| No SLO, APM or load-balancer request metrics; no sent-mail counter | Impact magnitude is `Assumed`; "emails are not going out" is `Likely` (inferred from an unconsumed queue) | Name an SLO or a sent-mail counter in environment.md; or look at the mail relay's own send log or dashboard. |
| ConfigMap write time not returned (W2-Q3, no managedFields) | When the live ConfigMap changed is not dated from the cluster; Helm revision 12 at 08:14:20 dates the apply | Read the object's managed-fields metadata with a binding that returns it. |
| Producer send rate (NumberOfMessagesSent) not pulled | The backlog growth rate cannot be split into "producers sending more" and "no consumers"; the cause of the crash is unaffected; drain time cannot be estimated | Pull the sent and deleted counts for notify-outbound over the last day. |
| Who ran the upgrade and which pipeline run applied commit 3f9a1c2 is not read (workflow name unknown, not guessed) | Trigger is dated by Helm and tied to the commit by the ConfigMap keys; the actor is unknown | Ask the owner of PR #214 (platform-dev) for the pipeline run of 08:14 UTC. |
| App source example-org/notify-worker not read | The requirement for NOTIFY_SMTP_RELAY_HOST at 3.8.1 is shown by the crash log, not by code at the deployed ref | Read config/load.go at the 3.8.1 tag with `gh` or a clone. |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (`lessons.md` does not exist) |
| Re-verified this run | none |
| History lookup | run after ranking: `incidents/` does not exist (the W0 listing of the output root shows only environment.md), so no grep was possible and there are no matches. No `from-history:` entries. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | iam simulate-principal-policy reply can omit requested actions and add others; compare returned action names with the requested list before saying all 10 were evaluated | W0-Q2 |
| process | kubectl | `kubectl logs --previous` holds only the latest crash of a container; date a crash loop's onset from the event firstTimestamp, not from the readable log | W2-Q2 |
| process | kubectl | `kubectl auth can-i --list` showed `*.*` get/list/watch for the ReadOnly role, which includes Secrets; the view ClusterRole would not | W0-Q4 |
| process | cloudwatch | get-metric-data on the notify SQS queues returned datapoints only for 07:50-08:45 on the incident day; empty earlier ranges are a coverage gap, not zero traffic | W1-Q8 |
| identifier | kubectl | notify-worker: namespace notify, Deployment, container and Helm release all named notify-worker; selector app.kubernetes.io/name=notify-worker plus app.kubernetes.io/instance=notify-worker | W1-Q5 |
| identifier | cloudwatch | SQS queues notify-outbound and notify-outbound-dlq in us-east-1 (profile prod-read), QueueName dimension | W1-Q8 |
| failure-mode | git | notify-worker 3.8.1 exits at startup with "required environment variable <NAME> is not set" (config/load.go:58) when a chart values key is renamed; compare key names in values-prod.yaml with the live ConfigMap keys | W2-Q2 |
