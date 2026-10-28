# Ledger: payments-worker staging 20261025-0715

Mode: Fast
Budget used: 15 evidence queries (waves 1-2) of the template Fast default 20 (environment.md sets no query cap; 11 wave-0 / profile-build API calls listed separately) · 0.218 GB Logs Insights scanned as reported (W1-Q12 and W2-Q2 returned the same statistics) of the template 2 GB; the environment.md ask threshold of 5 GB was never approached · 13 CloudWatch metric requests of 100 · no other metered units

## Problem

| Field | Value |
|---|---|
| What | Reporter: "payments-worker jobs have been failing in staging since about 06:30 UTC. Is prod affected too?" Measurable restatement: jobs consumed by ECS service payments-worker (cluster staging) fail, and failed messages accumulate in SQS queue payments-worker-dlq. Second question: whether the same failure exists in prod. |
| Where | payments-worker, environment staging (account 444455556666, eu-west-1, cluster staging, 2 Fargate tasks). Sibling in scope: payments-worker in prod (account 111122223333, profile prod-read), not readable this run (Gaps G1). orders-api shares the staging cluster but is a different service and was not examined. |
| When | Reported onset about 06:30 UTC (explicit zone). True onset from logs: first error 2026-10-25 06:24:51.204 UTC (W1-Q12), 41 s after the ECS deployment was created (06:24:10 UTC, W0-Q10). Reported time 01:30 America/Bogota; true onset 01:24:51 local. |
| Who is affected | Staging only as far as read: refund jobs (handler `refund`) on task definition :19. Capture jobs: no errors seen in the logs, not separately measured. Prod: unknown (G1). |
| Trigger | Operator report in chat (no alarm, ticket or link). |
| Mitigations already applied | None known. The service is still on task definition :19 (PRIMARY, COMPLETED 06:28:52 UTC) when read (W0-Q10); no rollback seen. |
| Assumptions made at intake | (1) Time 06:30 has an explicit zone (UTC), used as given; window 06:00 to now, converted to 01:00 America/Bogota (UTC-5, from environment.md). (2) `date -u` returned no output (W0-Q1), so "now" is taken as 07:15 UTC 2026-10-25, the end of the data the backends returned (Logs Insights data to 07:15, SQS to 07:10); the run directory name uses it. (3) environment.md has no budgets section except the 5 GB Logs Insights ask; the template Fast defaults are used for counting only. (4) Core flows per environment.md: payment capture and refunds; staging incidents SEV4 unless they block a release. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| staging-read | account 444455556666 (matches environment.md), role AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921 (session name not recorded) | no write allowed among the actions returned: 10 results, all implicitDeny. The reply did not contain 3 of the 10 requested actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) and contained 3 unrequested ones (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy). Not reported as "read-only confirmed"; the 3 missing actions are a gap (G3). No boxed warning. | Session valid. Resource-scoped writes not covered by the simulation. |
| prod-read | not established: SSO token expired and refresh failed (exit 255) | write capability unknown (gap): identity failed, so the principal could not be resolved; this is not a finding that the credentials can write | Gap G1. Not routed around. |
| Kubernetes | none (ECS Fargate only, per environment.md) | not applicable | no context listed |
| Sentry token SENTRY_AUTH_TOKEN | not available | not applicable | presence check printed no "set" line; treated as unset (G2). Culibox: `command -v agentbox-env` succeeded; the required notice was printed and the run continued standalone. |

## Impact

