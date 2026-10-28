# Investigation: orders-api prod: 5xx for about 19 minutes every morning from 02:00 UTC while the nightly reconcile job holds order locks

Run: orders-api-prod-20261021-0240 · Mode: Fast · Window: 2026-10-21 01:30–02:40 UTC (10:30–11:40 JST) · Onset: 2026-10-21 02:01 UTC (11:01 JST)
Access: prod-read: write capability unknown (gap). None of the 7 fixed write actions that returned a row is allowed (all implicitDeny). The simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack. No Kubernetes contexts (ECS Fargate only).

## TL;DR

| Field | Value |
|---|---|
| Cause | The nightly job `orders-reconcile-nightly` (EventBridge, `cron(0 2 * * ? *)`, 02:00 UTC = 11:00 JST) starts task `orders-reconcile:7`. The job runs `SELECT ... FOR UPDATE` over about 1.18 million rows of the previous day's orders from 02:00:12 to 02:19:48 UTC. Meanwhile orders-api writes (POST /orders, PATCH /orders/{id}) wait out the database lock-wait limit (about 50 s) and return HTTP 500. The release `2026.10.21-1` is not the cause. · label: Likely |
| Weakest link | That the API sessions' lock waits are waits on the job's locks. No database-side lock view was readable (the Aurora lookups returned nothing, and a database session is not allowed). The application log gave only 5 error lines against 339 counted target 5xx in the same minutes. This link is Likely and caps the cause. Every other link is Confirmed on its own query. |
| Impact | 439 target 5xx between 02:01 and 02:19 UTC (11:01–11:19 JST), peak 55/min at 02:04 UTC (11:04 JST). Over since 02:19 UTC; the alarm has been OK since 02:12 UTC. The same morning episode ran on all 15 mornings from 10-07 to 10-21. Share of requests failing: unknown. |
| Severity | SEV2 because both core flows in environment.md (POST /orders and PATCH /orders/{id}) are among the failing routes for about 19 minutes every morning. SEV1 if more than 5% of requests failed, which could not be read. The incident owner decides. |
| Pattern | scheduled · 6 alarm transitions into ALARM at 02:04–02:09 UTC in the 14 days of alarm history. The job's start preceded the onset by 1–2 minutes on 15 of 15 nights, including the two nights whose start slipped (10-14 02:05:02, 10-16 02:01:02) and whose onset slipped with it · Confirmed |
| Recommended action | First, ask the owners of the reconcile job to stop it from holding row locks on live order data for 20 minutes. They could commit in small batches, read without locking, or move the run to a quiet hour. Until that is done, expect the same 19-minute window every morning at about 02:00–02:20 UTC (11:00–11:20 JST) and the same page. Any change goes through `pre-flight` and a separate session; this run changed nothing. |
| Time to cause | About 5 minutes of wall time (simulated clock) from wave 0 to the first Likely, after wave 2. The cause as a whole did not reach Confirmed because of the weakest link. |
| Similar past incidents | No history yet (no `incidents/` directory under the output root). Within the data this is at least the 15th consecutive morning, and the alarm paged 6 times in the 14 days of history (10-08, 10-11, 10-14, 10-16, 10-19, 10-21). A permanent fix is therefore the first follow-up. |

## Impact

