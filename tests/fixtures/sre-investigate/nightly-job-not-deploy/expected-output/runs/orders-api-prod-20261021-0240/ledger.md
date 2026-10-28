# Ledger: orders-api prod 20261021-0240

Mode: Fast
Budget used: 17 shell calls (3 access in wave 0, 2 profile build, 12 evidence in waves 1-3) of the template's neutral Fast value of 20 (environment.md sets no query cap) · about 0.31 GB of logs scanned (W2-Q5 about 0.07 GB + W3-Q1 about 0.24 GB, both pro-rated, see the query rows) of a neutral 2 GB; environment.md's own limit is the ask threshold of 10 GB per query, never reached · 26 CloudWatch metric requests (22 in wave 1, 4 in wave 2) of a neutral 100 · no other metered units

## Problem

| Field | Value |
|---|---|
| What | Reporter: "orders-api in prod has been throwing 5xx since around 11 this morning. We shipped a release just before that." Restated: orders-api target 5xx above baseline starting 2026-10-21 02:01 UTC; the data says it ended 02:19 UTC. |
| Where | orders-api, prod, ECS Fargate cluster `prod`, service `orders-api` (6 tasks), ALB `app/prod-public/50dc6c495c0c9188`, target group `targetgroup/orders-api/943f017f100becff`. No siblings (one service, one region, one target group). |
| When | Reported: "around 11 this morning", Asia/Tokyo = 02:00 UTC on 2026-10-21 (reporter). True onset 02:01 UTC (first minute above 10 target 5xx, W1-Q2a); alarm into ALARM 02:04:00 UTC (W1-Q4). Ended: last 5xx datapoint 02:19 UTC; alarm OK 02:12 UTC. |
| Who is affected | Callers of `POST /orders` and `PATCH /orders/{id}` (both are core flows) that hit a database lock wait (about 50 s then HTTP 500); share of requests unknown (no request count readable). |
| Trigger | Report from the operator in chat. The only alarm on the service, `orders-api-5xx-high`, was found in wave 0 and used as a recurrence source. No ticket. |
| Mitigations already applied | none known. The recovery at about 02:19-02:20 UTC coincides with the nightly job stopping (02:20:14), not with an action by a person. |
| Assumptions made at intake | (1) Time zone for "around 11 this morning": Asia/Tokyo, UTC+9, given by the operator in chat (environment.md has no `timezone`); NOT taken from the `+09:00` in CloudWatch output. (2) Anchor 11:00 Tokyo = 02:00 UTC on 2026-10-21; window = 30 min before the anchor to now. (3) "Now" = 2026-10-21 02:40 UTC: the `date -u` probe printed nothing; the operator was told and could correct it; no correction came. (4) `git rev-parse --show-toplevel` printed nothing; the current directory was treated as the repo root. (5) environment.md defines only `insights_ask_threshold_gb` (10); the other budgets use the template's neutral values (Fast: 20 queries, 2 GB, 100 metric requests; window caps 48h/2h/12h/30m). |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | no write allowed among the 7 of 10 fixed actions the simulation returned (all implicitDeny); 3 fixed actions had no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) so "read-only confirmed" is NOT claimed; 3 extra rows outside the fixed list (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) were also implicitDeny and are not counted. No boxed warning shown (nothing allowed). | session valid; no Kubernetes contexts; environment.md lists no token-based datasource, so no token checks; `agentbox-env` not found (nothing said about Culibox) |

## Impact