| Field | Value |
|---|---|
| Symptom | Refund-handler jobs fail with `TypeError: refund_amount() missing 1 required positional argument: 'currency'` (payments_worker/handlers/refund.py line 48). 738 such errors 06:24:51 to 07:15 UTC, all on task definition revision 19. payments-worker-dlq grows from 0 (until 06:20) to 24 at 06:25 and 240 at 07:10, a steady +24 per 5 minutes. |
| Affected | Staging payments-worker, refund handler. payments-worker-jobs queue is not backing up (visible 0 to 9 throughout). Prod: unknown. Customer-facing: no (staging). Core flow "refunds" is affected in staging only. |
| Since / ongoing | 2026-10-25 06:24:51 UTC (01:24:51 local) · ongoing: yes (last sampled error 07:12:29, DLQ still rising at 07:10) |
| Suggested severity | SEV4 because it is non-production (environment.md: staging incidents are SEV4 unless they block a release). Whether it blocks a release is not known (Assumed). |
| Basis | queue depth W1-Q7, W1-Q8; log counts W1-Q12; samples W2-Q2 · label: Confirmed for staging; release impact Assumed |
| Third party in the path | none known (no third party in the profile; the payment provider, if any, is not named in environment.md) |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-25T06:00:00Z | 2026-10-25T07:15:00Z |
| Baseline (previous) | 2026-10-25T04:45:00Z | 2026-10-25T06:00:00Z |
| Baseline (−7d) | 2026-10-18T06:00:00Z | 2026-10-18T07:15:00Z |

The Logs Insights stats query (W1-Q12) deliberately used 03:00 to 07:15 (4 h 15 min, inside the 12 h `log_metric` cap) to find an earlier onset and a longer baseline in one scan.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none: the trigger is an operator report, no alarm was named and no alarm history was read. Sibling alarms: not listed. |
| Signal, 14d at 1h resolution | statistic Maximum of ApproximateNumberOfMessagesVisible per hour (saturation signal), payments-worker-dlq and payments-worker-jobs (W1-Q9, W1-Q10). DLQ: 1 hourly point returned (hour 05:00, covering 05:30-05:55 only), value 0; median 0 · p95 0 · max 0 · incident 240. Jobs: 1 point, max 7; incident max 9. |
| Coverage | CloudWatch returned 1 of 336 expected hourly points per queue (data starts 2026-10-25 05:30 UTC); previous-window coverage 05:30-06:00 of 04:45-06:00; −7d window returned nothing. Alarm history: not read. Logs: Insights data from 03:00 UTC (the requested start). |
| Class | unclassified · shape: step (failure rate steps from 0 to about 15 errors per minute at 06:24:51 and stays flat; DLQ depth is the constant-rate ramp it produces) |
| Reason | The rules need 14 days of signal or 30 days of alarm history; coverage is 1 of 336 hourly points and no alarm exists, so none of scheduled, chronic, recurring or sudden can be applied. Recorded as gap G6. |
| Label and queries | Assumed · W1-Q9, W1-Q10, W1-Q7, W1-Q8 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 03:12:07 | 2 lines "SQS ReceiveMessage throttled, retrying" on revision 18 (3 h before onset; none after 06:00) | Logs Insights | W1-Q12 |
| 05:30 | SQS metrics coverage begins; DLQ 0, jobs queue 0 to 7 | CloudWatch | W1-Q7, W1-Q8 |
| 06:24:10 | ECS deployment ecs-svc/2290457731864021954 created, task definition payments-worker:19 (PRIMARY) | ECS | W0-Q10 |
| 06:24:22 | ECS: service started 2 tasks (3e4f5a6b..., 7c8d9e0f...) | ECS service events | W0-Q10 |
| 06:24:51.204 | First TypeError at refund.py:48 on revision 19 (message_id msg-7c1d) | Logs Insights | W1-Q12, W2-Q2 |
| 06:25 | DLQ first non-zero point: 24 visible | CloudWatch | W1-Q8 |
| 06:25:03.882 | Second sampled error (msg-91aa) | Logs Insights | W2-Q2 |
| 06:27:31 | ECS: service stopped 2 running tasks (0f1e2d3c..., 9a8b7c6d...); revision not stated, presumed the old tasks (Assumed) | ECS service events | W0-Q10 |
| 06:28:52 | Deployment COMPLETED, service reached steady state (2/2 running, failedTasks 0) | ECS | W0-Q10 |
| 06:30 | Reported onset (from the reporter, not a query); DLQ 48 | operator report; CloudWatch | W1-Q8 |
| 06:31:40 | Sampled error (msg-0b3e) | Logs Insights | W2-Q2 |
| 07:10 | DLQ 240; jobs queue 8 | CloudWatch | W1-Q7, W1-Q8 |
| 07:12:29 | Last sampled error in the 03:00-07:15 pull (msg-e810); errors continue | Logs Insights | W1-Q12 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The rollout of task definition :19 (06:24:10 UTC) broke the refund handler: tasks on :19 raise a TypeError on refund jobs, which then end in the DLQ | errors only on :19 tasks, starting within about a minute of the rollout, none on :18; DLQ rising from about 06:25 | errors split by task_def_revision, 03:00-07:15 (W1-Q12): any :18 TypeError, or a first TypeError before 06:24:10, refutes it | main | Confirmed (rollout breaks refund jobs). Code origin PR #902: Likely (see below) |
| H2 | A configuration change in :19 (environment or secret names added, removed or moved) is the mechanism | a config-type error at task start; names differ between :18 and :19 | env/secret names of :18 against :19 (W2-Q1); a code-level call-signature error text refutes a config mechanism | main | Assumed (comparison unreadable, W2-Q1 empty); the error text is a Python call-signature TypeError, which does not look like a config failure |
| H3 | SQS ReceiveMessage throttling | throttle lines rising with the onset | count of "throttl" lines per revision 03:00-07:15 (W1-Q12) | main | Ruled out: 2 lines, both at 03:12 on :18, none after 06:00 |
| H4 | Downstream (payment provider) timeout or outage | timeout or connection errors, a ceiling shape | timeout / failed / error strings in the app log in the window (W1-Q12): any non-TypeError error refutes the downstream story | main | Ruled out for what the app log shows: all 738 matched errors are the TypeError. Provider side not visible. |
| H5 | Capacity or placement failure on ECS | running below desired, failedTasks above 0, rollout stuck | ECS service description (W0-Q10): running 2 of 2, pending 0, failedTasks 0, COMPLETED refutes it | main | Ruled out |
| H6 | Queue-side stall (consumers not draining, visibility timeout) | jobs queue depth climbing | jobs queue visible depth vs previous window (W1-Q7): flat 0 to 9 refutes it | main | Ruled out: consumers receive and fail messages, queue is not growing |
| H7 | A scheduled job or scheduled scaling action | onset within 15 min of a fire time | schedule listings (W1-Q3 to W1-Q6) | main | Assumed: all four listings returned an empty reply; the onset is 41 s after the deployment event; no `sched:` hypothesis because the class is unclassified, not scheduled |

