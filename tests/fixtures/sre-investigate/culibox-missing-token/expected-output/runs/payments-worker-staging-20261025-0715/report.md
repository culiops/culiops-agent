# Investigation: payments-worker staging: refund jobs fail with a TypeError and fill the dead-letter queue

Run: payments-worker-staging-20261025-0715 · Mode: Fast · Window: 2026-10-25 06:30–07:15 UTC (01:30–02:15 America/Bogota) · Onset: 06:24:51 UTC (01:24:51 America/Bogota)
Access: staging-read: no listed write action allowed among the 7 that returned a row (all implicitDeny); ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack returned no row, so write capability is only partly checked (gap), and the role is not called read-only. prod-read: write capability unknown (gap): the SSO session expired, so the check could not run.

## TL;DR

| Field | Value |
|---|---|
| Cause | Task definition revision 19 (deployed 06:24:10 UTC, 01:24:10 local) fails every refund job with `TypeError: refund_amount() missing 1 required positional argument: 'currency'` at `payments_worker/handlers/refund.py` line 48. The likely code origin is "refunds: support partial refunds (#902)" in release v4.12.0. · label: Likely |
| Weakest link | Rev 19 to PR #902 / v4.12.0 is not verified: the task definition read came back empty (no image tag) and the diff text was not read. The step from failed attempts to dead-lettered messages also rests on queue settings that came back empty. Both Likely. Confirmed parts: only rev 19 fails (738 identical errors, first at 06:24:51 UTC), the old revision shows none, and the DLQ went from 0 to 240. |
| Impact | Staging only. Refund jobs have been failing since 06:24:51 UTC (01:24:51 local) and were still failing at 07:10; 240 jobs in `payments-worker-dlq`, rising about 24 per 5 minutes. **Prod is not determined**: the prod-read session expired, so nothing about prod was read. |
| Severity | SEV4 (suggested) because it is staging and the severity scale rates staging SEV4 unless it blocks a release. Refunds are a core flow, so reconsider if prod runs the same release. The incident owner decides. |
| Pattern | unclassified · 14-day pull returned 1 of 336 hourly points, the −7d window was empty, no alarm history · Assumed |
| Recommended action | First find out whether prod runs the same release as staging: re-authenticate prod-read (see Gaps), then compare prod's current task definition image and its dead-letter queue. Then, for staging, decide between rolling back to the previous task definition revision (at the cost of also dropping the boto3 bump and anything else in rev 19) and correcting the `refund_amount()` call and releasing a fix. Redrive the dead-lettered jobs only after the fix, as a planned step. Check each with `pre-flight`. |
| Time to cause | First Likely in wave 1 (TypeError on rev 19 right after the rollout); the full chain at Likely in wave 2. Confirmed not reached. Minutes not measured: no clock was available in this environment. |
| Similar past incidents | none (no history yet) |

## Impact

- **Symptom.** Refund-handler jobs raise the TypeError above and end up in `payments-worker-dlq`. The jobs queue is not backing up (0–9 visible messages in every 5-minute bucket, W1-Q4), so jobs are being picked up and failing, not waiting.
- **Affected.** Staging, account 444455556666 (internal, non-production). DLQ visible messages: 0 in every bucket 05:30–06:20, 24 in the 06:25 bucket, 240 in the 07:10 bucket, with no drain (W1-Q4). 738 identical error lines from 06:24:51 to the end of the data (W2-Q1). The share of all jobs failing was not measured: no throughput metric was pulled and per-revision totals were not returned. Other handlers show no error lines carrying an `error` field in 03:00–07:15; lines logged without that field would not appear.
- **Since / ongoing.** 06:24:51 UTC (01:24:51 local), 5 minutes before the 06:30 UTC you gave. Ongoing at 07:10 UTC (02:10 local).
- **Is prod affected?** Not determined. The prod-read session is expired (Gaps G1), so no prod query ran and none was routed around. Prod is affected only if it runs the same release and receives refund jobs; neither was checked, so this is Assumed.
- **Basis.** No SLO and no request-count metric exist in the environment file: queue depth against baseline (W1-Q4) and error lines (W1-Q6, W2-Q1). Confirmed for the staging failure; Assumed for traffic share and for prod.
- **Third party in the path.** None known.