| Field | Value |
|---|---|
| Symptom | orders-api targets returned HTTP 5xx: 439 between 01:30 and 02:40 UTC (3 in the 70 minutes before); peak 55 per minute at 02:04. Lines show `ER_LOCK_WAIT_TIMEOUT` after about 50 s on `POST /orders` and `PATCH /orders/{id}`; one `GET /orders` took 8.1 s with status 200. |
| Affected | prod orders-api, customer-facing; both listed core flows appear in the error lines. Failing share of requests: unknown (RequestCount returned an empty object). |
| Since / ongoing | 02:01 UTC / ended: last 5xx datapoint 02:19 UTC, none to 02:40; alarm OK since 02:12 UTC |
| Suggested severity | SEV2 because it is a significant, partial, short degradation of a customer-facing service (peak 55 5xx/min for about 18 minutes) and both core flows appear in the error lines; SEV1 (core flow down or more than 5% of requests failing) cannot be shown without a request count. Incident owner decides. |
| Basis | W1-Q2a, W1-Q4, W2-Q5b, W3-Q1b · Confirmed for the counts and error types; Assumed for the failing share and the severity |
| Third party in the path | none known. `ECONNRESET` on the payments call (6 lines today) is an internal downstream by its name `PAYMENTS_URL` (name only); no vendor named. |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-21 01:30 | 2026-10-21 02:40 |
| Baseline (previous) | 2026-10-21 00:20 | 2026-10-21 01:30 |
| Baseline (-7d) | 2026-10-14 01:30 | 2026-10-14 02:40 |

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | `orders-api-5xx-high` into ALARM: 2026-10-08 02:04, 10-11 02:04, 10-14 02:09, 10-16 02:05, 10-19 02:04, 10-21 02:04; back to OK: 10-08 02:11, 10-11 02:11, 10-14 02:17, 10-16 02:12, 10-19 02:11, 10-21 02:12. All timestamps were printed with +09:00 and converted to UTC. No sibling alarms exist. |
| Signal, 14d at 1h resolution | `HTTPCode_Target_5XX_Count`, Sum, zero-filled (counter reported only in minutes with errors). 336 hourly points. Baseline with hours at or above the incident level (439) left out (only 10-14 02:00 = 455): median 1 · p95 6 · max 421 · n 335. Hours outside the 02:00 UTC hour: max 31 (10-15 14:00). The 02:00 UTC hour on the 14 nights 10-07 to 10-20: 88, 421, 61, 117, 386, 74, 52, 455, 133, 398, 69, 104, 412, 96 (median 110.5). Incident hour (02:00 on 10-21): 438. |
| Coverage | Metric: 336 of 336 hours returned, status Complete, window 2026-10-07 01:30 to 2026-10-21 01:30 UTC. Alarm history: 12 items, oldest 2026-10-08 02:04 UTC although 30 days back is 2026-09-21: no transitions 09-21 to 10-07 (or the alarm is younger; creation date not shown). The pattern before 2026-10-07 is not covered. |
| Class | `scheduled` · shape: `periodic` (fast ramp 13 to 55 per minute in three minutes, then decay over 15 minutes, at the same time of day) |
| Reason | Rule 1 (first match): at least three occurrences starting within +/-15 minutes of the same time of day. Six alarm episodes began 02:04, 02:04, 02:09, 02:05, 02:04, 02:04 UTC, and the 02:00 UTC hour is elevated on all 14 earlier nights. Minute-level alarm times, so the class can be Confirmed. The big nights (421, 386, 455, 398, 412, 438) recur every 2 to 3 days; why some nights are about 4x larger is not explained. |
| Label and queries | Confirmed · W1-Q3, W1-Q4, W2-Q2b |

## Timeline

