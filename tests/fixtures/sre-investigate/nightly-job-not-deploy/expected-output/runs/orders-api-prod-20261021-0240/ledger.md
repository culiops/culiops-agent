# Ledger: orders-api prod 20261021-0240

Mode: Fast
Budget used: 7 metered queries / 20 · 0.48 GB log scanned / 2 GB (W2-Q7 as reported, see its row; W3-Q3 reported 61 KB) · 22 CloudWatch metric requests / 100 · (final, after wave 3; free describe/list calls are logged but not counted, see Assumptions)

## Problem

| Field | Value |
|---|---|
| What | Reporter: "orders-api in prod has been throwing 5xx since around 11 this morning. We shipped a release just before that." Measurable restatement: HTTPCode_Target_5XX_Count on target group `targetgroup/orders-api/943f017f100becff` is elevated from about 02:00 UTC on 2026-10-21 (reporter's onset, to be confirmed by metrics). |
| Where | orders-api, prod, ECS cluster `prod`, us-east-1, behind ALB `prod-public`. No siblings (single service, single region). |
| When | Reported: "around 11 this morning" = 11:00 Asia/Tokyo = 02:00 UTC on 2026-10-21 (reporter's words, not from a query). True onset: not yet known. |
| Who is affected | Not yet known. Core flows in environment.md: checkout (`POST /orders`) and order status updates (`PATCH /orders/{id}`). |
| Trigger | A person's report in chat. Alarm `orders-api-5xx-high` exists on this target group (W0-Q4), and may be the alerting signal; the reporter did not name it. |
| Mitigations already applied | None known. Observation, not a mitigation: the alarm was last set to OK at 02:12 UTC (W0-Q4). |
| Assumptions made at intake | (1) Time zone: environment.md has no `timezone`; asked; the user answered "Tokyo time, UTC+9" in chat, recorded as Asia/Tokyo (UTC+9, no DST). Source: user, not environment.md, and not the +09:00 offset the AWS CLI printed. (2) Window rule 2 (a rough time of day): anchor 11:00 JST = 02:00 UTC, window from 30 minutes before the anchor to now: 01:30–02:40 UTC. (3) "Now": `date -u` returned nothing in the simulated world (no INDEX row, empty default), so "now" is taken as 02:40 UTC (11:40 JST). That is the end of the metric data the world covers and fits "this morning"; wave Start times below are approximate. (4) environment.md sets only the Logs Insights ask threshold (10 GB). Every other budget and window cap uses the template's neutral defaults (fast: 20 queries, 2 GB, 100 metric requests; per-query soft limit 1 GB; windows log_stats 48h, log_patterns 2h, log_metric 12h, log_raw 30m). (5) `budgets.fast.queries` is counted on metered telemetry queries (metric, Logs Insights, trace); describe/list/gh/git calls are free, are all logged, and are not counted. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | 7 of the 10 fixed actions returned implicitDeny (s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode). No row came back for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack: write capability unknown (gap) for those three. Three rows for actions not on the list (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; all implicitDeny) were ignored. Not "read-only confirmed". No boxed warning (nothing allowed). | Session valid. environment.md lists no token-based backend, so no token checks. Culibox: `command -v agentbox-env` failed (exit 1), nothing shown. No Kubernetes contexts (ECS Fargate only). |

## Impact

Source order: SLO (none named), then load-balancer request/error/duration metrics against baseline (wave 1), then `Assumed`.

| Field | Value |
|---|---|
| Symptom | HTTP 5xx from orders-api targets (ALB target-group `HTTPCode_Target_5XX_Count`). Which endpoint or flow fails is not known yet: the metric has no path split. |
| Affected | prod, single service, customer-facing. 439 target 5xx in 01:30–02:40 UTC, peak 55/min at 02:04 (alarm threshold 25/min). Previous window: 3. Same window 7 days earlier (10-14 01:30–02:40): 459, peak 57/min. Share of requests failing: unknown (RequestCount not returned). Core flows (checkout, order updates) not split out. |
| Since / ongoing | 2026-10-21 02:01 UTC (11:01 JST). Ongoing: no. Last elevated minute 02:19 UTC (2 errors); nothing above the 1/min background from 02:20 to 02:40; alarm back to OK at 02:12 UTC. |
| Suggested severity | SEV2 (revised after wave 2 from a provisional SEV3) because both listed core flows, POST /orders and PATCH /orders/{id}, appear among the failing routes, for about 19 minutes, on every one of the last 15 mornings. SEV1 if more than 5% of requests failed or checkout was effectively down; that cannot be told because the failing share is unknown. The incident owner decides. |
| Basis | W1-Q5, W1-Q6, W1-Q7, W1-Q9 (counts and timing: Confirmed) · W2-Q7 (routes, from a 5-line log sample: Likely) · failing share of requests: Assumed (no RequestCount) |
| Third party in the path | none known (profile) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-21 01:30:00 | 2026-10-21 02:40:00 |
| Baseline (previous) | 2026-10-21 00:20:00 | 2026-10-21 01:30:00 |
| Baseline (−7d) | 2026-10-14 01:30:00 | 2026-10-14 02:40:00 |

Re-anchored: no

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | `orders-api-5xx-high`, into ALARM: 2026-10-08 02:04, 10-11 02:04, 10-14 02:09, 10-16 02:05, 10-19 02:04, 10-21 02:04. Back to OK: 10-08 02:11, 10-11 02:11, 10-14 02:17, 10-16 02:12, 10-19 02:11, 10-21 02:12. All converted from the +09:00 stamps the CLI printed (e.g. 11:04:00+09:00 = 02:04:00Z). No sibling alarms exist (W0-Q4 listed one alarm). |
| Signal, 14d at 1h resolution | `HTTPCode_Target_5XX_Count`, Sum per hour (a counter), 2026-10-07 02:00 – 2026-10-21 01:30, 336 hourly buckets, reply sparse so zero-filled locally (233 non-zero). Median 1 · p95 6 (335 hours below the incident level, which drops only the 10-14 02:00 hour) · max excluding the incident 455 (10-14 02:00) · incident hour (10-21 02:00) 438. |
| Coverage | Alarm history: 14 days returned (oldest item 10-08 02:04) although 30 days were asked, so absence before 10-08 is not readable as absence of alarms. Metrics: hourly and per-minute reply cover 2026-10-07 00:00 – 2026-10-21 02:40. |
| Class | `scheduled` · shape: periodic (fixed time of day; a roughly 3-minute rise to a peak, then a slow decay over about 15 minutes) |
| Reason | Rule 1 (at least three starts no more than 15 minutes from one clock time): six alarm transitions at 02:04–02:09 UTC, and the 02:00 UTC hour is the top 5xx hour on 14 of 14 days (52 to 455 per hour). Per-minute data shows the same tent on 10-21 (02:01–02:19, peak 55 at 02:04) and 10-14 (02:06–02:24, peak 57 at 02:09). The size alternates: 386–455 per hour on 10-08, 10-11, 10-14, 10-16, 10-19 and 10-21; 52–133 on the other days. Outside the 02:00 hour the hourly maximum is 31. W3-Q1 adds the schedule: the nightly RunTask preceded the onset by 1–2 minutes on 15 of 15 nights, so minute-level times back the class (Confirmed). |
| Label and queries | Confirmed that the episode recurs at the same time of day (minute-level alarm times, six occurrences; 15 nightly starts) · W1-Q5, W1-Q7, W1-Q8, W1-Q9, W3-Q1. |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-14 02:06–02:24 | Same-shape 5xx episode a week earlier (459 in the window, peak 57/min at 02:09), before any release of today. | CloudWatch metrics | W1-Q7 |
| 2026-10-14 03:10:44 and 03:10:53 | Task definition `orders-api:41` registered (image `2026.10.14-2`); `UpdateService` to it by `deploy-pipeline`. The only deploy in the 14 days before today's. | ECS, CloudTrail | W2-Q3, W2-Q5 |
| 2026-10-20 19:02:10 | ECS service reached a steady state (the oldest of the 6 events returned). | ECS service events | W1-Q1 |
| 2026-10-21 01:18:02 | Release `2026.10.21-1` created on GitHub (notes: email delivery date, http client 3.4.1, admin pagination). | gh | W2-Q6 |
| 2026-10-21 01:21:58 | Task definition `orders-api:42` registered (image `2026.10.21-1`). | ECS | W2-Q3 |
| 2026-10-21 01:22:07 | ECS deployment `ecs-svc/4417203958112934411` created, task definition `orders-api:42`, PRIMARY (the release the reporter mentions). Circuit breaker enabled with rollback. | ECS describe-services | W1-Q1 |
| 2026-10-21 01:22:31 | Service started 6 tasks (all running revision 42, started 01:23:09–01:23:29). | ECS service events, describe-tasks | W1-Q1, W1-Q2 |
| 2026-10-21 01:25:48 and 01:29:12 | Service stopped 3 + 3 old tasks (their revision is not readable: stopped-task lookup returned none). | ECS service events | W1-Q1, W1-Q2 |
| 2026-10-21 01:31:40 | Deployment completed (rolloutState COMPLETED, failedTasks 0); steady state. | ECS service events | W1-Q1 |
| 2026-10-21 02:00 | Reporter's onset ("around 11 this morning" JST). From the reporter, not a query. | reporter | n/a |
| 2026-10-21 02:00:02 | CloudTrail `RunTask` on task definition `orders-reconcile:7` by `ecsEventsRole-session`; the rule `orders-reconcile-nightly` (`cron(0 2 * * ? *)`, UTC) targets exactly that task definition. | CloudTrail, EventBridge | W2-Q4, W2-Q1 |
| 2026-10-21 ~02:00:23 | Start of the wait of the first sampled failing request: it failed at 02:01:13.208 after 50,021 ms (`ER_LOCK_WAIT_TIMEOUT`, POST /orders). That puts the lock being waited on at or before 02:00:23, about 21 s after the job's RunTask. Derived: 02:01:13.208 minus 50.021 s. | Logs Insights | W2-Q7 |
| 2026-10-21 02:00:09 | Task `orders-reconcile:7` started (created 02:00:02.774); app log `reconcile: start … mode=SELECT ... FOR UPDATE` at 02:00:11.902. | ECS, Logs Insights | W3-Q2, W3-Q3 |
| 2026-10-21 02:00:12 | Job log: `locking orders rows created 2026-10-20 (estimated 1,184,000 rows)`. | Logs Insights | W3-Q3 |
| 2026-10-21 02:01 | First elevated minute: 13 target 5xx. Then 30, 45, **55 at 02:04**, 47, 38 … decaying to 2 at 02:19. Nothing above background after 02:19. | CloudWatch metrics | W1-Q5 |
| 2026-10-21 02:04:00 | Alarm `orders-api-5xx-high` OK → ALARM (datapoints 45 at 02:03, 30 at 02:02). Same alarm went to ALARM at 02:04 on 10-19, 10-11, 10-08, 02:05 on 10-16, 02:09 on 10-14. | CloudWatch alarm history | W1-Q9 |
| 2026-10-21 02:12:00 | Alarm ALARM → OK (23.0 at 02:10 and 21.0 at 02:11, below 25). The CLI printed 11:12+09:00; converted to UTC. | CloudWatch alarms and history | W0-Q4, W1-Q9 |
| 2026-10-21 02:19 | Last elevated minute (2 target 5xx). | CloudWatch metrics | W1-Q5 |
| 2026-10-21 02:19:48 | Job log: `committed 1184212 rows`; task stopping 02:19:52, stopped 02:20:14 (exit code 0). The last elevated 5xx minute (02:19) is the minute that contains the commit; 02:20 onward is at background. | Logs Insights, ECS | W3-Q3, W3-Q2, W1-Q5 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | `sched:orders-reconcile-nightly` (EventBridge rule, `cron(0 2 * * ? *)`, starts ECS task `orders-reconcile:7` on cluster `prod`) fires at 02:00 UTC and its run produces the 5xx episode. | Fire time within ±15 min of the onset every day; the onset moves when the fire time moves; the job runs about as long as the episode (02:01–02:19). | W2-Q1 schedule listing: no schedule firing within ±15 min of 02:00 UTC refutes it. Then W3 CloudTrail RunTask times against the per-minute onsets, and the job's own stopped-task times | main (Fast) | Likely (weakest link: that the API's lock waits are waits on the job's locks; see the bullet) |
| H1b | `sched:catalog-sitemap-weekly` (EventBridge rule, `cron(30 3 ? * SUN *)`, Lambda `catalog-sitemap`) causes the episode. | Fire within ±15 min of the onset; episodes only on Sundays. | W2-Q1: fires Sundays 03:30 UTC; today (10-21) is a Wednesday; episodes on 10-14, 10-16, 10-19 (Wed, Fri, Mon) | main (Fast) | Ruled out (W2-Q1) |
| H2 | Bad deploy: release `orders-api:42` (deployment created 01:22:07, completed 01:31:40) causes the errors. | Errors only on revision 42; none on the old revision; a diff on the failing path; onset aligned with the rollout. | Old against new: the same episode on days when revision 42 did not exist (task definition `registeredAt` and the deploy history in W2-Q3/Q5) refutes it | main (Fast) | Ruled out (W1-Q8, W2-Q3, W2-Q5: per revision, rev 42: 1 of 1 mornings with the episode; rev 41: 6 of 6; the revision before 41: 8 of 8) |
| H3 | Traffic spike or bot at 02:00 UTC: request volume jumps and the target errors under load. | Request count up against previous window and −7d; load concentrated on a few paths or clients. | Request count against previous window and −7d at baseline refutes it (W2-Q8; logs if the metric stays missing) | main (Fast) | open |
| H4 | Database lock contention (Aurora `orders-db`): writes wait for locks held by another session, time out and surface as 500s. | DB lock-wait errors in the app log at 02:01–02:19 on write routes; failing requests lasting about the lock-wait limit. | No DB errors in the app log refutes it (W2-Q7); DB-side metrics and lock holder cannot be read (rds lookup returned `{}`, no DB session allowed) | main (Fast) | Likely (merged with H1 as its mechanism; same weakest link) |
| H6 | Second error type: `ECONNRESET` (502) on the payments call, possibly from the http client bump in release `2026.10.21-1`. | `ECONNRESET` lines only on revision 42, or clearly more frequent on 42 than before; present outside 02:00–02:20. | `error_code` counts per revision for several mornings and a quiet hour (not run: a multi-day Insights count is above the window cap and the fast budget) | main (Fast) | Assumed (one sampled line, W2-Q7; no count) |
| H5 | Instance or task churn (task stops, Spot reclaim, placement failures) around 02:01. | Stopped tasks with a platform reason, service events, targets dropping out. | ECS service events and running count: none within ±10 min of the onset refutes it (W1-Q1, W1-Q2) | main (Fast) | Ruled out (W1-Q1: no service event between 01:31:40 and 02:40; W1-Q2: 6 of 6 desired tasks running since 01:23) |

- `H1` status: supported (Likely) · evidence: W2-Q1, W2-Q4, W3-Q1, W3-Q2, W3-Q3, W2-Q7 · note: three legs. Change: rule `orders-reconcile-nightly` starts the job at 02:00:02 UTC (Confirmed, W2-Q1, W2-Q4, W3-Q1). Mechanism: the job logs `SELECT ... FOR UPDATE` and "locking orders rows" at 02:00:12 and commits at 02:19:48 (Confirmed, W3-Q3, W3-Q2); the API's POST /orders and PATCH /orders/{id} fail with `ER_LOCK_WAIT_TIMEOUT` after about 50 s (Confirmed for the sampled lines, W2-Q7). Timing: onset follows RunTask by 1–2 minutes on 15 of 15 nights including the two nights whose fire time slipped (W3-Q1); the first failing wait began about 02:00:23, 11 s after the lock statement; the failures stop with the commit (Confirmed). Weakest link: that the API sessions wait on the job's locks (no database-side lock view, rds lookup returned `{}`) and that the 5-line log sample represents the 339 counted 5xx in the same minutes. Hence Likely.
- `H1b` status: refuted · evidence: W2-Q1.
- `H2` status: refuted · evidence: W1-Q8, W2-Q3, W2-Q5, W2-Q6 · note: the release (rollout 01:22:07–01:31:40) is a candidate, not a cause: the same episode ran at the same time of day under the two previous revisions. Release notes list an email field, an http client bump (3.4.1) and admin pagination; the diff was not read (gap). Environment variable and secret names are identical between revisions 41 and 42; only the image differs.
- `H3` status: open · evidence: W2-Q8 returned `{}` · note: RequestCount unreadable, so not tested; nothing in the data supports it (onset follows the job start, not a traffic ramp).
- `H4` status: supported (Likely) · evidence: W2-Q7, W3-Q3 · note: sampled error lines on POST /orders and PATCH /orders/{id} carry `ER_LOCK_WAIT_TIMEOUT` after about 50 s; 4 of the 5 sampled 5xx lines; the sample is 5 lines against 339 counted target 5xx in 01:51–02:11 (minutes 02:01–02:10), so it is qualitative. Treated as H1's mechanism.
- `H6` status: open · evidence: W2-Q7 · note: one 502 line in the sample; an http client bump is in the release notes; no count per revision.
- `H5` status: refuted · evidence: W1-Q1, W1-Q2 · note: a stopped-task lookup returned none, but the service events cover the onset.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/orders-api (via gh, no clone) | not read (no gh call returned it) | not read | ~02:45 (W2-Q6) | prod revision 42: image tag `2026.10.21-1` = release tag `2026.10.21-1` (created 2026-10-21T01:18:02Z, "Latest"); revision 41: image tag `2026.10.14-2` = release tag `2026.10.14-2`. Commit SHAs not read; a tag-to-ref rule is: image tag equals release tag. |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | ~02:40 (sim) | `TZ=UTC aws sts get-caller-identity --profile prod-read --region us-east-1 --output json` | n/a | free | Account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b; matches environment.md. link: the same CLI command |
| W0-Q2 | ~02:40 | `aws iam get-role --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` then `aws iam simulate-principal-policy` over the fixed 10 actions, `--profile prod-read` (one chained call) | n/a | free | get-role resolved the path `/aws-reserved/sso.amazonaws.com/`. Simulation: 7 of 10 requested actions implicitDeny; 3 requested actions have no row (gap); 3 unrequested rows ignored. No action allowed. |
| W0-Q3 | ~02:40 | `aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix "/ecs/orders-api" --output json` | n/a | free | `/ecs/orders-api` (30d retention, STANDARD, 64,424,509,440 stored bytes, created 2024-11) and `/ecs/orders-reconcile` (1,073,741,824 bytes). Scan estimate: 15 min = 0.022 GB; 70-min incident window = 0.104 GB; one day = 2.15 GB; 14 days = 30 GB (over the 10 GB ask threshold). `/ecs/orders-reconcile` is listed because its name starts with the prefix text, and is not the service's log group. |
| W0-Q4 | ~02:40 | `aws cloudwatch describe-alarms --profile prod-read --region us-east-1 --output json` | n/a | free | One alarm: `orders-api-5xx-high`, HTTPCode_Target_5XX_Count Sum, period 60, threshold 25, 2 of 3, state OK since 02:12 UTC. Dimensions: LB `app/prod-public/50dc6c495c0c9188`, TG `targetgroup/orders-api/943f017f100becff`. No composite alarms. |
| W0-Q5 | ~02:41 | helper: `aws ecs list-clusters --profile prod-read --region us-east-1` | n/a | free | cluster `prod` |
| W0-Q6 | ~02:41 | helper: `aws ecs list-services --cluster prod ...` | n/a | free | service `orders-api` (only service) |
| W0-Q7 | ~02:41 | helper: `aws ecs list-task-definition-families --status ACTIVE ...` | n/a | free | families `orders-api`, `orders-migrate`, `orders-reconcile` |
| W0-Q8 | ~02:41 | helper: `aws cloudwatch list-metrics --namespace AWS/ApplicationELB --metric-name RequestCount ...` | last 2 weeks | free | 6 metrics on TG `targetgroup/orders-api/943f017f100becff` / LB `app/prod-public/50dc6c495c0c9188`: 5XX, 4XX, RequestCount, TargetResponseTime, HealthyHostCount, UnHealthyHostCount. No `HTTPCode_ELB_5XX_Count` listed. |
| W0-Q9 | ~02:41 | helper: `aws elbv2 describe-target-groups --query "TargetGroups[?contains(TargetGroupName,'orders')]..."` | n/a | free | `{}` (nothing returned); target group name taken from W0-Q8 dimensions only |
| W0-Q10 | ~02:41 | helper: `aws rds describe-db-clusters --db-cluster-identifier orders-db ...` | n/a | free | `{}` (nothing returned); Aurora `orders-db` stays (unverified) |
| W1-Q1 | ~02:42 (sim) | `TZ=UTC aws ecs describe-services --profile prod-read --region us-east-1 --cluster prod --services orders-api --query 'services[0].{rollouts…, recentEvents: events[:30]…}'` (cluster `prod`, service `orders-api`: verified) | now | free | One deployment, PRIMARY, task def `orders-api:42`, created 01:22:07Z, COMPLETED 01:31:40Z, failedTasks 0, desired 6 running 6, circuit breaker on. 6 service events (01:22–01:31 and 10-20 19:02); no failed health checks or placement events. link: the same CLI command |
| W1-Q2 | ~02:42 | task mapping loop: `list-tasks --service-name orders-api --desired-status RUNNING` + `describe-tasks`, then `--desired-status STOPPED` (cluster `prod`) | now | free | RUNNING: 6 tasks, all `orders-api:42`, startedBy the 01:22 deployment, HEALTHY, started 01:23:09–01:23:29. STOPPED: empty (the 6 old tasks stopped 01:25–01:29 are no longer listed). No old-revision per-task evidence. |
| W1-Q3 | ~02:42 | `aws application-autoscaling describe-scheduled-actions --service-namespace ecs --resource-id service/prod/orders-api` | now | free | `{}`: no scheduled scaling actions returned (the service may not be a scalable target; desired count is a fixed 6) |
| W1-Q4 | ~02:42 | `aws application-autoscaling describe-scaling-activities --service-namespace ecs --resource-id service/prod/orders-api --max-results 50` | recent | free | `{}`: no scaling activities returned |
| W1-Q5 | ~02:42 | `get-metric-data` q-golden-60.json (req, t5xx, t5xx_pct, elb5xx, unhealthy, p95), LB `app/prod-public/50dc6c495c0c9188`, TG `targetgroup/orders-api/943f017f100becff` (verified) | incident 01:30–02:40, Period 60 | 5 metric requests | Only the 5xx series came back (Id `m1`, label HTTPCode_Target_5XX_Count, StatusCode Complete). Sum 439, peak 55 at 02:04, episode 02:01–02:19, background 1/min (01:44). The other Ids returned no result (gap). Confirmed for the counts. |
| W1-Q6 | ~02:42 | same query set | previous 00:20–01:30, Period 60 | 5 metric requests | 5xx: 3 (00:29, 01:24, 01:27, one each). Other Ids not returned (gap). |
| W1-Q7 | ~02:42 | same query set | minus7d 2026-10-14 01:30–02:40, Period 60 | 5 metric requests | 5xx: 459, episode 02:06–02:24, peak 57 at 02:09; background 1/min. Other Ids not returned (gap). |
| W1-Q8 | ~02:42 | `get-metric-data` q-recur-3600.json (main_err_raw hidden, main_err = FILL(raw,0), main_req, main_p99), same dimensions | 2026-10-07 01:30 – 2026-10-21 01:30, Period 3600 | 3 metric requests | Only the 5xx series came back, sparse (236 points in the file, 233 non-zero in the 336 hours of the window); zero-filled locally. Median 1, p95 6, max 455; the 02:00 UTC bucket is the top hour on 14 of 14 days (52–455). RequestCount and p99 not returned (gap). |
| W1-Q9 | ~02:42 | `TZ=UTC aws cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high --history-item-type StateUpdate --start-date 2026-09-21T02:40:00Z --end-date 2026-10-21T02:40:00Z` | 30d asked | free | 12 items (6 into ALARM, 6 back to OK), oldest 10-08 02:04Z. Into ALARM at 02:04–02:09 UTC every time. Confirmed (minute-level times). |
| W2-Q1 | ~02:44 (sim) | `aws events list-rules --query 'Rules[?ScheduleExpression]…'`, then `describe-rule` and `list-targets-by-rule` for each scheduled rule (`TZ=UTC`, prod-read, us-east-1) | now | free | 2 scheduled rules (the third rule, `orders-api-ecs-task-state`, has an event pattern, not a schedule, and was not read). `orders-reconcile-nightly`: ENABLED, `cron(0 2 * * ? *)` (EventBridge cron is UTC) = 02:00 UTC daily; target ECS cluster `prod`, task definition `orders-reconcile:7`, 1 Fargate task. `catalog-sitemap-weekly`: ENABLED, `cron(30 3 ? * SUN *)` = Sundays 03:30 UTC; target Lambda `catalog-sitemap`. link: the same CLI commands |
| W2-Q2 | ~02:44 | `aws scheduler list-schedules` | now | free | `{"Schedules": []}`: no EventBridge Scheduler schedules |
| W2-Q3 | ~02:44 | `aws ecs describe-task-definition` for `orders-api:41` and `orders-api:42` with the names-only `--query` | n/a | free | Rev 41: image tag `2026.10.14-2`, registeredAt 2026-10-14 03:10:44Z. Rev 42: image tag `2026.10.21-1`, registeredAt 2026-10-21 01:21:58Z. Same cpu 1024, memory 2048. Environment variable names identical in both (`APP_ENV`, `DB_HOST`, `DB_POOL_SIZE`, `LOG_LEVEL`, `PAYMENTS_URL`); secret name `DB_PASSWORD` in both. Only the image differs. Values not recorded. Log group `/ecs/orders-api` (awslogs). |
| W2-Q4 | ~02:44 | `aws cloudtrail lookup-events ReadOnly=false` 2026-10-21 00:01–02:16Z, `--query` keeps events with a resource name containing `orders` | 00:01–02:16Z | free | 2 events: `RunTask` 02:00:02Z by `ecsEventsRole-session`, resource task definition `orders-reconcile:7`; `UpdateService` 01:22:07Z by `deploy-pipeline` on `service/prod/orders-api`. `RegisterTaskDefinition` 01:21:58Z lists no resources and falls outside the resource filter (its time is known from W2-Q3). Nothing else in the window. |
| W2-Q5 | ~02:44 | `aws cloudtrail lookup-events EventName=UpdateService` 2026-10-07 00:00 – 2026-10-21 02:40Z, resource filter `orders-api` | 14d | free | 2 events: 2026-10-14 03:10:53Z (`orders-api:41`) and 2026-10-21 01:22:07Z (`orders-api:42`), both by `deploy-pipeline`. No other deploy in 14 days. |
| W2-Q6 | ~02:44 | `gh release list --repo example-org/orders-api --limit 10`; `gh release view --repo example-org/orders-api` | n/a | free (gh) | Releases 2026.10.21-1 (Latest, created 01:18:02Z), 2026.10.14-2, 2026.10.07-1. Notes of 2026.10.21-1 (release-bot): order confirmation email delivery date (#1182), http client library bump to 3.4.1 (#1185), admin order-search pagination (#1187). Notes are what people wrote; the diff was not read. |
| W2-Q7 | ~02:44 | Logs Insights, log group `/ecs/orders-api` (listed in W0-Q3; returned data), `fields @timestamp, @logStream, @message \| filter @message like /ERROR\|Error\|Exception\|Timeout\|timed out\|5[0-9][0-9]/ \| sort @timestamp asc \| limit 100`, queryId `c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b` | 2026-10-21 01:51–02:11Z (20 min, ladder rung: raw lines, within the 30-min cap) | est. 0.030 GB; actual reported `bytesScanned` 481,221,632 (0.48 GB), ratio 16 | Complete. 6 rows in my window (02:01:13, 02:02:41, 02:04:05, 02:07:30, 02:10:18 error lines with status 5xx, and one 200 "slow request" at 02:05:52). The reply also held rows dated 10-19 and later than 02:11 on 10-21; they are outside the window asked and were discarded. Fields seen: `level`, `status`, `route`, `error_code`, `msg`, `duration_ms`, `ecs_task_revision`. 4 lines `ER_LOCK_WAIT_TIMEOUT` (500, ~50.0 s): POST /orders 02:01:13 (insert order_lines), PATCH /orders/{id} 02:02:41 (update orders set status), POST /orders 02:04:05, POST /orders 02:10:18; 1 line `ECONNRESET` (502, 312 ms, "payments call reset by peer", POST /orders 02:07:30); all `ecs_task_revision` 42. Note: the statistics block of the reply describes the whole covered window of the reply, which is wider than my 20 minutes, so 0.48 GB is an upper bound; the 16x ratio is therefore an upper bound too. link: the same query in the Logs Insights console |
| W2-Q8 | ~02:44 | `get-metric-data` q-req-60.json (req, elb5xx, unhealthy, p95), same LB and TG | incident 01:30–02:40, Period 60 | 4 metric requests | `{}`: no MetricDataResults. Treated as a failed or empty reply, not as zero requests. |
| W3-Q1 | ~02:48 (sim) | `TZ=UTC aws cloudtrail lookup-events EventName=RunTask` 2026-10-07 00:00 – 2026-10-21 02:40Z, resource filter `orders-reconcile` | 14d | free | 15 `RunTask` events on task definition `orders-reconcile:7` by `ecsEventsRole-session`: 02:00:02Z on 13 days, **02:01:02 on 10-16 and 02:05:02 on 10-14**. Against the per-minute 5xx (W1-Q5/Q7 file, minutes with 3 or more): the elevated run starts 1 minute after RunTask on 12 days and 2 minutes after on 3 days (15 of 15), and it moved with the fire time on 10-14 (onset 02:06) and 10-16 (onset 02:02). Episode ends 02:09–02:23. Confirmed (minute-level, 15 occurrences). |
| W3-Q2 | ~02:48 | `aws ecs list-tasks --cluster prod --family orders-reconcile --desired-status STOPPED` then `describe-tasks` (names-only `--query`) | now | free | 1 stopped task of `orders-reconcile:7`, startedBy `events-rule/orders-reconcile-nightly`: created 02:00:02.774Z, started 02:00:09.531Z, stopping 02:19:52.006Z, stopped 02:20:14.448Z, `EssentialContainerExited`, container `reconcile` exit code 0 (normal finish). Ran 19 min 43 s. |
| W3-Q3 | ~02:48 | Logs Insights, log group `/ecs/orders-reconcile` (listed in W0-Q3), `fields @timestamp, @message \| sort @timestamp asc \| limit 100`, queryId `f0e1d2c3-b4a5-4968-8776-655443322110` | 2026-10-21 01:58–02:28Z (30 min) | est. 0.0007 GB; reported `bytesScanned` 61,440 (whole reply window; ratio about 0.09, an upper bound) | Complete. 5 rows in my window: 02:00:11.902 `reconcile: start … window=previous_day … mode=SELECT ... FOR UPDATE`; 02:00:12.448 `locking orders rows created 2026-10-20 (estimated 1,184,000 rows)`; 02:09:37.215 `progress 600000/1184212 rows`; 02:19:48.630 `committed 1184212 rows, 37 mismatches written to recon_exceptions`; 02:19:51.877 `done in 1179.9s`. Rows dated 10-19 and 10-20 in the reply were outside the window asked and were discarded. The job is the only writer named, and it holds row locks from 02:00:12 to 02:19:48. link: the same query in the Logs Insights console |
| W3-Q4 | ~02:48 | `gh api repos/example-org/orders-api/compare/2026.10.14-2...2026.10.21-1 --jq …` | n/a | free (gh) | `{}`: nothing returned. Treated as a gap (no access or no result), not as "no changes". |
| W3-Q5 | ~02:48 | `aws ecs describe-task-definition` for `orders-reconcile:6` and `orders-reconcile:7`, names-only `--query` | n/a | free | Rev 6: image tag `2026.08.19-1`, registered 2026-08-19 09:44:02Z, INACTIVE. Rev 7: image tag `2026.09.30-1`, registered 2026-09-30 10:02:17Z, ACTIVE; the job ran rev 7 on every night of the 14-day window (W3-Q1). Env names identical in both (`DB_HOST`, `RECON_BATCH_SIZE`, `RECON_LOCK_MODE`); secret `DB_PASSWORD`. Values not recorded. The job did not change inside the window; whether it began causing this after 2026-09-30 is not known (my metric history is 14 days). |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| `timezone` missing from environment.md (answered in chat as Asia/Tokyo, UTC+9) | none now; the next run asks again | add `timezone: Asia/Tokyo` to environment.md |
| Write capability unknown for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (simulation returned no row). This is not a finding that the credentials can write. | none on evidence; only the "read-only" statement is withheld | the operator confirms in chat that the role is read-only, or re-runs the simulation |
| No IaC repo or local clone in environment.md | IaC history cannot be read; "merged is not applied" questions stay open; any claim about config as declared is `Assumed` | add the IaC repo to environment.md `code:` |
| No tracing or error-tracker backend | per-endpoint latency, span counts and first-seen errors come from logs only | none needed unless the team has one |
| Core flows listed without a counter or datasource | business-metric comparison (checkout, order updates) cannot be run; flow impact has to come from log counts by path | name a counter or datasource in environment.md `core_flows` |
| `aws elbv2` and `aws rds` target and cluster lookups returned `{}` | target group and Aurora identifiers stay (unverified); database hypotheses have no metrics path from this run | check `elasticloadbalancing:DescribeTargetGroups` and `rds:DescribeDBClusters` permission or the names |
| W1-Q5..Q8 returned only the 5xx series: RequestCount, HTTPCode_ELB_5XX_Count, UnHealthyHostCount and TargetResponseTime (p95, p99) have no result | failing share of requests, LB-generated 5xx versus target 5xx, unhealthy targets and latency are not read; the impact share and severity stay `Assumed`; "no latency change" cannot be claimed | a human re-runs those metrics for the same windows, or checks the `cloudwatch:GetMetricData` permission and the query Ids |
| ECS stopped tasks: `list-tasks --desired-status STOPPED` returned none (W1-Q2) although the service events show 6 tasks stopped at 01:25–01:29 | no per-task evidence (exit codes, stop reasons) for the old revision; the old-against-new split must come from logs | none; stopped tasks expire after about an hour |
| Application Auto Scaling returned `{}` for scheduled actions and scaling activities (W1-Q3, W1-Q4) | "no scaling change" is read as none returned, not as proof the service is not scaled | none unless the team uses autoscaling on this service |
| Alarm history returned 14 days although 30 were asked (W1-Q9) | recurrence before 10-08 cannot be read from the alarm; the metrics carry the 14-day recurrence | none |
| The second try for RequestCount, ELB 5xx, unhealthy hosts and p95 (W2-Q8) returned `{}` | the failing share of requests, ELB-generated 5xx and latency stay unread; severity and "who is affected in %" stay `Assumed` | a human reads those four metrics for 01:30–02:40 UTC in the console, or checks `cloudwatch:GetMetricData` |
| Application log lines are a thin sample: 5 lines with status 5xx in 01:51–02:11 against 339 counted target 5xx in the same minutes (W2-Q7 vs W1-Q5) | the share of lock-wait errors among the 439 is not known; the mechanism is qualitative; log sampling or loss is unexplained | a human checks the log pipeline (sampling, non-blocking log mode) or runs a count of `error_code` for the 02:00 hour |
| The release diff was not read: `gh api …/compare/2026.10.14-2...2026.10.21-1` returned `{}` (W3-Q4) and there is no local clone | the claim that the release does not touch the failing path rests on the old-against-new split (W1-Q8, W2-Q3, W2-Q5), not on the diff | a human reads the compare of 2026.10.14-2…2026.10.21-1 for the order write path, or adds a clone path to environment.md |
| Fast mode reached its third wave: no hourly 5xx history beyond 14 days, no `error_code` counts per revision or per day, no count of the 02:00 hour split by route | when the daily episode began (the job's current revision was registered 2026-09-30), the share of lock waits among the 5xx, and whether `ECONNRESET` is new are open | ask for "go deep": a longer hourly pull (metric, cheap) and an `error_code` by revision count (estimated about 30 GB for 14 days, above the 10 GB ask threshold, so it would ask first) |
| Aurora `orders-db`: no metrics, no maintenance or backup window, no lock holder readable | the lock holder cannot be named from the database side; "the job holds the lock" is at most `Likely` | a DBA reads the lock and transaction view for 02:00–02:20 UTC (a database session, not allowed here) |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no `lessons.md` under the output root) |
| Re-verified this run | none |
| History lookup | Run after H1–H5 were ranked. `grep -ril -e orders-api -e errors-5xx -e orders-db .culiops/sre-investigate/incidents/` returned nothing; `grep -h 'type: failure-mode' .culiops/sre-investigate/lessons.md` returned nothing. No matched files, no matched fields, no `from-history:` entries. (The output root holds only environment.md.) |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | cloudwatch | `get-metric-data` replies from this account carry one entry labelled `HTTPCode_Target_5XX_Count` with Id `m1`, not the Ids sent (`t5xx`, `req`, ...); the other Ids sent in the same call had no entry, so check the returned Ids before reading a missing series as zero | W1-Q5 |
| identifier | cw-logs | Log group `/ecs/orders-api` holds JSON lines with `level`, `status`, `route`, `error_code`, `msg`, `duration_ms` and `ecs_task_revision` (= ECS task definition revision), usable for a per-revision split | W2-Q7 |
| process | cw-logs | Lines with status 5xx in `/ecs/orders-api` are a thin sample of the ALB target 5xx count (5 lines against 339 in 01:51–02:11 UTC): size an incident from the ALB metric, not from log line counts | W2-Q7 |
| failure-mode | cw-logs | Daily 02:00 UTC `orders-reconcile-nightly` job runs `SELECT ... FOR UPDATE` on about 1.18M orders rows for about 19.7 min; orders-api writes (POST /orders, PATCH /orders/{id}) fail after about 50 s with ER_LOCK_WAIT_TIMEOUT, onset 1–2 min after RunTask | W3-Q3 |