## Causal chain

1. Trigger: ECS deployment `ecs-svc/2290457731864021954` of task definition `payments-worker:19` was created at 06:24:10 UTC (01:24:10 local); its tasks started at 06:24:22 UTC; the two old tasks stopped at 06:27:31 UTC; steady state at 06:28:52 UTC. · Confirmed · W1-Q1
2. Mechanism: Rev 19 tasks raise `TypeError: refund_amount() missing 1 required positional argument: 'currency'` at `refund.py:48` on refund jobs. 738 identical lines, the first at 06:24:51 UTC (01:24:51 local), which is 41 s after the rollout was created and 29 s after its tasks started. The old revision (log field says 18) has no TypeError in 03:00–07:15, including the 3 minutes it ran beside the new tasks, and no earlier occurrence exists. Per-revision totals were not returned, so this split is failing counts only. · Confirmed (failures are on rev 19 only, and the onset follows the rollout start) · W1-Q6, W2-Q1
   - Code origin: the newest release range v4.11.0 to v4.12.0 contains `6c1d0e2 refunds: support partial refunds (#902)`, which changes `payments_worker/handlers/refund.py` (14 lines), the file in the failing frame, plus a boto3 bump. The deployed ref could not be resolved and no patch was read, so this is a candidate on the failing path, not a verified diff. · Likely · W2-Q2, W2-Q3
3. Symptom: refund jobs fail and the DLQ fills (0 to 240 between 06:20 and 07:10 UTC). The 738 error lines against 240 DLQ messages is about 3 attempts per dead-lettered message, which fits a redrive after roughly three receives. The redrive policy was not read, so that link is an inference. · DLQ rise: Confirmed (W1-Q4); failed attempts becoming those DLQ messages: Likely (W2-Q1, W3-Q1)

Alternatives, in rank order:
- H3, upstream producer began sending refund messages without a currency: Assumed, not ruled out. The producer is unknown, per-revision totals are missing, and it is not shown that the old tasks received any refund job in the overlap. It fits worse than the deploy (onset 41 s after the worker rollout; `refund.py` changed in the newest release). (W2-Q1)
- Ruled out: H2, a scheduled job near 06:24, because no EventBridge rule or Scheduler schedule is listed in the default bus and group (W2-Q4); H4, capacity or task churn, because running 2 of 2, no failed tasks and steady state at 06:28:52 (W1-Q1; the stopped-task detail was unreadable); H5, provider timeout or outage, because the `error` breakdown over 03:00–07:15 holds only the TypeError and two old-revision throttle lines (W2-Q1; lines without an `error` field are not covered).
- Noted, not a hypothesis: two `SQS ReceiveMessage throttled, retrying` lines on the old revision, the first at 03:12:07 UTC (22:12 local, previous day), three hours before the onset and absent from rev 19. They are not onset-aligned.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1: prod-read SSO session expired ("Token has expired and refresh failed"); no identity, no write check, no prod reads | "Is prod affected?" cannot be answered from prod data; everything about prod is Assumed | `! aws sso login --profile prod-read` |
| G2: `SENTRY_AUTH_TOKEN` is unset | no Sentry issues, first-seen times or release tags; error-tracker corroboration is missing (the staging log evidence is unaffected) | set the `SENTRY_AUTH_TOKEN` environment variable (name only, a read-only token) in the shell that runs this session |
| G3: staging-read write check partial (3 of 10 fixed actions returned no row; 3 unrequested rows returned) | the Access line cannot say "read-only confirmed" | re-run the simulation, or ask the account owner to confirm the role is read-only |
| G4: stopped-task list came back empty although a service event names two stopped tasks 48 minutes earlier | the replaced tasks' revision, stop code and exit codes are unknown; "old revision" is presumed from the event and the log field | read it within an hour of a rollout, or from the task definition history |
| G5: recurrence unclassified (1 of 336 hourly points, −7d empty, no alarm history) | a schedule or an earlier occurrence cannot be excluded from history alone | give the name of a DLQ or job-failure alarm, or metrics with full retention |
| G6: CloudTrail returned nothing for a window that contains a deployment | who or what started the 06:24:10 deployment is unknown; "nobody changed anything" is not concluded | rerun without the resource-name filter over 06:15–06:30, or ask the deployment pipeline owner |
| G7: task definition read came back empty (no image tag, no previous revision number, no variable names) | PR #902 / v4.12.0 is a candidate only, which caps the cause at Likely | read the image tag of `payments-worker:19` and of the previous revision, or ask the deploy owner which release went out at 06:24 UTC |
| G8: queue redrive settings unread; per-revision totals not returned | the step from failed attempts to DLQ messages is Likely; H3 stays open | read the jobs queue's redrive settings; count lines per revision including lines with no `error` field |