Times are UTC; rows from the reporter are marked.

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-09-30 10:02:17 | task definition `orders-reconcile:7` registered (image tag 2026.09.30-1); live revision of the nightly job since then | ECS | W2-Q1f |
| 2026-10-14 02:05:02 | nightly RunTask starts 5 minutes late (02:05:02 instead of 02:00:02) | CloudTrail | W2-Q2b |
| 2026-10-14 02:06 to 02:24 | 5xx ramp (14 at 02:06, peak 57 at 02:09, 2 at 02:24), total 459 | CloudWatch | W1-Q2c |
| 2026-10-14 03:10:44 / 03:10:53 | `orders-api:41` registered / UpdateService (deploy-pipeline role) | ECS, CloudTrail | W2-Q1e, W2-Q2c |
| 2026-10-21 01:18:02 | release 2026.10.21-1 created (release-bot) | gh | W2-Q3b |
| 2026-10-21 01:21:58 | `orders-api:42` registered (image tag 2026.10.21-1) | ECS, CloudTrail | W2-Q1d, W2-Q2a |
| 2026-10-21 01:22:07 | UpdateService / deployment ecs-svc/4417203958112934411 starts | CloudTrail, ECS | W2-Q2a, P-Q2c |
| 2026-10-21 01:22:31 to 01:22:51 | 6 new tasks created; 01:25:48 and 01:29:12 old tasks (3 each) stopped | ECS service events | P-Q2c, W1-Q1b |
| 2026-10-21 01:31:40 | deployment completed, steady state; no service event after this | ECS service events | P-Q2c |
| 2026-10-21 02:00 (reporter) | operator's "around 11 this morning" in Tokyo | reporter | operator line 1 |
| 2026-10-21 02:00:02 | EventBridge rule `orders-reconcile-nightly` starts `orders-reconcile:7` (RunTask); task started 02:00:09 | CloudTrail, ECS | W2-Q2a, W1-Q1e |
| 2026-10-21 02:01 | first minute above 10 target 5xx (13) | CloudWatch | W1-Q2a |
| 2026-10-21 02:01:13 | first `ER_LOCK_WAIT_TIMEOUT` line seen (POST /orders, 50 s) | Logs Insights | W2-Q5b |
| 2026-10-21 02:04 | peak 55 per minute; alarm into ALARM at 02:04:00 | CloudWatch | W1-Q2a, W1-Q4 |
| 2026-10-21 02:12 | alarm back to OK | CloudWatch | W1-Q4 |
| 2026-10-21 02:19 | last 5xx datapoint (2) | CloudWatch | W1-Q2a |
| 2026-10-21 02:20:14 | reconcile task stopped, exit code 0 (stopping at 02:19:52) | ECS | W1-Q1e |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| sched:orders-reconcile-nightly | The nightly reconcile task (02:00 UTC) causes database lock contention and orders-api writes fail while it runs | onset within +/-15 min of the fire time; same on earlier nights; start and stop follow the job; lock-related errors in app logs | CloudTrail RunTask times against 5xx start on late-start nights; stopped-task window; app error lines | main | Likely (schedule and timing Confirmed; lock holder is inferred) |
| H-deploy | Release 2026.10.21-1 (orders-api:42) broke the failing path | errors start as the new revision takes traffic; a new error type | same spike before this revision existed; UpdateService history | main | Ruled out |
| H-db | Database lock contention or CPU | lock-wait errors in logs; Aurora lock, connection, CPU metrics up | Aurora metrics at baseline plus flat per-request query count | main | Assumed (DB metrics unreadable; lock-wait errors in logs support it) |
| H-churn | Task churn, probe failures, scheduling failure | stopped tasks, unhealthy targets, scheduling events near 02:00 | stopped tasks and service events | main | Ruled out |
| H-payments | Payments downstream resets cause the 5xx | ECONNRESET dominates the error codes | error count by code | main | Ruled out (6 of 442 error lines) |
| H-traffic | Traffic spike or bot | request count above baseline | request count | main | Assumed (no request count readable) |

- `sched:orders-reconcile-nightly` status: supported · evidence: W1-Q1e, W1-Q2, W1-Q4, W2-Q1a, W2-Q1b, W2-Q2a, W2-Q2b, W2-Q5b, W3-Q1b · note: main session, Fast mode. Weakest link = that the job (not something else at 02:00 UTC) holds the contended locks.
- `H-deploy` status: refuted · evidence: W1-Q2c (same spike 7 days earlier), W1-Q3 (14 nights), W2-Q2c (only two deployments in 14 days, 10-14 03:10 and 10-21 01:22), W2-Q1d/e (only the image tag differs between :41 and :42) · note: ruled out on timing and recurrence; the code diff was not readable (W3-Q2), release notes are context only.
- `H-db` status: open · evidence: W2-Q4a, W2-Q4b (empty replies), W2-Q5b, W3-Q1b · note: the lock-wait errors are the database's own symptom; no DB-side data.
- `H-churn` status: refuted · evidence: P-Q2c (no service event after 01:31:40), W1-Q1b (all 6 tasks created 01:22:31-01:22:51 and healthy), W1-Q1c (no stopped tasks of the service).
- `H-payments` status: refuted · evidence: W3-Q1b · note: no baseline day was queried, so the 6 resets are not called noise.
- `H-traffic` status: open · evidence: none readable (W1-Q2d..f empty).

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (read through `gh`, no local clone) | (unverified) | not read | not read | release tag 2026.10.21-1 (= image tag of orders-api:42, created 2026-10-21T01:18:02Z); commit SHA not resolved; diff against 2026.10.14-2 not readable (W3-Q2) |

