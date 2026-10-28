# Investigation: orders-api prod: 5xx on 2026-10-21, 02:01-02:19 UTC, lined up with the nightly reconcile job

Run: orders-api-prod-20261021-0240 · Mode: Fast · Window: 2026-10-21 01:30-02:40 UTC (10:30-11:40 Asia/Tokyo; zone given by the operator)

## TL;DR

| Field | Value |
|---|---|
| Cause | Not the release. The 5xx are database lock-wait timeouts on order writes, and they start and stop with the nightly `orders-reconcile` task (EventBridge rule `orders-reconcile-nightly`, 02:00 UTC = 11:00 Tokyo), which has caused the same spike on every one of the last 15 nights · label: Likely |
| Weakest link | That the reconcile job is what holds the locks the order writes wait on (Likely): the evidence is timing (start, stop and the shifted start on 10-14 and 10-16) plus lock-wait errors in the app logs; there is no database-side lock data and the job's own logs were not read |
| Impact | `POST /orders` and `PATCH /orders/{id}` (both core flows) failed with HTTP 500 after about 50 s lock waits: 439 target 5xx from 02:01 to 02:19 UTC, peak 55 per minute at 02:04. Over: back to baseline since 02:20 UTC (11:20 Tokyo). Failing share of requests unknown |
| Severity | SEV2 because it is a significant, partial, short degradation of customer-facing core flows; SEV1 cannot be shown without a request count (more than 5% failing was neither seen nor ruled out). The incident owner decides |
| Pattern | scheduled · alarm episodes start 02:04-02:09 UTC on six days (10-08, 10-11, 10-14, 10-16, 10-19, 10-21) and the 02:00 UTC hour is elevated on all 14 earlier nights · Confirmed |
| Recommended action | Ask the owner of the nightly reconcile job to look at how the job locks rows and at its batch size and start time, because it is the first suspect (details under Follow-ups). The release 2026.10.21-1 does not need to be rolled back for this symptom |
| Time to cause | not measured (the clock probe printed nothing); first Likely after wave 1, and the cause stayed Likely after wave 3 |
| Similar past incidents | none in `incidents/` (does not exist yet). This is the sixth alarm episode in 14 days, and the 15th night in a row with an elevated 02:00 UTC hour (2026-10-07 to 2026-10-21) |

The permanent fix is the first follow-up, because this repeats every night.

## Impact

- Symptom: HTTP 500 after about 50 seconds with `ER_LOCK_WAIT_TIMEOUT` on `POST /orders` (insert order_lines) and `PATCH /orders/{id}` (update orders set status); one `GET /orders` took 8.1 s with status 200; one 502 `ECONNRESET` on a payments call. Of 442 error lines today (00:00-02:40 UTC), 431 are lock waits (97.5%), 6 resets, 5 upstream timeouts (W3-Q1). Target 5xx: 439 between 01:30 and 02:40 UTC against 3 in the previous 70 minutes (W1-Q2a, W1-Q2b). Confirmed.
- Affected: prod orders-api (6 tasks, all healthy on revision 42, none replaced), customer-facing. Share of requests failing: unknown, because RequestCount came back empty (W1-Q2d). Assumed.
- Start and end: 02:01 UTC (11:01 Tokyo) to 02:19 UTC (11:19 Tokyo); alarm `orders-api-5xx-high` in ALARM 02:04-02:12 UTC. The operator reported it as ongoing; the data says it has ended (no 5xx datapoint 02:20-02:40 UTC; the metric is reported only in minutes with errors). Confirmed.
- Measured with: target 5xx counts against the previous and -7d windows and the app error lines. No SLO is named. A comparable spike a week earlier: 459 in 02:06-02:24 UTC on 2026-10-14 (W1-Q2c).
- Third party in the path: none known. The payments calls are to an internal-looking service; 6 resets today do not matter for this spike.

## Causal chain

1. Trigger: EventBridge rule `orders-reconcile-nightly` (cron(0 2 * * ? *), UTC) starts task `orders-reconcile:7` at 02:00:02 UTC; it runs until 02:20:14 UTC (exit code 0). The job has done this every night, with the image from 2026-09-30. · Confirmed · W1-Q1e, W1-Q5a, W2-Q1a, W2-Q1b, W2-Q2a, W2-Q2b.
2. Mechanism: the job's database work leaves order inserts and status updates waiting about 50 seconds for row locks, until MySQL's lock-wait timeout fires. Error lines show the lock waits (Confirmed, W2-Q5b, W3-Q1b); that the job holds those locks is inferred from timing: the 5xx ramp starts one minute after the job's actual start (02:00:02 -> 02:01; 10-16 02:01:02 -> 02:02; 10-14 02:05:02 -> 02:06) and the last 5xx datapoint (02:19) is one minute before the job ends (02:20:14). · Likely · W1-Q2, W1-Q4, W2-Q2b, W2-Q5b, W3-Q1b.
3. Symptom: HTTP 500 on `POST /orders` and `PATCH /orders/{id}`, 439 target 5xx at a peak of 55 per minute, 02:01-02:19 UTC. · Confirmed · W1-Q2a, W2-Q5b, W3-Q1b.

The cause is capped at Likely by link 2.