Open items need your input.

## To confirm, a human would…

1. Read the image tag (or digest) of task definition `payments-worker:19` and of the previous revision, and check that they correspond to v4.12.0 and v4.11.0 (or to a commit containing PR #902). A match ties the code change to the rollout and supports upgrading the cause to Confirmed; a mismatch sends the search elsewhere in the release.
2. Open the patch of PR #902 for `payments_worker/handlers/refund.py` around line 48 and look for a changed `refund_amount()` signature (a new `currency` parameter) or a call site that was not updated. That would confirm the mechanism.
3. Read the jobs queue's redrive settings (maximum receive count, visibility timeout) and have its owner look at a few dead-lettered messages. They should be refund jobs, and their count should be close to the error count divided by the maximum receive count. Receiving messages hides them from consumers for the visibility timeout, so this needs the owner's care.
4. After re-authenticating prod-read, read which task definition and release prod's payments-worker runs, the depth of prod's dead-letter queue and whether prod's log group shows the same TypeError. Or ask the prod owner. This is the answer to "is prod affected?".
5. Ask the team that produces `payments-worker-jobs` whether any change to the refund message format shipped around 06:24 UTC. A yes would revive H3; a no keeps the deploy as the lead.
6. Ask the deployment pipeline owner (or read CloudTrail without the resource filter) who started the 06:24:10 deployment and from which commit.
7. After setting `SENTRY_AUTH_TOKEN`, compare the `payments-worker` project's first-seen time and release tag for this TypeError with the 06:24:51 UTC onset.

## Follow-ups

Prose only. Each is a candidate for a human, to be checked with `pre-flight` before it is applied.

| Kind | Item |
|---|---|
| Fix | Either return the staging service to the previous task definition revision, at the cost of losing everything else in rev 19 (including the boto3 bump), or correct the `refund_amount()` call in the refund handler and release a fix. After the fix, plan a redrive of the dead-lettered refund jobs; redriving earlier would only send them through the same failure again. |
| Prevention | Consider making a deployment fail and roll back on its own when the queue's failures climb right after a rollout (for example an ECS deployment rollback tied to an alarm on dead-letter depth), at the cost of an extra alarm to tune and a slower rollout. Consider a test that calls the refund path with a real job payload before release. |
| Observability gap | No alarm on dead-letter depth was known, so this was noticed by a person at about 06:30 UTC, six minutes after it started. Log lines carry `task_def_revision` but no release version, and per-revision totals cannot be counted from lines without an `error` field. The Sentry token and the prod session were unavailable during the incident. |

## Cost

20 queries · 0.218 GB of logs (two Insights queries, each reported 0.109 GB with identical statistics, counted separately) · 8 CloudWatch metric requests · no other metered units · well under $0.01 in metered charges at list prices (not re-checked this run)