- **Symptom.** HTTP 500 from orders-api targets, measured as the ALB target-group `HTTPCode_Target_5XX_Count` (W1-Q5). In the application log sample, the failing routes are POST /orders (insert order_lines) and PATCH /orders/{id} (update orders set status). Each fails after about 50 s with `ER_LOCK_WAIT_TIMEOUT` (W2-Q7). One 502 `ECONNRESET` on a payments call also appears.
- **Window.** 02:01–02:19 UTC (11:01–11:19 JST), peak 55/min at 02:04 UTC (11:04 JST). 439 target 5xx in 01:30–02:40 UTC, against 3 in the previous 70 minutes (W1-Q6) and 459 in the same window a week earlier. The a-week-ago episode ran 02:06–02:24 UTC on 10-14 (W1-Q7). Ongoing: no. The last elevated minute was 02:19 UTC, and the background is about 1 error in some minutes.
- **Alarm.** `orders-api-5xx-high` (target 5xx above 25/min, 2 of 3 datapoints) went to ALARM at 02:04 UTC and back to OK at 02:12 UTC (W0-Q4, W1-Q9).
- **Basis.** Load-balancer target 5xx counts against the baseline (no SLO is named). The counts and timing are Confirmed. The failing share of requests is Assumed: RequestCount, ELB-generated 5xx, unhealthy hosts and latency did not come back from either metric attempt (W1-Q5..Q8, W2-Q8).
- **Affected.** Prod, a single service in one region, customer-facing. The listed core flows are among the failing routes (sampled lines only).
- **Third party in the path.** None known. The payments dependency appeared once as `ECONNRESET`; its owner and status page are not known.

## Causal chain

1. **Trigger.** The EventBridge rule `orders-reconcile-nightly` (`cron(0 2 * * ? *)`, UTC) starts ECS task `orders-reconcile:7` on cluster `prod`. CloudTrail shows `RunTask` at 02:00:02 UTC today, and the task started at 02:00:09 UTC. The same rule fired 15 times from 10-07 to 10-21, at 02:00:02 on 13 nights, 02:01:02 on 10-16 and 02:05:02 on 10-14. · Confirmed · W2-Q1, W2-Q4, W3-Q1, W3-Q2
2. **Mechanism, leg A (the job).** The job logs `mode=SELECT ... FOR UPDATE` at 02:00:11.9, then "locking orders rows created 2026-10-20 (estimated 1,184,000 rows)" at 02:00:12. It commits 1,184,212 rows at 02:19:48 UTC and the task stops at 02:19:52–02:20:14 with exit code 0. The job holds locks for about 19.6 minutes. · Confirmed · W3-Q3, W3-Q2
3. **Mechanism, leg B (the API).** orders-api write requests fail with HTTP 500 and `ER_LOCK_WAIT_TIMEOUT` after 50.0 s. The sample shows 4 lines: POST /orders at 02:01:13, 02:04:05 and 02:10:18, and PATCH /orders/{id} at 02:02:41. The first failing request began waiting at about 02:00:23 UTC, 11 s after the job's lock statement. · Confirmed for the sampled lines · W2-Q7. The sample is 5 error lines against 339 counted target 5xx in the same minutes, so the share of lock waits among all the 5xx is not known.
4. **Mechanism, link A to B.** The API sessions wait on the job's locks. · **Likely** · W3-Q3 + W2-Q7 + the timing below. There is no database-side lock view.
5. **Timing.** The first elevated 5xx minute follows RunTask by 1 minute on 12 nights and 2 minutes on 3 nights (15 of 15). The onset moved with the fire time on 10-14 (RunTask 02:05:02, onset 02:06) and 10-16 (RunTask 02:01:02, onset 02:02). The last elevated minute (02:19) contains the commit at 02:19:48. · Confirmed · W3-Q1, W1-Q5, W1-Q7
6. **Symptom.** Target 5xx of 439 in the window, peaking at 55/min at 02:04 UTC and stopping with the job. The alarm paged at 02:04 and cleared at 02:12 UTC. · Confirmed · W1-Q5, W1-Q9

**Ruled out (falsification query shown).**

