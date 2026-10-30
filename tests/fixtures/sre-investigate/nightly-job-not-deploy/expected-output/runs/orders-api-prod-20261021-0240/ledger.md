# Ledger: orders-api prod 20261021-0240

Mode: Fast (operator asked for Fast; incident reported as ongoing)
Budget used (after wave 3, final): 18 / 20 queries (counted: every call except the identity and write-check calls W0-Q1, W0-Q2 and the local `ls` W0-Q5) · 0.481 / 2 GB logs scanned (reported bytesScanned of W2-Q5 0.481 GB plus W3-Q1 0.00006 GB) · 19 / 100 CloudWatch metric requests (18 for the three golden-signal windows, 1 for the 14-day pull) · no other metered units. Budgets other than `insights_ask_threshold_gb: 10` are not set in environment.md; template Fast defaults used.

## Problem

| Field | Value |
|---|---|
| What | Reported: "orders-api in prod has been throwing 5xx since around 11 this morning. We shipped a release just before that." Measurable restatement: HTTP 5xx returned by the orders-api targets behind ALB prod-public from about 11:00 local (02:00 UTC) on 2026-10-21. |
| Where | orders-api, prod, account 111122223333, us-east-1, ECS cluster `prod`. No sibling regions, shards or tenants; 6 ECS tasks are the replicas. |
| When | Reported: "around 11 this morning" = about 02:00 UTC 2026-10-21 (Asia/Tokyo, UTC+9, zone given by the user in chat). Measured onset: 02:01 UTC (first minute with a burst, 13 target 5xx). Alarm entered ALARM 02:04:00 UTC, back to OK 02:12:00 UTC. Last non-zero minute 02:19 UTC. |
| Who is affected | Callers of orders-api through ALB prod-public. Failing share of requests not measurable (RequestCount not returned, gap). Sampled failing lines are `POST /orders` and `PATCH /orders/{id}`, the two core flows in environment.md (W2-Q5). |
| Trigger | Operator report in chat; alarm `orders-api-5xx-high` (not named by the reporter) fired 02:04 UTC. |
| Mitigations already applied | none known |
| Assumptions made at intake | (1) environment.md has no `timezone`; the user answered "Tokyo time, UTC+9", used as Asia/Tokyo (no DST); recorded here and not written to environment.md. (2) "around 11 this morning" is local: window = 30 min before 11:00 JST (01:30 UTC) to now (02:40 UTC). (3) Budgets other than the Insights threshold are not in environment.md; template Fast defaults used. (4) The shell `date` command returns nothing in this simulated machine; the run start 02:40 UTC is taken from the newest data timestamp the account returns, and Start times in the query log are nominal. (5) Budget unit "queries" = tool calls (a call may chain commands of one kind); identity and write-check calls are not counted. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read (account 111122223333, us-east-1; matches environment.md) | role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b (IAM Identity Center permission set; session name not recorded) | no write action allowed in the 7 actions that were answered (all implicitDeny: s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode); write capability unknown (gap) for 3 of the 10: ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no row. Not "read-only confirmed". | No token-based backend listed in environment.md, so no token check. Culibox: `command -v agentbox-env` failed, nothing printed. Three unasked rows (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; implicitDeny) came back in the reply; not counted. |
| Kubernetes | none in environment.md (ECS Fargate estate) | not applicable | no context to check |

## Impact

Source order: no SLO named; request/error metrics against baseline (errors only, requests did not return); so the failing share is `Assumed`.

| Field | Value |
|---|---|
| Symptom | Target 5xx burst: 438 target 5xx between 02:01 and 02:19 UTC (peak 55/min at 02:04), against 3 in the 70 minutes before and a similar burst (459, peak 57/min at 02:09) in the same time-of-day window seven days earlier. Sampled lines: 500s from 50-second database lock waits, and one 502 from a payments connection reset. |
| Affected | orders-api behind ALB prod-public, all 6 tasks (single target group). Failing share of requests unknown (RequestCount gap). Core flows `POST /orders` (checkout) and `PATCH /orders/{id}` both appear in sampled failing lines (W2-Q5). Customer-facing vs internal: unknown (ALB is named prod-public; Assumed). |
| Since / ongoing | Onset 02:01 UTC (11:01 JST). Ongoing: no. Last non-zero minute 02:19 UTC; no datapoint 02:20-02:40 (HTTPCode_Target_5XX_Count is reported only when non-zero, so absence = 0). Alarm back to OK 02:12:00 UTC. |
| Suggested severity | SEV2 because a prod service behind a public-named ALB returned up to 55 5xx/min for about 19 minutes (partial degradation, core flows among the failures). SEV1 (a core flow down, or more than 5% of requests failing) cannot be shown: the failing share was not measurable. The incident owner decides. |
| Basis | ALB target 5xx counts against the previous window and -7d · W1-Q3 · Confirmed for the counts; failing share `Assumed`; core-flow involvement from 6 sampled lines · W2-Q5 · Likely |
| Third party in the path | none known (a payments service is called via PAYMENTS_URL, an internal-looking host; one sampled 502; see H7) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-21 01:30:00 | 2026-10-21 02:40:00 |
| Baseline (previous) | 2026-10-21 00:20:00 | 2026-10-21 01:30:00 |
| Baseline (-7d) | 2026-10-14 01:30:00 | 2026-10-14 02:40:00 |

