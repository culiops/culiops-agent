# Ledger: payments-worker staging 20261025-0715

Mode: Fast
Budget used: 20 / 20 queries · 0.218 / 2 GB logs scanned (W1-Q6 and W2-Q1 each reported 0.109 GB; counted separately, conservatively) · 8 / 100 CloudWatch metric requests · (local shell reads and the clock call are not counted as queries). Waves after wave 0: 3 of 3 allowed (wave 1: 6 calls, wave 2: 5 calls, wave 3: 1 call).

## Problem

| Field | Value |
|---|---|
| What | Reporter: "payments-worker jobs have been failing in staging since about 06:30 UTC. Is prod affected too?" Restated: jobs consumed from SQS `payments-worker-jobs` by ECS service payments-worker (cluster staging) fail and end up in `payments-worker-dlq`; errors appear in log group `/ecs/payments-worker`. |
| Where | payments-worker, staging (account 444455556666, eu-west-1, cluster `staging`). Sibling environment prod (account 111122223333, cluster `prod`) is in scope for the question but unreadable this run (expired SSO session, gap G1). |
| When | Reported: "about 06:30 UTC", 2026-10-25 (date assumed). True onset from data: first error line 06:24:51 UTC (W1-Q6, W2-Q1); first non-zero DLQ bucket 06:25 UTC (W1-Q4). Ongoing at 07:10 (DLQ still rising). |
| Who is affected | Staging jobs handled by payments-worker; the failing code path is the refund handler (all 738 error lines carry the same refund_amount() TypeError). Share of all jobs: not measured. Prod: unknown. |
| Trigger | Operator report in chat; no alarm, ticket or link given. |
| Mitigations already applied | none known (not stated by the reporter) |
| Assumptions made at intake | 1. 06:30 UTC has an explicit zone, so it is used as given (window rule 1). 2. Today = 2026-10-25 and now = 07:15 UTC: `date -u` returned nothing in this shell, so the latest time the world data covers was taken. 3. Repo root = current directory (`git rev-parse --show-toplevel` printed nothing). 4. Local zone America/Bogota (UTC-5) from environment.md. 5. Fast budgets are the template defaults (environment.md sets only the 5 GB Insights ask threshold). 6. Staging is the investigated environment; prod is the sibling named in the question. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| staging-read | account 444455556666 (matches environment.md), role AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921 | no listed write action allowed among the 7 that returned a row (all implicitDeny); 3 of the 10 fixed actions returned no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack): write capability only partly checked (gap G3). Not called read-only. | session active. Three extra rows for unrequested actions (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; implicitDeny) ignored. No boxed warning (nothing allowed). |
| prod-read | no identity: "Error when retrieving token from sso: Token has expired and refresh failed" | write capability unknown (gap): the session expired, so the check could not run; not a finding that the credentials can write | gap G1. Not retried, no other profile tried. |
| (token) SENTRY_AUTH_TOKEN | not applicable | not applicable | unset (presence check printed nothing) -> gap G2 |
| (Culibox) | not applicable | not applicable | `command -v agentbox-env` succeeded; notice printed; `agentbox-env` never called; run is standalone |

## Impact

| Field | Value |
|---|---|
| Symptom | refund-handler jobs raise `TypeError: refund_amount() missing 1 required positional argument: 'currency'` (payments_worker/handlers/refund.py line 48) and end up in `payments-worker-dlq`; the jobs queue itself is not backing up (0-9 visible messages throughout) |
| Affected | staging only (verified); DLQ depth 0 until 06:20, 24 in the 06:25 bucket, 240 in the 07:10 bucket, growing about 24 per 5 minutes, never draining; 738 error lines 06:24:51-07:15; percentage of all jobs failing not measured (no throughput metric pulled; per-revision totals not returned); internal/non-production. Prod: unreadable. |
| Since / ongoing | 06:24:51 UTC (first error line) / ongoing at 07:10 UTC |
| Suggested severity | SEV4 because environment.md rates staging incidents SEV4 unless they block a release; refunds are a core flow, so reconsider if it blocks a release or prod runs the same revision |
| Basis | no SLO; no request-count metric: queue depth against baseline (W1-Q4) and error lines (W1-Q6, W2-Q1) · label: Confirmed for the staging failure, Assumed for the share of traffic and for prod |
| Third party in the path | none known |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-25 06:30:00 | 2026-10-25 07:15:00 |
| Baseline (previous) | 2026-10-25 05:45:00 | 2026-10-25 06:30:00 (the 06:25 bucket already contains the onset; clean baseline = 05:45-06:20) |
| Baseline (-7d) | 2026-10-18 06:30:00 | 2026-10-18 07:15:00 (returned no data) |