Other hypotheses, in rank order:
- Release 2026.10.21-1 (task definition orders-api:42): Ruled out. The same spike happened at the same time on 10-08, 10-11 and 10-14 (the last one, 459 5xx, before the 03:10 UTC deploy of :41), and CloudTrail shows only two orders-api deployments in 14 days (10-14 03:10:53 and 10-21 01:22:07 UTC). The deployment finished 29 minutes before the first 5xx and nothing replaced tasks afterwards. Between :41 and :42 only the image tag differs in the task definition (same variable names, same size; values are deliberately not read). The code diff could not be read, so this rests on timing and recurrence, not on code. · W1-Q2c, W1-Q3, W2-Q1d, W2-Q1e, W2-Q2c, P-Q2c, W1-Q1b.
- Task churn, probe failures, scheduling failure: Ruled out. All 6 tasks created 01:22:31-01:22:51 UTC, healthy, none stopped; no service event after 01:31:40 UTC. · P-Q2c, W1-Q1b, W1-Q1c.
- Payments or upstream timeouts as the cause: Ruled out for this spike (11 of 442 error lines); no baseline day was queried, so they are not called noise. · W3-Q1b.
- Database lock contention or CPU as such: open (Assumed). The lock-wait errors are its symptom, but no database metric could be read. · W2-Q4a, W2-Q4b.
- Traffic spike or bot: open (Assumed). Request count unreadable. · W1-Q2d.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| `/ecs/orders-reconcile` logs not read (one log query per wave; Fast mode has three waves) | nothing shows what the job locks, how long its batches run or whether it logs lock waits; caps the mechanism link at Likely | say "go deep", or read that log group for 02:00-02:20 UTC |
| Aurora `orders-db` metrics returned an empty object and the cluster name comes only from environment.md (W2-Q4) | the database hypothesis can be neither supported nor refuted from the database side | confirm the cluster identifier, then read DatabaseConnections, RowLockTime, Deadlocks and CPU for 02:00-02:20 UTC |
| `GetMetricData` returned an empty object for RequestCount, ELB 5xx, TargetResponseTime, UnHealthyHostCount and ECS CPU/memory (W1-Q2d..f) although `list-metrics` lists them | no failing percentage, no latency, no host-health or saturation data; severity and impact share stay Assumed; traffic and capacity are untested | open the same metrics in the CloudWatch console for 01:30-02:40 UTC, or find out why the call returns an empty object |
| Release diff unreadable (`gh api compare` returned an empty object) | the release is ruled out on timing and recurrence, not on code | read PRs #1182, #1185 and #1187 |
| Write capability for 3 of the 10 fixed actions was not evaluated (the simulation reply lacked ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) | none on the findings; the credentials cannot be called read-only confirmed | read-only check: `aws iam list-attached-role-policies --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, or ask the account owner |
| Application Auto Scaling calls returned an empty object | cannot say whether the service autoscales; low impact (6/6 tasks, no churn) | check auto scaling for the service in the console |
| No IaC repo named in environment.md | IaC history not read; where the schedule is defined is unknown | name the IaC repo in environment.md |
| No business counter named for the two core flows | core-flow impact is seen only through error lines | name a counter |
| Alarm history starts 2026-10-08 and the metric pull 2026-10-07 | cannot say whether the pattern predates 2026-10-07 or the 2026-09-30 image of the job | pull the 5xx count at one-hour Period for about 60 days |
| Clock and git probes printed nothing | the window and run id assume now = 2026-10-21 02:40 UTC; the operator was told | none unless "now" is wrong |

Open items need your input.

## To confirm, a human would…

1. Look at Aurora `orders-db` for 02:00-02:20 UTC on 2026-10-21 (Performance Insights or the engine's lock-wait views) and see whether the sessions blocking the order writes belong to the reconcile job's database user. That would turn link 2 into Confirmed; blockers from another source would refute it.
2. Read the `/ecs/orders-reconcile` logs for the same minutes: batch sizes, what it locks and whether its slow batches line up with the lock waits. Also ask its owner what `RECON_LOCK_MODE` and `RECON_BATCH_SIZE` are set to (this run read names only).
3. Explain why some nights are about four times bigger (421, 386, 455, 398, 412, 438 against 52-133): compare the job's input size per night.
4. Read the request counts per route for 02:00-02:20 UTC to say whether more than 5% of `POST /orders` or `PATCH /orders/{id}` requests failed (that would make it SEV1).
5. Ask the release owner to confirm that #1182, #1185 and #1187 do not touch the order write path.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Have the owner of the nightly reconcile job change how it takes row locks and how big its batches are, so that it no longer blocks order inserts and updates, at the cost of a longer-running job or more database round trips; or, if the job must lock, move its start to the quietest window, at the cost of delaying the reconciliation result and the chance that the new window carries a different load. Assess the choice with `pre-flight` in a separate session. This repeats nightly (15th night in a row, sixth alarm episode in 14 days), so this is the first item |
| Fix | Consider a shorter lock-wait timeout in orders-api so that blocked requests fail fast instead of holding a worker for 50 seconds, at the cost of failing sooner for callers (which would need a retry or a clear error). This reduces the damage; it does not remove the cause |
| Prevention | Make the page for `orders-api-5xx-high` say that the nightly job is running at 02:00-02:20 UTC, or suppress it for the known night-job window until the fix lands, at the cost of a blind spot in that window. Six pages in 14 days at the same time of day are alert fatigue |
| Observability gap | Make request counts, latency, database lock metrics and the job's duration readable together (they came back empty or were not connected), and add a counter for the two core flows, so the next run can state the failing percentage and the lock holder instead of Assumed |

## Cost

17 shell calls (12 evidence calls in waves 1-3, 3 in wave 0, 2 for the profile build) · about 0.31 GB of logs scanned (pro-rated from the result statistics, see the ledger) · 26 CloudWatch metric requests · no X-Ray or other metered units · about 0.002 USD in metered charges at list prices recalled from memory, not checked this session (Logs Insights about 0.005 USD per GB scanned; GetMetricData about 0.01 USD per 1,000 metrics requested)
