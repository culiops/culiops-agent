# Ledger: notify-worker prod 20261022-0850

Mode: Fast
Budget used: metered queries 6 / 20 · log GB scanned 0 / 2 · CloudWatch metric requests 6 / 100 · other metered units none · 38 read-only calls in total (19 in wave 0, 13 in wave 1, 5 in wave 2, 1 in wave 3) (final state after wave 3; Fast budgets are the template defaults because environment.md sets no per-mode totals). Wave 1 held 13 calls, above the usual ten, because its fixed legs (change events, three-window signals, recurrence pulls) need them.

## Problem

| Field | Value |
|---|---|
| What | Reported: "notify-worker pods in prod are crash-looping and emails aren't going out." Measurable restatement: Deployment `notify-worker` in namespace `notify` has pods in CrashLoopBackOff and emails from the `notify-outbound` queue are not being sent (to be measured in wave 1). |
| Where | prod, EKS cluster `prod`, namespace `notify`, Deployment `notify-worker`. One deployment; no sibling regions, shards or tenants named in environment.md. |
| When | Reported 08:50 UTC (now; no time given). True onset: not yet known. |
| Who is affected | Consumers of transactional email (order confirmations, password resets): the core flow named in environment.md. Count not yet measured. |
| Trigger | Operator report in chat. No alarm, ticket or link given. |
| Mitigations already applied | None known (none stated by the reporter). |
| Assumptions made at intake | (1) No onset given, so the Fast default window is the last two hours: 06:50-08:50 UTC. (2) Zone: UTC, from `Timezone: UTC` in environment.md, so local time equals UTC. (3) Clock: `date -u` has no INDEX row in this simulation; Start times use 08:50:00 UTC, the reference time in world/INDEX.md. (4) environment.md has no per-mode budgets; template Fast defaults apply (20 queries, 2 GB logs, 100 CloudWatch metric requests) and only metered calls (CloudWatch GetMetricData, log scans) count against them. (5) Service `notify-worker`, environment `prod` taken from the request; context and profile from environment.md. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| `prod-read` (AWS) | account 111122223333 (matches environment.md), role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | no write allowed among the 7 evaluated actions (implicitDeny); 3 of the 10 requested actions returned no result row (gap G1) | session valid; no token-based backend listed in environment.md; `agentbox-env` absent, nothing shown about Culibox |
| context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `notify` | cluster `prod`, role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, group `eks-readonly` | no write verbs in `notify` (only `create` on the three self-review APIs, which are excluded) | current context equals this context. `*.*` has get/list/watch, which is broader than the built-in `view` role (it can read Secrets); never used, Secrets are not read. |

## Impact

Source order: no SLO and no request/error/duration metrics in environment.md, so workload state and queue depth stand in; magnitude beyond that is Assumed.