| Hypothesis | Why | Query |
|---|---|---|
| Bad deploy: release `2026.10.21-1` (task definition `orders-api:42`) | Old against new, by revision. New, rev 42 (rollout 01:22:07–01:31:40 UTC, 39 min before the first error): the episode ran on 1 of 1 mornings (438 target 5xx in the 02:00 UTC hour). Old, rev 41 (in service from 2026-10-14 03:10:53 UTC until 01:22 today): 6 of 6 mornings (133, 398, 69, 104, 412, 96). The revision before 41: 8 of 8 mornings, 10-07 to 10-14 (88, 421, 61, 117, 386, 74, 52, 455). The 10-14 episode (02:06–02:24 UTC) ended before rev 41 was even registered (03:10:44 UTC). The same failure recurred before the new revision existed. Environment variable and secret names are identical between rev 41 and rev 42; only the image differs. The release notes list an email field, an http client bump (3.4.1) and admin pagination. The diff was not read (gap), so this rests on the split, not on the diff. | W1-Q8, W2-Q3, W2-Q5, W2-Q6 |
| `catalog-sitemap-weekly` (`cron(30 3 ? * SUN *)`) | Fires Sundays at 03:30 UTC, not within 15 minutes of 02:00. Today is a Wednesday, and episodes ran on Wed, Fri and Mon. | W2-Q1 |
| Task churn, placement or stop events | No ECS service event between 01:31:40 UTC and 02:40; 6 of 6 desired tasks running since 01:23. | W1-Q1, W1-Q2 |

**Still open, in rank order.**
1. The chain above (Likely, as capped).
2. `ECONNRESET` (502) on the payments call, possibly tied to the http client bump in the release: **Assumed**. One sampled line, no count per revision.
3. A traffic spike or bot at 02:00: **Assumed**, untested. RequestCount was unreadable. Nothing in the data supports it, because the onset follows the job's start, not a traffic ramp.
4. Why some mornings are about 4 times larger. The 02:00 UTC hour is 386–455 target 5xx on 10-08, 10-11, 10-14, 10-16, 10-19 and 10-21, and 52–133 on the other mornings. This run does not explain it.
5. When the daily episode began. The job's current revision was registered on 2026-09-30, and the metric history read here is 14 days.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| RequestCount, ELB-generated 5xx, unhealthy hosts and TargetResponseTime (p95, p99) returned nothing in both attempts (W1-Q5..Q8, W2-Q8) | The failing share of requests, severity (SEV1 vs SEV2), latency and "ELB vs target 5xx" are `Assumed` or unread | Read those four metrics for 02:00–02:20 UTC in the console, or check the `cloudwatch:GetMetricData` permission |
| Application log is a thin sample: 5 status-5xx lines against 339 counted target 5xx in 01:51–02:11 UTC (W2-Q7 vs W1-Q5) | The share of lock waits among all 5xx is unknown; the mechanism is qualitative | Check the log pipeline (sampling, loss), or run a count of `error_code` for the 02:00 hour |
| Aurora `orders-db`: the `rds` and `elbv2` lookups returned `{}` (W0-Q9, W0-Q10); no metrics, no maintenance or backup window, no lock holder | The job as lock holder is at most `Likely`; the database leg of the chain has no direct evidence | A DBA reads the lock and transaction view for 02:00–02:20 UTC; check `rds:DescribeDBClusters` and `elasticloadbalancing:DescribeTargetGroups` permissions |
| Release diff not read: `gh api …/compare/2026.10.14-2...2026.10.21-1` returned `{}` (W3-Q4); no local clone | The deploy is cleared by the old-against-new split only | Read the compare for the order write path, or add a clone path to environment.md |
| Stopped orders-api tasks (01:25–01:29 UTC) were no longer listable (W1-Q2) | No per-task mechanism evidence for the old revision; the split came from metrics and deploy dates | None (stopped tasks expire after about an hour) |
| Application Auto Scaling returned `{}` for scheduled actions and scaling activities (W1-Q3, W1-Q4) | "No scaling change" is read as none returned, not proof | None needed unless the service is meant to autoscale |
| Alarm history returned 14 days though 30 were asked (W1-Q9) | Recurrence before 10-08 is not read from the alarm | None; the metrics carry the 14-day recurrence |
| Core flows listed with no counter or datasource; no IaC repo; no tracing or error tracker | Per-flow impact comes only from log samples; config as declared is unread | Name counters under `core_flows` and add the IaC repo in environment.md |
| Write capability unknown for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (no simulation row). This is not a finding that the credentials can write. | None on evidence; only a "read-only" statement is withheld | Confirm in chat that the role is read-only, or re-run the simulation |
| `timezone` missing in environment.md (the user gave Asia/Tokyo, UTC+9, in chat) | None now | Add that zone to environment.md |
| Fast mode stopped after wave 3: no hourly history beyond 14 days, no `error_code` counts per revision or per day | When the episode began, the lock-wait share and whether `ECONNRESET` is new are open | Ask for "go deep": a longer hourly metric pull, and an `error_code` by revision count (about 30 GB estimated for 14 days, above the 10 GB ask threshold, so it would ask first) |