- H1 status: supported · evidence: W0-Q10, W1-Q12, W2-Q2, W1-Q8 · note: old-against-new evidence is that revision 18 has no TypeError (it ran alongside :19 from 06:24:22 to about 06:27:31) while :19 has 738. Code origin: stack frame file `payments_worker/handlers/refund.py:48` is the file changed by commit 6c1d0e2 "refunds: support partial refunds (#902)" (14 lines) in the 2-commit gap v4.11.0..v4.12.0 (W2-Q4). The deployed image tag was not readable (W2-Q1 empty), so :19 = v4.12.0 is not verified: Likely.
- H2 status: open · evidence: W2-Q1 (empty) · note: lower rank than H1; no config-type error text in W1-Q12.
- H3 status: refuted · evidence: W1-Q12.
- H4 status: refuted (app-log scope) · evidence: W1-Q12.
- H5 status: refuted · evidence: W0-Q10.
- H6 status: refuted · evidence: W1-Q7.
- H7 status: open · evidence: W1-Q3, W1-Q4, W1-Q5, W1-Q6 (empty replies).
- Model tier: Fast mode, all hypotheses tested by the main session. Early-stop rule: H1 reached Confirmed and H3 to H6 are Ruled out; H2 and H7 are Assumed, not Ruled out, so wave 2 still ran its change-source and sample queries; no wave 3.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/payments-worker (read through `gh`, read-only; no local clone listed) | not returned (unverified) | not read | read in W2-Q4 (clock unavailable) | not resolved: task definition image tags unreadable (W2-Q1). `gh` listed a 2-commit gap v4.11.0..v4.12.0 (6c1d0e2 partial refunds #902; b4a9f37 boto3 bump #899); that these tags are the :18 and :19 images is not verified. |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | — | local shell: `date -u +%H:%M:%S` | now | none | empty output; clock unavailable, "now" assumed 07:15Z. |
| W0-Q2 | — | `aws sts get-caller-identity --profile staging-read --region eu-west-1` (profile staging-read verified) | now | free | account 444455556666 = environment.md; role AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921. Confirmed. link: re-run the command |
| W0-Q3 | — | `aws iam get-role --profile staging-read --role-name AWSReservedSSO_ReadOnly_9f8e7d6c5b4a3921 --query Role.Arn --output text` | now | free | role path /aws-reserved/sso.amazonaws.com/ resolved. |
| W0-Q4 | — | `aws iam simulate-principal-policy --profile staging-read --policy-source-arn <role arn from W0-Q3> --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack` | now | free | 10 results, all implicitDeny; 3 requested actions missing from the reply, 3 unrequested present (G3). Details: `raw/` not kept (no values). |
| W0-Q5 | — | `aws sts get-caller-identity --profile prod-read --region eu-west-1` | now | free | exit 255: "Token has expired and refresh failed" (SSO). Gap G1. |
| W0-Q6 | — | local shell: presence check of SENTRY_AUTH_TOKEN with `${SENTRY_AUTH_TOKEN:+x}` | now | none | no "set" line printed; treated as unset. Gap G2. |
| W0-Q7 | — | `aws logs describe-log-groups --profile staging-read --region eu-west-1 --log-group-name-prefix /ecs/payments-worker --output json` | now | free; estimate for 03:00-07:15: 3,758,096,384 B x 15,300 s / (14 d x 86,400 s) = 0.048 GB | log group /ecs/payments-worker verified: STANDARD, retention 14 d, 3.76 GB stored. link: re-run |
| W0-Q8 | — | helper PROFILE: `aws ecs list-clusters --profile staging-read --region eu-west-1` | now | free | cluster `staging` (verified). |
| W0-Q9 | — | helper PROFILE: `aws ecs list-services --profile staging-read --region eu-west-1 --cluster staging` | now | free | services orders-api, payments-worker (verified). |
| W0-Q10 | — | helper PROFILE and Phase 2 deploy record: `aws ecs describe-services --profile staging-read --region eu-west-1 --cluster staging --services payments-worker` | now | free | PRIMARY deployment ecs-svc/2290457731864021954, task def payments-worker:19, created 06:24:10Z, COMPLETED 06:28:52Z; desired 2, running 2, pending 0, failedTasks 0; FARGATE; events: started 2 tasks 06:24:22, stopped 2 tasks 06:27:31, steady state 06:28:52. Confirmed. |
| W0-Q11 | — | helper PROFILE: `aws sqs list-queues --profile staging-read --region eu-west-1 --queue-name-prefix payments-worker` | now | free | payments-worker-jobs, payments-worker-dlq (verified). |
| W0-Q12 | — | helper PROFILE: `aws elbv2 describe-target-groups --profile staging-read --region eu-west-1 --query "TargetGroups[?contains(TargetGroupName,'payments-worker')].TargetGroupArn"` | now | free | empty reply `{}`; no target group recorded (worker service, expected); not treated as proof. |
| W0-Q13 | — | helper PROFILE: `aws rds describe-db-clusters --profile staging-read --region eu-west-1 --query "DBClusters[?contains(DBClusterIdentifier,'payments-worker')].DBClusterIdentifier"` | now | free | empty reply `{}`; no data store recorded (unverified). |
| W1-Q1 | — | ECS service description | now | free | reused W0-Q10 (not repeated). |
| W1-Q2 | — | `aws ecs list-tasks --profile staging-read --region eu-west-1 --cluster staging --service-name payments-worker --desired-status STOPPED --output json` | now (ECS keeps stopped tasks about 1 h) | free | empty reply `{}` although the service event names 2 tasks stopped at 06:27:31: treated as unreliable, not as "none". Stop reasons unknown (G5). |
| W1-Q3 | — | `aws events list-rules --profile staging-read --region eu-west-1 --output json` (schedule expressions) | now | free | empty reply `{}`. Not used as a negative. |
| W1-Q4 | — | `aws scheduler list-schedules --profile staging-read --region eu-west-1 --output json` | now | free | empty reply `{}`. Not used as a negative. |
| W1-Q5 | — | `aws application-autoscaling describe-scheduled-actions --profile staging-read --region eu-west-1 --service-namespace ecs --resource-id service/staging/payments-worker --output json` | now | free | empty reply `{}`. |
| W1-Q6 | — | `aws application-autoscaling describe-scaling-activities --profile staging-read --region eu-west-1 --service-namespace ecs --resource-id service/staging/payments-worker --output json` | now | free | empty reply `{}`; no scaling activity visible (running count stayed 2 in W0-Q10). |
| W1-Q7 | — | `aws cloudwatch get-metric-data` AWS/SQS ApproximateNumberOfMessagesVisible, QueueName=payments-worker-jobs (verified), Period 300, Maximum, three windows (queue verified in W0-Q11) | incident 06:00-07:15; previous 04:45-06:00; −7d 2026-10-18 06:00-07:15 | 3 metric requests | incident: 15 points, 0 to 9, median 5; previous: 6 points (05:30-05:55 only), 0 to 7, median 3.5; −7d: no data. No backlog. Confirmed (queue not growing). raw/m-sqs-jobs.json |
| W1-Q8 | — | same for QueueName=payments-worker-dlq (verified), three windows | same | 3 metric requests | incident: 0 at 06:00-06:20, then 24 at 06:25, +24 every 5 min, 240 at 07:10; previous: 0 (6 points); −7d: no data. Confirmed. raw/m-sqs-dlq.json |
| W1-Q9 | — | same metric, jobs queue, Period 3600, Maximum, 2026-10-11T06:00Z to 2026-10-25T06:00Z | 14 d x 1 h | 1 metric request | 1 of 336 hourly points (hour 05:00): max 7. Coverage gap (G6). |
| W1-Q10 | — | same, dlq queue | 14 d x 1 h | 1 metric request | 1 of 336 hourly points: max 0. Coverage gap (G6). |
| W1-Q11 | — | `aws cloudwatch get-metric-data` AWS/ECS CPUUtilization and MemoryUtilization (ClusterName=staging, ServiceName=payments-worker) and AWS/SQS NumberOfMessagesSent, NumberOfMessagesDeleted, ApproximateAgeOfOldestMessage (jobs queue), Period 300, incident window | 06:00-07:15 | 5 metric requests | empty reply `{}`: rate, saturation and age signals not obtained (G5). |
| W1-Q12 | — | Logs Insights on /ecs/payments-worker (verified): `filter @message like /(?i)error|exception|timeout|failed|throttl/ \| stats count(*) as n, min(@timestamp) as first by task_def_revision, error` (fields task_def_revision, error verified by this result) | 03:00-07:15 | est 0.048 GB (below 5 GB ask) | 740 matches in 288,104 records scanned, 0.109 GB scanned (2.3 x the estimate). Revision 19: "TypeError: refund_amount() missing 1 required positional argument: 'currency'" n=738, first 06:24:51.204. Revision 18: "SQS ReceiveMessage throttled, retrying" n=2, first 03:12:07.660. No other error text. Confirmed (mechanism). raw/li-9a0b1c2d.json |
| W2-Q1 | — | `aws ecs describe-task-definition --profile staging-read --region eu-west-1 --task-definition payments-worker:18` and `:19` with names-only `--query` (images, env and secret names) | now | free | both replies empty `{}`: image tags and env/secret names unreadable (G4). |
| W2-Q2 | — | Logs Insights on /ecs/payments-worker: `fields @timestamp, @message \| filter @message like /refund_amount/ \| sort @timestamp asc \| limit 100` | 06:15-06:35 (20 min, inside the 30 min raw cap) | est 0.004 GB | 3 lines in the window (06:24:51.204, 06:25:03.882, 06:31:40.017): JSON with level error, task_def_revision 19, handler refund, file payments_worker/handlers/refund.py, line 48; statistics returned as in W1-Q12 (0.109 GB, 740 matched), so the scan figure is suspect and counted as returned. Confirmed. raw/li-3a4b5c6d.json |
| W2-Q3 | — | `TZ=UTC aws cloudtrail lookup-events --profile staging-read --region eu-west-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-25T04:25:00Z --end-time 2026-10-25T06:40:00Z --output json` | 04:25-06:40 | free | empty reply `{}` although a deployment happened at 06:24: who or what deployed is unknown (G5). |
| W2-Q4 | — | `gh pr list --repo example-org/payments-worker --state merged --limit 20 --json number,title,mergedAt,mergeCommit` (read-only) | recent merges | free | reply is a compare summary: 2 commits between v4.11.0 and v4.12.0: 6c1d0e2 "refunds: support partial refunds (#902)" and b4a9f37 "deps: bump boto3 to 1.40.61 (#899)"; files changed: payments_worker/handlers/refund.py (14 lines), requirements.txt (2). Deployed ref not verified. Likely. |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1 prod-read: SSO token expired and refresh failed (W0-Q5). Write capability of prod-read unknown. | The question "is prod affected?" cannot be answered. No claim about prod is made. Whether :19 / v4.12.0 reached prod is unknown. | `! aws sso login --profile prod-read`, then ask for a prod wave. |
| G2 SENTRY_AUTH_TOKEN not set (W0-Q6). | Sentry issues, first-seen vs onset and release tags were not read; the log evidence stands alone. | Export SENTRY_AUTH_TOKEN (read-only scopes) in the shell that runs the skill; the variable name only is recorded. |
| G3 staging-read write-check incomplete: the simulation reply omitted ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack (W0-Q4). | "Read-only confirmed" is not claimed; no boxed warning because nothing returned was allowed. | Ask the account owner to confirm the role is read-only, or rerun the simulation once the reply lists all 10 actions. |
| G4 Task definition image tags and env/secret names unreadable (W2-Q1 empty). | Mapping :19 to v4.12.0 and PR #902 is Likely, not Confirmed; H2 stays Assumed. | A human reads the image tag of payments-worker:18 and :19 in the ECS console. |
| G5 Empty `{}` replies: stopped tasks (W1-Q2), schedules (W1-Q3 to W1-Q6), ECS/SQS rate and age metrics (W1-Q11), CloudTrail (W2-Q3), target group and RDS lookups (W0-Q12, W0-Q13). | None used as a negative. H7 (schedule) stays Assumed; stop reasons, who deployed, and consumer rate/age are unknown. | Re-run those reads with a profile or role that returns data, or ask the owning team. |
| G6 Recurrence coverage: 1 of 336 hourly points per queue, no alarm history. | Recurrence class is unclassified (Assumed); no history-based claim. | Check whether the queues are new or CloudWatch history is missing; name the alarm on payments-worker-dlq if there is one. |
| G7 No business counter for refunds / payment capture in environment.md. | Impact is sized from queue depth and error logs, not from refund success counts. | Add a refund counter (name and datasource) to environment.md. |
| G8 No IaC repo, local clone or tracing/APM backend in environment.md. | IaC history and drift were not read; dependency map comes from the profile only. | Name the IaC repo and any trace backend in environment.md. |

## Untrusted text

none seen. Log lines read (W1-Q12, W2-Q2) are structured error records; none contained instruction-like text.

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none: `ls .culiops/sre-investigate` lists only environment.md, so there is no lessons.md. |
| Re-verified this run | none (no lessons). |
| History lookup | run after the ranked hypotheses existed: `ls .culiops/sre-investigate/incidents` and `cat .culiops/sre-investigate/lessons.md` both printed "No such file or directory". No history yet; no `from-history:` hypothesis. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| identifier | cw-logs | Log group /ecs/payments-worker holds JSON lines with fields task_def_revision, error, handler, file, line; group by task_def_revision to split old from new rollout. | W1-Q12 |
| process | cw-logs | Logs Insights bytesScanned was 2.3 times the storedBytes-based estimate (109 MB against 47.5 MB for 255 min); keep a margin when estimating. | W1-Q12 |
| process | aws | iam simulate-principal-policy returned 10 results with 3 action names that were not requested and 3 requested ones missing; compare returned names with the fixed list before saying read-only confirmed. | W0-Q4 |
| process | aws | ecs list-tasks STOPPED, cloudtrail lookup-events and describe-task-definition returned an empty reply right after a deploy; treat an empty reply as unverified, not as none. | W1-Q2 |
| failure-mode | cw-logs | After a rollout, an ECS deployment can report COMPLETED while every refund job fails; split Logs Insights errors by task_def_revision and watch the DLQ visible count (about +24 per 5 min here). | W1-Q12 |