| Field | Value |
|---|---|
| Symptom | All notify-worker pods in CrashLoopBackOff (0/3 ready, 11 restarts each); `notify-outbound` is no longer drained (visible messages 16 at 08:10, 120 at 08:15, 9,660 at 08:45); transactional email is not being sent |
| Affected | prod, namespace `notify`, 3 of 3 replicas (single deployment, no siblings); core flow transactional email (order confirmations, password resets), customer-facing; DLQ stays at 0 so messages wait rather than fail |
| Since / ongoing | 08:14 UTC (Helm release 12 at 08:14:20, first new pod started 08:14:33, queue depth leaves baseline at 08:15) / ongoing: yes |
| Suggested severity | SEV1 because a customer-facing core flow (transactional email) is down: no worker is consuming |
| Basis | W1-Q4, W1-Q6, W1-Q7, W1-Q8, W1-Q12 · Confirmed that consumers are 0/3 and the backlog grows about 1,590 per 5 minutes (about 318 per minute) · Likely for "emails are not delivered" (no delivery counter) · Assumed for the number of customers or emails affected |
| Third party in the path | SMTP relay (host set through ConfigMap key; not implicated by any evidence); no contact route in the profile. The run cannot contact vendors. |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-22 06:50 | 2026-10-22 08:50 |
| Baseline (previous) | 2026-10-22 04:50 | 2026-10-22 06:50 |
| Baseline (-7d) | 2026-10-15 06:50 | 2026-10-15 08:50 |

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not applicable: trigger is a chat report, no alarm named; whether an alarm exists on `notify-outbound` was not checked (G7) |
| Signal, 14d at 1h resolution | `ApproximateNumberOfMessagesVisible`, Maximum, Period 3600 (saturation gauge) · median, p95, max: not computable, W1-Q11 and W1-Q13 returned `{}` · incident value 9,660 at 08:45 (5-minute max) · only reference level: 7-27 at 07:50-08:10 (W1-Q8) |
| Coverage | W1-Q8: 12 of 24 expected 5-minute points (07:50-08:45; nothing for 06:50-07:45). W1-Q9 (04:50-06:50), W1-Q10 (-7d), W1-Q11 (14d) and W1-Q13 (DLQ 14d): no data returned (`{}`), a gap, not zero. Helm history (W1-Q6) shows release 11 on 2026-10-07 and no other release in the last 15 days; ReplicaSet history (W1-Q1, W1-Q2) shows only revisions 6 and 7. |
| Class | `unclassified` · shape: step (consumption stops at about 08:14), seen as a steady ramp of queue backlog from 08:15 |
| Reason | The 14-day signal and the baselines returned no data and there is no alarm history, so neither `sudden`, `chronic`, `recurring` nor `scheduled` can be tested. Only one change (release 12) sits near the onset, and the backlog rises by an exact 1,590 per 5 minutes after it, which fits one change, not a periodic pattern. Recorded as a gap (G3). |
| Label and queries | Assumed · W1-Q8, W1-Q9, W1-Q10, W1-Q11, W1-Q13 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-07 10:02:18 | Helm release 11 (superseded): previous release, ran 15 days | helm history | W1-Q6 |
| 2026-10-07 09:51:09 | Commit `9e8d7c6` "raise concurrency to 8 (#201)" merged; applied as release 11 eleven minutes later | git | W2-Q1 |
| 08:03:41 | Commit `3f9a1c2` "align config key names with the shared SMTP chart (#214)" merged: renames values key `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST` | git | W2-Q1, W3-Q1 |
| 07:50-08:10 | `notify-outbound` depth 11, 13, 7, 27, 16 (consumers keeping up); DLQ 0 | CloudWatch | W1-Q8, W1-Q12 |
| 08:14:20 | Helm release 12 of `notify-worker` deployed (chart 1.8.0 and app 3.8.1 same as release 11) | helm history, helm list | W1-Q6, W0-Q18 |
| about 08:14 | Old ReplicaSet `7f6b8c5d2e` scaled 3 to 0 (Killing x3), new ReplicaSet `5c8d7b9f4c` scaled 0 to 3; strategy Recreate | kubectl events, describe deployment | W1-Q3, W1-Q7 |
| 08:14:33 | First pod of the new ReplicaSet starts (`8wq2d`) | kubectl describe pod | W1-Q4 |
| 08:15 | `notify-outbound` depth 120, first value above baseline; then +1,590 every 5 minutes to 9,660 at 08:45 | CloudWatch | W1-Q8 |
| 08:15-08:47 | All 3 pods in CrashLoopBackOff, 11 restarts each; latest crash 08:47:56 | kubectl get pods, describe pod, events | W0-Q15, W1-Q4, W1-Q3 |
| 08:50 | Report received: pods crash-looping, emails not going out | reporter, not a query | - |

## Hypotheses