## To confirm, a human would…

1. Have a DBA, or an Aurora performance view, look at the lock and transaction details for 02:00–02:20 UTC. If the sessions blocking the orders-api writes belong to the reconcile job's connection, the weakest link is confirmed. If another session holds them, the cause is not this job. This run is not allowed a database session.
2. Read RequestCount and the ELB-side 5xx in the console for 02:00–02:20 UTC to get the failing share of requests. More than 5% would make this a SEV1 under the default scale.
3. Ask the reconcile job's owners what the setting named `RECON_LOCK_MODE` allows (for example a non-locking mode), what changed between task definition revision 6 (2026-08-19) and revision 7 (2026-09-30), and since when the morning episode has existed.
4. Read the compare of releases 2026.10.14-2 and 2026.10.21-1 for anything on the order write path, to close the deploy leg on the diff as well as on the split.
5. Ask the owner of the payments service, and check the log pipeline, about the single `ECONNRESET` and about why the log holds so few of the counted 5xx. A count of `error_code` by revision would show whether the resets are new with revision 42.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | **Permanent fix first (this is at least the 15th consecutive morning).** Change how the nightly reconciliation touches live order data. It should stop holding `SELECT ... FOR UPDATE` row locks on about 1.2 million rows in one roughly 20-minute transaction. Options include taking locks in small batches that commit separately, reading from a consistent snapshot or a replica without locking, or reconciling a copy. The cost is more code and a longer total runtime. A non-locking read can miss concurrent changes unless the job re-checks them, and a replica adds lag. Assess it with `pre-flight` and hand it to `iac-change-execution` or the job's owners in a new session. |
| Fix | Consider moving the job to the hour with the lowest order-write traffic, once request data show whether 02:00 UTC (11:00 JST) is a busy hour. The cost is that reconciliation results arrive later, and that it must avoid the other scheduled jobs (the weekly sitemap rule runs Sundays at 03:30 UTC). It only shifts the window if the job still takes locks. |
| Fix | Consider giving the orders-api write requests a much shorter database lock-wait limit than the current 50 s, with a bounded retry. Callers then get a fast error instead of waiting about a minute. The cost is more visible short errors during ordinary brief locks, and it does not remove the cause. |
| Prevention | The alarm `orders-api-5xx-high` paged on 6 of 15 mornings (a recurring pattern with a known cause). Until the fix lands, add the job's start and end as context on the page, or a runbook link, so the on-call person does not re-investigate each time. Put a check in the job's change process: any change to what it locks needs a staging run beside write traffic. |
| Observability gap | Request count, error rate and latency were unreadable for the incident hour, and the core flows have no counters. Application error lines are a thin sample of the counted 5xx. There is no database lock or wait metric in view. Add per-route request and error counters for checkout and order updates, keep request-level error logging complete, and add a database lock-wait signal and a job start/end marker. |

## Cost

7 metered queries (4 CloudWatch metric reads in wave 1, 1 metric read and 1 Logs Insights query in wave 2, 1 Logs Insights query in wave 3) · 0.48 GB of logs scanned (as reported; an upper bound, plus 61 KB for the job's log) · 22 CloudWatch metric requests · no other metered units; ECS, EventBridge, CloudTrail, IAM and `gh` reads are free · under $0.01 in metered charges (list prices from memory, not re-checked this session)