Wider windows used for specific queries: raw lines 06:20-06:40 (W1-Q6); Insights counts 03:00-07:15 (W2-Q1); recurrence 14 d ending 06:30 (W1-Q5).

Re-anchored: no. The window came from an explicit-zone time (rule 1), not from rules 2-5; the true onset (06:24:51, W1-Q6) is 5 minutes before the anchor, not more than 15.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not applicable: the trigger is a chat report; no alarm was named, so no alarm history was pulled. Siblings' alarms: none known. |
| Signal, 14d at 1h resolution | statistic Maximum of `ApproximateNumberOfMessagesVisible` (saturation gauge) for the DLQ and the jobs queue (W1-Q5). 1 of 336 hourly points returned (the 05:30 bucket): DLQ 24, jobs 9. Median, p95 and the 14-day maximum cannot be computed. That one point also contains the onset (06:25 DLQ bucket), so it is not a baseline. Incident peak (5-min buckets, W1-Q4): DLQ 240 at 07:10. Log side (W2-Q1, 03:00-07:15): no TypeError before 06:24:51. |
| Coverage | CloudWatch SQS metrics returned data only for 05:30-07:10 on 2026-10-25; the -7d window and the rest of the 14 days returned `{}` (no data, which is not zero). Logs Insights returned lines from 03:12 (first old-revision line seen) to 07:12. |
| Class | unclassified · shape: step (failure rate steps from zero to a steady ~4.8 DLQ messages/min at 06:24-06:25; the DLQ depth ramps linearly because nothing drains it) |
| Reason | no alarm history, 1 of 336 hourly points, empty -7d window: neither `scheduled`, `chronic`, `recurring` nor `sudden` can be shown. Recorded as gap G5. Within the data available: DLQ was 0 in every 5-min bucket 05:30-06:20 (W1-Q4) and the log shows no TypeError from the old revision in 03:00-06:24 (W2-Q1). |
| Label and queries | Assumed (class unknown) · W1-Q4, W1-Q5, W2-Q1 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 03:12:07 | old revision (log field 18) logs `SQS ReceiveMessage throttled, retrying`; 2 such lines in 03:00-07:15, none from rev 19 | Logs Insights | W2-Q1 |
| 05:30-06:20 | DLQ visible = 0 in every 5-min bucket; jobs queue visible 0-9 | CloudWatch SQS | W1-Q4 |
| 06:24:10 | ECS deployment `ecs-svc/2290457731864021954` created, PRIMARY, task definition payments-worker:19 | ECS describe-services | W1-Q1 |
| 06:24:22 | service started 2 tasks (3e4f5a6b..., 7c8d9e0f...) | ECS service events | W1-Q1 |
| 06:24:51 | first error line: rev 19, handler refund, TypeError missing `currency`, refund.py:48 | Logs Insights | W1-Q6, W2-Q1 |
| 06:25:03 | second error line, different message id, same error | Logs Insights | W1-Q6 |
| 06:25 (bucket 06:25-06:30) | first non-zero DLQ bucket: 24 | CloudWatch SQS | W1-Q4 |
| 06:27:31 | service stopped 2 running tasks (0f1e2d3c..., 9a8b7c6d...); presumed old revision, revision not shown (stopped-task detail empty) | ECS service events | W1-Q1, W1-Q2 |
| 06:28:52 | rollout COMPLETED; service reached steady state; running 2 / desired 2, failedTasks 0 | ECS describe-services | W1-Q1 |
| 06:30 | reporter's "about 06:30" (from the reporter, not a query) | reporter | n/a |
| 06:31:40 | another error line, same error, rev 19 | Logs Insights | W1-Q6 |
| 07:10 (bucket 07:10-07:15) | DLQ 240, still rising; 738 TypeError lines on rev 19 by the end of the window | CloudWatch SQS, Logs Insights | W1-Q4, W2-Q1 |
| (undated) | newest release range v4.11.0 -> v4.12.0 contains "refunds: support partial refunds (#902)" touching refund.py; release/merge time not shown, link to rev 19 unverified | gh | W2-Q2 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Bad deploy: the code in task definition payments-worker:19 (rolled out 06:24:10) calls `refund_amount()` without `currency` at refund.py:48, so every refund job on rev 19 raises TypeError, is retried and lands in the DLQ | errors only on rev 19; the old revision handled refund jobs without this error, including in the 06:24:22-06:27:31 overlap; the rev 18-to-19 diff touches refund.py | Insights counts by `task_def_revision`, `error` for 03:00-07:15 (W2-Q1): the old revision failing the same way at a comparable rate, or the same error before 06:24:10, refutes it. Result: new 738 / old 0; no earlier occurrence. Not refuted. | main | Likely (rev 19 only and onset after the rollout start: Confirmed; code origin PR #902 and the DLQ link: Likely, capped by the weakest link) |
| H2 | `sched:` a scheduled job or rule fired near 06:24 and produced the failing refund jobs | onset within +-15 min of a fire time; earlier occurrences at the same time | EventBridge rule and Scheduler listings (W2-Q4): no schedule firing near 06:24:51 refutes it. Result: nothing listed. | main | Ruled out (scope: default event bus and default Scheduler group; in-app schedulers not searched) |
| H3 | Upstream producer began sending refund messages without a `currency` field (producer deploy or schema change), independent of the worker release | old and new revisions both fail on the same messages in the overlap; the error is about a missing message field | same revision split as H1 (W2-Q1): the old revision handling refund jobs cleanly in the overlap refutes it. Result: old revision shows 0 TypeErrors, but per-revision totals were not returned, so it is not shown that the old tasks received any refund job in the overlap. Producer unknown. | main | Assumed (not refuted; evidence needed: producer deploy history, message bodies, per-revision totals) |
| H4 | Capacity, placement or task churn (OOM, Spot, failed starts) | stopped tasks with failure reasons; running below desired; failed deployment | ECS counts and events: running = desired and no failed tasks throughout refutes it (W1-Q1) | main | Ruled out (caveat: stopped-task detail unreadable, W1-Q2) |
| H5 | Downstream timeout or third-party outage (payment provider) | timeouts or provider errors in the error breakdown | Insights breakdown of the `error` field: only non-timeout, non-provider errors refutes it (W2-Q1). Result: only the TypeError and 2 old-revision throttle lines. | main | Ruled out (scope: only lines that carry an `error` field) |

- H1 status: supported · evidence: W1-Q1, W1-Q6, W2-Q1, W2-Q2 · note: kept in by the old-against-new rule (only the new revision fails, onset after rollout start, no earlier occurrence); Confirmed is capped to Likely because the diff on the failing path is not tied to rev 19 (deployed ref unresolved, W2-Q3) and the patch was not read.
- H2 status: refuted · evidence: W2-Q4.
- H3 status: open · evidence: W2-Q1 (partial) · note: fits the timing worse than H1 (onset 41 s after the worker rollout, refund.py changed in the newest release) but is not excluded.
- H4 status: refuted · evidence: W1-Q1, W1-Q6.
- H5 status: refuted · evidence: W2-Q1.
- Not a hypothesis, recorded: the 2 `SQS ReceiveMessage throttled, retrying` lines (rev 18, first 03:12:07, W2-Q1) are three hours before the onset and absent from rev 19; no `noise` lesson exists to discount them, so they are recorded as not onset-aligned and not tested on throttle metrics.
- from-history: none (see Memory).

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/payments-worker | not read | not read | not read (no local clone listed; read via `gh` only) | NOT RESOLVED: the task definition read returned `{}` (W2-Q3), so the image tag is unknown. Reported as "newest release range v4.11.0 -> v4.12.0; deployment not verified": commits 6c1d0e2 (refunds: support partial refunds, #902, touches payments_worker/handlers/refund.py, 14 lines) and b4a9f37 (deps: bump boto3 to 1.40.61, #899, touches requirements.txt) |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | n/a (no clock) | `aws sts get-caller-identity --profile staging-read --region eu-west-1` | n/a | free | account 444455556666, role AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921 · Confirmed · link: same command |
| W0-Q2 | n/a | `aws sts get-caller-identity --profile prod-read --region eu-west-1` | n/a | free | exit 255, SSO token expired and refresh failed -> gap G1 · link: same command |
| W0-Q3 | n/a | staging-read write-check chain: `sts get-caller-identity --query Arn` -> `iam get-role --role-name AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921` -> `iam simulate-principal-policy` (10 fixed actions) | n/a | free | 7 of the fixed actions implicitDeny; 3 without a row; 3 unrequested rows -> gap G3 |
| W0-Q4 | n/a | prod-read write-check chain (same form) | n/a | free | stops at first step, same expired-token error -> gap G1 |
| W0-Q5 | n/a | `aws logs describe-log-groups --profile staging-read --region eu-west-1 --log-group-name-prefix "/ecs/payments-worker"` | n/a | free; estimate 0.003 GB / 15 min, 0.048 GB for 03:00-07:15 | `/ecs/payments-worker` STANDARD, 14 d retention, 3.76 GB stored · Confirmed |
| W0-Q6 | n/a | `aws ecs list-clusters --profile staging-read --region eu-west-1` (helper) | n/a | free | cluster `staging` |
| W0-Q7 | n/a | `aws ecs list-services --cluster staging --profile staging-read --region eu-west-1` (helper) | n/a | free | `orders-api`, `payments-worker` |
| W0-Q8 | n/a | `aws sqs list-queues --queue-name-prefix payments-worker --profile staging-read --region eu-west-1` (helper) | n/a | free | `payments-worker-jobs`, `payments-worker-dlq` |
| W1-Q1 | n/a (no clock) | `TZ=UTC aws ecs describe-services --profile staging-read --region eu-west-1 --cluster staging --services payments-worker` with the changes-playbook `--query` | current state + events | free | one deployment: PRIMARY, task def payments-worker:19, created 06:24:10, COMPLETED, updated 06:28:52, running 2 / desired 2, failedTasks 0. Events: 06:24:22 started 2 tasks; 06:27:31 stopped 2 running tasks; 06:28:52 steady state. No ACTIVE (old) deployment remains. · Confirmed · link: ECS console service events |
| W1-Q2 | n/a | `list-tasks --desired-status STOPPED` then `describe-tasks` (changes playbook, stopped tasks) | last ~1 h | free | list-tasks returned `{}` (no `taskArns`), so describe-tasks did not run. Inconsistent with the 06:27:31 event naming two stopped tasks 48 minutes earlier, so recorded as "no usable result", not "no stopped tasks" -> gap G4 |
| W1-Q3 | n/a | `application-autoscaling describe-scaling-activities` and `describe-scheduled-actions` for `service/staging/payments-worker` (chained) | n/a | free | both returned `{}`: no scaling activity or scheduled action listed; desired = running = 2 throughout in W1-Q1 · Likely nothing relevant |
| W1-Q4 | n/a | `aws cloudwatch get-metric-data` x3 windows, file q-sqs-300.json: Maximum of `AWS/SQS ApproximateNumberOfMessagesVisible`, QueueName `payments-worker-jobs` and `payments-worker-dlq` (both verified), Period 300 | incident 06:30-07:15; previous 05:45-06:30; -7d 2026-10-18 06:30-07:15 | 6 metric requests | incident: DLQ 48,72,96,120,144,168,192,216,240 (06:30...07:10), jobs 9,1,9,3,8,9,5,2,8. previous: DLQ 0 in 05:45-06:20, 24 at 06:25; jobs 4,7,0,4,0,4,9,6,1 (05:45-06:25). -7d: `{}` no data (not zero). DLQ +24 per 5 min from 06:25, never drains; jobs queue 0-9 throughout (no backlog). · Confirmed (metric) · link: CloudWatch console, namespace AWS/SQS |
| W1-Q5 | n/a | `get-metric-data` file q-recur-3600.json, Period 3600, Stat Maximum, same two queues | 2026-10-11 06:30 to 2026-10-25 06:30 (14 d) | 2 metric requests | 1 of 336 hourly points (05:30 bucket): DLQ 24, jobs 9; rest empty -> gap G5 |
| W1-Q6 | n/a | Logs Insights on `/ecs/payments-worker` (verified), query `fields @timestamp, @logStream, @message \| filter @message like /ERROR\|Error\|Exception\|Timeout\|timed out/ \| sort @timestamp asc \| limit 100`, query id 3a4b5c6d-7e8f-4091-a2b3-c4d5e6f70812 | 06:20-06:40 (20 min, raw rung, under the 30 min cap) | est. 0.004 GB; actual bytesScanned 0.109 GB (109,051,904), recordsScanned 288,104; ratio actual/estimate ~29 | 3 lines in window: 06:24:51.204, 06:25:03.882, 06:31:40.017, all `level:error`, `task_def_revision:19`, handler `refund`, error `TypeError: refund_amount() missing 1 required positional argument: 'currency'` (payments_worker/handlers/refund.py:48), different message ids. Statistics block says recordsMatched 740 (see W2-Q1, where it equals 738 + 2); not used as a count for this window. · Confirmed (lines exist) · link: Logs Insights console |
| W2-Q1 | n/a | Logs Insights on `/ecs/payments-worker`, query `stats count(*), min(@timestamp) as first by task_def_revision, error`, query id 9a0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d (field names verified by W1-Q6 lines) | 03:00-07:15 (4.25 h, metric rung, under the 12 h cap) | est. 0.048 GB; actual bytesScanned 0.109 GB (ratio ~2.3); statistics identical to W1-Q6's, flagged | rev 19: TypeError missing `currency` ×738, first 06:24:51.204. rev 18: `SQS ReceiveMessage throttled, retrying` ×2, first 03:12:07.660. Old revision: 0 TypeErrors; per-revision totals not returned (lines without `error` are dropped by the grouping) · Confirmed (failing counts per revision) · link: Logs Insights console |
| W2-Q2 | n/a | `gh pr list --repo example-org/payments-worker --state merged --limit 20 --json number,title,mergedAt,mergeCommit` | n/a | free (rate limit) | reply is a release-compare summary: 2 commits between v4.11.0 and v4.12.0; `6c1d0e2 refunds: support partial refunds (#902)` changes payments_worker/handlers/refund.py (14 lines), `b4a9f37 deps: bump boto3 (#899)` changes requirements.txt; no dates, no patch; not tied to rev 19 · Likely (candidate on the failing path) |
| W2-Q3 | n/a | `aws ecs list-task-definitions --family-prefix payments-worker` and `describe-task-definition payments-worker:19` (chained) | n/a | free | both `{}`: no image, no revision list, no env-var names -> gap G7 |
| W2-Q4 | n/a | `aws events list-rules` and `aws scheduler list-schedules` (chained) | n/a | free | both `{}`: no rule or schedule listed -> H2 Ruled out within that scope |
| W2-Q5 | n/a | `aws cloudtrail lookup-events` ReadOnly=false, resource filter `payments-worker` | 04:24:00-06:40:00 (onset -2 h to +15 min) | free | `{}`: no events; inconsistent with the 06:24:10 deployment -> "no usable result", gap G6 |
| W3-Q1 | n/a | `aws sqs get-queue-attributes --queue-url .../payments-worker-jobs --attribute-names RedrivePolicy VisibilityTimeout` | n/a | free | `{}`: no Attributes -> redrive policy unread, gap G8 |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1: prod-read SSO session expired ("Token has expired and refresh failed"); no identity, no write check, no prod reads | "Is prod affected?" cannot be answered from prod data. Any statement about prod is Assumed. | `! aws sso login --profile prod-read` |
| G2: `SENTRY_AUTH_TOKEN` is unset | no Sentry issues, first-seen times or release tags; error-tracker corroboration missing (does not weaken the staging log evidence) | set the `SENTRY_AUTH_TOKEN` environment variable (name only; a read-only token) in the shell that runs this session |
| G3: staging-read write check partial (3 of 10 fixed actions returned no row) | none on the investigation; the access line cannot say "read-only confirmed" | re-run the simulation, or ask the account owner to confirm the role is read-only |
| G4: stopped-task detail empty (W1-Q2) | the two replaced tasks' task definition revision, stop code and exit codes are unknown; "old revision" is presumed from the service event and the log field | read within the hour of a rollout, or read the task definition history with a CloudTrail-capable role |
| G5: recurrence unclassified: 1 of 336 hourly points, -7d empty, no alarm history | class stays unknown; a schedule or earlier occurrence cannot be excluded from history alone | give the name of a DLQ or job-failure alarm (alarm history), or metrics with full retention |
| G6: CloudTrail returned nothing for a window that contains a deployment | who or what started the 06:24:10 deployment is unknown; "nobody changed anything" is NOT concluded | rerun without the resource-name filter over 06:15-06:30, or ask the deployment pipeline owner |
| G7: task definition read empty (W2-Q3): no image tag, no old revision number, no env-var names | the code behind rev 19 is unverified: PR #902 / v4.12.0 is a candidate only, which caps the cause at Likely | read the image tag of payments-worker:19 and of the previous revision, or ask the deploy owner which release went out at 06:24 |
| G8: queue redrive policy unread (W3-Q1) and per-revision totals not returned (W2-Q1) | the step "failed attempts become DLQ messages" is Likely (about 3 error lines per DLQ message is only an inference); the old revision's refund-job volume is unknown, so H3 stays open | read the jobs queue's redrive settings; count lines per revision including lines with no `error` field |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: `lessons.md` does not exist |
| Re-verified this run | none |
| History lookup | run after the ranked hypotheses existed: `grep -rli -e payments-worker -e job-failure -e queue-backlog .culiops/sre-investigate/incidents/` and `grep -n "failure-mode" .culiops/sre-investigate/lessons.md`: no matches (neither path exists). No `from-history:` entries. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | `iam simulate-principal-policy` returned rows for 3 actions not asked and no row for 3 of the 10 fixed actions; compare the returned names with the requested list before saying read-only | W0-Q3 |
| process | cw-logs | Insights estimate from describe-log-groups storedBytes was 0.004 GB for a 20-minute window on /ecs/payments-worker but bytesScanned was 0.109 GB (about 29 times higher); treat the estimate as an order of magnitude and record the actual | W1-Q6 |
| process | aws | `aws ecs list-tasks --desired-status STOPPED` returned an empty reply 48 minutes after a service event named two stopped tasks; read stopped tasks in wave 0 or from CloudTrail, never treat the empty reply as none | W1-Q2 |
| identifier | cw-logs | /ecs/payments-worker holds JSON lines with fields level, task_def_revision, handler, error, message_id, file, line; `stats count(*) by task_def_revision, error` gives the old-versus-new split but drops lines that have no `error` field, so it gives no per-revision totals | W2-Q1 |
| process | github | `gh pr list` on example-org/payments-worker returned a release-compare summary with no dates or patch; it cannot date a release against a rollout, read the task definition image tag first | W2-Q2 |
| process | aws | `cloudtrail lookup-events` with ReadOnly=false and a resource-name filter returned nothing around a known deployment; rerun without the resource filter before reading it as no writes | W2-Q5 |