Ranked after wave 1 by fit to onset (08:14), shape (consumption stops at once) and blast radius (3 of 3 pods). Fast mode: the main session tests them, tier `main`.

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Helm release 12 changed a config key the app requires: the ConfigMap rendered by release 12 lacks `NOTIFY_SMTP_RELAY_HOST`, so app 3.8.1 exits at start | all 3 pods die at config load with that message from the first start after 08:14; ConfigMap key names differ from what the app requires | ConfigMap key names include `NOTIFY_SMTP_RELAY_HOST` (refutes); another pod's previous log shows a different error (refutes); crashes predate 08:14 (refutes) | main | Confirmed |
| H2 | New image or chart release is broken (bad deploy) | image tag or chart changed in release 12; failure is a code error | image and chart diff between release 11 and 12 on the failing path | main | Ruled out |
| H3 | `SMTP_PASSWORD` Secret missing or wrong | pods stuck in `CreateContainerConfigError`, or an auth error after config load | pod reaches `Started` and the log names a different variable | main | Ruled out |
| H4 | Memory or CPU limits (OOM) | `OOMKilled`, exit 137 | Last State reason and exit code | main | Ruled out |
| H5 | Probe, image pull or scheduling failure | `Unhealthy`, `ErrImagePull`, `FailedScheduling`, `Pending` pods | events and probes in the pod template | main | Ruled out |
| H6 | Node or infrastructure churn | failures on one node, node events at 08:14 | pods spread over nodes, node events | main | Ruled out |
| H7 | SMTP relay or SQS downstream outage | timeouts, errors after start-up | does the process reach a network call before dying | main | Ruled out (as the crash cause) |
| H8 | Scheduled job or CronJob | fire time within 15 minutes of 08:14 | CronJob listing | main | Ruled out |