## Query log

Clock probe (`date -u`) printed nothing in every wave, so the Start column cannot be filled; order is by ID.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | clock n/a | local: `date -u +%H:%M:%S; command -v agentbox-env` | n/a | none | no output; `agentbox-env` not found |
| W0-Q2 | clock n/a | prod-read: `sts get-caller-identity`; `iam get-role` (role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, from the sts reply); `iam simulate-principal-policy` (10 fixed actions) | n/a | free | account 111122223333 matches; 7 of 10 fixed actions returned implicitDeny, 3 missing rows (gap), 3 extra rows. Not "read-only confirmed". link: `aws iam simulate-principal-policy` read-only |
| W0-Q3 | clock n/a | prod-read: `logs describe-log-groups --log-group-name-prefix /ecs/` | n/a | free; 15-min estimate for /ecs/orders-api 0.022 GB | `/ecs/orders-api` 64,424,509,440 bytes stored, retention 30 d; `/ecs/orders-reconcile` 1,073,741,824 bytes · identifiers verified (listed) |
| W0-Q4 | clock n/a | prod-read: `cloudwatch describe-alarms` | current | free | one alarm `orders-api-5xx-high`, OK since 02:12 UTC, threshold 25/min, 2 of 3 datapoints |
| W0-Q5 | clock n/a | local: `ls .culiops/sre-investigate` | n/a | none | only environment.md: no profile, no lessons, no incidents |
| P-Q1 | clock n/a | [helper PROFILE, cheapest tier] prod-read: `ecs list-clusters`; `cloudwatch list-metrics --namespace AWS/ApplicationELB`; `ecs list-task-definition-families --status ACTIVE` | n/a | free | cluster `prod`; six ALB metrics for TG `targetgroup/orders-api/943f017f100becff` + LB `app/prod-public/50dc6c495c0c9188` (no HTTPCode_ELB_5XX_Count listed); families orders-api, orders-migrate, orders-reconcile |
| P-Q2 | clock n/a | [helper PROFILE, cheapest tier] prod-read: `ecs list-services --cluster prod`; `ecs describe-services --cluster prod --services orders-api` | current | free | service orders-api ACTIVE FARGATE 6/6; PRIMARY deployment created 01:22:07Z, COMPLETED 01:31:40Z, td orders-api:42; circuit breaker on; service events newest 01:31:40Z (6 events) |
| W1-Q1 | clock n/a | prod-read: `ecs list-tasks` (running, stopped-for-service, stopped-cluster) + `describe-tasks` | current; stopped tasks last about 1 h | free | 6 running tasks all `orders-api:42` created 01:22:31-01:22:51Z HEALTHY; no stopped task for the service; 1 cluster-wide stopped task: `orders-reconcile:7` startedBy rule `orders-reconcile-nightly`, started 02:00:09Z, stopped 02:20:14Z, exit 0. Confirmed |
| W1-Q2 | clock n/a | prod-read: `cloudwatch get-metric-data` q-5xx-60 and q-signals-60, three windows (raw/m-5xx-*.json, raw/m-signals-*.json) | incident 01:30-02:40Z; previous 00:20-01:30Z; -7d 2026-10-14 01:30-02:40Z; Period 60 | 21 metric requests | 5xx: incident 439 (20 non-zero minutes, peak 55 at 02:04), previous 3, -7d 459 (peak 57 at 02:09); same shape a week earlier. q-signals (RequestCount, ELB 5xx, p95, UnHealthyHostCount, ECS CPU, ECS memory) returned `{}` in all three windows: a failed read, not zeros (gap). Confirmed for the 5xx counts |
| W1-Q3 | clock n/a | prod-read: `get-metric-data` q-recur-3600 (FILL zero) + jq statistics | 2026-10-07 01:30 to 2026-10-21 01:30Z; Period 3600 | 1 metric request | 336 of 336 hours; median 1, p95 6, max 421 (hours at or above 439 left out); 02:00 UTC hour elevated on all 14 nights (52 to 455). Confirmed |
| W1-Q4 | clock n/a | prod-read: `cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high` + jq UTC conversion (raw/alarm-history-utc.tsv) | 2026-09-21 01:30 to 2026-10-21 02:40Z | free | 12 items; 6 episodes into ALARM at 02:04-02:09Z; none before 10-08. Confirmed |
| W1-Q5 | clock n/a | prod-read: `events list-rules` (schedule only), `scheduler list-schedules`, `application-autoscaling describe-scaling-activities`, `describe-scheduled-actions` (service/prod/orders-api) | current | free | `orders-reconcile-nightly` cron(0 2 * * ? *) UTC; `catalog-sitemap-weekly` cron(30 3 ? * SUN *); no Scheduler schedules; both Application Auto Scaling calls returned `{}` (gap) |
| W2-Q1 | clock n/a | prod-read: `events describe-rule` and `list-targets-by-rule` (`orders-reconcile-nightly`); `ecs list-task-definitions` + `describe-task-definition` for orders-api 42/41 and orders-reconcile 7/6, names only (raw/c-taskdefs.json) | current | free | rule targets `orders-reconcile:7` in cluster prod; :42 vs :41 differ only in image tag and registration time; :7 vs :6 same env names; :7 live since 2026-09-30. Confirmed |
| W2-Q2 | clock n/a | prod-read: `cloudtrail lookup-events` x3 (ReadOnly=false 00:01-02:16Z; EventName=RunTask and EventName=UpdateService 2026-10-07 to 2026-10-21 02:20Z), us-east-1, CloudTrailEvent omitted | as stated | free | 3 ECS writes in the window; 15 RunTask events (02:00:02Z nightly; 10-14 02:05:02Z; 10-16 02:01:02Z); 2 UpdateService events (10-14 03:10:53Z, 10-21 01:22:07Z). Confirmed |
| W2-Q3 | clock n/a | `gh release list`, `gh release view` (latest), example-org/orders-api | current | free | releases 2026.10.21-1 (latest), 2026.10.14-2, 2026.10.07-1; notes #1182, #1185, #1187 (context only). Tag equals deployed image tag |
| W2-Q4 | clock n/a | prod-read: `cloudwatch list-metrics --namespace AWS/RDS --dimensions DBClusterIdentifier=orders-db` (unverified); `get-metric-data` q-rds-60 (DatabaseConnections, CPUUtilization, RowLockTime, Deadlocks) | incident window 01:30-02:40Z; Period 60 | 4 metric requests | both returned `{}`; `orders-db` stays `(unverified)`; nothing learned (gap) |
| W2-Q5 | clock n/a | Logs Insights `/ecs/orders-api` (verified): `fields @timestamp, @message \| filter @message like /(?i)error\|exception\|"status":5/ \| sort @timestamp asc \| limit 100` (queryId c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b) | 2026-10-21 02:00-02:20Z | est. 0.030 GB | Complete; 8 rows; 6 `ER_LOCK_WAIT_TIMEOUT` (about 50 s) on POST /orders and PATCH /orders/{id}, 1 `ECONNRESET` 502 (payments), 1 slow 200. bytesScanned in the statistics block (0.48 GB) belongs to the source file's two covered windows (140 min); pro-rated to this query about 0.069 GB; ratio to estimate 2.3. Sample, not a count. Confirmed (that these errors occurred) |
| W3-Q1 | clock n/a | Logs Insights `/ecs/orders-api`: `filter ispresent(error_code) \| stats count(*) as n by error_code, bin(1d)` (queryId 2b7e9a10-3c4d-4e5f-8a9b-0c1d2e3f4a5b) | 2026-10-21 00:00-02:40Z | est. 0.24 GB | Complete; ER_LOCK_WAIT_TIMEOUT 431, ECONNRESET 6, UPSTREAM_TIMEOUT 5 (442 lines; metric shows 439 in 01:30-02:40 plus 3 earlier). The statistics block (30.2 GB) is for the source file's 14-day window; pro-rated about 0.24 GB, ratio 1.0. Confirmed |
| W3-Q2 | clock n/a | `gh api --method GET repos/example-org/orders-api/compare/2026.10.14-2...2026.10.21-1` with a `--jq` filter | n/a | free | returned `{}`: no commits or files; release diff unreadable (gap) |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability for 3 of the 10 fixed actions was not evaluated (simulation reply lacked ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack and held 3 other actions) | none on the investigation (it is read-only); the credentials cannot be called "read-only confirmed" | read-only follow-up: `aws iam list-attached-role-policies --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, or ask the account owner to confirm the role is read-only |
| `GetMetricData` returned `{}` for RequestCount, HTTPCode_ELB_5XX_Count, TargetResponseTime, UnHealthyHostCount and ECS CPU and memory (W1-Q2d..f), although `list-metrics` lists most of them | no error percentage, no latency, no host-health or saturation data; severity and impact share stay `Assumed`; H-traffic is untestable; capacity is not tested | open the same metrics in the CloudWatch console for 01:30-02:40 UTC, or find out why the call returns an empty object |
| Aurora `orders-db` metrics returned `{}` and the cluster name is only from environment.md (W2-Q4) | H-db cannot be supported or refuted from the database side; the mechanism link stays `Likely` | confirm the cluster identifier, then read DatabaseConnections, RowLockTime, Deadlocks and CPU for 02:00-02:20 UTC |
| `/ecs/orders-reconcile` logs not read (one log query per wave; Fast mode has three waves) | nothing shows what the job locks, how long its batches run or whether it logs lock waits; caps the mechanism link at `Likely` | say "go deep", or read that log group for 02:00-02:20 UTC |
| Release diff unreadable (`gh api compare` returned `{}`) | the release is ruled out on timing and recurrence, not on code | read PRs #1182, #1185, #1187 |
| Application Auto Scaling calls returned `{}` | cannot say whether the service autoscales; low impact (6/6 tasks, no churn) | check the service's auto scaling in the console |
| No IaC repo named in environment.md | IaC history not read; the schedule's source of truth is unknown | name the IaC repo in environment.md |
| No business counter for checkout or order status in environment.md | core-flow impact is only seen through error lines, not a counter against the same window 7 days earlier | name a counter |
| Alarm history starts 2026-10-08 and the metric pull starts 2026-10-07 | cannot say whether the pattern predates 2026-10-07 | pull `HTTPCode_Target_5XX_Count` at Period 3600 for 60 days |
| Clock and git probes printed nothing | the window and run id assume now = 2026-10-21 02:40 UTC; the operator was told | none needed unless "now" is wrong |

## Untrusted text

none seen.

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (`lessons.md` does not exist) |
| Re-verified this run | none |
| History lookup | `incidents/` does not exist (W0-Q5), so no match; it was to run only after the ranked list existed |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | A service-scoped list of STOPPED ECS tasks missed the scheduled task that mattered; also list the cluster's stopped tasks and read `startedBy` (events-rule/...) | W1-Q1d |
| identifier | cw-logs | `/ecs/orders-api` holds JSON lines with the fields level, status, route, error_code, msg, duration_ms, ecs_task_revision | W2-Q5b |
| identifier | cloudwatch | orders-api ALB metrics use LoadBalancer `app/prod-public/50dc6c495c0c9188` and TargetGroup `targetgroup/orders-api/943f017f100becff`; HTTPCode_Target_5XX_Count is reported only for minutes with errors | W1-Q2a |
| process | cloudwatch | `get-metric-data` for RequestCount, TargetResponseTime, UnHealthyHostCount and ECS CPU/memory returned an empty object although list-metrics lists them; treat as a failed read, not zero | W1-Q2d |
| process | aws | `iam simulate-principal-policy` returned rows for ecs:StopTask, ec2:ModifyInstanceAttribute and iam:AttachRolePolicy instead of 3 of the 10 requested actions; check the action names in the reply | W0-Q2d |
| identifier | cloudwatch | Aurora `orders-db`: list-metrics and get-metric-data (DBClusterIdentifier=orders-db) returned an empty object; the name is unverified | W2-Q4a |
| failure-mode | cw-logs | orders-api 5xx at 02:00-02:20 UTC on nights the orders-reconcile task runs: ER_LOCK_WAIT_TIMEOUT (about 50 s) on POST /orders and PATCH /orders/{id}; alarm orders-api-5xx-high fires 02:04-02:09 on the big nights | W3-Q1b |