Re-anchored: no (the measured onset 02:01 is 1 minute from the assumed anchor 02:00 and inside the window)

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | orders-api-5xx-high into ALARM: 10-08 02:04:00, 10-11 02:04:00, 10-14 02:09:00, 10-16 02:05:00, 10-19 02:04:00, 10-21 02:04:00; back to OK: 02:11, 02:11, 02:17, 02:12, 02:11, 02:12 (tool printed +09:00 offsets, converted to UTC). No sibling alarms exist. Each ALARM time is the RunTask time of that day plus 4 minutes (W2-Q4: 02:00:02, 02:00:02, 02:05:02, 02:01:02, 02:00:02, 02:00:02). |
| Signal, 14d at 1h resolution | HTTPCode_Target_5XX_Count Sum per hour (counter; zero-filled because the metric is reported only when non-zero), 2026-10-07 01:00 to 2026-10-21 01:00, 336 points (233 returned, 103 zero-filled) · median 1 · p95 6 (both over the 335 hours below the incident level 438) · max before the incident 455 (10-14 02:00) · incident 438 (hour 02:00-03:00 on 10-21, from W1-Q3). The 02:00 UTC hour was the day's highest hour on all 14 days: 88, 421, 61, 117, 386, 74, 52, 455, 133, 398, 69, 104, 412, 96 (10-07 to 10-20). The highest value outside the 02:00 hour is 31. |
| Coverage | Metric pull: 14 days complete. Alarm history: 30 days requested, oldest item returned 2026-10-08 (the API keeps about 14 days), so transitions before 10-08 are not visible. CloudTrail RunTask history: 10-07 to 10-21 (15 events). |
| Class | `scheduled` · shape: periodic (a burst at the same time each day), decaying over about 20 minutes |
| Reason | Rule 1 matched: six alarm transitions into ALARM within +/-15 min of 02:04 UTC (02:04, 02:04, 02:09, 02:05, 02:04, 02:04) on 10-08, 10-11, 10-14, 10-16, 10-19, 10-21; and the hourly signal peaks in the 02:00 hour on 14 of 14 prior days. Not chronic (incident 438 > p95 6). |
| Label and queries | Confirmed · W1-Q4, W1-Q5, W2-Q4 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 10-07 to 10-20, 02:00 hour daily | 5xx burst in the 02:00-03:00 hour on every day (52 to 455 per hour) | CloudWatch hourly | W1-Q4 |
| 10-07 to 10-21, 02:00:02 daily | RunTask of orders-reconcile:7 by ecsEventsRole on 13 days; 02:05:02 on 10-14; 02:01:02 on 10-16 | CloudTrail | W2-Q4 |
| 10-07 02:58:31 | orders-api:40 registered (image 2026.10.07-1) by deploy-pipeline | ECS task definition | W2-Q1 |
| 10-14 02:05:02 | RunTask of the reconcile job (5 minutes late) | CloudTrail | W2-Q4 |
| 10-14 02:06-02:24 | Burst 14, 31, 46, 57 (peak 02:09) decaying to 2 at 02:24 (-7d window); starts one minute after the late RunTask | CloudWatch minute | W1-Q3 |
| 10-14 03:10:44 and 03:10:53 | orders-api:41 registered (image 2026.10.14-2), then UpdateService | CloudTrail, ECS | W2-Q1, W2-Q4 |
| 10-20 19:02:10 | ECS service reached a steady state (earlier event; not interpreted) | ECS service events | W1-Q1 |
| 10-21 01:18:02 | Release 2026.10.21-1 created (release-bot) | gh release view | W2-Q1 |
| 10-21 01:21:58 | orders-api:42 registered (image 2026.10.21-1) | CloudTrail, ECS | W2-Q1, W2-Q3 |
| 10-21 01:22:07 | UpdateService; deployment ecs-svc/4417203958112934411 created | CloudTrail, ECS | W2-Q3, W1-Q1 |
| 10-21 01:22:31 | 6 new tasks started (all orders-api:42, running 01:23:09-01:23:29) | ECS events, describe-tasks | W1-Q1, W1-Q2 |
| 10-21 01:25:48 and 01:29:12 | 3 old tasks stopped each time (6 old tasks total) | ECS service events | W1-Q1 |
| 10-21 01:31:40 | Deployment COMPLETED; service at steady state (29 minutes before the onset) | ECS service events | W1-Q1 |
| 10-21 01:44 | 1 target 5xx (background level; the only 5xx between rollout completion and the onset) | CloudWatch minute | W1-Q3 |
| 10-21 02:00:02 | RunTask orders-reconcile:7 (rule orders-reconcile-nightly, cron(0 2 * * ? *)) | CloudTrail | W2-Q3, W1-Q6 |
| 10-21 02:00:09 | Reconcile container started | ECS describe-tasks | W2-Q2 |
| 10-21 02:00:11.902 | Reconcile log: "start run_id=20261021-0200 window=previous_day batch_size=5000 mode=SELECT ... FOR UPDATE" | Logs Insights /ecs/orders-reconcile | W3-Q1 |
| 10-21 02:00:12.448 | Reconcile log: "locking orders rows created 2026-10-20 (estimated 1,184,000 rows)" | Logs Insights /ecs/orders-reconcile | W3-Q1 |
| 10-21 02:00 | Reporter: "around 11" local = 02:00 UTC (from the reporter, not from a query) | reporter | n/a |
| about 02:00:23 | First failing request starts waiting (logged 02:01:13.208 with duration 50,021 ms; computed) | Logs Insights | W2-Q5 |
| 10-21 02:01 | First burst minute: 13 target 5xx | CloudWatch minute | W1-Q3 |
| 10-21 02:01:13 | First sampled error line: POST /orders, 500, ER_LOCK_WAIT_TIMEOUT | Logs Insights | W2-Q5 |
| 10-21 02:04 | Peak 55/min; alarm into ALARM at 02:04:00 | CloudWatch, alarm history | W1-Q3, W1-Q5 |
| 10-21 02:09:37 | Reconcile log: "progress 600000/1184212 rows" | Logs Insights /ecs/orders-reconcile | W3-Q1 |
| 10-21 02:12:00 | Alarm back to OK | alarm history | W1-Q5 |
| 10-21 02:19 | Last non-zero minute (2); zero after | CloudWatch minute | W1-Q3 |
| 10-21 02:19:48.630 | Reconcile log: "committed 1184212 rows, 37 mismatches written to recon_exceptions" | Logs Insights /ecs/orders-reconcile | W3-Q1 |
| 10-21 02:19:51.877 | Reconcile log: "done in 1179.9s" | Logs Insights /ecs/orders-reconcile | W3-Q1 |
| 10-21 02:19:52 and 02:20:14 | Reconcile task stopping, stopped (exit code 0) | ECS describe-tasks | W2-Q2 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| sched:orders-reconcile-nightly | The nightly reconcile job (EventBridge rule orders-reconcile-nightly, cron(0 2 * * ? *), family orders-reconcile) starts at 02:00 UTC and its work degrades orders-api for about 20 minutes each day (database contention or call volume; mechanism open). | Onset within minutes of 02:00 (seen); same time on earlier days (seen); a reconcile task running 02:00 to about 02:20 today (seen); orders-api error lines starting 02:01 with a database lock or timeout mechanism (seen); burst moves when the job's start moves (seen). | The rule is DISABLED or has no ECS target, or no reconcile task ran at 02:00 on 10-21, or the orders-api errors are not clustered in the job's run window, or the burst does not follow the job when its start time shifts: rule/targets/task (W2-Q2), RunTask history (W2-Q4), orders-api log lines (W2-Q5). | main | Likely |
| H2 | Release orders-api:42 (rollout 01:22:07-01:31:40) broke the failing path. | Only revision 42 fails; errors begin as the new tasks take traffic; a diff touches the failing path. | Old-against-new split: same 02:00 bursts on days when only older revisions existed; the new revision's clean stretch between rollout completion 01:31:40 and onset 02:01; onset after rollout completion (W1-Q1, W1-Q3, W1-Q4, W2-Q1, W2-Q4). | main | Ruled out |
| H3 | Database lock contention (row lock waits on the orders data store) is the mechanism of the 5xx. | Lock-wait, pool-wait or timeout errors in orders-api lines at 02:01-02:20; durations at the lock wait limit. | No such error codes in the lines at onset (W2-Q5); database metrics not readable (Aurora orders-db not listed, W0-Q8). | main | Likely |
| sched:aurora-backup-window | A fixed-clock database backup or maintenance window near 02:00 UTC is the cause. | Burst start fixed to the clock. | The burst start should not move with the reconcile job's start time. It did move: RunTask 02:05:02 on 10-14 with burst from 02:06; RunTask 02:01:02 on 10-16 with alarm at 02:05 (W1-Q3, W1-Q5, W2-Q4). The window itself was not read (describe-db-clusters empty, W0-Q8). | main | Ruled out |
| H5 | A traffic spike or an unknown daily caller sends more work at 02:00. | RequestCount rises at 02:01 against previous and -7d; requests concentrated on a few paths or clients. | RequestCount at baseline. RequestCount did not return (W1-Q3); no volume signal exists in the data read. | main | Assumed |
| H6 | Task, node or scaling churn (stopped tasks, scale-in, failed health checks). | Stopped tasks with reasons near 02:01; service events; scaling activity. | No stopped tasks, no service events, running = desired: W1-Q1, W1-Q2, W1-Q6. | main | Ruled out |
| H7 | The HTTP client library bump in release 2026.10.21-1 (#1185) makes calls to the payments service reset (ECONNRESET, 502). | 502s with ECONNRESET only on revision 42, outside the 02:00 window too. | The new revision's 5xx count between rollout completion (01:31:40) and the onset (02:01): 1 in total (W1-Q3); only one 502 sampled, at 02:07:30 (W2-Q5). Rate of 502s per revision not measured. | main | Assumed |

- sched:orders-reconcile-nightly status: supported (not confirmed) · evidence: W1-Q4, W1-Q5, W1-Q6, W2-Q2, W2-Q3, W2-Q4, W2-Q5, W3-Q1 · note: change (RunTask 02:00:02, schedule), timing (first blocked request began waiting about 02:00:23, 11 s after the job logged its start; burst ends 02:19 and the job commits at 02:19:48; the burst moved with the job on 10-14 and 10-16) and the job's own log of SELECT ... FOR UPDATE over about 1.18M orders rows are all shown. Not Confirmed: no database-side view shows that the blocked orders-api statements wait on this job's locks, and only 6 error lines were sampled, so the lock-wait share of the 438 5xx is not counted. Label capped at Likely by the mechanism link.
- H2 status: refuted · evidence: W1-Q1, W1-Q3, W1-Q4, W2-Q1, W2-Q4 · note: split per revision, from metrics plus the registration and UpdateService times: bursts of 52 to 455 5xx in the 02:00 hour on every one of the 14 days before revision 42 existed (revision 40 era 10-07 or 10-08 to 10-14: 421, 61, 117, 386, 74, 52, 455; revision 41 era 10-15 to 10-20: 133, 398, 69, 104, 412, 96; 10-07: 88 before revision 40 was registered), against 438 in revision 42's first 02:00 hour. Revision 42's own stretch from rollout completion 01:31:40 to onset 02:01 had 1 5xx. Release diff not read (compare reply empty, gap), so "touches the failing path" is unknown; it does not matter for the verdict because the same failure predates the release.
- H3 status: supported · evidence: W2-Q5 · note: 4 of 6 sampled lines are lock wait timeouts at about 50 s; share of the 438 not counted (no stats query within the log budget).
- sched:aurora-backup-window status: refuted for a fixed-clock window · evidence: W1-Q3, W1-Q5, W2-Q4 · note: window not readable.
- H5 status: open (untestable) · evidence: none · note: gap on RequestCount; no signal pointing to volume.
- H6 status: refuted · evidence: W1-Q1 (no service event after 01:31:40, desired 6 = running 6), W1-Q2 (stopped-task list empty, ECS keeps stopped tasks about an hour so no task stopped since about 01:44; all 6 tasks started 01:23 and HEALTHY), W1-Q6 (no scaling schedule or activity returned; replies were empty) · note: capacity saturation (CPU, memory) was not read and is not covered by this refutation.
- H7 status: open · evidence: W1-Q3, W2-Q5 · note: one sampled 502; the 29-minute stretch before the onset on revision 42 had 1 5xx, which does not support a general client-library problem.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (read through `gh`, no local clone) | not read | not resolved (compare reply `{}`) | n/a | by tag, from the task definitions: 2026.10.21-1 (orders-api:42, running), 2026.10.14-2 (orders-api:41), 2026.10.07-1 (orders-api:40); tag = release tag (gh release view returned it); commit SHAs not resolved |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 02:40:05 | sts get-caller-identity + iam get-role, profile prod-read, us-east-1 (role name taken from the caller ARN) | n/a | free · free | Account 111122223333 matches environment.md; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b under /aws-reserved/sso.amazonaws.com/ · Confirmed · link: `aws sts get-caller-identity --profile prod-read` |
| W0-Q2 | 02:40:05 | iam simulate-principal-policy, the fixed list of 10 write actions, profile prod-read | n/a | free · free | 7 of 10 asked actions implicitDeny; 3 asked actions returned no row (gap); 3 unasked rows ignored · Confirmed for the 7 · link: `aws iam simulate-principal-policy --profile prod-read` |
| W0-Q3 | 02:40:05 | logs describe-log-groups --log-group-name-prefix /ecs/ (profile prod-read) | n/a | free · free | /ecs/orders-api (STANDARD, retention 30 d, 64.42 GB stored, created 2024-11-04) (verified, listed); /ecs/orders-reconcile (retention 30 d, 1.07 GB) (verified, listed; another workload). Estimate for the last 15 min on /ecs/orders-api: 64,424,509,440 B x 900 s / 2,592,000 s = 0.022 GB (about 2.1 GB/day; no Insights scan run) · Confirmed (listing) · link: `aws logs describe-log-groups --log-group-name-prefix /ecs/ --profile prod-read` |
| W0-Q4 | 02:40:05 | cloudwatch describe-alarms (no filter), profile prod-read | n/a | free · free | One MetricAlarm: orders-api-5xx-high (AWS/ApplicationELB HTTPCode_Target_5XX_Count, Sum, period 60, > 25, 2 of 3 datapoints, TreatMissingData notBreaching; LB app/prod-public/50dc6c495c0c9188, TG targetgroup/orders-api/943f017f100becff; action SNS oncall-page). State OK since 02:12:00 UTC (tool printed 11:12 +09:00; converted). No sibling alarms · Confirmed · link: `aws cloudwatch describe-alarms --profile prod-read` |
| W0-Q5 | 02:41:10 | local `ls .culiops/service-discovery` (profile build, helper) | n/a | free | No such file or directory (exit 1): no service-discovery catalog; suggest running `service-discovery` after the incident · Confirmed |
| W0-Q6 | 02:41:10 | ecs list-clusters; ecs list-task-definition-families --status ACTIVE (helper, profile prod-read) | n/a | free · free | Cluster `prod` (only one); families orders-api, orders-migrate, orders-reconcile (verified, listed) · Confirmed · link: `aws ecs list-clusters --profile prod-read` |
| W0-Q7 | 02:41:10 | cloudwatch list-metrics --namespace AWS/ApplicationELB --dimensions TargetGroup=targetgroup/orders-api/943f017f100becff (helper) | last 2 weeks | free · free | 6 metrics under LB app/prod-public/50dc6c495c0c9188 + TG targetgroup/orders-api/943f017f100becff: HTTPCode_Target_5XX_Count, HTTPCode_Target_4XX_Count, RequestCount, TargetResponseTime, HealthyHostCount, UnHealthyHostCount (dimension values verified, listed). HTTPCode_ELB_5XX_Count is not in the list, but the filter was on the TG dimension, which that metric does not carry, so its absence says nothing · Confirmed |
| W0-Q8 | 02:41:10 | rds describe-db-clusters (no filter; helper) | n/a | free · free | Empty reply `{}`: no cluster listed. Aurora `orders-db` (environment.md) stays (unverified) · Assumed (no data) |
| W0-Q9 | 02:42:00 | ecs list-services --cluster prod (helper wave 2) | n/a | free · free | Service orders-api in cluster prod (verified, listed) · Confirmed · link: `aws ecs list-services --cluster prod --profile prod-read` |
| W1-Q1 | 02:44:10 | ecs describe-services --cluster prod --services orders-api, query: deployments + 30 newest events (profile prod-read; cluster prod, service orders-api verified) | current state | free · free | ACTIVE, desired 6 running 6 pending 0; one deployment PRIMARY ecs-svc/4417203958112934411 on orders-api:42, created 01:22:07, COMPLETED 01:31:40 (circuit breaker on, rollback on); events: 6 tasks started 01:22:31, old tasks stopped 01:25:48 (3) and 01:29:12 (3), steady state 01:31:40; nothing newer than 01:31:40; an earlier steady state at 10-20 19:02:10 · Confirmed · link: `aws ecs describe-services --cluster prod --services orders-api --profile prod-read` |
| W1-Q2 | 02:44:10 | ecs list-tasks (RUNNING, then STOPPED) --service-name orders-api + describe-tasks for the running ones (profile prod-read) | current state | free · free | RUNNING: 6 tasks, all orders-api:42, started 01:23:09-01:23:29, HEALTHY. STOPPED: empty (ECS keeps stopped tasks about an hour, so no stop since about 01:44; none during 02:01-02:19). Revision map in raw/c-task-revisions.tsv · Confirmed |
| W1-Q3 | 02:44:10 | cloudwatch get-metric-data, file q-golden-60.json (RequestCount, HTTPCode_Target_5XX_Count, HTTPCode_ELB_5XX_Count, UnHealthyHostCount, HealthyHostCount, TargetResponseTime p95; period 60), three windows, LB app/prod-public/50dc6c495c0c9188 + TG targetgroup/orders-api/943f017f100becff (verified) | incident 01:30-02:40, previous 00:20-01:30, -7d 10-14 01:30-02:40, 60 s | 18 metric requests · 18 | Only one series came back in each reply (HTTPCode_Target_5XX_Count; its Id printed as m1, matched by Label), StatusCode Complete. Incident: 20 non-zero minutes, total 439 (01:44 = 1; 02:01-02:19 = 438; peak 55 at 02:04). Previous: 3 (00:29, 01:24, 01:27, 1 each). -7d: 459 (stray 1s at 01:39, 01:42, 01:52, 01:58; burst 02:06-02:24, peak 57 at 02:09). Zero after 02:19. The other five Ids had no entry and no message: gap, not zero · Confirmed (5xx counts) · link: CloudWatch console, metric HTTPCode_Target_5XX_Count for the TG above. Table in raw/m-golden-5xx.tsv |
| W1-Q4 | 02:44:10 | cloudwatch get-metric-data, file q-recur-3600.json (main_err_raw HTTPCode_Target_5XX_Count Sum, ReturnData false; main_err = FILL(main_err_raw, 0)), period 3600, same dimensions | 2026-10-07 01:00 to 2026-10-21 01:00 (14d, aligned to the hour so buckets are whole hours) | 1 metric request · 1 | 233 of 336 hours returned, 103 zero-filled; stats in the Recurrence table; 02:00 hour is the daily maximum on 14 of 14 days · Confirmed · link: CloudWatch console |
| W1-Q5 | 02:44:10 | cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high --history-item-type StateUpdate, jq epoch conversion to UTC | 2026-09-21 01:30 to 2026-10-21 02:40 | free · free | 12 items = 6 ALARM episodes, ALARM entries at 02:04, 02:04, 02:09, 02:05, 02:04, 02:04 UTC on 10-08, 10-11, 10-14, 10-16, 10-19, 10-21; oldest item 10-08 (history kept about 14 days) · Confirmed · link: `aws cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high --profile prod-read` |
| W1-Q6 | 02:44:10 | events list-rules (rules with a ScheduleExpression); scheduler list-schedules; application-autoscaling describe-scheduled-actions and describe-scaling-activities for service/prod/orders-api (one chained call) | current state; activities as kept | free · free | EventBridge: orders-reconcile-nightly ENABLED cron(0 2 * * ? *) (02:00 UTC daily), catalog-sitemap-weekly ENABLED cron(30 3 ? * SUN *) (Sunday 03:30 UTC; 10-21 is a Wednesday, so no fire near the onset). Scheduler: no schedules. Application Auto Scaling: both replies empty (`{}`), read as no scheduled action and no scaling activity returned (cannot distinguish "no scalable target" from "no activity") · Confirmed for the rules; Assumed for scaling |
| W2-Q1 | 02:48:10 | ecs list-task-definitions --family-prefix orders-api; ecs describe-task-definition for the last three (orders-api:40, :41, :42; names of env vars and secrets only); gh release list; gh release view 2026.10.21-1; gh api compare 2026.10.14-2...2026.10.21-1 (example-org/orders-api; tag taken from the running image, verified) | current definitions | free · free | Revisions 40, 41, 42: images 2026.10.07-1, 2026.10.14-2, 2026.10.21-1; registered 10-07 02:58:31, 10-14 03:10:44, 10-21 01:21:58 by deploy-pipeline; cpu 1024 / memory 2048 in all; env names identical in all three (APP_ENV, DB_HOST, DB_POOL_SIZE, LOG_LEVEL, PAYMENTS_URL) and secret name DB_PASSWORD (values not read: a changed value would not show). Release 2026.10.21-1 created 01:18:02Z: #1182 order confirmation email delivery date, #1185 HTTP client bump to 3.4.1, #1187 admin order-search pagination. Compare reply `{}`: no commits or files (gap) · Confirmed (definitions, release); app diff not read · link: `gh release view 2026.10.21-1 --repo example-org/orders-api` |
| W2-Q2 | 02:48:10 | events describe-rule + list-targets-by-rule orders-reconcile-nightly; ecs describe-task-definition orders-reconcile:7 (names only); ecs list-tasks --family orders-reconcile --desired-status STOPPED + describe-tasks | current state; stopped tasks kept about 1 h | free · free | Rule ENABLED cron(0 2 * * ? *), "Nightly ledger reconciliation of the orders table"; target ECS RunTask cluster prod, Fargate, count 1, orders-reconcile:7 (network settings not read). orders-reconcile:7: image 2026.09.30-1, registered 2026-09-30 10:02:17 (before the 14-day window), cpu 2048, memory 4096, command python -m reconcile --window previous_day, env names DB_HOST, RECON_BATCH_SIZE, RECON_LOCK_MODE, secret DB_PASSWORD (values not read; the names suggest batching and a row-lock mode, a lead only). Today's task 7e4b...0123: created 02:00:02.774, started 02:00:09.531, stopping 02:19:52.006, stopped 02:20:14.448, startedBy events-rule/orders-reconcile-nightly, EssentialContainerExited, exit code 0 · Confirmed · link: `aws ecs describe-rule` as above with `--profile prod-read` |
| W2-Q3 | 02:48:10 | cloudtrail lookup-events ReadOnly=false, all sources, projection without the CloudTrailEvent record | 2026-10-21 00:01 to 02:16 (onset minus 2 h to plus 15 min) | free · free | 3 write events: RegisterTaskDefinition 01:21:58 and UpdateService (service orders-api) 01:22:07, both by role deploy-pipeline; RunTask 02:00:02 by ecsEventsRole session, task definition orders-reconcile:7. No other writes in the window (no database, security group, alarm or scaling change) · Confirmed · link: CloudTrail event IDs 5e1a0012-0015-4001-8015-00000000e2a2, 5e1a0013-0015-4001-8016-000000001b6b, 5e1a000f-0015-4002-8000-0000000007df |
| W2-Q4 | 02:48:10 | cloudtrail lookup-events EventName=RunTask, then EventName=UpdateService (two calls, one attribute each) | 2026-10-07 00:00 to 2026-10-21 02:40 | free · free | RunTask orders-reconcile:7 by ecsEventsRole: 15 events, one per day, 02:00:02 on 13 days, 02:05:02 on 10-14, 02:01:02 on 10-16. UpdateService orders-api: 10-14 03:10:53 and 10-21 01:22:07 (deploy-pipeline). No UpdateService on 10-07 although orders-api:40 was registered that day (unexplained; gap). Raw table in raw/c-cloudtrail-14d.tsv · Confirmed |
| W2-Q5 | 02:48:10 | logs start-query + get-query-results, /ecs/orders-api (verified, listed), fields @timestamp, @logStream, @message, filter /(?i)(error\|warn\|exception\|timeout\|timed out)/, sort asc, limit 100; fields `ecs_task_revision`, `error_code`, `route`, `status` now verified (returned in lines, and ecs_task_revision 42 ties the lines to task definition orders-api:42) | 2026-10-21 01:51:00 to 02:11:00 (onset minus 10 to plus 10 min; 20 min, cap 30 min) | est 0.030 GB; actual 0.481 GB (reply statistics; about 16x the estimate) | 6 lines in the window: 02:01:13.208 POST /orders 500 ER_LOCK_WAIT_TIMEOUT "insert order_lines: Lock wait timeout exceeded; try restarting transaction" 50,021 ms; 02:02:41.877 PATCH /orders/{id} 500 ER_LOCK_WAIT_TIMEOUT "update orders set status: Lock wait timeout exceeded" 50,008 ms; 02:04:05.390 POST /orders 500 same, 50,017 ms; 02:05:52.114 GET /orders 200 warn "slow request" 8,120 ms; 02:07:30.662 POST /orders 502 ECONNRESET "payments call reset by peer" 312 ms; 02:10:18.045 POST /orders 500 same lock wait, 50,030 ms. All revision 42. No earlier match from 01:51 to 02:01. Completed (not stopped). Shares of error codes not counted · Confirmed (these lines) · link: Logs Insights console, log group /ecs/orders-api, 01:51-02:11 UTC |
| W3-Q1 | 02:52:10 | logs start-query + get-query-results, /ecs/orders-reconcile (verified, listed), fields @timestamp, @logStream, @message, sort asc, limit 100 (no filter: small group) | 2026-10-21 02:00:00 to 02:25:00 (25 min, cap 30 min) | est 0.0006 GB (1,073,741,824 B x 1,500 s / 2,592,000 s), about 0.01 GB at the 16x ratio measured in W2-Q5 · actual 0.00006 GB (61,440 B, the reply's statistics block) | 5 lines in the window: 02:00:11.902 start run_id=20261021-0200 window=previous_day batch_size=5000 mode=SELECT ... FOR UPDATE; 02:00:12.448 locking orders rows created 2026-10-20 (estimated 1,184,000 rows); 02:09:37.215 progress 600000/1184212 rows; 02:19:48.630 committed 1184212 rows, 37 mismatches written to recon_exceptions; 02:19:51.877 done in 1179.9s. Lines for 10-19 and 10-20 in the reply are outside the requested window and were not used. Completed. No instruction-like text · Confirmed (these lines) · link: Logs Insights console, log group /ecs/orders-reconcile, 02:00-02:25 UTC |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability unknown (gap), prod-read: the simulation answered 7 of the 10 fixed actions; ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack returned no row (W0-Q2). Not a finding that the credentials can write. | The report cannot say "read-only confirmed"; the run itself stays read-only. | Ask the owner of the SSO permission set to confirm it is ReadOnlyAccess or tighter. |
| `timezone` is empty in environment.md | Resolved for this run by the user's answer (Asia/Tokyo, UTC+9); the next run asks again. | Add `timezone: Asia/Tokyo` to environment.md. |
| No tracing backend, no error tracker, no Prometheus/Loki connected (environment.md) | Per-endpoint latency, span counts, issue first-seen cannot be checked; hypotheses that need them stay `Assumed`. | Connect a trace or error-tracking datasource in environment.md. |
| No SLO or core-flow counter named in environment.md | Impact sized from ALB metrics only; business-counter check for checkout and order updates not possible. | Name an SLO or a flow counter in environment.md. |
| No IaC repo and no local clone named (environment.md) | IaC history and app diff only through read-only `gh`; merged-vs-applied cannot be tied. | Add the IaC repo and/or a local clone path to environment.md. |
| Aurora `orders-db` not listed (W0-Q8 returned `{}`); no database metrics or lock view read | The lock holder cannot be identified from the database side; H3 and the link "the job holds the locks" stay `Likely`; the backup/maintenance window was not read. | Confirm the cluster identifier and region with the owner; add it to environment.md; a database owner can read lock waits and Performance Insights for 02:00-02:20 UTC. |
| W1-Q3 returned only the 5xx series: RequestCount, HTTPCode_ELB_5XX_Count, UnHealthyHostCount, HealthyHostCount and TargetResponseTime p95 had no result entry in any of the three replies (no StatusCode, no message) | Failing share of requests (needed for SEV1 at >5%), the app-vs-ALB 5xx cross-check, unhealthy targets and latency are unread; H5 (traffic) cannot be tested by metrics. | Read RequestCount, TargetResponseTime and UnHealthyHostCount for 01:30-02:40 UTC in the CloudWatch console, or ask the owner whether prod-read may call GetMetricData for them. |
| Alarm history holds about 14 days: oldest item 2026-10-08 although 30 days were requested (W1-Q5) | Transitions before 10-08 are not visible; the class rests on 6 episodes in 14 days plus the hourly pull and 15 RunTask events. | none needed for this run. |
| Application Auto Scaling replies were empty (W1-Q6) | "No scaling change" is `Assumed`, not shown. | Ask the owner whether the service has a scalable target. |
| `gh api` compare of 2026.10.14-2...2026.10.21-1 returned `{}` (W2-Q1): no commits or files | Whether release 2026.10.21-1 touches the order-write path or the payments client is unknown; H2's verdict does not depend on it (the failure predates the release), but H7 does. | Read the diff of PRs #1182, #1185 and #1187 on GitHub. |
| Environment variable values are not readable through the task definition query by design (W2-Q1, W2-Q2) | A changed value (for example a pool size or reconcile batch size) between revisions would not be visible; only names were compared (identical). | The service owner compares the values of DB_POOL_SIZE and the reconcile settings across revisions. |
| CloudTrail shows no RegisterTaskDefinition or UpdateService for orders-api:40 on 10-07 (W2-Q4), although it was registered 02:58:31 that day | The revision in service on 10-08 to 10-13 is inferred from the next UpdateService (10-14 03:10:53), not shown. Affects only the per-revision list for H2, not its verdict. | Check the deployment history in the pipeline. |
| Logs Insights scan was 16x the storedBytes estimate (W2-Q5); the reply's statistics block describes the whole covered window of its file | Budget forecasting for the same log group needs the measured ratio; the by-error-code share of the 438 5xx was not counted within the budget. | Raise `budgets.fast.log_gb_scanned` or run a by-error_code stats query for 02:00-02:20 UTC. |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (`ls .culiops/sre-investigate` shows only environment.md; no lessons.md) |
| Re-verified this run | none |
| History lookup | `grep -rEil 'orders-api\|orders-reconcile\|5xx\|lock' .culiops/sre-investigate/incidents/ --include='*.md'` run after the ranked list existed (service, dependency and symptom words): no output; no `incidents/` directory exists. No matched files, so no `from-history:` entries. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | cloudwatch | A get-metric-data batch of six metrics returned one series only (Id printed as m1, Label HTTPCode_Target_5XX_Count); match series by Label and record absent Ids as a gap, never as zero. | W1-Q3 |
| process | cloudwatch | describe-alarm-history prints +09:00 offsets and keeps about 14 days; convert with the epoch function, and do not take the user's zone from the offset. | W1-Q5 |
| identifier | cw-logs | orders-api logs are in /ecs/orders-api; /ecs/orders-reconcile in the same prefix is a different workload. | W0-Q3 |
| identifier | cw-logs | /ecs/orders-api lines are JSON with level, status, route, error_code, msg, duration_ms and ecs_task_revision; ecs_task_revision is the ECS task definition revision of orders-api. | W2-Q5 |
| process | cw-logs | Logs Insights on /ecs/orders-api scanned about 16x the storedBytes estimate (0.481 GB reported against 0.030 GB); size the next query of this group with that ratio. | W2-Q5 |
| failure-mode | aws | orders-api 5xx burst at 02:00-02:20 UTC daily: ER_LOCK_WAIT_TIMEOUT (about 50 s) on POST /orders and PATCH /orders/{id} while the orders-reconcile-nightly task runs its SELECT ... FOR UPDATE batch; the burst follows the RunTask time. | W2-Q4 |
| identifier | cw-logs | /ecs/orders-reconcile lines are plain text (start, locking orders rows, progress, committed, done in N s) and give the job's run window to the second. | W3-Q1 |