- H1 status: supported (confirmed) · evidence: W1-Q4, W1-Q5, W1-Q6, W2-Q2, W2-Q4, W2-Q5, W3-Q1 · note: main session, Fast mode.
- H2 status: refuted · evidence: W3-Q1 (diff touches only the values key), W1-Q6 (chart 1.8.0 and app 3.8.1 in both releases), W1-Q7 (image tag 3.8.1) · note: the old ReplicaSet's image was not read directly (G6).
- H3 status: refuted · evidence: W1-Q4 (container started 12 times, secret reference `Optional: false` resolved), W1-Q5 (fatal names `NOTIFY_SMTP_RELAY_HOST`) · note: a wrong password cannot be tested read-only and would only show after start-up (see report, To confirm).
- H4 status: refuted · evidence: W1-Q4 (reason Error, exit code 1, not OOMKilled or 137; crash 19 ms after start).
- H5 status: refuted · evidence: W1-Q3 (3 pods scheduled on 3 nodes, image already present, started), W1-Q7 (no probes in the pod template).
- H6 status: refuted · evidence: W1-Q3 (the only Killing events are the old ReplicaSet at the rollout; 3 different nodes fail identically).
- H7 status: refuted as crash cause · evidence: W1-Q5 (exit during config load, before any network call) · note: relay health itself is not tested (read-only); unknown until workers run again.
- H8 status: refuted · evidence: W2-Q3 (no CronJobs); the only change near onset is a Helm release.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/notify-deploy (local clone `~/src/notify-deploy`) | `main` assumed (unverified; `origin/main` returned commits) | not read | clone age not verified (no fetch allowed) | commit `3f9a1c2` (merged 2026-10-22 08:03:41 UTC) is the change in Helm release 12; `9e8d7c6` (2026-10-07 09:51:09 UTC) was in release 11 |
| example-org/notify-worker (via `gh`) | not read | not read | not read | image tag 3.8.1; code not read (G8) |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 08:50:00 | shell: `printf '%s\n' "${CULIOPS_HOME:-}"` | - | free | empty: CULIOPS_HOME unset, root is `.culiops/sre-investigate/` |
| W0-Q2 | 08:50:00 | git: `git check-ignore -q .culiops/sre-investigate` | - | free | exit 0, no output: ignored |
| W0-Q3 | 08:50:00 | file: `cat .culiops/sre-investigate/environment.md` | - | free | found (world/environment.md): UTC, profile prod-read, context prod, ns notify, core flow transactional email |
| W0-Q4 | 08:50:00 | file: `ls .culiops/sre-investigate` | - | free | only `environment.md`: no profiles/, lessons.md or incidents/ |
| W0-Q5 | 08:50:00 | `cat .culiops/sre-investigate/lessons.md` | - | free | No such file or directory (no lessons) |
| W0-Q6 | 08:50:00 | `cat .culiops/sre-investigate/profiles/notify-worker-prod.md` | - | free | No such file or directory (no stored profile: build one) |
| W0-Q7 | 08:50:00 | shell: `command -v agentbox-env` | - | free | exit 1, no output: standalone |
| W0-Q8 | 08:50:00 | aws sts get-caller-identity --profile prod-read | - | free | account 111122223333 matches; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b |
| W0-Q9 | 08:50:00 | kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod | - | free | assumed-role AWSReservedSSO_ReadOnly_..., group eks-readonly |
| W0-Q10 | 08:50:00 | kubectl config current-context | - | free | arn:aws:eks:us-east-1:111122223333:cluster/prod |
| W0-Q11 | 08:50:00 | kubectl auth can-i --list --context ... --namespace notify | - | free | `*.*` [get list watch]; create only on selfsubject{reviews,accessreviews,rulesreviews}: no write verbs |
| W0-Q12 | 08:50:00 | aws iam get-role --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | - | free | role ARN resolved (path /aws-reserved/sso.amazonaws.com/) |
| W0-Q13 | 08:50:00 | aws iam simulate-principal-policy --profile prod-read (10 fixed actions) | - | free | 10 rows all implicitDeny, but 3 requested actions missing and 3 unrequested present (G1) |
| W0-Q14 | 08:50:00 | helper PROFILE: kubectl --context CTX -n notify get deployments | now | free | `notify-worker` 0/3 ready, 3 up-to-date, 0 available, age 211d |
| W0-Q15 | 08:50:00 | helper PROFILE: kubectl ... -n notify get pods | now | free | 3 pods `notify-worker-5c8d7b9f4c-{8wq2d,jt6kz,x4p9n}` CrashLoopBackOff, 11 restarts, 35m |
| W0-Q16 | 08:50:00 | helper PROFILE: kubectl ... -n notify get services,ingresses,hpa | now | free | no output: none found (verified for this namespace) |
| W0-Q17 | 08:50:00 | helper PROFILE: kubectl ... -n notify get configmap | now | free | `notify-worker-config` (4 keys), `kube-root-ca.crt` |
| W0-Q18 | 08:50:00 | helper PROFILE: helm list --kube-context CTX -n notify | now | free | release `notify-worker` rev 12, updated 2026-10-22 08:14:20 UTC, chart 1.8.0, app 3.8.1 |
| W0-Q19 | 08:50:00 | helper PROFILE: aws sqs list-queues --profile prod-read --region us-east-1 --queue-name-prefix notify | now | free | `notify-outbound`, `notify-outbound-dlq` |
| W1-Q1 | 08:50:00 | kubectl ... -n notify rollout history deployment/notify-worker | - | free | revisions 6 and 7 only, change-cause none |
| W1-Q2 | 08:50:00 | kubectl ... -n notify get rs --sort-by=.metadata.creationTimestamp | - | free | `5c8d7b9f4c` 3/3 desired, 0 ready, 35m; `7f6b8c5d2e` 0/0, 15d |
| W1-Q3 | 08:50:00 | kubectl ... -n notify get events --sort-by=.lastTimestamp | last hour | free | at 35m ago: old RS scaled to 0 (3 Killing), new RS scaled to 3, 3 pods scheduled on 3 nodes; later: BackOff on all 3 pods; image already present; no probe, pull or scheduling events |
| W1-Q4 | 08:50:00 | kubectl ... -n notify describe pod notify-worker-5c8d7b9f4c-8wq2d | now | free | start 08:14:33; Last State Terminated Error exit code 1 (08:47:56); 11 restarts; limits 500m CPU, 256Mi; env from ConfigMap `notify-worker-config` and Secret `notify-smtp` key `password` (names only); annotation `checksum/config` present |
| W1-Q5 | 08:50:00 | kubectl ... -n notify logs notify-worker-5c8d7b9f4c-8wq2d --previous --timestamps --tail=50 | last crash 08:47:56 | free | fatal at config load: required environment variable NOTIFY_SMTP_RELAY_HOST is not set (config/load.go:58), 19 ms after start; raw/w1-q5-logs-previous-8wq2d.txt |
| W1-Q6 | 08:50:00 | helm history notify-worker --kube-context CTX -n notify --max 10 | - | free | rev 11 (2026-10-07 10:02:18, superseded) and rev 12 (2026-10-22 08:14:20, deployed); both chart 1.8.0 and app 3.8.1 |
| W1-Q7 | 08:50:00 | kubectl ... -n notify describe deployment notify-worker | now | free | strategy Recreate; 3 desired, 0 available; env from ConfigMap `notify-worker-config`; no probes listed; image tag 3.8.1; revision 7 |
| W1-Q8 | 08:50:00 | aws cloudwatch get-metric-data --profile prod-read --region us-east-1, AWS/SQS ApproximateNumberOfMessagesVisible QueueName=notify-outbound (verified, W0-Q19), Period 300, Maximum | incident 06:50-08:50 | est. 1 metric request, actual 1 | 12 points 07:50-08:45: 11,13,7,27,16 then 120, 1710, 3300, 4890, 6480, 8070, 9660; nothing before 07:50; raw/w1-q8-q12-sqs-incident.tsv |
| W1-Q9 | 08:50:00 | same metric, notify-outbound | previous 04:50-06:50 | 1 request | `{}`: no data (gap G3) |
| W1-Q10 | 08:50:00 | same metric, notify-outbound | -7d 2026-10-15 06:50-08:50 | 1 request | `{}`: no data (gap G3) |
| W1-Q11 | 08:50:00 | same metric, notify-outbound, Period 3600, Maximum | 14d 2026-10-08 06:50 to 2026-10-22 06:50 | 1 request | `{}`: no data (gap G3) |
| W1-Q12 | 08:50:00 | same metric, QueueName=notify-outbound-dlq (verified, W0-Q19), Period 300, Maximum | incident 06:50-08:50 | 1 request | 12 points 07:50-08:45, all 0 |
| W1-Q13 | 08:50:00 | same metric, notify-outbound-dlq, Period 3600, Maximum | 14d 2026-10-08 06:50 to 2026-10-22 06:50 | 1 request | `{}`: no data (gap G3) |
| W2-Q1 | 08:50:00 | git -C ~/src/notify-deploy log origin/main --since=2026-10-07T00:00:00Z --until=2026-10-22T09:00:00Z --date=iso-strict --format='%h %cI %an %s' -- charts/notify-worker (from the previous release 11 to now) | 2026-10-07 to 2026-10-22 | free | 2 commits: `3f9a1c2` 2026-10-22 08:03:41 UTC "align config key names with the shared SMTP chart (#214)"; `9e8d7c6` 2026-10-07 09:51:09 UTC "raise concurrency to 8 (#201)" (11 minutes before release 11) |
| W2-Q2 | 08:50:00 | kubectl ... -n notify get configmap notify-worker-config -o json, filtered with jq '.data \| keys' (names only) | now | free | keys: NOTIFY_FROM_ADDRESS, NOTIFY_QUEUE_URL, NOTIFY_WORKER_CONCURRENCY, SMTP_RELAY_HOST. `NOTIFY_SMTP_RELAY_HOST` is absent. Values not recorded. |
| W2-Q3 | 08:50:00 | kubectl --context CTX get cronjobs -A | now | free | no output: no CronJobs |
| W2-Q4 | 08:50:00 | kubectl ... -n notify logs notify-worker-5c8d7b9f4c-jt6kz --previous --timestamps --tail=50 | last crash | free | same fatal message as W1-Q5 |
| W2-Q5 | 08:50:00 | kubectl ... -n notify logs notify-worker-5c8d7b9f4c-x4p9n --previous --timestamps --tail=50 | last crash | free | same fatal message as W1-Q5 |
| W3-Q1 | 08:50:00 | git -C ~/src/notify-deploy show 3f9a1c2 (whole commit, no path filter) | commit | free | one file changed, `charts/notify-worker/values-prod.yaml`: key `NOTIFY_SMTP_RELAY_HOST` removed, key `SMTP_RELAY_HOST` added with the same value (values not recorded); no image, chart or other key changed |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1 AWS write-check incomplete: the simulation reply had no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack, and instead listed ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy (all implicitDeny) | none on the investigation (it is read-only regardless); the "no broad write found" statement covers 7 of 10 actions only | re-run the simulation and compare the action names, or have the role owner confirm the role is ReadOnlyAccess |
| G2 No log backend in environment.md: the wave-0 log probe was skipped | app logs come only from `kubectl logs --previous` (one crash deep per pod); no log history or counts | add a log datasource row (Loki, CloudWatch Logs) to environment.md |
| G3 CloudWatch SQS pulls returned no data for the previous window, the -7d window and both 14-day pulls (`{}`), and the incident window only from 07:50 | recurrence class is `unclassified` (Assumed); no -7d or 14-day baseline for queue depth, so the size of the backlog is compared only with the 80 minutes before onset | a human could check the queue's metric retention and dimensions in the CloudWatch console, or name another source |
| G4 No email-delivery counter, SLO or request metrics in environment.md | the number of emails or customers affected is Assumed; "emails are not delivered" is Likely, inferred from consumers 0/3 and the growing backlog | add a flow counter or SLO source to environment.md `core_flows` / `slo` |
| G5 Apply provenance: who or what ran Helm release 12 (CI job or a person) and the pipeline's apply record were not read; environment.md names no pipeline, and Helm and Kubernetes changes are not in CloudTrail | the tie between merged commit `3f9a1c2` and release 12 rests on the live ConfigMap key set plus the release time (11 minutes after the merge, like release 11 after its commit), not on a pipeline record | ask the owners of `notify-deploy` for the deploy job run that produced release 12 |
| G6 The old ReplicaSet's image was not read directly (`get rs` table has no image) | "image unchanged" rests on the commit diff and identical chart and app version in releases 11 and 12 | a human can compare the two ReplicaSets' images with the names-only recipe in the changes playbook |
| G7 Alarm coverage on `notify-outbound` (depth or age) not checked | unknown whether detection was delayed; no alarm history for recurrence | list the alarms for the queue in the CloudWatch console |
| G8 Application code (`example-org/notify-worker` at tag 3.8.1) not read | which variable name the app requires comes from its own fatal log line (W1-Q5), not from code; whether a later app version accepts `SMTP_RELAY_HOST` is unknown | read `config/load.go` at the deployed tag with read-only `gh`, or ask the app owners |
| G9 Freshness of the `notify-deploy` clone not verified (no fetch allowed) and the default branch name `main` is assumed | commits after the clone's last fetch could be missing; release 12 is explained by `3f9a1c2` already | confirm with `gh` against the remote |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (`lessons.md` does not exist) |
| Re-verified this run | none |
| History lookup | run after H1-H8 were ranked: `grep -rEl 'notify-worker\|crash-restart\|queue-backlog' .culiops/sre-investigate/incidents/` printed nothing; the directory does not exist (W0-Q4), so no history yet and no `from-history:` leads |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| failure-mode | kubectl | CrashLoopBackOff right after a values-only Helm release (chart and image unchanged): `kubectl logs --previous` names the missing environment variable; compare it with the ConfigMap key names and the values diff | W1-Q5 |
| identifier | kubectl | Deployment notify-worker in namespace notify, Helm release notify-worker, queues notify-outbound and notify-outbound-dlq; no log backend, logs only through kubectl logs --previous | W0-Q14 |
| process | cloudwatch | SQS get-metric-data for notify-outbound returned points only for 07:50-08:45 and nothing for the previous, -7d and 14d windows; treat as a coverage gap and check retention before trusting any baseline | W1-Q11 |
