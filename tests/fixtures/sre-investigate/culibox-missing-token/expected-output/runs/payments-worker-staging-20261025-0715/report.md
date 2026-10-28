
# Investigation: payments-worker staging: refund jobs failing with a TypeError since the :19 rollout

Run: payments-worker-staging-20261025-0715 · Mode: Fast · Window: 2026-10-25 06:00 to 07:15 UTC (01:00 to 02:15 America/Bogota, UTC-5)

## TL;DR

| Field | Value |
|---|---|
| Cause | The rollout of ECS task definition payments-worker:19 (created 06:24:10 UTC) made every refund job fail with `TypeError: refund_amount() missing 1 required positional argument: 'currency'` at payments_worker/handlers/refund.py:48; the likely code origin is the "support partial refunds" change (#902, commit 6c1d0e2) · label: Confirmed for the rollout and the error; the code origin is Likely |
| Weakest link | Which commit is inside :19: the task definition image tags could not be read (W2-Q1 empty), so :19 = release v4.12.0 / PR #902 is Likely, not Confirmed. The cause sentence in the first clause does not depend on it (old tasks had no such error, new tasks did, 41 s after rollout start). The DLQ growth being these same failed jobs is Likely (redrive policy not read). |
| Impact | Staging only as far as read: refund jobs fail since 06:24:51 UTC and land in payments-worker-dlq (240 messages at 07:10, rising 24 per 5 min); the jobs queue is not backing up. Ongoing. Prod: not answerable, prod-read session expired. |
| Severity | SEV4 because it is non-production (staging incidents are SEV4 unless they block a release; whether it blocks one is not known). The incident owner decides. |
| Pattern | unclassified · 1 of 336 hourly points returned and no alarm history · Assumed |
| Recommended action | A human should put staging payments-worker back on task definition :18 (or ship a fix to the refund handler) through the team's normal deploy path, and hold this release back from prod until the refund handler is fixed; check the change with `pre-flight` first. Then check whether prod already runs the same release, and only after the fix decide what to do with the messages in payments-worker-dlq. |
| Time to cause | Clock unavailable (`date -u` printed nothing); Confirmed in wave 1, wave 2 added the sample lines and the code candidate. |
| Similar past incidents | no history yet |

## Impact

Symptom: refund-handler jobs fail with the TypeError above. 738 errors between 06:24:51 UTC (01:24:51 local) and 07:15 UTC, all on task definition revision 19 (W1-Q12, W2-Q2). payments-worker-dlq goes from 0 (to 06:20) to 24 at 06:25, 48 at 06:30, 240 at 07:10: a constant rise of 24 per 5 minutes (W1-Q8). payments-worker-jobs stays at 0 to 9 visible, as before (W1-Q7), so the consumers receive and fail messages and the queue does not back up. Reported onset 06:30 UTC; the true onset is 06:24:51, before the report.

Affected: staging, cluster staging, 2 Fargate tasks, refund handler. Capture jobs showed no errors in the logs but were not measured separately. Customer-facing: no. Core flow "refunds" is affected in staging only; there is no refund counter in environment.md, so the size comes from queue depth and error logs (Confirmed for staging).

Prod: not answerable. The profile prod-read has an expired SSO session (W0-Q5), so nothing about prod was read and no claim about prod is made. Whether :19 / v4.12.0 reached prod is unknown.

Third party in the path: none known.

## Causal chain

1. Trigger: ECS deployment ecs-svc/2290457731864021954 to payments-worker:19 created at 06:24:10 UTC, new tasks started 06:24:22, rollout COMPLETED 06:28:52 with 2 of 2 running and no failed tasks, so ECS saw nothing wrong · Confirmed · W0-Q10
2. Mechanism: tasks on revision 19 raise `TypeError: refund_amount() missing 1 required positional argument: 'currency'` at refund.py:48 in the `refund` handler; first error 06:24:51.204, 41 s after the rollout began; 738 of the 740 matched error lines. Revision 18 tasks, which ran alongside :19 from 06:24:22 until about 06:27:31, logged no such error; their only matched lines are 2 SQS throttle retries at 03:12, three hours earlier · Confirmed · W1-Q12, W2-Q2
3. Symptom: refund jobs fail in staging (738 errors) and failed messages accumulate in payments-worker-dlq, starting 06:25 (34 s after the first error) · jobs failing: Confirmed (W1-Q12); DLQ growth caused by these failures: Likely, the redrive policy was not read (W1-Q8)
4. Code origin (side branch, not needed for steps 1 to 3): the failing file is the file changed by commit 6c1d0e2 "refunds: support partial refunds (#902)" (14 lines in refund.py) between v4.11.0 and v4.12.0; the other commit in that gap is a boto3 bump (#899, requirements.txt only) · Likely · W2-Q4. The error text is a call-signature mismatch (a `currency` argument now required), which fits a change to the refund function. Deployed ref not verified.

Ruled out (queries in the ledger): SQS throttling (2 lines, 03:12, none after 06:00; W1-Q12), a downstream or provider timeout as far as the app log shows (every matched error is the TypeError; W1-Q12), capacity or placement on ECS (running 2 of 2, failedTasks 0; W0-Q10), a stalled consumer or queue-side backlog (jobs queue flat; W1-Q7).

Still open, Assumed: a configuration change in :19 as the mechanism (task definition env and secret names could not be compared, W2-Q1 empty; the error text does not look like a config failure), and a schedule (four schedule listings returned empty replies, W1-Q3 to W1-Q6; the onset is 41 s after the deployment event).

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| prod-read: SSO session expired, refresh failed (W0-Q5). Write capability of prod-read unknown. | "Is prod affected?" is unanswered; no claim about prod. | `! aws sso login --profile prod-read`, then ask for a prod wave (prod payments-worker, its DLQ and the task definition image tag). |
| SENTRY_AUTH_TOKEN not set (W0-Q6). | Sentry first-seen and release data not read; log evidence stands alone. | Export SENTRY_AUTH_TOKEN with read-only scopes in the shell that runs the skill. |
| staging-read write-check incomplete: 3 of the 10 requested actions missing from the simulation reply (W0-Q4). | "Read-only confirmed" is not claimed; nothing returned was allowed, so no warning. | Have the account owner confirm the role is read-only, or rerun the simulation until all 10 actions are listed. |
| Task definition image tags, env and secret names unreadable (W2-Q1 empty). | :19 = v4.12.0 / #902 is Likely; H2 (config) stays Assumed. | Read the image tag and env/secret names of payments-worker:18 and :19 in the ECS console. |
| Empty replies: stopped tasks, schedules, ECS/SQS rate and age metrics, CloudTrail, target group and RDS lookups (W1-Q2 to W1-Q6, W1-Q11, W2-Q3, W0-Q12, W0-Q13). | None used as a negative. Who deployed, why the old tasks stopped, and consumer rate are unknown. | Re-run with a profile that returns data, or ask the owning team. |
| Recurrence: 1 of 336 hourly points, no alarm history (W1-Q9, W1-Q10). | Pattern is unclassified. | Check whether the queues are new or metric history is missing; name any alarm on payments-worker-dlq. |
| No refund / capture counter, no IaC repo, no trace backend in environment.md. | Impact sized from queue depth and logs; IaC drift not checked. | Add the counter, IaC repo and trace backend to environment.md. |

Open items need your input.

## To confirm, a human would…

1. Open task definitions payments-worker:18 and :19 in the ECS console and read the image tags: if :19 carries v4.12.0 (or the commit of #902) and :18 carries v4.11.0, the code origin moves from Likely to Confirmed.
2. Read payments_worker/handlers/refund.py around line 48 at the :19 image's commit, and the patch of #902: if `refund_amount` gained a required `currency` parameter and the call site in the handler does not pass it, that explains the TypeError.
3. Read the redrive policy of payments-worker-jobs: if the maximum receive count is 3, the 738 errors against about 246 dead-lettered messages (240 at 07:10) fit three attempts per message, which would confirm the DLQ link.
4. In the prod account, after signing in, read which task definition and image tag payments-worker runs, whether payments-worker-dlq is growing, and whether the same TypeError appears in /ecs/payments-worker: this answers the prod question.
5. Ask who or what started the 06:24 deployment (a pipeline run or a person); CloudTrail returned nothing to this run.
6. Check whether anything uses the refund handler's output in staging tests (for example a release gate), to settle whether the incident blocks a release and the severity moves above SEV4.

## Cost

15 evidence queries (waves 1 and 2; 11 more API calls in wave 0 and the profile build) · 0.218 GB of logs scanned as reported (2 Logs Insights queries) · 13 CloudWatch metric requests · no other metered units · about USD 0.0011 in metered charges (Logs Insights 0.218 GB at the published per-GB scan price, plus 13 metric requests at the published GetMetricData price; check the CloudWatch pricing page for current rates)
